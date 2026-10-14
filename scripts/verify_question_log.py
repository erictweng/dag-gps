#!/usr/bin/env python3
"""Real Chromium question/verdict/restart proof on a copied pinned Honcho snapshot."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.server import WorkspaceServer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    workspace = args.out / 'workspace'
    workspace.mkdir(exist_ok=True)
    if (workspace / 'query-log.jsonl').exists():
        parser.error('Use a fresh output directory; previous evidence is not overwritten')
    snapshot = json.loads(args.snapshot.read_text())
    snapshot['queryCode'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                             for p in ['web/scorer.js', 'web/router.js', 'web/query-service.js']}
    snapshot['scorerSha256'] = snapshot['queryCode']['web/scorer.js']
    path = workspace / 'snapshot.json'
    path.write_text(json.dumps(snapshot))
    key = workspace / 'session'
    server = WorkspaceServer(workspace, port=0, session_file=key)
    server.store.project_dir(snapshot['projectId']).mkdir(parents=True, exist_ok=True)
    server.store.record(snapshot, path)
    port = server.port
    original_url = server.url
    for phase in ('before', 'after'):
        if phase == 'after':
            server = WorkspaceServer(workspace, port=port, session_file=key)
            assert original_url == server.url, 'private link changed after restart'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = dict(os.environ, DAG_TEST_URL=original_url)
            subprocess.run(['node', str(ROOT / 'scripts/smoke_question_log.cjs'), phase,
                            str(args.out.resolve())], env=env, check=True)
        finally:
            server.shutdown()
            thread.join()
    questions = server.query_log.entries(snapshot['projectId'])
    assert len(questions) == 5 and all(q['verdict'] for q in questions)
    receipt = {'questions': len(questions), 'statuses': [q['status'] for q in questions],
               'sameLinkAfterRestart': True, 'verdictsPersisted': True,
               'snapshotId': snapshot['snapshotId'], 'commit': snapshot['source']['commit']}
    (args.out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    main()
