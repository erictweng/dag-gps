#!/usr/bin/env python3
"""Real app import and browser proof against the explicitly pinned public Honcho."""
import json
from pathlib import Path
import subprocess
import sys
import threading

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.server import WorkspaceServer

OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'artifacts/function-layer/honcho'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    server = WorkspaceServer(OUT / 'workspace', port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(['node', str(ROOT / 'scripts/verify_function_honcho.cjs'), server.url, str(OUT)],
                                cwd=ROOT, timeout=400)
        if result.returncode:
            return result.returncode
        projects = server.store.projects()
        project = next(p for p in projects if p['repo'] == 'plastic-labs/honcho')
        path, snapshot = server.store.snapshot(project['projectId'], project['current']['snapshotId'])
        (OUT / 'snapshot.json').write_text(json.dumps(snapshot))
        symbols = snapshot['map']['symbol_graph']
        (OUT / 'symbols.json').write_text(json.dumps(symbols['nodes'], indent=2))
        print(json.dumps({'snapshotPath': str(path), 'files': len(snapshot['inventory']), 'symbolCounts': symbols['counts']}))
    finally:
        server.shutdown()
    return 0


if __name__ == '__main__':
    sys.exit(main())
