"""Manual integration gate: real pinned imports, isolated scratch server, UI."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
baseline = '--baseline' in sys.argv
code = ROOT / 'artifacts/folder-tree/base' if baseline else ROOT
sys.path.insert(0, str(code))
from app.server import WorkspaceServer

out = ROOT / 'artifacts/folder-tree'
workspace = Path(os.environ['TMPDIR']) / 'folder-tree-workspace'
workspace.mkdir(parents=True, exist_ok=True)
cache = Path('/Users/aibert/projects/dag-gps-question-parser/artifacts/question-parser/workspace/git-cache')
if cache.exists() and not (workspace / 'git-cache').exists():
    shutil.copytree(cache, workspace / 'git-cache', dirs_exist_ok=True)
server = WorkspaceServer(workspace, port=0)
assert server.port not in (8765, 8766, 8767)
threading.Thread(target=server.serve_forever, daemon=True).start()
try:
    for repo, name, pin in [('honcho', 'plastic-labs/honcho', '3922af856d78ec41133916deec4d821fa9c5a92e'),
                            ('salesroom', 'erictweng/salesroom-app', '5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce')]:
        target = out / repo / 'baseline-import' if baseline else out / repo
        target.mkdir(parents=True, exist_ok=True)
        start = time.perf_counter()
        subprocess.run(['node', str(ROOT / 'tests/folder_tree_browser.cjs')], input=json.dumps({
            'url': server.url, 'repo': name, 'pin': pin, 'out': str(target), 'importOnly': baseline}), text=True, check=True, timeout=400)
        project = next(p for p in server.store.projects() if p['repo'] == name)
        _, snapshot = server.store.snapshot(project['projectId'], project['current']['snapshotId'])
        (target / 'snapshot.json').write_text(json.dumps(snapshot))
        print(json.dumps({'repo': repo, 'browserSeconds': time.perf_counter() - start,
                          'nodes': len(snapshot['map']['nodes']), 'snapshot': str(target / 'snapshot.json')}))
finally:
    server.shutdown()
