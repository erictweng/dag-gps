"""Versioned local release contract: inputs, producer boundaries, tested bytes.

Receipts are local evidence, not signatures or protection from a malicious writer
rewriting both receipt and payload. Use a single release writer.
"""
import hashlib
import os
from pathlib import Path
import subprocess

SCHEMA = 'dag-gps-verification/v2'
OUTPUT_ROOTS = {'artifacts', 'dist'}
CACHE_DIRS = {'__pycache__', '.pytest_cache', 'node_modules', '.DS_Store'}
BUNDLE_DIRS = [('dist/quest-refresh', 'quest'), ('dist/dag-gps', 'self-legacy'),
               ('dist/release-session-quest', 'quest-grouping-worker-sample'),
               ('dist/release-session-self', 'self-grouping-worker-sample')]
BUNDLE = [(source + '/' + name, target + '/' + name)
          for source, target in BUNDLE_DIRS
          for name in ('index.html', 'map.json', 'diff.json', 'report.json')]
BUNDLE += [('dist/onboarding-quest.html', 'editors/quest.html'),
           ('dist/onboarding-dag-gps.html', 'editors/self.html'),
           ('artifacts/release-session-quest-layers.json', 'samples/quest-layers.json'),
           ('artifacts/release-session-self-layers.json', 'samples/self-layers.json'),
           ('maps/quest-coder/layers.json', 'inputs/quest-layers.json'),
           ('maps/quest-coder/tours.json', 'inputs/quest-tours.json'),
           ('maps/dag-gps/layers.json', 'inputs/self-legacy-layers.json'),
           ('docs/V1_RELEASE.md', 'V1_RELEASE.md'),
           ('docs/SUPPORTED_SOURCES.md', 'SUPPORTED_SOURCES.md')]
EVIDENCE = ['artifacts/release-' + name + '.json'
            for name in ('browser', 'accessibility', 'performance', 'ui-performance')]
# Build and smoke intentionally rebuild timestamp-bearing navigators. Freeze the
# final generation at the end of smoke: refresh/tour/impact/trust/onboarding/
# feedback consumers exercise it. Editors have no later legitimate writer.
PRODUCERS = {
    'build': ['dist/onboarding-quest.html', 'dist/onboarding-dag-gps.html',
              'artifacts/onboarding-quest-draft.json'],
    'smoke': ['dist/quest-refresh', 'dist/dag-gps', 'dist/quest-no-tours',
              'dist/quest-coder.html', 'dist/onboarding-dag-gps', 'dist/onboarding-quest'],
    'release_session': ['dist/release-session-quest', 'dist/release-session-self',
                        'artifacts/release-session-*', EVIDENCE[0]],
    'accessibility': [EVIDENCE[1]],
    'performance': [EVIDENCE[2]],
    'ui_performance': [EVIDENCE[3], 'dist/release-synthetic-1000.html',
                       'dist/release-synthetic-5000.html',
                       'artifacts/release-synthetic-1000.json',
                       'artifacts/release-synthetic-5000.json'],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root, *args):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def input_inventory(root):
    """All relevant recursive code/test/data/docs, including untracked/ignored
    additions; all tracked paths as a conservative extra. Build outputs and
    interpreter caches are explicitly separate, never inputs to discovery.
    """
    names = set(git(root, 'ls-files', '-z').split('\0')) - {''}
    # Walk all non-output project trees, not just today's directories: a new
    # untracked package/fixture must not evade freezing by choosing a new folder.
    for directory, dirs, files in os.walk(root):
        base = Path(directory)
        dirs[:] = [name for name in dirs if name != '.git' and name not in CACHE_DIRS
                   and not (base == root and name in OUTPUT_ROOTS)]
        for name in dirs:
            if (base / name).is_symlink():
                raise ValueError('Unsafe input directory symlink: ' + str(base / name))
        for name in files:
            if name != '.git' and name not in CACHE_DIRS:
                names.add((base / name).relative_to(root).as_posix())
    names = {n for n in names if n.split('/')[0] not in OUTPUT_ROOTS
             and '.git' not in Path(n).parts
             and not any(part in CACHE_DIRS for part in Path(n).parts)}
    return inventory(root, sorted(names))


def inventory(root, selectors):
    paths = set()
    for selector in selectors:
        matches = list(root.glob(selector)) if '*' in selector else [root / selector]
        if not matches:
            raise ValueError('Missing frozen inventory: ' + selector)
        for p in matches:
            if not p.exists():
                raise ValueError('Missing frozen input: ' + str(p))
            children = p.rglob('*') if p.is_dir() else [p]
            for child in children:
                if child.is_file():
                    if child.is_symlink() or root.resolve() not in child.resolve().parents:
                        raise ValueError('Unsafe frozen input path: ' + str(child))
                    paths.add(child.relative_to(root).as_posix())
    return {name: sha(root / name) for name in sorted(paths)}


def same(expected, actual, label):
    if expected != actual:
        added = sorted(actual.keys() - expected.keys())
        deleted = sorted(expected.keys() - actual.keys())
        changed = sorted(k for k in expected.keys() & actual.keys() if expected[k] != actual[k])
        raise ValueError(label + ' inventory/bytes changed: added=' + repr(added) +
                         ' deleted=' + repr(deleted) + ' changed=' + repr(changed))


def verify_inputs(root, expected):
    same(expected, input_inventory(root), 'Gate input')


def provenance(root):
    return dict(head=git(root, 'rev-parse', 'HEAD'),
                status=git(root, 'status', '--porcelain', '--untracked-files=all'),
                diff=hashlib.sha256((git(root, 'diff', '--binary', 'HEAD') + '\n' +
                                    git(root, 'diff', '--binary', '--cached')).encode()).hexdigest())


def verify_provenance(root, expected):
    if provenance(root) != expected:
        raise ValueError('HEAD/worktree provenance changed during verification')


def verify_artifacts(root, artifacts):
    for group in artifacts.values():
        same(group['files'], inventory(root, group['selectors']), 'Verified artifact')


def freeze(root, artifacts, gate, extra=()):
    selectors = list(PRODUCERS.get(gate, [])) + list(extra)
    # Screenshots and actual downloads are evidence too. Resolve only within this
    # worktree; no paths supplied by JSON are ever executed.
    import json
    for name in PRODUCERS.get(gate, []):
        if name in EVIDENCE:
            report = json.loads((root / name).read_text())
            references = list(report.get('screenshots', []))
            for session in report.get('sessions', []):
                references.extend(session[k] for k in ('downloadedLayers', 'downloadedAliases', 'downloadedFeedback'))
            for reference in references:
                try:
                    selectors.append(Path(reference).resolve().relative_to(root.resolve()).as_posix())
                except ValueError:
                    raise ValueError('Release evidence outside worktree: ' + reference)
    artifacts[gate] = dict(boundary='successful producer/test gate: ' + gate,
                           selectors=selectors, files=inventory(root, selectors))


def expected_payloads(root, report):
    if report.get('schema') != SCHEMA:
        raise ValueError('Unbound/old verification contract; rerun release_check.py (requires ' + SCHEMA + ')')
    verify_inputs(root, report['inputs'])
    verify_provenance(root, report['provenance_start'])
    if report['provenance_start'] != report['provenance_end']:
        raise ValueError('Start/end verification provenance differs')
    verify_artifacts(root, report['artifacts'])
    expected = dict(report['inputs'])
    for group in report['artifacts'].values():
        for name, digest in group['files'].items():
            if name in expected and expected[name] != digest:
                raise ValueError('Conflicting frozen artifact: ' + name)
            expected[name] = digest
    missing = [name for name in [s for s, _ in BUNDLE] + EVIDENCE if name not in expected]
    if missing:
        raise ValueError('Missing verified payload/evidence binding: ' + repr(missing))
    return expected
