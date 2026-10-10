"""Transport-neutral local agent tools; repository and agent text is untrusted data.

Only submit_explanation writes, exclusively to the separate explanation store.
No model invocation, network acquisition, shell, or imported-code execution.
"""
import hashlib
import json
from pathlib import Path
import re

from app.context import build_context, git_dir_for, read_source
from app.explanation_store import store_explanation
from app.query_worker import QueryWorker, QueryWorkerError
from app.server import ApiError, WorkspaceStore

MAX_REQUEST_BYTES = 1024 * 1024
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
TOOLS = frozenset(('list_projects', 'find_nodes', 'get_dependencies',
                   'get_dependents', 'find_path', 'get_source', 'get_context',
                   'submit_explanation'))
_PROJECT = re.compile(r'p-[0-9a-f]{20}\Z')
_SNAPSHOT = re.compile(r'[0-9a-f]{64}\Z')
_CONTINUATION = re.compile(r'offset:[0-9]{1,12}\Z')


class BridgeError(ValueError):
    """Invalid or unsupported tool input."""


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False,
                      sort_keys=True, separators=(',', ':')).encode('utf-8')


def _fields(value, required, optional=()):
    if type(value) is not dict or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise BridgeError('Missing or unknown fields')


def _text(value, name, limit):
    if (type(value) is not str or not value or len(value) > limit
            or any(ord(c) < 32 or ord(c) == 127 for c in value)):
        raise BridgeError('Invalid ' + name)
    value.encode('utf-8')
    return value


def _query_request(args, snapshot_id, require_id=False):
    required = {'query', 'requestId'} if require_id else {'query'}
    _fields(args, required, {'continuation', 'chosenNodeId'})
    query = _text(args['query'], 'query', 4096)
    request = {'query': query, 'snapshotId': snapshot_id}
    if 'continuation' in args:
        continuation = args['continuation']
        if type(continuation) is not str or not _CONTINUATION.fullmatch(continuation):
            raise BridgeError('Invalid continuation')
        request['continuation'] = continuation
    if 'chosenNodeId' in args:
        request['chosenNodeId'] = _text(args['chosenNodeId'], 'chosenNodeId', 4096)
    request['requestId'] = (_text(args['requestId'], 'requestId', 200) if require_id
                            else 'agent-' + hashlib.sha256(_json_bytes(request)).hexdigest())
    return request


class AgentBridge:
    """Call .call(request) for a bounded {ok, result|error} JSON-native reply.

    ROOT is a trusted local workspace, not an agent-controlled request field.
    The one-shot CLI owns its QueryWorker, closed after every query.
    """
    def __init__(self, root):
        self.root = Path(root)

    def call(self, request):
        try:
            # Also bound requests from non-CLI transports, and detach caller data.
            encoded = _json_bytes(request)
            if len(encoded) > MAX_REQUEST_BYTES:
                raise BridgeError('Request exceeds 1 MiB')
            request = json.loads(encoded)
            result = self._dispatch(request)
            response = {'ok': True, 'result': result}
            if len(_json_bytes(response)) + 1 > MAX_RESPONSE_BYTES:
                raise BridgeError('Response exceeds 4 MiB')
            return response
        except (ValueError, TypeError, RecursionError, OverflowError, OSError,
                ApiError, QueryWorkerError) as error:
            return {'ok': False, 'error': str(error)[:500] or 'Invalid request'}

    def _dispatch(self, request):
        _fields(request, {'tool'}, {'projectId', 'snapshotId', 'args'})
        tool = request['tool']
        if type(tool) is not str or tool not in TOOLS:
            raise BridgeError('Unknown tool')
        args = request.get('args', {})
        if type(args) is not dict:
            raise BridgeError('args must be an object')
        # WorkspaceStore initializes directories: require them to exist so query
        # consumers do not create workspaces merely by listing or reading them.
        if not all((self.root / name).is_dir() for name in ('projects', 'git-cache')):
            raise BridgeError('Workspace does not exist')
        store = WorkspaceStore(self.root)
        if tool == 'list_projects':
            _fields(request, {'tool'}, {'args'})
            _fields(args, set())
            return store.projects()
        for key, pattern in (('projectId', _PROJECT), ('snapshotId', _SNAPSHOT)):
            if type(request.get(key)) is not str or not pattern.fullmatch(request[key]):
                raise BridgeError('Invalid ' + key)
        snapshot_path, snapshot = store.snapshot(request['projectId'], request['snapshotId'])
        if tool == 'get_source':
            _fields(args, {'path'}, {'start', 'end'})
            _text(args['path'], 'path', 4096)
            for key in ('start', 'end'):
                if key in args and type(args[key]) is not int:
                    raise BridgeError('Invalid ' + key)
            return read_source(git_dir_for(self.root / 'git-cache', snapshot), snapshot, **args)
        paths = {}
        if tool in ('get_dependencies', 'get_dependents', 'find_path'):
            keys = {'from', 'to'} if tool == 'find_path' else {'path'}
            _fields(args, keys)
            paths = {node['path']: node['id'] for node in snapshot['map']['nodes'] if node['kind'] == 'file'}
            for key in keys:
                if _text(args[key], key, 4096) not in paths:
                    raise BridgeError('Unknown file node path')
            if tool == 'find_path':
                query = 'path from ' + args['from'] + ' to ' + args['to']
            else:
                query = ('dependencies of ' if tool == 'get_dependencies' else 'what depends on ') + args['path']
            query_request = _query_request({'query': query}, snapshot['snapshotId'])
        elif tool == 'submit_explanation':
            _fields(args, {'request', 'explanation'}, {'useContext'})
            if 'useContext' in args and type(args['useContext']) is not bool:
                raise BridgeError('useContext must be a boolean')
            query_request = _query_request(args['request'], snapshot['snapshotId'], require_id=True)
        else:
            query_request = _query_request(args, snapshot['snapshotId'])
        with QueryWorker(snapshot_path, snapshot) as worker:
            packet = worker.query(query_request)
        if tool in ('get_dependencies', 'get_dependents') and packet.get('seedNodeId') != paths[args['path']]:
            raise BridgeError('Query grammar cannot resolve this exact file path')
        if tool == 'find_path':
            selected = packet['selectedNodeIds']
            if (packet['operation'] != 'PATH' or not selected
                    or selected[0] != paths[args['from']] or selected[-1] != paths[args['to']]):
                raise BridgeError('Query grammar cannot resolve these exact file paths')
        if tool == 'get_context' or (tool == 'submit_explanation' and args.get('useContext', False)):
            context = build_context(git_dir_for(self.root / 'git-cache', snapshot), snapshot, packet)
        else:
            context = None
        if tool == 'get_context':
            return {'packet': packet, 'context': context}
        if tool == 'submit_explanation':
            # Never accept a supplied packet/context. Storage validates digest,
            # revision, request identity, citations and optional context file set.
            return store_explanation(self.root, snapshot, packet, args['explanation'], context=context)
        return packet
