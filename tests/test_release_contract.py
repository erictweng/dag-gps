"""Synthetic isolated contract tests; never release gate evidence."""
import json
from unittest import mock
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


class InputContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / 'artifacts')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        for name in ['tests/test_aliases.py', 'tests/test_build_map.py', 'tests/test_render.py',
                     'tests/fixtures/nested/input.json', 'docs/SUPPORTED_SOURCES.md',
                     'scripts/runner.py', 'web/template.html', 'maps/unit/map.json', 'eval/cases.jsonl']:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('synthetic unit fixture')
        (self.root / '.gitignore').write_text('artifacts/\ndist/\n__pycache__/\n')
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Unit', '-c', 'user.email=unit@example.invalid',
                        'commit', '-qm', 'synthetic unit'], cwd=self.root, check=True)

    def contract(self):
        import release_contract
        return release_contract

    def test_complete_recursive_inventory_and_ignored_outputs_separate(self):
        c = self.contract()
        before = c.input_inventory(self.root)
        for name in ['tests/test_aliases.py', 'tests/test_build_map.py', 'tests/test_render.py',
                     'docs/SUPPORTED_SOURCES.md', 'tests/fixtures/nested/input.json']:
            self.assertIn(name, before)
        for name in ['artifacts/out.json', 'dist/index.html', 'scripts/__pycache__/runner.pyc']:
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text('ignored generated output')
        self.assertEqual(before, c.input_inventory(self.root))

    def test_edits_additions_deletions_and_renames_fail_closed(self):
        c = self.contract()
        for action in ['edit', 'add', 'delete', 'rename']:
            with self.subTest(action=action):
                before = c.input_inventory(self.root)
                p = self.root / 'tests/test_aliases.py'
                original = p.read_bytes()
                other = self.root / 'tests/new_untracked_test.py'
                if action == 'edit': p.write_text('edited')
                if action == 'add': other.write_text('new untracked code')
                if action == 'delete': p.unlink()
                if action == 'rename': p.rename(other)
                with self.assertRaises(ValueError):
                    c.verify_inputs(self.root, before)
                other.unlink(missing_ok=True)
                p.write_bytes(original)

    def test_head_and_worktree_provenance_drift_rejected(self):
        c = self.contract()
        before = c.provenance(self.root)
        p = self.root / 'tests/test_render.py'
        p.write_text('uncommitted change')
        with self.assertRaises(ValueError): c.verify_provenance(self.root, before)
        subprocess.run(['git', 'add', '.'], cwd=self.root, check=True)
        subprocess.run(['git', '-c', 'user.name=Unit', '-c', 'user.email=unit@example.invalid',
                        'commit', '-qm', 'drift'], cwd=self.root, check=True)
        with self.assertRaises(ValueError): c.verify_provenance(self.root, before)

    def test_ignored_relevant_code_not_silently_excluded(self):
        c = self.contract()
        (self.root / '.gitignore').write_text('tests/new*.py\nartifacts/\ndist/\n')
        (self.root / 'tests/new_hidden.py').write_text('untracked but relevant')
        self.assertIn('tests/new_hidden.py', c.input_inventory(self.root))
        before = c.input_inventory(self.root)
        p = self.root / 'new-package/fixtures/nested.py'
        p.parent.mkdir(parents=True)
        p.write_text('new relevant code outside existing source directories')
        self.assertIn('new-package/fixtures/nested.py', c.input_inventory(self.root))
        with self.assertRaises(ValueError): c.verify_inputs(self.root, before)

    def run_synthetic_gates(self, build, consumer, producers):
        # Actual subprocess commands in an isolated synthetic Git root. Only the
        # unavailable private-source prerequisite is mocked, NEVER gate outcomes.
        import release_check as runner
        c = self.contract()
        (self.root / '.verify.json').write_text(json.dumps(dict(required_files=[],
            commands={'build': build, 'test': consumer}, timeout_seconds=10)))
        output = self.root / 'artifacts/verification'
        real_run = subprocess.run
        def source_probe(command, **kwargs):
            if command[:2] == ['git', '-C']:
                return subprocess.CompletedProcess(command, 0, stdout=b'', stderr=b'')
            return real_run(command, **kwargs)
        with mock.patch.object(runner, 'ROOT', self.root), mock.patch.object(c, 'PRODUCERS', producers), \
             mock.patch.object(sys, 'argv', ['release_check.py', '--legacy-only', '--output', str(output)]), \
             mock.patch.object(runner.subprocess, 'run', side_effect=source_probe):
            self.assertEqual(runner.main(), 1)
        report = json.loads((output / 'verification.json').read_text())
        self.assertEqual([row['returncode'] for row in report['results']], [0, 0, 1])
        self.assertEqual(report['results'][-1]['name'], 'integrity')
        self.assertTrue((output / 'test.stdout.log').is_file())
        self.assertFalse((output / 'package-result.json').exists())
        return report

    def test_runner_rejects_omitted_test_edit_across_gates_with_receipt(self):
        report = self.run_synthetic_gates('python3 -c "print(123)"',
            "python3 -c \"from pathlib import Path; Path('tests/test_render.py').write_text('changed')\"", {})
        self.assertIn('Gate input', report['results'][-1]['error'])

    def test_runner_rejects_head_drift_even_with_identical_source_bytes(self):
        report = self.run_synthetic_gates('python3 -c "print(123)"',
            'git -c user.name=Unit -c user.email=unit@example.invalid commit --allow-empty -qm drift', {})
        self.assertNotEqual(report['provenance_start']['head'], report['provenance_end']['head'])
        self.assertIn('provenance', report['results'][-1]['error'])

    def test_runner_rejects_artifact_changes_across_later_consumer_gates(self):
        report = self.run_synthetic_gates(
            "python3 -c \"from pathlib import Path; Path('dist').mkdir(); Path('dist/generated.html').write_text('tested')\"",
            "python3 -c \"from pathlib import Path; Path('dist/generated.html').write_text('changed')\"",
            {'build': ['dist/generated.html']})
        self.assertIn('Verified artifact', report['results'][-1]['error'])


if __name__ == '__main__':
    unittest.main()
