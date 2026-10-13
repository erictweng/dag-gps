#!/usr/bin/env python3
"""Import through the production browser flow; snapshot stays in this worktree."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.server import WorkspaceServer

parser = argparse.ArgumentParser()
parser.add_argument('repo', choices=['honcho', 'salesroom'])
parser.add_argument('--out', type=Path)
args = parser.parse_args()
repo, pin = {'honcho': ('plastic-labs/honcho', '3922af856d78ec41133916deec4d821fa9c5a92e'),
             'salesroom': ('erictweng/salesroom-app', '5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce')}[args.repo]
out = args.out or ROOT / ('artifacts/question-parser/' + args.repo)
out.mkdir(parents=True, exist_ok=True)
server = WorkspaceServer(ROOT / 'artifacts/question-parser/workspace', port=0)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    subprocess.run(['node', str(ROOT / 'scripts/verify_question_parser.cjs'), server.url, str(out),
                    'https://github.com/' + repo, pin], check=True, timeout=400)
    project = next(p for p in server.store.projects() if p['repo'] == repo)
    _, snapshot = server.store.snapshot(project['projectId'], project['current']['snapshotId'])
    (out / 'snapshot.json').write_text(json.dumps(snapshot))
    print(json.dumps({'repo': repo, 'pin': pin, 'inventory': len(snapshot['inventory']),
                      'mapped': len(snapshot['map']['nodes']), 'out': str(out)}))
finally:
    server.shutdown()
