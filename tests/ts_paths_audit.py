"""Audit pinned new edges against actual Git blobs and retain compact evidence."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts/ts-paths'


def read(path):
    return json.loads(path.read_text())


def encoded(obj):
    return json.dumps(obj, sort_keys=True, separators=(',', ':')).encode()


if __name__ == '__main__':
    cache = Path(sys.argv[1])
    report = {}
    for repo in ('salesroom', 'honcho'):
        snapshots = [read(OUT / v / repo / 'snapshot.json') for v in ('before', 'after')]
        previews = [read(OUT / v / repo / 'publication/preview.json') for v in ('before', 'after')]
        edges = [{k: s['map'][k] for k in ('edges', 'file_edges')} for s in snapshots]
        report[repo] = {'edgeSha256': [hashlib.sha256(encoded(e)).hexdigest() for e in edges],
                        'importEdges': [sum(e['type'] == 'import' for e in s['map']['file_edges']) for s in snapshots],
                        'diagnosticCounts': [p['diagnostics']['counts'] for p in previews],
                        'seconds': [read(OUT / v / repo / 'timing.json')['seconds'] for v in ('before', 'after')]}
        if repo == 'honcho':
            assert encoded(edges[0]) == encoded(edges[1])
            continue
        before = {(e['from'], e['to']) for e in edges[0]['file_edges'] if e['type'] == 'import'}
        after = {(e['from'], e['to']) for e in edges[1]['file_edges'] if e['type'] == 'import'}
        assert not before - after
        added = sorted(after - before)
        entry = next(p for p in cache.glob('repo-*') if 'salesroom' in read(p / 'metadata.json')['repo_id'])
        git_dir = entry / 'repo.git'
        pin = snapshots[0]['source']['commit']
        def blob(path):
            return subprocess.check_output(['git', '--git-dir', str(git_dir), 'show', pin + ':' + path], text=True)
        report[repo]['tsconfig'] = blob('tsconfig.json')
        citations = []
        for source, target in added:
            spec = '@/' + target.removeprefix('src/').rsplit('.', 1)[0]
            lines = [(i, line.strip()) for i, line in enumerate(blob(source).splitlines(), 1)
                     if ('"' + spec + '"') in line or ("'" + spec + "'") in line]
            assert lines, (source, target, spec)
            blob(target)  # prove exact destination exists at the same commit
            citations.append({'from': source, 'to': target, 'line': lines[0][0], 'source': lines[0][1]})
        assert ('src/components/content/VideoPlayer.tsx', 'src/lib/youtube.ts') in added
        report[repo]['addedEdges'] = citations
        chosen = [c for c in citations if c['from'] == 'src/components/content/VideoPlayer.tsx']
        chosen += [c for c in citations if c not in chosen][:10 - len(chosen)]
        assert len(chosen) == 10
        report[repo]['spotChecks'] = chosen
    (OUT / 'graph-report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: {a: b for a, b in v.items() if a not in ('addedEdges', 'tsconfig')} for k, v in report.items()}, indent=2))
