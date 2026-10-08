"""Release runner must fail closed, rather than certify a plausible subset."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / (name + '.py'))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / 'artifacts').mkdir(exist_ok=True)

    def test_real_failure_is_retained_and_prevents_later_commands(self):
        runner = load('release_check')
        (ROOT / 'artifacts').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as directory:
            output = Path(directory)
            rows = runner.run({'bad': 'python3 -c "import sys; print(123); sys.exit(7)"',
                               'must_not_run': 'python3 -c "raise Exception()"'}, output)
            self.assertEqual([r['returncode'] for r in rows], [7])
            self.assertIn('123', (output / 'bad.stdout.log').read_text())
            self.assertFalse((output / 'must_not_run.stdout.log').exists())

    def test_timeout_is_failure(self):
        runner = load('release_check')
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as directory:
            with mock.patch.object(runner.subprocess, 'Popen') as popen, mock.patch.object(runner.os, 'killpg') as kill:
                popen.return_value.wait.side_effect = [subprocess.TimeoutExpired('probe', 1), 124]
                popen.return_value.pid = 123
                rows = runner.run({'timeout': 'probe'}, Path(directory), 1)
                kill.assert_called_once_with(123, runner.signal.SIGKILL)
            self.assertEqual(rows[0]['returncode'], 124)

    def test_missing_source_returns_nonzero(self):
        result = subprocess.run([sys.executable, 'scripts/release_check.py', '--quest-repo',
                                 str(ROOT / 'artifacts' / 'nonexistent-release-repo')], cwd=ROOT,
                                text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Missing pinned quest Git source', result.stderr)

    def test_positive_unit_bundle_keeps_verification_path_after_citation_review(self):
        # Synthetic unit-only payloads live in a disposable isolated root. These
        # do not count as browser/build evidence or a real release candidate.
        package = load('package_release')
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as directory:
            root = Path(directory)
            (root / 'artifacts').mkdir()
            commit = 'a' * 40
            outputs = ['dist/quest-refresh', 'dist/dag-gps', 'dist/release-session-quest', 'dist/release-session-self']
            for output in outputs:
                folder = root / output
                folder.mkdir(parents=True)
                for name in ['index.html', 'diff.json', 'report.json']:
                    (folder / name).write_text('Synthetic unit fixture only')
                (folder / 'map.json').write_text(json.dumps({'meta': {'repo': 'synthetic/unit', 'commit': commit, 'counts': {}}}))
            tours = {'repo': 'synthetic/unit', 'commit': commit, 'tours': [{'steps': [{'evidence': [{'path': 'unit.py', 'start': 1, 'end': 1, 'excerpt': 'pass'}]}], 'links': []}]}
            (root / 'dist/quest-refresh/index.html').write_text('var TOUR_DATA = ' + json.dumps(tours) + ';\n')
            for name in ['dist/onboarding-quest.html', 'dist/onboarding-dag-gps.html', 'artifacts/release-session-quest-layers.json', 'artifacts/release-session-self-layers.json', 'maps/quest-coder/layers.json', 'maps/quest-coder/tours.json', 'maps/dag-gps/layers.json', 'docs/V1_RELEASE.md', 'docs/SUPPORTED_SOURCES.md']:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text('Synthetic unit fixture only')
            for name in ['release-browser.json', 'release-performance.json']:
                (root / 'artifacts' / name).write_text('{}')
            (root / 'artifacts/release-ui-performance.json').write_text(json.dumps({'browserVersion': 'unit', 'playwrightVersion': 'unit'}))
            (root / 'artifacts/release-accessibility.json').write_text(json.dumps({'states': [{'axe': {'engineVersion': 'unit'}}]}))
            verification = root / 'verification.json'
            names = ['build', 'test', 'smoke', 'release_session', 'accessibility', 'performance', 'ui_performance', 'milestone_acceptance']
            verification.write_text(json.dumps({'legacy_only': False, 'results': [{'name': name, 'returncode': 0} for name in names], 'build_commit': commit, 'inputs': {}, 'timestamp': 'synthetic-unit-only'}))
            with mock.patch.object(package, 'ROOT', root), mock.patch.object(sys, 'argv', ['package_release.py', '--verification', str(verification)]), mock.patch.object(package.subprocess, 'check_output', side_effect=lambda command, **kwargs: commit if command[1] == 'rev-parse' else ''):
                self.assertEqual(package.main(), 0)
            manifest = json.loads((root / 'dist/release/v1.0.0-rc.1/manifest.json').read_text())
            self.assertEqual(manifest['verification']['path'], str(verification))
            self.assertEqual(manifest['verification']['sha256'], package.sha(verification))
            self.assertEqual(manifest['privacy']['cited_source_review']['uniqueSourceRanges'], 1)

    def test_packaging_refuses_legacy_or_partial_verification(self):
        package = load('package_release')
        with tempfile.TemporaryDirectory(dir=ROOT / 'artifacts') as directory:
            path = Path(directory) / 'verification.json'
            for legacy, rows in [(True, []), (False, [{'name': 'build', 'returncode': 0}]),
                                 (False, [{'name': k, 'returncode': 1 if k == 'performance' else 0}
                                          for k in ['build', 'test', 'smoke', 'release_session', 'accessibility', 'performance', 'ui_performance']])]:
                path.write_text(json.dumps(dict(legacy_only=legacy, results=rows)))
                with mock.patch.object(sys, 'argv', ['package_release.py', '--verification', str(path)]):
                    with self.assertRaisesRegex(ValueError, 'Candidate blocked'):
                        package.main()
