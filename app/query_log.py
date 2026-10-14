"""Bounded, workspace-local question journal. One server owns a workspace root."""
from __future__ import annotations

import json
import secrets
import threading
import time
from pathlib import Path

LABELS = ('match', 'no match', 'unsure')
MAX_LINE = 128 * 1024
MAX_BYTES = 10 * 1024 * 1024


def label_for_status(status):
    return 'match' if status == 'matched' else 'no match' if status == 'no-match' else 'unsure'


def timestamp():
    return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())


def read_entries(path):
    """Fold the retained generations, oldest first; tolerate a torn final write."""
    questions = {}
    for source in (Path(str(path) + '.1'), path):
        if not source.exists():
            continue
        with source.open('rb') as handle:
            for line in handle:
                if len(line) > MAX_LINE or not line.endswith(b'\n'):
                    continue
                try:
                    row = json.loads(line)
                    key = (row['projectId'], row['entryId'])
                    if row['kind'] == 'question':
                        questions[key] = dict(row, verdict=None, verdictAt=None)
                    elif row['kind'] == 'verdict' and key in questions and row['label'] in LABELS:
                        questions[key].update(verdict=row['label'], verdictAt=row['at'])
                except (ValueError, KeyError, TypeError):
                    continue
    # Checkpoint copies keep the original creation stamp, so a corrected old
    # question keeps its place. Rows without a stamp (older logs) sort first.
    ordered = sorted(questions.values(), key=lambda q: q.get('createdNs') or 0)
    return list(reversed(ordered))


class QueryLog:
    def __init__(self, root, *, max_bytes=MAX_BYTES):
        self.path = Path(root) / 'query-log.jsonl'
        self.lock = threading.Lock()
        self.max_bytes = max_bytes

    def _append(self, record):
        line = (json.dumps(record, ensure_ascii=True, sort_keys=True) + '\n').encode('ascii')
        if len(line) > min(MAX_LINE, self.max_bytes):
            raise ValueError('Question log record exceeds byte limit')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        torn = False
        if self.path.exists() and self.path.stat().st_size:
            with self.path.open('rb') as handle:
                handle.seek(-1, 2)
                torn = handle.read(1) != b'\n'
        if self.path.exists() and self.path.stat().st_size + len(line) + int(torn) > self.max_bytes:
            self.path.replace(Path(str(self.path) + '.1'))
            torn = False
        # No per-request fsync. A crash may lose the latest line, not interleave writes.
        with self.path.open('ab') as handle:
            if torn:
                handle.write(b'\n')
            handle.write(line)

    def question(self, project_id, snapshot, body, packet, latency_ms):
        entry_id = 'q-' + secrets.token_hex(16)
        row = {'kind': 'question', 'entryId': entry_id, 'at': timestamp(), 'createdNs': time.time_ns(),
               'projectId': project_id, 'snapshotId': snapshot['snapshotId'],
               'commit': snapshot['source']['commit'], 'requestId': body['requestId'],
               'query': body['query'], 'operation': packet['operation'], 'status': packet['status'],
               'label': label_for_status(packet['status']), 'latencyMs': round(latency_ms, 3),
               'selectedNodeIds': [s for s in packet['selectedNodeIds'][:10] if len(s) <= 256],
               'alternatives': [a['nodeId'] for a in packet['alternatives'][:10] if len(a['nodeId']) <= 256]}
        with self.lock:
            self._append(row)
        return entry_id

    def entries(self, project_id):
        with self.lock:
            return [q for q in read_entries(self.path) if q['projectId'] == project_id]

    def verdict(self, project_id, entry_id, label):
        with self.lock:
            entry = next((q for q in read_entries(self.path)
                          if q['projectId'] == project_id and q['entryId'] == entry_id), None)
            if entry is None:
                raise KeyError(entry_id)
            if entry['verdict'] != label:
                at = timestamp()
                # If rotation drops this question's generation, retain its identity
                # next to the verdict, so an acknowledged correction stays readable.
                question = {k: v for k, v in entry.items() if k not in ('verdict', 'verdictAt')}
                self._append(question)
                self._append({'kind': 'verdict', 'projectId': project_id, 'entryId': entry_id,
                              'label': label, 'at': at})
                entry.update(verdict=label, verdictAt=at)
            return entry
