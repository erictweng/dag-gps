#!/usr/bin/env python3
"""Package local-only release candidate examples after real gates pass."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'v1.0.0-rc.1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verification', default='artifacts/release-check/verification.json')
    args = parser.parse_args()
    verification_path = ROOT / args.verification
    report = json.loads(verification_path.read_text())
    required = {'build', 'test', 'smoke', 'release_session', 'accessibility', 'performance', 'ui_performance', 'milestone_acceptance'}
    results = {r['name']: r['returncode'] for r in report['results']}
    if report['legacy_only'] or not required.issubset(results) or any(results.values()):
        raise ValueError('Candidate blocked: missing/failed actual release gates')
    current_commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if report['build_commit'] != current_commit:
        raise ValueError('Verification commit differs from HEAD; rerun release_check.py')
    for source, digest in report['inputs'].items():
        if not (ROOT / source).is_file() or sha(ROOT / source) != digest:
            raise ValueError('Gate input changed after verification: ' + source)
    out = ROOT / 'dist' / 'release' / VERSION
    out.mkdir(parents=True, exist_ok=True)
    candidates = []
    for source, target in [('dist/quest-refresh', 'quest'), ('dist/dag-gps', 'self-legacy'),
                           ('dist/release-session-quest', 'quest-grouping-worker-sample'),
                           ('dist/release-session-self', 'self-grouping-worker-sample')]:
        for name in ['index.html', 'map.json', 'diff.json', 'report.json']:
            candidates.append((source + '/' + name, target + '/' + name))
    candidates += [('dist/onboarding-quest.html', 'editors/quest.html'),
                   ('dist/onboarding-dag-gps.html', 'editors/self.html'),
                   ('artifacts/release-session-quest-layers.json', 'samples/quest-layers.json'),
                   ('artifacts/release-session-self-layers.json', 'samples/self-layers.json'),
                   ('maps/quest-coder/layers.json', 'inputs/quest-layers.json'),
                   ('maps/quest-coder/tours.json', 'inputs/quest-tours.json'),
                   ('maps/dag-gps/layers.json', 'inputs/self-legacy-layers.json'),
                   ('docs/V1_RELEASE.md', 'V1_RELEASE.md'),
                   ('docs/SUPPORTED_SOURCES.md', 'SUPPORTED_SOURCES.md')]
    # Pattern scan is bounded evidence, not a comprehensive secret certification.
    patterns = [r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                r'gh[pousr]_[A-Za-z0-9]{30,}', r'sk-[A-Za-z0-9]{32,}']
    hits = []
    for source, target in candidates:
        src = ROOT / source
        if not src.is_file():
            raise ValueError('Missing bundle input: ' + source)
        text = src.read_text()
        for pattern in patterns:
            if re.search(pattern, text):
                hits.append(dict(file=source, pattern=pattern))
    compiled = re.search(r'^var TOUR_DATA = (.+);$', (ROOT / 'dist/quest-refresh/index.html').read_text(), re.M)
    if not compiled:
        raise ValueError('Missing compiled quest tour evidence in navigator')
    tours = json.loads(compiled.group(1))
    ranges = {}
    literal_credential = r"(?i)(?:secret|password|api[_-]?key|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_./+=-]{12,}['\"]"
    occurrences = 0
    for tour in tours['tours']:
        for item in tour['steps'] + tour['links']:
            for evidence in item.get('evidence', []):
                occurrences += 1
                key = (evidence['path'], evidence['start'], evidence['end'])
                excerpt = evidence['excerpt'].encode('utf-8')
                ranges[key] = dict(path=key[0], start=key[1], end=key[2], bytes=len(excerpt),
                                   sha256=hashlib.sha256(excerpt).hexdigest())
                if re.search(literal_credential, evidence['excerpt']):
                    hits.append(dict(file=key[0], pattern='literal credential assignment in cited excerpt'))
    private_review = dict(repo=tours['repo'], commit=tours['commit'], tourCount=len(tours['tours']),
                          citationOccurrences=occurrences, uniqueSourceRanges=len(ranges),
                          excerptBytes=sum(r['bytes'] for r in ranges.values()), matches=len(hits),
                          ranges=list(ranges.values()), scope='Cited excerpts plus bounded bundle token scan; not comprehensive privacy/secret certification')
    (ROOT / 'artifacts/release-private-source-review.json').write_text(json.dumps(private_review, indent=2) + '\n')
    if hits:
        raise ValueError('Potential credential pattern in bundle; inspect locally, do not share: ' +
                         ', '.join(h['file'] for h in hits))
    files = []
    for source, target in candidates:
        src, dest = ROOT / source, out / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        files.append(dict(path=target, source=source, bytes=dest.stat().st_size, sha256=sha(dest)))
    maps = {target: json.loads((ROOT / source / 'map.json').read_text())
            for source, target in [('dist/quest-refresh', 'quest'), ('dist/dag-gps', 'self-legacy'),
                                   ('dist/release-session-quest', 'quest-grouping-worker-sample'),
                                   ('dist/release-session-self', 'self-grouping-worker-sample')]}
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    manifest = dict(schema='dag-gps-release/v1', version=VERSION, status='release-candidate',
                    generated_at=datetime.datetime.now().astimezone().isoformat(), build_commit=commit,
                    dirty_tracked_worktree=bool(subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT, text=True)),
                    source_pins={k: dict(repo=m['meta']['repo'], commit=m['meta'].get('snapshot_commit', m['meta']['commit']), counts=m['meta']['counts']) for k, m in maps.items()},
                    files=files, file_count=len(files), total_bytes=sum(f['bytes'] for f in files),
                    verification=dict(path=str(verification_path), sha256=sha(verification_path), timestamp=report['timestamp'], results=results),
                    environment=dict(report.get('environment', {}),
                                     browser=json.loads((ROOT / 'artifacts/release-ui-performance.json').read_text())['browserVersion'],
                                     playwright=json.loads((ROOT / 'artifacts/release-ui-performance.json').read_text())['playwrightVersion'],
                                     axe=json.loads((ROOT / 'artifacts/release-accessibility.json').read_text())['states'][0]['axe']['engineVersion']),
                    release_evidence={str(p.relative_to(ROOT)): sha(p) for p in [
                        ROOT / 'artifacts/release-browser.json', ROOT / 'artifacts/release-accessibility.json',
                        ROOT / 'artifacts/release-performance.json', ROOT / 'artifacts/release-ui-performance.json']},
                    build_inputs={str(p.relative_to(ROOT)): sha(p) for directory in ['web', 'scripts'] for p in sorted((ROOT / directory).glob('*')) if p.is_file() and p.suffix in ['.py', '.js', '.cjs', '.html', '.mjs']},
                    privacy=dict(local_only=True, public_upload=False, contains_private_source_excerpts=True, cited_source_review=private_review,
                                 pattern_scan='No matches for PEM private-key / GitHub token / sk-token patterns. Not a comprehensive credential audit.',
                                 sharing_review='Review inline tour excerpts, repository paths, maps and exported names before sharing; no exports of query history included.'),
                    human_acceptance=dict(unaided_session='pending Eric', semantic_grouping='pending Eric; worker samples only', real_user_tuning='deferred; zero confirmed user labels'))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    # Read back bundle bytes and the exact manifest; external-style packaging verification.
    loaded = json.loads((out / 'manifest.json').read_text())
    assert loaded['file_count'] == len(loaded['files'])
    for item in loaded['files']:
        assert sha(out / item['path']) == item['sha256']
        assert (out / item['path']).stat().st_size == item['bytes']
    print(json.dumps(dict(manifest=str(out / 'manifest.json'), files=len(files), bytes=manifest['total_bytes'], commit=commit)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, AssertionError) as error:
        print('Release package blocked: ' + str(error), file=sys.stderr)
        sys.exit(1)
