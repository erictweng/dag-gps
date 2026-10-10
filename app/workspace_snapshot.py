"""Adapt a verified Phase 1 publication into a dag-gps-workspace/v1 snapshot.

The publication is trusted local-store state only after its ownership receipt,
exact membership and output digests validate. The envelope binds the map digest
and the exact query-code bytes (scorer/router/query service) that will answer
questions, so a packet cannot claim provenance from different code. No model
calls, network access or imported-source execution.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Optional

from app.contracts import SNAPSHOT_SCHEMA, validate_snapshot
from app.snapshots import SnapshotError, _read_receipt

ROOT = Path(__file__).resolve().parents[1]
QUERY_CODE = ('web/scorer.js', 'web/router.js', 'web/query-service.js')
MAX_PUBLICATION_JSON_BYTES = 64 * 1024 * 1024


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                      allow_nan=False).encode('utf-8')


def query_code_digests(root: Path = ROOT) -> dict[str, str]:
    return {name: _sha((root / name).read_bytes()) for name in QUERY_CODE}


def _read_output(target: Path, name: str, digest: str) -> Any:
    path = target / name
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_PUBLICATION_JSON_BYTES:
        raise SnapshotError('Publication output is not a bounded regular file: ' + name)
    data = path.read_bytes()
    if _sha(data) != digest:
        raise SnapshotError('Publication output changed after receipt validation: ' + name)
    return json.loads(data.decode('utf-8'))


def load_publication(output_dir: Any, *, project_id: Optional[str] = None,
                     code_root: Path = ROOT) -> dict[str, Any]:
    """Return a validated workspace snapshot envelope for a published preview."""
    target = Path(output_dir)
    receipt = _read_receipt(target)
    if receipt is None:
        raise SnapshotError('No published preview at ' + str(target))
    inventory = _read_output(target, 'inventory.json', receipt['outputs']['inventory.json'])
    preview = _read_output(target, 'preview.json', receipt['outputs']['preview.json'])
    source = preview.get('source') or {}
    if (preview.get('snapshotId') != receipt['snapshotId'] or source.get('commit') != receipt['source']['commit']
            or source.get('repo') != receipt['source']['repo']
            or inventory.get('manifestSha256') != preview.get('manifestSha256')):
        raise SnapshotError('Publication files disagree about source identity')
    code = query_code_digests(code_root)
    graph = preview['map']
    snapshot = {
        'schema': SNAPSHOT_SCHEMA,
        'projectId': project_id or 'github:' + source['repo'],
        'snapshotId': preview['snapshotId'],
        'mapSha256': _sha(canonical_json(graph)),
        'scorerSha256': code['web/scorer.js'],
        'queryCode': code,
        'source': {'kind': 'git-commit', 'repo': source['repo'], 'commit': source['commit'],
                   'url': source.get('url'), 'worktreeId': None,
                   'manifestSha256': preview['manifestSha256']},
        # A Phase 1 preview is never a reviewed/validated map, even when complete.
        'state': 'dependency-preview',
        'extractionState': preview.get('state'),
        'grouping': {'status': 'proposed', 'reviewed': False},
        'inventory': [{'path': f['path'], 'sha256': f['sha256'], 'lineCount': f['lineCount'],
                       'contentKind': f.get('contentKind'), 'extraction': f.get('extraction')}
                      for f in inventory['files']],
        'map': graph,
        'limitations': [value for value in preview.get('limitations', []) if isinstance(value, str)][:50],
    }
    validate_snapshot(snapshot)
    return snapshot


def write_snapshot(snapshot: Mapping[str, Any], path: Any) -> str:
    """Write the envelope canonically; returns its SHA-256 (for receipts)."""
    data = canonical_json(snapshot)
    Path(path).write_bytes(data)
    return _sha(data)
