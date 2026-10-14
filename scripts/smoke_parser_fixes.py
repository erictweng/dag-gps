#!/usr/bin/env python3
"""Serve pinned snapshots through the real application for parser browser checks."""
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
from app.contracts import validate_snapshot

out = ROOT / 'artifacts/question-parser/benchmark-fixes/browser'
workspace = out / 'workspace'
workspace.mkdir(parents=True, exist_ok=True)
server = WorkspaceServer(workspace, port=0)
projects = {}
for repo in ['honcho', 'salesroom']:
    snapshot = json.loads((ROOT / f'artifacts/question-parser/{repo}/snapshot.json').read_text())
    snapshot['queryCode'] = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                             for p in ['web/scorer.js', 'web/router.js', 'web/query-service.js']}
    snapshot['scorerSha256'] = snapshot['queryCode']['web/scorer.js']
    validate_snapshot(snapshot)
    target = workspace / (repo + '-snapshot.json')
    target.write_text(json.dumps(snapshot))
    server.store.project_dir(snapshot['projectId']).mkdir(parents=True, exist_ok=True)
    server.store.record(snapshot, target)
    projects[repo] = snapshot['projectId']
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    result = subprocess.run(['node', str(ROOT / 'scripts/smoke_parser_fixes.cjs')],
                            input=json.dumps({'url': server.url, 'projects': projects, 'out': str(out)}),
                            text=True, cwd=ROOT, env=os.environ, timeout=180)
    raise SystemExit(result.returncode)
finally:
    server.shutdown()
