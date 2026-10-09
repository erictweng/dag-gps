"""Bounded immutable repository inventory and provisional dependency previews.

Imported Git objects are read as data from an acquisition-validated bare repository.
This module never checks out or executes imported source, hooks, dependencies, or
repository commands.  Preview grouping is path-only and is never marked reviewed.
"""
from __future__ import annotations

import collections
import hashlib
import html
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from typing import Any, Callable, Mapping, Optional

from app.repositories import (
    RepositoryAcquisitionError,
    _cancelled,
    _run_git,
    _validate_entry,
)


INVENTORY_SCHEMA = 'dag-gps-inventory/v1'
PREVIEW_SCHEMA = 'dag-gps-dependency-preview/v1'
RECEIPT_SCHEMA = 'dag-gps-preview-publication/v1'
# Ownership receipts hold fixed fields, two <=4 KiB strings and digests; anything
# larger is malformed and is rejected from lstat size before it is opened.
MAX_RECEIPT_BYTES = 64 * 1024
EXTRACTOR_VERSION = 'dag-gps-static-v2-workspace-1'
_SUPPORTED_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs', '.py', '.sql'}
_EXCLUDED_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'vendor',
                  'dist', 'artifacts', 'build', '.next'}
_DEFAULT_LIMITS = {
    'timeout_seconds': 60.0,
    'max_members': 20000,
    'max_expanded_bytes': 256 * 1024 * 1024,
    'max_file_bytes': 8 * 1024 * 1024,
    'max_process_output_bytes': 4 * 1024 * 1024,
    'max_graph_output_bytes': 16 * 1024 * 1024,
    'max_tree_output_bytes': 32 * 1024 * 1024,
}
_COMMIT = re.compile(r'[0-9a-f]{40}\Z')
_SHA256 = re.compile(r'[0-9a-f]{64}\Z')
_OBJECT = re.compile(br'[0-9a-f]{40}\Z')
_REQUIRED_OUTPUTS = frozenset({'inventory.json', 'preview.json', 'index.html'})
_PUBLICATION_FILES = _REQUIRED_OUTPUTS | {'receipt.json'}
_PRODUCER_FILES = (
    'app/snapshots.py',
    'app/repositories.py',
    'scripts/import_graph.py',
    'scripts/python_static.py',
    'scripts/build_map.py',
    'scripts/onboarding.py',
)
_WINDOWS_RESERVED = re.compile(r'(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?\Z', re.I)


class SnapshotError(RuntimeError):
    """Inventory, extraction, validation, or publication failed safely."""


class SnapshotCancelled(SnapshotError):
    pass


def _notify(progress: Optional[Callable[[dict[str, Any]], None]], stage: str, **data: Any) -> None:
    if progress is not None:
        progress({'stage': stage, **data})


def _limits(values: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    result = dict(_DEFAULT_LIMITS)
    if values is not None:
        if type(values) is not dict or set(values) - set(result):
            raise ValueError('Unknown workspace snapshot limit')
        result.update(values)
    timeout = result['timeout_seconds']
    if type(timeout) not in (int, float) or isinstance(timeout, bool) or timeout <= 0 or timeout > 600:
        raise ValueError('timeout_seconds must be between 0 and 600')
    for key in result:
        if key == 'timeout_seconds':
            continue
        if type(result[key]) is not int or result[key] < 1:
            raise ValueError(key + ' must be a positive integer')
    return result


def _safe_path(value: str) -> str:
    if (not value or len(value) > 4096 or value != unicodedata.normalize('NFC', value)
            or '\\' in value or re.match(r'^[A-Za-z]:', value)
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        raise SnapshotError('Git tree contains an unsafe or ambiguous path')
    parts = value.split('/')
    if any(part in {'', '.', '..'} for part in parts) or PurePosixPath(value).is_absolute():
        raise SnapshotError('Git tree contains an unsafe or traversing path')
    for part in parts:
        portable = unicodedata.normalize('NFC', part).casefold().rstrip(' .')
        if portable != unicodedata.normalize('NFC', part).casefold() or not portable:
            raise SnapshotError('Git tree contains a non-portable trailing dot or space')
        if _WINDOWS_RESERVED.fullmatch(portable):
            raise SnapshotError('Git tree contains a reserved portable path component')
    return value


def _portable_key(value: str) -> tuple[str, ...]:
    return tuple(unicodedata.normalize('NFC', part).casefold().rstrip(' .')
                 for part in value.split('/'))


def _parse_tree(raw: bytes, max_members: int) -> list[dict[str, Any]]:
    """Parse ``git ls-tree -rz --long`` bytes without repairing hostile names."""
    if type(raw) is not bytes:
        raise SnapshotError('Git tree listing must be bytes')
    records = []
    exact = set()
    portable = set()
    for item in raw.split(b'\0'):
        if not item:
            continue
        if len(records) >= max_members:
            raise SnapshotError('Git tree member limit exceeded')
        try:
            header, encoded_path = item.split(b'\t', 1)
            mode, kind, object_id, size_raw = header.split(b' ', 3)
            path = encoded_path.decode('utf-8', 'strict')
        except (ValueError, UnicodeError) as error:
            raise SnapshotError('Git tree contains malformed or non-UTF-8 metadata') from error
        path = _safe_path(path)
        key = _portable_key(path)
        if path in exact:
            raise SnapshotError('Duplicate Git tree path')
        if key in portable:
            raise SnapshotError('Git tree contains portable-name collisions')
        exact.add(path); portable.add(key)
        if kind not in {b'blob', b'commit'} or not _OBJECT.fullmatch(object_id):
            raise SnapshotError('Git tree contains an unsupported object')
        if size_raw == b'-':
            size = None
        else:
            try:
                size = int(size_raw)
            except ValueError as error:
                raise SnapshotError('Git tree contains an invalid blob size') from error
            if size < 0:
                raise SnapshotError('Git tree contains an invalid blob size')
        records.append({'path': path, 'mode': mode.decode('ascii'), 'kind': kind.decode('ascii'),
                        'object': object_id.decode('ascii'), 'size': size})
    return records


def _run_trusted(command: list[str], *, timeout: float, cancel: Any,
                 max_output_bytes: int, bounded_path: Optional[Path] = None,
                 max_bounded_bytes: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a shipped parser with bounded output/deadline and process-group cleanup."""
    if (bounded_path is None) != (max_bounded_bytes is None):
        raise ValueError('bounded_path and max_bounded_bytes must be provided together')
    env = {key: os.environ[key] for key in ('TMPDIR', 'LANG', 'LC_ALL', 'LC_CTYPE') if key in os.environ}
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=False, env=env,
                               start_new_session=True, shell=False)
    started = time.monotonic()
    while True:
        if _cancelled(cancel):
            _terminate(process)
            raise SnapshotCancelled('Workspace snapshot cancelled')
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0:
            _terminate(process)
            raise SnapshotError('Static extraction exceeded its deadline')
        if bounded_path is not None:
            assert max_bounded_bytes is not None
            try:
                info = bounded_path.lstat()
                if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                        or info.st_size > max_bounded_bytes):
                    _terminate(process)
                    raise SnapshotError('Static extractor graph output exceeded its limit')
            except FileNotFoundError:
                pass
        try:
            stdout, stderr = process.communicate(timeout=min(0.05, remaining))
            break
        except subprocess.TimeoutExpired as error:
            observed = sum(len(value or b'') for value in (error.output, error.stderr))
            if observed > max_output_bytes:
                _terminate(process)
                raise SnapshotError('Static extraction output exceeded its limit')
    if len(stdout) + len(stderr) > max_output_bytes:
        raise SnapshotError('Static extraction output exceeded its limit')
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if result.returncode:
        detail = stderr.decode('utf-8', 'replace').strip().replace('\n', ' ')[:500]
        raise SnapshotError('Trusted static extractor failed' + (': ' + detail if detail else ''))
    return result


def _terminate(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=0.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait()
    process.communicate()


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False,
                       separators=(',', ':')) + '\n').encode('utf-8')


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _producer_manifest() -> dict[str, Any]:
    """Hash the checked-in Python producers that determine inventory/preview bytes."""
    root = Path(__file__).resolve().parents[1]
    files = {}
    for relative in _PRODUCER_FILES:
        path = root / relative
        try:
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise SnapshotError('Workspace producer is not a standalone regular file')
            data = path.read_bytes()
        except OSError as error:
            raise SnapshotError('Unable to fingerprint workspace producer bytes') from error
        files[relative] = _sha(data)
    return {'schema': 'dag-gps-preview-producer/v1', 'files': files}


def _source_included(path: str) -> bool:
    return (Path(path).suffix.lower() in _SUPPORTED_EXTENSIONS
            and not (set(path.split('/')[:-1]) & _EXCLUDED_DIRS))


def _validated_acquisition(acquisition: Mapping[str, Any], bounds: Mapping[str, Any], cancel: Any) -> tuple[Path, str, str, str]:
    if type(acquisition) is not dict:
        raise SnapshotError('Acquisition result is required')
    url, repo_id, commit, raw_git_dir = (acquisition.get(key) for key in ('url', 'repo_id', 'commit', 'git_dir'))
    if not all(type(value) is str for value in (url, repo_id, commit, raw_git_dir)) or not _COMMIT.fullmatch(commit):
        raise SnapshotError('Acquisition result has invalid source identity')
    git_dir = Path(raw_git_dir)
    entry = git_dir.parent
    try:
        checked = _validate_entry(entry, repo_id=repo_id, url=url, commit=commit,
                                  timeout=float(bounds['timeout_seconds']), cancel=cancel,
                                  allow_file_protocol=False,
                                  max_output_bytes=bounds['max_process_output_bytes'])
    except RepositoryAcquisitionError as error:
        # Synthetic acquisition caches are valid bare objects too, but their metadata
        # was acquired with file transport. Validation itself performs no transport.
        try:
            checked = _validate_entry(entry, repo_id=repo_id, url=url, commit=commit,
                                      timeout=float(bounds['timeout_seconds']), cancel=cancel,
                                      allow_file_protocol=True,
                                      max_output_bytes=bounds['max_process_output_bytes'])
        except RepositoryAcquisitionError as final:
            raise SnapshotError('Acquired repository cache is no longer valid') from final
    if checked.resolve() != git_dir.resolve():
        raise SnapshotError('Acquisition Git directory identity changed')
    return checked, url, repo_id, commit


def _inventory(git_dir: Path, url: str, repo_id: str, commit: str,
               bounds: Mapping[str, Any], cancel: Any,
               staging: Path) -> tuple[dict[str, Any], list[str]]:
    try:
        listing = _run_git(['--git-dir', str(git_dir), 'ls-tree', '-rz', '--long', commit],
                           text=False, timeout=float(bounds['timeout_seconds']), cancel=cancel,
                           max_output_bytes=bounds['max_tree_output_bytes']).stdout
    except RepositoryAcquisitionError as error:
        raise SnapshotError('Unable to read authoritative Git tree') from error
    records = _parse_tree(listing, bounds['max_members'])
    expanded = 0
    for record in records:
        mode, kind, size = record['mode'], record['kind'], record['size']
        if mode == '120000':
            raise SnapshotError('Git tree contains a symbolic link; targets are never followed')
        if mode == '160000' or kind == 'commit':
            raise SnapshotError('Git tree contains an unsupported submodule')
        if mode not in {'100644', '100755'} or kind != 'blob' or size is None:
            raise SnapshotError('Git tree contains an unsupported special member')
        if size > bounds['max_file_bytes']:
            raise SnapshotError('Git tree per-file byte limit exceeded')
        expanded += size
        if expanded > bounds['max_expanded_bytes']:
            raise SnapshotError('Git tree expanded byte limit exceeded')

    source_root = staging / 'source-data'
    source_root.mkdir()
    files = []
    source_paths = []
    for record in records:
        if _cancelled(cancel):
            raise SnapshotCancelled('Workspace snapshot cancelled')
        try:
            data = _run_git(['--git-dir', str(git_dir), 'cat-file', 'blob', record['object']],
                            text=False, timeout=float(bounds['timeout_seconds']), cancel=cancel,
                            max_output_bytes=bounds['max_file_bytes'] + 1024).stdout
        except RepositoryAcquisitionError as error:
            raise SnapshotError('Unable to read authoritative Git blob') from error
        if len(data) != record['size']:
            raise SnapshotError('Git blob size differs from authoritative tree')
        target = source_root.joinpath(*record['path'].split('/'))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise SnapshotError('Duplicate materialized source path')
        target.write_bytes(data)
        try:
            text = data.decode('utf-8', 'strict')
            is_text = '\x00' not in text
        except UnicodeDecodeError:
            text = ''
            is_text = False
        supported = _source_included(record['path'])
        status = 'included' if supported and is_text else 'unsupported'
        reason = (None if status == 'included' else
                  'Binary/non-UTF-8 content is inventoried but not parsed.' if not is_text else
                  'File type or excluded directory is outside documented static extraction scope.')
        if supported and is_text:
            source_paths.append(record['path'])
        files.append({
            'path': record['path'], 'bytes': len(data), 'sha256': _sha(data),
            'gitMode': record['mode'], 'contentKind': 'utf-8-text' if is_text else 'binary',
            'lineCount': len(text.splitlines()) if is_text else None,
            'extraction': {'status': status, 'reason': reason},
        })
    manifest = [{'path': item['path'], 'bytes': item['bytes'], 'sha256': item['sha256']}
                for item in files]
    inventory = {
        'schema': INVENTORY_SCHEMA,
        'source': {'kind': 'git-commit', 'url': url, 'repo': repo_id, 'commit': commit},
        'manifestSha256': _sha(_canonical(manifest)),
        'counts': {'files': len(files), 'bytes': expanded,
                   'text': sum(item['contentKind'] == 'utf-8-text' for item in files),
                   'binary': sum(item['contentKind'] == 'binary' for item in files),
                   'extractionIncluded': len(source_paths),
                   'extractionUnsupported': len(files) - len(source_paths)},
        'limits': dict(bounds), 'files': files,
        'limitations': [
            'Authoritative committed regular files are inventoried from Git tree/blob objects; links, submodules and special members reject the snapshot.',
            'Unsupported and binary files remain visible but receive no fabricated dependency links.',
            'Inventory success is independent of static dependency extraction completeness.',
        ],
    }
    return inventory, source_paths


def _extract(source_root: Path, source_paths: list[str], options: Mapping[str, Any],
             bounds: Mapping[str, Any], cancel: Any, staging: Path) -> tuple[dict[str, Any], list[str]]:
    requested = options.get('tops')
    if requested is None:
        tops = sorted({path.split('/', 1)[0] for path in source_paths})
    else:
        if (type(requested) is not list or not requested or len(requested) > 1000
                or any(type(value) is not str or not value or value.startswith('-')
                       or value not in {path.split('/', 1)[0] for path in source_paths}
                       for value in requested)
                or len(set(requested)) != len(requested)):
            raise ValueError('extractor tops must be unique observed top-level source paths')
        tops = list(requested)
    graph_path = staging / 'extractor.json'
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'import_graph.py'
    _run_trusted([sys.executable, str(script), str(source_root), str(graph_path), *tops],
                 timeout=float(bounds['timeout_seconds']), cancel=cancel,
                 max_output_bytes=bounds['max_process_output_bytes'],
                 bounded_path=graph_path,
                 max_bounded_bytes=bounds['max_graph_output_bytes'])
    try:
        info = graph_path.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                or info.st_size > bounds['max_graph_output_bytes']):
            raise SnapshotError('Static extractor graph output exceeded its limit')
        graph_bytes = graph_path.read_bytes()
        if len(graph_bytes) > bounds['max_graph_output_bytes']:
            raise SnapshotError('Static extractor graph output exceeded its limit')
        graph = json.loads(graph_bytes.decode('utf-8'))
    except (OSError, ValueError, UnicodeError) as error:
        raise SnapshotError('Static extractor emitted invalid JSON') from error
    if type(graph) is not dict:
        raise SnapshotError('Static extractor emitted invalid graph')
    return graph, tops


def _modules():
    scripts = str(Path(__file__).resolve().parents[1] / 'scripts')
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import build_map  # type: ignore
    import onboarding  # type: ignore
    return build_map, onboarding


def _preview(inventory: dict[str, Any], source_paths: list[str], graph: dict[str, Any],
             tops: list[str], options: Mapping[str, Any], snapshot_id: str) -> dict[str, Any]:
    build_map, onboarding = _modules()
    groups = onboarding.group_files(source_paths)
    layer_of, unmapped, duplicate = build_map.assign_layers(source_paths, groups)
    import_pairs = [tuple(value) for value in graph.get('edges', [])] + [tuple(value) for value in graph.get('pyedges', [])]
    routes = [path for path in source_paths if path.startswith('app/api/') and path.endswith('/route.ts')]
    file_edges, drops = build_map.file_level_edges(import_pairs, graph.get('api_calls', {}), routes,
                                                    graph.get('rpcs', {}), graph.get('sqlfns', {}),
                                                    layer_of, source_paths)
    for edge in file_edges:
        edge['witness'] = {'path': edge['from'], 'start': None, 'end': None,
                           'kind': 'static-file-relationship'}
    layer_edges = build_map.rollup(import_pairs, layer_of)
    http_edges, http_misses = build_map.http_edges(graph.get('api_calls', {}), layer_of, routes)
    rpc_edges, rpc_misses = build_map.rpc_edges(graph.get('rpcs', {}), graph.get('sqlfns', {}), layer_of)
    layer_edges += http_edges + rpc_edges
    layer_edges.sort(key=lambda edge: (edge['from'], edge['to'], edge['type']))
    layer_ids = [group['id'] for group in groups]
    layer_cycle = build_map.find_cycle(build_map.adjacency(layer_edges, layer_ids))
    by_path = {item['path']: item for item in inventory['files']}
    nodes = [{'id': group['id'], 'kind': 'layer', 'label': group['label'],
              'desc': group['desc']} for group in groups]
    nodes += [{'id': path, 'kind': 'file', 'path': path, 'label': os.path.basename(path),
               'layer': layer_of[path], 'lines': by_path[path]['lineCount']}
              for path in source_paths]
    layers = {group['id']: {'files': list(group['files'])} for group in groups}
    extracted = sorted(set(graph.get('nodes', {})) & set(source_paths))
    unsupported = graph.get('unsupported', [])
    unresolved = graph.get('unresolved', [])
    unscanned = sorted(set(source_paths) - set(extracted))
    diagnostics = {
        'unresolved': unresolved,
        'unsupported': unsupported,
        'external': graph.get('ext', {}),
        'file_cycles': graph.get('cycles', []),
        'layer_cycle': layer_cycle,
        'non_source_connections': drops,
        'unresolved_http': http_misses,
        'unresolved_rpc': rpc_misses,
        'unmapped': unmapped,
        'duplicate_assignments': duplicate,
    }
    diagnostics['counts'] = {
        'unresolved': len(unresolved) + len(http_misses) + len(rpc_misses),
        'unsupported': len(unsupported),
        'external': sum(len(value) for value in graph.get('ext', {}).values()),
        'fileCycles': len(graph.get('cycles', [])),
        'unscanned': len(unscanned),
    }
    partial = bool(unresolved or unsupported or unscanned or http_misses or rpc_misses
                   or layer_cycle or inventory['counts']['extractionUnsupported'])
    map_data = {
        'meta': {'repo': inventory['source']['repo'], 'snapshot_commit': inventory['source']['commit'],
                 'extractor': EXTRACTOR_VERSION,
                 'counts': {'layers': len(groups), 'files': len(source_paths),
                            'edges': len(layer_edges), 'file_edges': len(file_edges)}},
        'nodes': nodes, 'edges': layer_edges, 'file_edges': file_edges, 'layers': layers,
    }
    preview = {
        'schema': PREVIEW_SCHEMA, 'snapshotId': snapshot_id,
        'state': 'partial' if partial else 'ready',
        'source': inventory['source'], 'manifestSha256': inventory['manifestSha256'],
        'inventoryCounts': inventory['counts'], 'limits': inventory['limits'],
        'grouping': {'status': 'proposed', 'reviewed': False,
                     'basis': 'deterministic parent-folder paths'},
        'publicationBlocked': bool(layer_cycle or unresolved or unmapped or duplicate),
        'extraction': {'extractor': EXTRACTOR_VERSION,
                       'scope': {'tops': tops, 'paths': source_paths,
                                 'extractedPaths': extracted, 'unscannedPaths': unscanned},
                       'options': dict(options)},
        'map': map_data, 'diagnostics': diagnostics,
        'limitations': [
            'This is a provisional static dependency preview, not reviewed architecture or an approved legacy map.',
            'Edges are static file evidence, not runtime execution, coverage, or guaranteed impact.',
            'Folder grouping is path-only; real file and layer cycles are retained and disclosed.',
            'Unsupported, unresolved, external, and unscanned relationships remain unknown and visible.',
        ],
    }
    _validate_preview(preview, set(source_paths))
    return preview


def _validate_preview(preview: Mapping[str, Any], source_paths: set[str]) -> None:
    try:
        if preview['grouping'] != {'status': 'proposed', 'reviewed': False} and preview['grouping'].get('reviewed') is not False:
            raise SnapshotError('Preview grouping may not claim review')
        graph = preview['map']
        nodes = graph['nodes']
        ids = [node['id'] for node in nodes]
        if len(ids) != len(set(ids)):
            raise SnapshotError('Preview contains duplicate node IDs')
        kinds = {node['id']: node['kind'] for node in nodes}
        for node in nodes:
            if node['kind'] == 'file':
                if node.get('path') not in source_paths or kinds.get(node.get('layer')) != 'layer':
                    raise SnapshotError('Preview contains invalid file ownership')
        for edge in graph['edges']:
            if kinds.get(edge['from']) != 'layer' or kinds.get(edge['to']) != 'layer':
                raise SnapshotError('Preview contains a corrupt layer endpoint')
        for edge in graph['file_edges']:
            if kinds.get(edge['from']) != 'file' or kinds.get(edge['to']) != 'file':
                raise SnapshotError('Preview contains a corrupt file endpoint')
        owned = []
        for layer, detail in graph['layers'].items():
            if kinds.get(layer) != 'layer':
                raise SnapshotError('Preview contains unknown layer ownership')
            owned.extend(detail['files'])
        if sorted(owned) != sorted(source_paths) or len(owned) != len(set(owned)):
            raise SnapshotError('Preview ownership is incomplete or duplicated')
    except SnapshotError:
        raise
    except (KeyError, TypeError, AttributeError) as error:
        raise SnapshotError('Preview structure is invalid') from error


def _render_html(inventory: dict[str, Any], preview: dict[str, Any]) -> bytes:
    payload = json.dumps({'inventory': inventory, 'preview': preview}, ensure_ascii=False,
                         separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    title = html.escape(preview['source']['repo'])
    page = """<!doctype html>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dependency preview — %s</title>
<style>body{font:16px system-ui;margin:2rem;color:#18202a;background:#f6f7f9}main{max-width:1100px;margin:auto}section{background:white;padding:1rem;margin:1rem 0;border:1px solid #ccd2d9;border-radius:8px}.warn{color:#8a3b00}table{border-collapse:collapse;width:100%%}td,th{text-align:left;padding:.35rem;border-bottom:1px solid #ddd}code{overflow-wrap:anywhere}button{padding:.4rem;text-align:left;overflow-wrap:anywhere}.file-select[aria-current="true"]{outline:3px solid #315ea8}.muted{color:#56606b}dt{font-weight:700;margin-top:.6rem}dd{margin-left:0;overflow-wrap:anywhere}#file-detail:focus{outline:3px solid #315ea8;outline-offset:3px}</style>
<main><h1>Dependency preview</h1><p id="identity"></p><p class="warn" id="status"></p><section><h2>Inventory</h2><p id="counts"></p><table><thead><tr><th>Path</th><th>Bytes</th><th>Kind</th><th>Extraction</th></tr></thead><tbody id="files"></tbody></table></section><section id="file-detail" tabindex="-1" hidden aria-live="polite"><h2>Selected file details</h2><dl><dt>Path</dt><dd><code id="detail-path"></code></dd><dt>SHA-256</dt><dd><code id="detail-sha256"></code></dd><dt>Kind</dt><dd id="detail-kind"></dd><dt>Line count</dt><dd id="detail-lines"></dd><dt>Extraction reason</dt><dd id="detail-reason"></dd><dt>Provisional group</dt><dd id="detail-group"></dd><dt>Incident directed links and source witnesses</dt><dd><ul id="detail-links"></ul></dd></dl></section><section><h2>Provisional grouping and links</h2><p id="graph"></p><ul id="groups"></ul></section><section><h2>Diagnostics</h2><pre id="diagnostics"></pre></section><section><h2>Limits and limitations</h2><pre id="limits"></pre><ul id="limitations"></ul></section></main>
<script type="application/json" id="workspace-data">%s</script>
<script>(()=>{'use strict';const d=JSON.parse(document.getElementById('workspace-data').textContent),p=d.preview,i=d.inventory,txt=(id,v)=>document.getElementById(id).textContent=v;txt('identity',p.source.url+' @ '+p.source.commit);txt('status',(p.state==='partial'?'PARTIAL — ':'')+'Grouping is proposed, never reviewed. Publication blocked: '+p.publicationBlocked);txt('counts',i.counts.files+' files, '+i.counts.bytes+' bytes; '+i.counts.extractionIncluded+' extraction candidates, '+i.counts.extractionUnsupported+' unsupported.');const fileNodes=new Map(p.map.nodes.filter(n=>n.kind==='file').map(n=>[n.path,n])),detail=document.getElementById('file-detail'),linkList=document.getElementById('detail-links'),buttons=[];function activate(f,button){for(const value of buttons)value.setAttribute('aria-current',String(value===button));txt('detail-path',f.path);txt('detail-sha256',f.sha256);txt('detail-kind',f.contentKind);txt('detail-lines',f.lineCount===null?'Unknown':String(f.lineCount));txt('detail-reason',f.extraction.reason||'Included in documented static extraction scope.');const node=fileNodes.get(f.path);txt('detail-group',node?node.layer:'Not in provisional graph (unsupported for extraction).');linkList.replaceChildren();const incident=p.map.file_edges.filter(e=>e.from===f.path||e.to===f.path);if(!incident.length){const li=document.createElement('li');li.textContent='No extracted incident directed links.';linkList.appendChild(li)}for(const edge of incident){const li=document.createElement('li'),direction=edge.from===f.path?'outgoing':'incoming',w=edge.witness&&edge.witness.path?edge.witness.path:'unknown';li.textContent=direction+' '+edge.type+': '+edge.from+' → '+edge.to+'; source witness path: '+w;linkList.appendChild(li)}detail.hidden=false;detail.focus()}const body=document.getElementById('files');for(const f of i.files){const r=document.createElement('tr'),pathCell=document.createElement('td'),button=document.createElement('button');button.type='button';button.className='file-select';button.textContent=f.path;button.setAttribute('aria-current','false');button.addEventListener('click',()=>activate(f,button));button.addEventListener('keydown',event=>{const index=buttons.indexOf(button),next=event.key==='ArrowDown'?index+1:event.key==='ArrowUp'?index-1:index;if(next!==index&&buttons[next]){event.preventDefault();buttons[next].focus()}});buttons.push(button);pathCell.appendChild(button);r.appendChild(pathCell);for(const v of [String(f.bytes),f.contentKind,f.extraction.status]){const c=document.createElement('td');c.textContent=v;r.appendChild(c)}body.appendChild(r)}txt('graph',p.map.meta.counts.layers+' proposed groups; '+p.map.meta.counts.file_edges+' file links; '+p.map.meta.counts.edges+' group links.');const groups=document.getElementById('groups');for(const [id,g] of Object.entries(p.map.layers)){const li=document.createElement('li');li.textContent=id+': '+g.files.length+' files';groups.appendChild(li)}txt('diagnostics',JSON.stringify(p.diagnostics,null,2));txt('limits',JSON.stringify(p.limits,null,2));const limitations=document.getElementById('limitations');for(const value of p.limitations){const li=document.createElement('li');li.textContent=value;limitations.appendChild(li)}})();</script>
""" % (title, payload)
    return page.encode('utf-8')


def _publication_file(path: Path, label: str) -> os.stat_result:
    try:
        info = path.lstat()
    except OSError as error:
        raise SnapshotError('Existing publication is missing ' + label) from error
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise SnapshotError('Existing publication contains linked or special files')
    return info


def _valid_producer(value: Any) -> bool:
    return (type(value) is dict
            and set(value) == {'schema', 'files'}
            and value.get('schema') == 'dag-gps-preview-producer/v1'
            and type(value.get('files')) is dict
            and set(value['files']) == set(_PRODUCER_FILES)
            and all(type(digest) is str and _SHA256.fullmatch(digest)
                    for digest in value['files'].values()))


def _read_bounded_receipt(path: Path, info: os.stat_result) -> bytes:
    """Read ownership metadata only after a size check, without following links."""
    if info.st_size > MAX_RECEIPT_BYTES:
        raise SnapshotError('Existing publication receipt exceeds %d bytes' % MAX_RECEIPT_BYTES)
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
                or opened.st_size > MAX_RECEIPT_BYTES):
            raise SnapshotError('Existing publication receipt changed during validation')
        data = os.read(fd, MAX_RECEIPT_BYTES + 1)
    finally:
        os.close(fd)
    if len(data) > MAX_RECEIPT_BYTES:
        raise SnapshotError('Existing publication receipt exceeds %d bytes' % MAX_RECEIPT_BYTES)
    return data


def _read_receipt(target: Path) -> Optional[dict[str, Any]]:
    try:
        if target.is_symlink() or not target.is_dir():
            raise SnapshotError('Refusing to replace an unowned publication path')
        names = {entry.name for entry in target.iterdir()}
        if names != _PUBLICATION_FILES:
            raise SnapshotError('Existing publication has unexpected or missing files')
        infos = {name: _publication_file(target / name, name) for name in _PUBLICATION_FILES}
        receipt = json.loads(_read_bounded_receipt(target / 'receipt.json',
                                                   infos['receipt.json']).decode('utf-8'))
        expected_keys = {'schema', 'cacheKey', 'snapshotId', 'source', 'outputs',
                         'producer', 'manualOverlays'}
        source = receipt.get('source') if type(receipt) is dict else None
        if (type(receipt) is not dict or set(receipt) != expected_keys
                or receipt.get('schema') != RECEIPT_SCHEMA
                or type(receipt.get('cacheKey')) is not str
                or not _SHA256.fullmatch(receipt['cacheKey'])
                or type(receipt.get('snapshotId')) is not str
                or not _SHA256.fullmatch(receipt['snapshotId'])
                or type(source) is not dict
                or set(source) != {'kind', 'url', 'repo', 'commit'}
                or source.get('kind') != 'git-commit'
                or any(type(source.get(key)) is not str or not source[key] or len(source[key]) > 4096
                       for key in ('url', 'repo'))
                or type(source.get('commit')) is not str
                or not _COMMIT.fullmatch(source['commit'])
                or type(receipt.get('outputs')) is not dict
                or set(receipt['outputs']) != _REQUIRED_OUTPUTS
                or not all(type(value) is str and _SHA256.fullmatch(value)
                           for value in receipt['outputs'].values())
                or not _valid_producer(receipt.get('producer'))
                or receipt.get('manualOverlays') != 'separate; never overwritten or marked reviewed'):
            raise SnapshotError('Existing publication has no valid ownership receipt')
        for name, digest in receipt['outputs'].items():
            if _sha((target / name).read_bytes()) != digest:
                raise SnapshotError('Existing publication bytes differ from its receipt')
        return receipt
    except FileNotFoundError:
        raise SnapshotError('Existing publication has no valid ownership receipt')
    except SnapshotError:
        raise
    except (OSError, ValueError, UnicodeError, KeyError) as error:
        raise SnapshotError('Existing publication has an invalid ownership receipt') from error


def _result(target: Path, snapshot_id: str, cache_hit: bool) -> dict[str, Any]:
    receipt = _read_receipt(target)
    if receipt is None or receipt['snapshotId'] != snapshot_id:
        raise SnapshotError('Published workspace identity differs from its receipt')
    hashes = {name: _sha((target / name).read_bytes())
              for name in _PUBLICATION_FILES}
    base = str(target.resolve())
    return {'snapshot_id': snapshot_id, 'cache_hit': cache_hit,
            'inventory_path': str(Path(base) / 'inventory.json'),
            'preview_path': str(Path(base) / 'preview.json'),
            'html_path': str(Path(base) / 'index.html'),
            'receipt_path': str(Path(base) / 'receipt.json'),
            'output_sha256': hashes}


def build_workspace_snapshot(acquisition: Mapping[str, Any], output_dir: Any, *,
                             limits: Optional[Mapping[str, Any]] = None,
                             extractor_options: Optional[Mapping[str, Any]] = None,
                             progress: Optional[Callable[[dict[str, Any]], None]] = None,
                             cancel: Any = None, _fault: Optional[str] = None) -> dict[str, Any]:
    """Inventory, extract, validate, and atomically publish one pinned preview.

    ``progress`` receives ``inventory-ready`` before extraction begins.  The output
    directory is a whole-directory publication: caught failures restore the prior
    validated directory. Manual overlays belong beside it (for example
    ``manual-overlays/``), are not read as approval, and are never overwritten.
    """
    bounds = _limits(limits)
    options = {} if extractor_options is None else dict(extractor_options)
    if type(extractor_options) not in (dict, type(None)) or set(options) - {'tops'}:
        raise ValueError('Unknown extractor option')
    if _cancelled(cancel):
        raise SnapshotCancelled('Workspace snapshot cancelled')
    git_dir, url, repo_id, commit = _validated_acquisition(acquisition, bounds, cancel)
    raw_target = Path(output_dir).expanduser()
    if raw_target.is_symlink():
        raise SnapshotError('Publication target may not be a symbolic link')
    target = raw_target.parent.resolve() / raw_target.name
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.parent.is_symlink():
        raise SnapshotError('Publication parent may not be a symbolic link')
    existing = _read_receipt(target) if target.exists() or target.is_symlink() else None
    staging = Path(tempfile.mkdtemp(prefix='.workspace-stage-', dir=str(target.parent)))
    backup = target.parent / ('.workspace-backup-' + str(os.getpid()))
    if backup.exists():
        shutil.rmtree(staging, ignore_errors=True)
        raise SnapshotError('Workspace publication backup collision')
    replaced = False
    promoted = False
    try:
        producer = _producer_manifest()
        inventory, source_paths = _inventory(git_dir, url, repo_id, commit, bounds, cancel, staging)
        identity = {'repo': repo_id, 'commit': commit, 'manifestSha256': inventory['manifestSha256'],
                    'extractor': EXTRACTOR_VERSION, 'producer': producer,
                    'options': options, 'limits': dict(bounds)}
        snapshot_id = _sha(_canonical(identity))
        cache_key = snapshot_id
        _notify(progress, 'inventory-ready', snapshot_id=snapshot_id,
                files=inventory['counts']['files'], bytes=inventory['counts']['bytes'])
        if existing is not None and existing.get('cacheKey') == cache_key:
            if _producer_manifest() != producer:
                raise SnapshotError('Workspace producer bytes changed during cache validation')
            shutil.rmtree(staging)
            return _result(target, snapshot_id, True)
        if source_paths:
            graph, tops = _extract(staging / 'source-data', source_paths, options, bounds, cancel, staging)
        else:
            graph = {'nodes': {}, 'edges': [], 'pyedges': [], 'api_calls': {}, 'rpcs': {},
                     'sqlfns': {}, 'cycles': [], 'unresolved': [], 'unsupported': [], 'ext': {}}
            tops = []
            (staging / 'extractor.json').write_text(json.dumps(graph), encoding='utf-8')
        preview = _preview(inventory, source_paths, graph, tops, options, snapshot_id)
        inventory_bytes = _canonical(inventory)
        preview_bytes = _canonical(preview)
        html_bytes = _render_html(inventory, preview)
        if _producer_manifest() != producer:
            raise SnapshotError('Workspace producer bytes changed during snapshot generation')
        outputs = {'inventory.json': _sha(inventory_bytes), 'preview.json': _sha(preview_bytes),
                   'index.html': _sha(html_bytes)}
        receipt = {'schema': RECEIPT_SCHEMA, 'cacheKey': cache_key, 'snapshotId': snapshot_id,
                   'source': inventory['source'], 'outputs': outputs, 'producer': producer,
                   'manualOverlays': 'separate; never overwritten or marked reviewed'}
        receipt_bytes = _canonical(receipt)
        if len(receipt_bytes) > MAX_RECEIPT_BYTES:
            raise SnapshotError('Generated publication receipt exceeds %d bytes' % MAX_RECEIPT_BYTES)
        for name, data in (('inventory.json', inventory_bytes), ('preview.json', preview_bytes),
                           ('index.html', html_bytes), ('receipt.json', receipt_bytes)):
            (staging / name).write_bytes(data)
        shutil.rmtree(staging / 'source-data')
        (staging / 'extractor.json').unlink()
        for name, digest in outputs.items():
            if _sha((staging / name).read_bytes()) != digest:
                raise SnapshotError('Staged workspace output readback failed')
        if existing is not None:
            target.rename(backup); replaced = True
        staging.rename(target)
        promoted = True
        if _fault == 'readback':
            raise SnapshotError('Injected publication readback fault')
        published = _read_receipt(target)
        if published != receipt:
            raise SnapshotError('Published workspace output readback failed')
        if backup.exists():
            shutil.rmtree(backup)
        _notify(progress, 'preview-ready', snapshot_id=snapshot_id,
                state=preview['state'], file_edges=len(preview['map']['file_edges']))
        return _result(target, snapshot_id, False)
    except SnapshotCancelled:
        if target.exists() and replaced:
            shutil.rmtree(target, ignore_errors=True); backup.rename(target)
        elif target.exists() and promoted:
            shutil.rmtree(target, ignore_errors=True)
        raise
    except Exception as error:
        if target.exists() and replaced:
            shutil.rmtree(target, ignore_errors=True); backup.rename(target)
        elif target.exists() and promoted:
            shutil.rmtree(target, ignore_errors=True)
        if isinstance(error, (SnapshotError, ValueError)):
            raise
        raise SnapshotError('Workspace snapshot failed safely') from error
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        if backup.exists() and not target.exists():
            backup.rename(target)
