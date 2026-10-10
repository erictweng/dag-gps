"""Store/list validated agent explanations beside an immutable revision.

Layout: ROOT/projects/<projectId>/explanations/<snapshotId>/<key>.json, where key =
sha256(requestId)[:32]. A record is written only after validate_explanation passes
against the trusted snapshot and exact packet; records are re-validated on read, so
an edited/stale file is reported as invalid instead of being displayed. Explanations
never modify the snapshot or graph.
"""
import hashlib
import json
import os
import re
import time
from pathlib import Path

from app.explanations import ExplanationError, packet_digest, validate_explanation
from app.workspace_snapshot import canonical_json

RECORD_SCHEMA = 'dag-gps-explanation-record/v1'
_PROJECT = re.compile(r'p-[0-9a-f]{20}\Z')
_SNAPSHOT = re.compile(r'[0-9a-f]{64}\Z')
MAX_RECORD_BYTES = 2 * 1024 * 1024
MAX_RECORDS = 200


def _directory(root, project_id, snapshot_id):
    if type(project_id) is not str or not _PROJECT.fullmatch(project_id):
        raise ExplanationError('Invalid project ID')
    if type(snapshot_id) is not str or not _SNAPSHOT.fullmatch(snapshot_id):
        raise ExplanationError('Invalid snapshot ID')
    return Path(root) / 'projects' / project_id / 'explanations' / snapshot_id


def _allowed(context, snapshot, packet):
    if context is None:
        return None
    if (type(context) is not dict or context.get('schema') != 'dag-gps-context/v1'
            or context.get('snapshotId') != snapshot['snapshotId']
            or context.get('requestId') != packet['requestId']
            or context.get('packetSha256') != packet_digest(packet)):
        raise ExplanationError('Context does not belong to this packet and revision')
    return [f['path'] for f in context.get('files', [])]


def store_explanation(root, snapshot, packet, explanation, context=None):
    """Validate then atomically store. Returns the stored record."""
    allowed = _allowed(context, snapshot, packet)
    validate_explanation(explanation, snapshot, packet, allowed_paths=allowed)
    directory = _directory(root, snapshot['projectId'], snapshot['snapshotId'])
    directory.mkdir(parents=True, exist_ok=True)
    record = {'schema': RECORD_SCHEMA, 'storedAt': int(time.time()), 'packet': packet,
              'contextFiles': allowed, 'explanation': explanation}
    data = canonical_json(record)
    if len(data) > MAX_RECORD_BYTES:
        raise ExplanationError('Explanation record too large')
    key = hashlib.sha256(packet['requestId'].encode('utf-8')).hexdigest()[:32]
    target = directory / (key + '.json')
    temporary = directory / ('.' + key + '.tmp')
    temporary.write_bytes(data)
    os.replace(temporary, target)
    return record


def list_explanations(root, snapshot):
    """Return [{'record': ..., 'valid': bool, 'error': str|None}] newest first."""
    directory = _directory(root, snapshot['projectId'], snapshot['snapshotId'])
    if not directory.is_dir():
        return []
    out = []
    for path in sorted(directory.glob('*.json'))[:MAX_RECORDS]:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_RECORD_BYTES:
            out.append({'record': None, 'valid': False, 'error': 'Unreadable record'})
            continue
        try:
            record = json.loads(path.read_bytes().decode('utf-8'))
            if type(record) is not dict or record.get('schema') != RECORD_SCHEMA:
                raise ExplanationError('Unknown record schema')
            packet = record['packet']
            files = record.get('contextFiles')
            validate_explanation(record['explanation'], snapshot, packet,
                                 allowed_paths=files if files is not None else None)
            out.append({'record': record, 'valid': True, 'error': None})
        except (ValueError, KeyError, TypeError) as error:
            out.append({'record': None, 'valid': False, 'error': str(error)[:300]})
    out.sort(key=lambda item: -(item['record'] or {}).get('storedAt', 0))
    return out
