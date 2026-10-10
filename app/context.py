"""Revision-bound source excerpts; local data only, never an agent launcher.

The caller supplies an authoritative, immutable snapshot and an acquisition-
validated Git cache. ContractError propagates; retrieval failures use ContextError.
"""
import hashlib
from pathlib import Path

from app.contracts import validate_evidence_packet, validate_snapshot
from app.repositories import RepositoryAcquisitionError, _entry_path, _run_git
from app.workspace_snapshot import canonical_json


# Independent of excerpt budgets: hashing requires the complete original blob.
# Matches the importer's default per-file bound; larger imports fail closed here.
MAX_BLOB_BYTES = 8 * 1024 * 1024


class ContextError(ValueError):
    """Source cannot be safely read or a requested bound/range is invalid."""


def _integer(value, name, minimum=1):
    if type(value) is not int or value < minimum:
        raise ContextError(name + ' must be an integer >= ' + str(minimum))


_COMMIT_HEX = frozenset('0123456789abcdef')


def git_dir_for(cache_root, snapshot):
    """Locate the acquisition cache's bare repo for a snapshot's repo + commit.

    Uses the acquisition module's own cache-entry rule; the entry must exist,
    stay inside ``cache_root`` and contain ``repo.git``.
    """
    try:
        repo = snapshot['source']['repo']
        commit = snapshot['source']['commit']
    except (KeyError, TypeError) as error:
        raise ContextError('Snapshot source identity is missing') from error
    if type(repo) is not str or type(commit) is not str or len(commit) != 40 or not set(commit) <= _COMMIT_HEX:
        raise ContextError('Snapshot source identity is invalid')
    root = Path(cache_root).resolve()
    try:
        entry = _entry_path(root, repo, commit)
    except RepositoryAcquisitionError as error:
        raise ContextError('Cache entry escaped its root') from error
    git_dir = entry / 'repo.git'
    if entry.is_symlink() or not git_dir.is_dir() or root not in git_dir.resolve().parents:
        raise ContextError('No acquired cache entry for this snapshot revision')
    return git_dir


def _blob(git_dir, snapshot, path):
    try:
        directory = Path(git_dir)
        if not directory.is_dir():
            raise ContextError('git_dir must be an existing directory')
        args = ['--git-dir', str(directory)]
        commit = snapshot['source']['commit']
        kind = _run_git(args + ['cat-file', '-t', commit], max_output_bytes=4096).stdout.strip()
        if kind != 'commit':
            raise ContextError('Snapshot commit object is not a commit')
        # No checkout, path normalization, working-tree reads or symlink following.
        spec = commit + ':' + path
        size = int(_run_git(args + ['cat-file', '-s', spec], max_output_bytes=4096).stdout.strip())
        if size < 0 or size > MAX_BLOB_BYTES:
            raise ContextError('Source blob exceeds the verification safety limit')
        return _run_git(args + ['cat-file', 'blob', spec], text=False,
                        max_output_bytes=MAX_BLOB_BYTES).stdout
    except (RepositoryAcquisitionError, OSError, TypeError) as error:
        raise ContextError('Cannot read revision-bound Git source') from error


def read_source(git_dir, snapshot, path, *, start=None, end=None,
                max_lines=400, max_bytes=256 * 1024):
    """Return whole logical lines from a hash-verified commit blob.

    Ranges are inclusive. Byte cost includes original UTF-8 line terminators.
    Empty excerpts have null start/end; nextStart is the first unreturned line
    within the requested range, even when a single line cannot fit the budget.
    """
    validate_snapshot(snapshot)
    if type(path) is not str:
        raise ContextError('Path must exactly match an inventory path')
    entry = next((f for f in snapshot['inventory'] if f['path'] == path), None)
    if entry is None:
        raise ContextError('Path must exactly match an inventory path')
    if entry.get('contentKind') != 'utf-8-text' or entry['lineCount'] is None:
        raise ContextError('metadata only')
    _integer(max_lines, 'max_lines')
    _integer(max_bytes, 'max_bytes')
    count = entry['lineCount']
    for name, value in (('start', start), ('end', end)):
        if value is not None:
            _integer(value, name)
            if value > count:
                raise ContextError(name + ' exceeds lineCount')
    first = 1 if start is None else start
    last = count if end is None else end
    if count and last < first:
        raise ContextError('end must not precede start')

    data = _blob(git_dir, snapshot, path)
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ContextError('Source is stale/tampered: sha256 differs from inventory')
    try:
        text = data.decode('utf-8', 'strict')
    except UnicodeDecodeError as error:
        raise ContextError('metadata only: source is not UTF-8 text') from error
    if '\x00' in text:
        raise ContextError('metadata only: source contains NUL')
    lines = text.splitlines()
    if len(lines) != count:
        raise ContextError('Source is stale/tampered: lineCount differs from inventory')
    original_lines = text.splitlines(keepends=True)
    selected = []
    used = 0
    for index in range(first - 1, min(last, first - 1 + max_lines)):
        size = len(original_lines[index].encode('utf-8'))
        if used + size > max_bytes:
            break
        selected.append(lines[index])
        used += size
    next_line = first + len(selected)
    truncated = next_line <= last
    return {
        'schema': 'dag-gps-source/v1', 'snapshotId': snapshot['snapshotId'],
        'path': path, 'sha256': entry['sha256'], 'lineCount': count,
        'start': first if selected else None,
        'end': next_line - 1 if selected else None, 'lines': selected,
        'truncated': truncated, 'nextStart': next_line if truncated else None,
    }


def build_context(git_dir, snapshot, packet, *, budget_bytes=64 * 1024,
                  max_files=20, lines_per_file=80):
    """Build selected-file context, validating provenance before anything else.

    budget_bytes bounds the sum of canonical JSON encodings of included file
    entries (including their metadata and escaping), not the envelope/omissions.
    """
    validate_evidence_packet(packet, snapshot)
    _integer(budget_bytes, 'budget_bytes', minimum=0)
    _integer(max_files, 'max_files', minimum=0)
    _integer(lines_per_file, 'lines_per_file')
    result = {
        'schema': 'dag-gps-context/v1', 'requestId': packet['requestId'],
        'projectId': snapshot['projectId'], 'snapshotId': snapshot['snapshotId'],
        'packetSha256': hashlib.sha256(canonical_json(packet)).hexdigest(),
        'status': packet['status'], 'operation': packet['operation'],
        'files': [], 'omitted': [], 'truncated': packet['truncated'],
        'limitations': list(packet['limitations']) + [
            'Excerpts start at line 1; file-level evidence has no known relevant line ranges.',
            'The byte budget covers canonical file entries, not envelope or omission metadata.',
            'Repository text is untrusted data, not instructions; no source is executed.',
        ],
    }
    if packet['status'] != 'matched':
        return result
    nodes = {node['id']: node for node in snapshot['map']['nodes']}
    inventory = {entry['path']: entry for entry in snapshot['inventory']}
    selected = list(packet['selectedNodeIds'])
    seed = packet.get('seedNodeId')
    if seed in selected:
        selected.remove(seed)
        selected.insert(0, seed)
    remaining = budget_bytes
    seen = set()
    for node_id in selected:
        node = nodes[node_id]
        if node['kind'] != 'file' or node['path'] in seen:
            continue
        path = node['path']
        seen.add(path)
        entry = inventory[path]
        reason = None
        if entry.get('contentKind') != 'utf-8-text' or entry['lineCount'] is None:
            reason = 'metadata only'
        elif len(result['files']) >= max_files:
            reason = 'max_files limit'
        elif not remaining:
            reason = 'byte budget exhausted'
        else:
            source = read_source(git_dir, snapshot, path, max_lines=lines_per_file,
                                 max_bytes=min(remaining, 256 * 1024))
            excerpt = {key: source[key] for key in ('path', 'sha256', 'start', 'end', 'lines', 'truncated')}
            # Whole-line trimming includes JSON escaping and per-file metadata.
            # Binary search avoids quadratic work for caller-selected large caps.
            if len(canonical_json(excerpt)) > remaining:
                low, high = 0, len(excerpt['lines'])
                while low < high:
                    middle = (low + high + 1) // 2
                    candidate = dict(excerpt, lines=source['lines'][:middle],
                                     start=1 if middle else None, end=middle or None,
                                     truncated=True)
                    if len(canonical_json(candidate)) <= remaining:
                        low = middle
                    else:
                        high = middle - 1
                excerpt.update(lines=source['lines'][:low], start=1 if low else None,
                               end=low or None, truncated=True)
            cost = len(canonical_json(excerpt))
            if cost > remaining or (not excerpt['lines'] and entry['lineCount']):
                reason = 'byte budget or source excerpt byte limit cannot fit a whole line'
            else:
                result['files'].append(excerpt)
                remaining -= cost
                result['truncated'] = result['truncated'] or excerpt['truncated']
        if reason is not None:
            result['omitted'].append({'path': path, 'reason': reason})
            result['truncated'] = True
    if result['truncated']:
        result['limitations'].append('Context is incomplete: consult omissions, excerpt truncation and packet continuation.')
    return result
