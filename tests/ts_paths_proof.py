"""Manual pinned production-import proof; not a unit test or network operation."""
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.snapshots import build_workspace_snapshot
from app.workspace_snapshot import load_publication

if __name__ == '__main__':
    cache, version = Path(sys.argv[1]), sys.argv[2]
    out = ROOT / 'artifacts/ts-paths' / version
    out.mkdir(parents=True, exist_ok=True)
    for entry in sorted(cache.glob('repo-*')):
        acquisition = json.loads((entry / 'metadata.json').read_text())
        acquisition['git_dir'] = str(entry / 'repo.git')
        repo = 'salesroom' if 'salesroom' in acquisition['repo_id'] else 'honcho'
        start = time.perf_counter()
        result = build_workspace_snapshot(acquisition, out / repo / 'publication')
        elapsed = time.perf_counter() - start
        snapshot = load_publication(out / repo / 'publication')
        (out / repo / 'snapshot.json').write_text(json.dumps(snapshot))
        report = {'seconds': elapsed, 'cache_hit': result.get('cache_hit'), 'result': result}
        (out / repo / 'timing.json').write_text(json.dumps(report, indent=2))
        print(repo, elapsed, flush=True)
