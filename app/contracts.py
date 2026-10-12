"""Pure Phase 0 evidence contracts; no importer, server, UI or model calls.

The snapshot supplied to validation must come from the trusted local snapshot
store, not from the request under validation. This checks provenance/structure,
not architectural meaning, actual filesystem bytes, or human consent UI.
"""
import re
import math

PACKET_SCHEMA = 'dag-gps-evidence/v1'
SNAPSHOT_SCHEMA = 'dag-gps-workspace/v1'
MAX_PACKET_BYTES = 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_SNAPSHOT_VALUES = 10000000
MAX_PACKET_VALUES = 1000000
MAX_SELECTED_NODES = 200
MAX_SELECTED_EDGES = 400
MAX_SOURCE_REFS = 200
MAX_WITNESSES = 200
MAX_ALTERNATIVES = 20
STATUSES = {'matched', 'needs-choice', 'no-match', 'no-path', 'unsupported', 'stale'}
OPERATIONS = {'LOCATE', 'UPSTREAM', 'DOWNSTREAM', 'PATH', 'NOT_SURE', 'IMPACT', 'CALLERS', 'CALLEES', 'FLOW', 'TRACE'}
HIGHLIGHTS = {'relevant', 'potential-impact', 'changed', 'agent-inferred'}
EVIDENCE_KINDS = {'observed-source', 'static-import', 'static-boundary', 'curated-source', 'agent-inferred'}
_DIGEST = re.compile(r'[0-9a-f]{64}\Z')
_COMMIT = re.compile(r'[0-9a-f]{40}\Z')


class ContractError(ValueError):
    pass


def default_controls():
    return {'recordQueries': False, 'agentEnabled': False}


def require_agent_consent(value):
    if type(value) is not bool:
        raise ContractError('Agent consent must be an explicit boolean')
    if value is not True:
        raise PermissionError('Explicit agent consent is required')


def _required(obj, key, name):
    if key not in obj:
        raise ContractError(name + ' must be explicitly present, including null when unknown')
    return obj[key]


def _finite_json(value, name, max_values):
    """Check JSON-native data without serializing whole snapshots or doing IO."""
    active = set()
    count = 0

    def text(value):
        try:
            value.encode('utf-8')
        except UnicodeError as error:
            raise ContractError(name + ' contains invalid Unicode') from error

    def walk(item, depth):
        nonlocal count
        count += 1
        if count > max_values or depth > MAX_JSON_DEPTH:
            raise ContractError(name + ' exceeds JSON structure bounds')
        kind = type(item)
        if item is None or kind in (bool, int):
            return
        if kind is float:
            if not math.isfinite(item):
                raise ContractError(name + ' contains nonfinite JSON numbers')
            return
        if kind is str:
            text(item)
            return
        if kind not in (dict, list):
            raise ContractError(name + ' must use JSON-native types')
        identity = id(item)
        if identity in active:
            raise ContractError(name + ' contains circular JSON data')
        active.add(identity)
        try:
            if kind is dict:
                for key, child in item.items():
                    if type(key) is not str:
                        raise ContractError(name + ' object keys must be strings')
                    text(key)
                    walk(child, depth + 1)
            else:
                for child in item:
                    walk(child, depth + 1)
        finally:
            active.remove(identity)

    walk(value, 0)


def _obj(value, name):
    if type(value) is not dict:
        raise ContractError(name + ' must be an object')
    return value


def _text(value, name, limit=512):
    if type(value) is not str or not value or len(value) > limit or any(ord(c) < 32 for c in value):
        raise ContractError(name + ' must be a bounded nonempty string')
    return value


def _enum(value, choices, name):
    _text(value, name)
    if value not in choices:
        raise ContractError('Unknown ' + name)
    return value


def _hash(value, name):
    if type(value) is not str or not _DIGEST.fullmatch(value):
        raise ContractError(name + ' must be a full lowercase SHA-256 digest')
    return value


def _path(value):
    _text(value, 'Source path', 4096)
    if '\\' in value or re.match(r'^[A-Za-z]:', value) or any(p in {'', '.', '..'} for p in value.split('/')):
        raise ContractError('Source path must be a literal relative POSIX path')
    return value


def _array(value, name, limit):
    if type(value) is not list or len(value) > limit:
        raise ContractError(name + ' must be a bounded array')
    return value


def _unique_ids(value, name, limit, known=None):
    values = _array(value, name, limit)
    for node_id in values:
        _text(node_id, name)
    if len(set(values)) != len(values) or (known is not None and not set(values).issubset(known)):
        raise ContractError(name + ' contains duplicate/unknown IDs')
    return values


def _edge(value):
    value = _obj(value, 'Edge')
    return tuple(_text(value.get(key), 'Edge ' + key) for key in ('from', 'to', 'type'))


def _symbol_catalog(extension, files, ids, kinds, edges):
    extension = _obj(extension, 'Symbol graph')
    if extension.get('schema') != 'dag-gps-symbols/v1':
        raise ContractError('Unsupported symbol graph schema')

    def cite(value):
        path = _path(value.get('path'))
        start, end = value.get('start'), value.get('end')
        count = files.get(path, {}).get('lineCount')
        if (type(start) is not int or type(end) is not int or start < 1 or end < start
                or count is None or end > count):
            raise ContractError('Symbol/call range must fit inventoried source')

    symbols = {}
    for n in _array(extension.get('nodes'), 'Symbols', 100000):
        _obj(n, 'Symbol')
        ident = _text(n.get('id'), 'Symbol ID')
        if ident in kinds or ident in symbols or n.get('kind') != 'symbol':
            raise ContractError('Duplicate/invalid symbol node')
        cite(n)
        _text(n.get('qualname'), 'Qualified name')
        symbols[ident] = n
    for ident, n in symbols.items():
        parent = n.get('parentId')
        if parent is not None and (parent not in symbols or symbols[parent]['path'] != n['path']):
            raise ContractError('Unknown symbol parent')
        ids.append(ident)
        kinds[ident] = 'symbol'
    call_edges = {}
    for e in _array(extension.get('edges'), 'Call edges', 1000000):
        a, b, kind = _edge(e)
        if a not in symbols or b not in symbols or kind != 'call' or e.get('confidence') != 'resolved':
            raise ContractError('Call edge must connect resolved symbols')
        if (a, b, kind) in edges:
            raise ContractError('Duplicate call edge')
        sites = _array(e.get('sites'), 'Call sites', 100000)
        if not sites:
            raise ContractError('Call edges require line evidence')
        for site in sites:
            cite(_obj(site, 'Call site'))
            if site['path'] != symbols[a]['path']:
                raise ContractError('Call site must belong to caller file')
        edges.add((a, b, kind))
        call_edges[(a, b, kind)] = e
    for call in _array(extension.get('unresolved'), 'Unresolved calls', 1000000):
        cite(_obj(call, 'Unresolved call'))
        if call.get('confidence') != 'unresolved' or call.get('to') is not None or (call.get('from') is not None and call['from'] not in symbols):
            raise ContractError('Unresolved call cannot guess a target')
    counts = _obj(extension.get('counts'), 'Symbol counts')
    expected = {'symbols': len(symbols), 'resolved': sum(len(e['sites']) for e in call_edges.values()),
                'unresolved': len(extension['unresolved'])}
    if counts != expected or any(type(n) is not int for n in counts.values()):
        raise ContractError('Symbol counts must equal observed definitions and call sites')
    return call_edges


def validate_snapshot(snapshot):
    snapshot = _obj(snapshot, 'Snapshot')
    _finite_json(snapshot, 'Snapshot', MAX_SNAPSHOT_VALUES)
    if snapshot.get('schema') != SNAPSHOT_SCHEMA:
        raise ContractError('Unsupported snapshot schema')
    _text(snapshot.get('projectId'), 'Project ID')
    _text(snapshot.get('snapshotId'), 'Snapshot ID')
    _hash(snapshot.get('mapSha256'), 'Map digest')
    _hash(snapshot.get('scorerSha256'), 'Scorer digest')
    source = _obj(snapshot.get('source'), 'Source identity')
    if source.get('kind') != 'git-commit':
        raise ContractError('Phase 0 supports pinned Git snapshots; live/generic sources need a later contract')
    commit = source.get('commit')
    worktree_id = _required(source, 'worktreeId', 'Source worktree ID')
    if type(commit) is not str or not _COMMIT.fullmatch(commit) or worktree_id is not None:
        raise ContractError('Pinned source requires a full commit and no live worktree identity')
    _text(source.get('repo'), 'Repository identity')
    _hash(source.get('manifestSha256'), 'Source manifest digest')
    _enum(snapshot.get('state'), {'inventory-ready', 'dependency-preview', 'validated-map'}, 'snapshot state')
    grouping = _obj(snapshot.get('grouping'), 'Grouping')
    if type(grouping.get('reviewed')) is not bool:
        raise ContractError('Grouping review must be an explicit boolean')
    _enum(grouping.get('status'), {'proposed', 'reviewed'}, 'grouping status')
    if grouping['reviewed'] != (grouping['status'] == 'reviewed'):
        raise ContractError('Grouping review marker contradicts status')
    if snapshot['state'] == 'validated-map' and not grouping['reviewed']:
        raise ContractError('Unreviewed grouping cannot be a validated map')
    files = {}
    for item in _array(snapshot.get('inventory'), 'Inventory', 100000):
        item = _obj(item, 'Inventory entry')
        path = _path(item.get('path'))
        if path in files:
            raise ContractError('Duplicate inventory path')
        _hash(item.get('sha256'), 'File digest')
        lines = _required(item, 'lineCount', 'Source line count')
        if lines is not None and (type(lines) is not int or lines < 0):
            raise ContractError('Line count must be known nonnegative integer or null')
        files[path] = item
    graph = _obj(snapshot.get('map'), 'Map')
    meta = _obj(graph.get('meta'), 'Map metadata')
    if meta.get('snapshot_commit') != source['commit'] or meta.get('repo') != source['repo']:
        raise ContractError('Map source identity differs from snapshot identity')
    nodes = _array(graph.get('nodes'), 'Map nodes', 100000)
    ids = []
    for node in nodes:
        node = _obj(node, 'Map node')
        ids.append(_text(node.get('id'), 'Node ID'))
        _enum(node.get('kind'), {'file', 'layer'}, 'code-map node kind')
        if node['kind'] == 'file' and _path(node.get('path')) not in files:
            raise ContractError('File node must reference inventoried source')
    if len(ids) != len(set(ids)):
        raise ContractError('Duplicate map node ID')
    kinds = {node['id']: node['kind'] for node in nodes}
    for node in nodes:
        if node['kind'] == 'file':
            layer = _text(node.get('layer'), 'File layer ID')
            if kinds.get(layer) != 'layer':
                raise ContractError('File ownership must reference a known layer')
    edges = set()
    for field in ('edges', 'file_edges'):
        for value in _array(graph.get(field), field, 1000000):
            a, b, kind = _edge(value)
            if a not in kinds or b not in kinds or kinds[a] != kinds[b]:
                raise ContractError('Dangling or mixed-kind edge')
            if (field == 'edges' and kinds[a] != 'layer') or (field == 'file_edges' and kinds[a] != 'file'):
                raise ContractError('Edge is in the wrong graph scope')
            if (a, b, kind) in edges:
                raise ContractError('Duplicate typed graph edge')
            edges.add((a, b, kind))
    call_edges = _symbol_catalog(graph['symbol_graph'], files, ids, kinds, edges) if 'symbol_graph' in graph else {}
    # Legitimate directed cycles remain data, not silently deleted links.
    return {'nodeIds': set(ids), 'nodeKinds': kinds, 'edges': edges, 'files': files, 'callEdges': call_edges}


def validate_evidence_packet(packet, snapshot):
    import json
    packet = _obj(packet, 'Evidence packet')
    _finite_json(packet, 'Evidence packet', MAX_PACKET_VALUES)
    try:
        encoded = json.dumps(packet, ensure_ascii=False, allow_nan=False).encode('utf-8')
    except (TypeError, ValueError, RecursionError) as error:
        raise ContractError('Packet must be finite JSON data') from error
    if len(encoded) > MAX_PACKET_BYTES:
        raise ContractError('Packet exceeds byte limit')
    graph = validate_snapshot(snapshot)
    def check_call(edge):
        if edge.get('type') == 'call' and edge != graph['callEdges'].get(_edge(edge)):
            raise ContractError('Call evidence differs from observed call sites')
    if packet.get('schema') != PACKET_SCHEMA:
        raise ContractError('Unsupported evidence schema')
    if packet.get('manifestSha256') != snapshot['source']['manifestSha256']:
        raise ContractError('Evidence source manifest differs from snapshot identity')
    _text(packet.get('requestId'), 'Request ID')
    for field in ('projectId', 'snapshotId', 'mapSha256', 'scorerSha256'):
        if packet.get(field) != snapshot[field]:
            raise ContractError('Evidence provenance differs: ' + field)
    _enum(packet.get('status'), STATUSES, 'query status')
    _enum(packet.get('operation'), OPERATIONS, 'operation')
    selected = _unique_ids(packet.get('selectedNodeIds'), 'Selected nodes', MAX_SELECTED_NODES, graph['nodeIds'])
    if 'unresolvedCalls' in packet or 'unresolvedCallCount' in packet:
        expected = [c for c in snapshot['map'].get('symbol_graph', {}).get('unresolved', []) if c.get('from') in selected]
        if packet.get('unresolvedCalls') != expected[:100] or type(packet.get('unresolvedCallCount')) is not int or packet['unresolvedCallCount'] != len(expected):
            raise ContractError('Unresolved call evidence must match the selected symbols')
    selected_edges = _array(packet.get('selectedEdges'), 'Selected edges', MAX_SELECTED_EDGES)
    edge_keys = [_edge(edge) for edge in selected_edges]
    if len(set(edge_keys)) != len(edge_keys):
        raise ContractError('Duplicate selected edge')
    for a, b, kind in edge_keys:
        if (a, b, kind) not in graph['edges'] or a not in selected or b not in selected or kind == 'realtime':
            raise ContractError('Selected edge must be an observed traversal edge between selected nodes')
    for edge in selected_edges:
        check_call(edge)
    witnesses = _array(packet.get('witnesses'), 'Witnesses', MAX_WITNESSES)
    for witness in witnesses:
        witness = _obj(witness, 'Witness')
        chain = _unique_ids(witness.get('nodeIds'), 'Witness nodes', MAX_SELECTED_NODES, graph['nodeIds'])
        links = _array(witness.get('edges'), 'Witness edges', MAX_SELECTED_EDGES)
        if not chain or len(links) != len(chain) - 1:
            raise ContractError('Witness must contain a contiguous directed chain')
        for i, link in enumerate(links):
            check_call(link)
            a, b, kind = _edge(link)
            if (a, b) != (chain[i], chain[i + 1]) or (a, b, kind) not in graph['edges'] or kind == 'realtime':
                raise ContractError('Witness contains an invented/reversed traversal edge')
    alternatives = _array(packet.get('alternatives'), 'Alternatives', MAX_ALTERNATIVES)
    alternative_ids = []
    for alternative in alternatives:
        alternative = _obj(alternative, 'Alternative')
        alternative_ids.append(alternative.get('nodeId'))
        _text(alternative.get('reason'), 'Alternative reason', 2048)
    _unique_ids(alternative_ids, 'Alternative IDs', MAX_ALTERNATIVES, graph['nodeIds'])
    status = packet['status']
    if status == 'matched' and not selected:
        raise ContractError('Matched result needs a selected known node')
    if status in {'needs-choice', 'no-match', 'stale'} and (selected or selected_edges or witnesses):
        raise ContractError('Uncertain/stale result cannot highlight a guessed route')
    if status == 'no-path' and (packet['operation'] not in {'PATH', 'FLOW'} or selected_edges or witnesses):
        raise ContractError('No-path cannot contain a claimed route')
    highlight = packet.get('highlightState')
    _enum(highlight, HIGHLIGHTS, 'highlight semantics')
    if highlight == 'potential-impact':
        if status != 'matched' or packet['operation'] not in {'IMPACT', 'DOWNSTREAM'}:
            raise ContractError('Potential impact requires a matched impact/dependent operation')
        seed = _text(packet.get('seedNodeId'), 'Impact query seed')
        if seed not in selected or (packet['operation'] == 'IMPACT' and graph['nodeKinds'].get(seed) != 'file'):
            raise ContractError('Impact query seed must be known, selected and appropriate to the operation')
        consumers = set(selected) - {seed}
        if not consumers:
            raise ContractError('A seed-only location is not witnessed potential impact')
        supported = {w['nodeIds'][0] for w in witnesses if w['edges'] and w['nodeIds'][-1] == seed}
        if not consumers.issubset(supported):
            raise ContractError('Each potential-impact selection needs a directed witness ending at the query seed')
    if highlight == 'changed':
        changes = _obj(snapshot.get('changes'), 'Observed snapshot changes')
        _text(changes.get('baselineSnapshotId'), 'Observed baseline snapshot ID')
        if packet.get('baselineSnapshotId') != changes.get('baselineSnapshotId'):
            raise ContractError('Changed highlights require an explicit observed baseline')
        changed = _unique_ids(changes.get('changedNodeIds'), 'Changed nodes', 100000, graph['nodeIds'])
        if not set(selected).issubset(changed):
            raise ContractError('Relevant/affected nodes are not automatically actually changed')
    for ref in _array(packet.get('sourceRefs'), 'Source references', MAX_SOURCE_REFS):
        ref = _obj(ref, 'Source reference')
        path = _path(ref.get('path'))
        _enum(ref.get('evidenceKind'), EVIDENCE_KINDS, 'evidence kind')
        file = graph['files'].get(path)
        if (file is None or ref.get('snapshotId') != snapshot['snapshotId']
                or ref.get('sha256') != file['sha256']):
            raise ContractError('Source reference must match inventoried revision/hash/evidence kind')
        start = _required(ref, 'start', 'Citation start')
        end = _required(ref, 'end', 'Citation end')
        if start is None and end is None:
            continue
        count = file.get('lineCount')
        if (type(start) is not int or type(end) is not int or start < 1 or end < start
                or count is None or end > count):
            raise ContractError('Citation range must be known, inclusive and within source')
    truncated = packet.get('truncated')
    if type(truncated) is not bool:
        raise ContractError('Truncation must be explicit')
    continuation = _required(packet, 'continuation', 'Continuation')
    if truncated:
        _text(continuation, 'Continuation', 1024)
    elif continuation is not None:
        raise ContractError('Complete result cannot carry hidden continuation')
    limitations = _array(packet.get('limitations'), 'Limitations', 100)
    for limitation in limitations:
        _text(limitation, 'Limitation', 2048)
    if status == 'unsupported' and not limitations:
        raise ContractError('Unsupported requests must disclose a limitation, not claim a complete answer')
    return packet
