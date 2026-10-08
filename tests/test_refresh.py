"""Real temporary Git snapshots exercise the refresh pipeline (stdlib only)."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_map as bm
import build_project as bp


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.invalid')
        self.put('a.js', "import './b.js';\n")
        self.put('b.js', 'export const b = 1;\n')
        self.put('gone.py', 'x = 1\n')
        self.first = self.commit()
        self.layers = self.root / 'layers.json'
        self.spec = {'layers': [
            {'id': 'a', 'label': 'Consumer', 'globs': ['a.js', 'gone.py']},
            {'id': 'b', 'label': 'Dependency', 'globs': ['b.js']}], 'manual_edges': []}
        self.write_spec()
        self.out = self.root / 'out'

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True).strip()

    def put(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'fixture snapshot')
        return self.git('rev-parse', 'HEAD')

    def write_spec(self):
        self.layers.write_text(json.dumps(self.spec))

    def build(self, ref=None, **kw):
        return bp.build_project(str(self.repo), ref or self.first, str(self.layers), str(self.out), **kw)

    def published(self):
        return {p.name: p.read_bytes() for p in self.out.iterdir() if p.is_file()}

    def test_actual_added_deleted_and_typed_connections(self):
        self.build()
        (self.repo / 'gone.py').unlink()
        self.put('new.js', "import './b.js';\n")
        self.put('a.js', 'export const a = 1;\n')
        self.spec['layers'][0]['globs'].append('new.js')
        self.write_spec()
        second = self.commit()
        report = self.build(second)
        diff = json.loads((self.out / 'diff.json').read_text())
        self.assertEqual(diff['added_files'], ['new.js'])
        self.assertEqual(diff['deleted_files'], ['gone.py'])
        self.assertIn({'scope': 'file_edges', 'from': 'new.js', 'to': 'b.js', 'type': 'import'}, diff['added_connections'])
        self.assertIn({'scope': 'file_edges', 'from': 'a.js', 'to': 'b.js', 'type': 'import'}, diff['removed_connections'])
        self.assertEqual(diff['baseline']['commit'], self.first)
        self.assertEqual(diff['snapshot']['commit'], second)
        self.assertEqual(report['meta']['snapshot_commit'], second)

    def test_assignment_change_is_not_silent(self):
        self.build()
        self.spec['layers'][0]['globs'].remove('gone.py')
        self.spec['layers'][1]['globs'].append('gone.py')
        self.write_spec()
        self.build()
        diff = json.loads((self.out / 'diff.json').read_text())
        self.assertEqual(diff['assignment_changes'], [{'id': 'gone.py', 'from': 'a', 'to': 'b'}])
        self.assertEqual(diff['summary']['node_changes'], 3)
        self.assertEqual([n['id'] for n in diff['node_changes']], ['a', 'b', 'gone.py'])

    def test_mutable_worktree_not_extracted(self):
        self.put('uncommitted.js', "import './missing.js';")
        self.put('a.js', 'broken worktree')
        self.build()
        doc = json.loads((self.out / 'map.json').read_text())
        self.assertNotIn('uncommitted.js', [n['id'] for n in doc['nodes']])
        self.assertEqual(doc['file_edges'][0]['to'], 'b.js')

    def test_unmapped_failure_preserves_every_artifact(self):
        self.build()
        before = self.published()
        self.put('unknown.js', 'export const x = 1;')
        second = self.commit()
        with self.assertRaisesRegex(bp.BuildFailure, 'UNMAPPED unknown.js'):
            self.build(second)
        self.assertEqual(before, self.published())

    def test_duplicate_assignment_failure_preserves(self):
        self.build()
        before = self.published()
        self.spec['layers'][1]['globs'].append('a.js')
        self.write_spec()
        with self.assertRaisesRegex(bp.BuildFailure, 'DOUBLE a.js'):
            self.build()
        self.assertEqual(before, self.published())

    def test_cycle_failure_preserves(self):
        self.build()
        before = self.published()
        self.put('b.js', "import './a.js';")
        second = self.commit()
        with self.assertRaisesRegex(bp.BuildFailure, 'cycle:'):
            self.build(second)
        self.assertEqual(before, self.published())

    def test_unresolved_failure_preserves(self):
        self.build()
        before = self.published()
        self.put('a.js', "require('./missing.cjs');")
        second = self.commit()
        with self.assertRaisesRegex(bp.BuildFailure, 'UNRESOLVED:./missing.cjs'):
            self.build(second)
        self.assertEqual(before, self.published())

    def test_low_level_builder_preserves_failed_output(self):
        target = self.root / 'valid.json'
        target.write_text('previous valid artifact')
        self.spec['layers'][1]['globs'].append('a.js')
        self.write_spec()
        _, checks, _ = bm.build(str(self.repo), self.first, str(self.layers), str(target), ['a.js', 'b.js'])
        self.assertFalse(all(ok for ok, _, _ in checks))
        self.assertEqual(target.read_text(), 'previous valid artifact')

    def test_promotion_error_rolls_back_bytes(self):
        self.build()
        before = self.published()
        original = os.replace
        calls = []
        def fail_once(src, dest):
            calls.append(str(dest))
            if len(calls) == 3:
                raise OSError('injected promotion error')
            return original(src, dest)
        with patch.object(bp.os, 'replace', side_effect=fail_once):
            with self.assertRaisesRegex(OSError, 'injected'):
                # call publish directly: build_map also uses os.replace
                with tempfile.TemporaryDirectory(dir=self.out) as stage:
                    for name in before:
                        (Path(stage) / name).write_text('replacement')
                    bp.publish(stage, self.out, sorted(before))
        self.assertEqual(before, self.published())

    def test_render_failure_preserves(self):
        self.build()
        before = self.published()
        with patch.object(bp, 'render', side_effect=ValueError('bad template')):
            with self.assertRaisesRegex(ValueError, 'bad template'):
                self.build()
        self.assertEqual(before, self.published())

    def test_identity_normalizes_remote_not_spec(self):
        for url in ['git@github.com:someone/project.git', 'https://github.com/someone/project.git']:
            if 'origin' in self.git('remote').split():
                self.git('remote', 'set-url', 'origin', url)
            else:
                self.git('remote', 'add', 'origin', url)
            self.assertEqual(bp.repo_identity(str(self.repo)), 'someone/project')
        self.git('remote', 'remove', 'origin')
        self.assertEqual(bp.repo_identity(str(self.repo)), 'local:' + str(self.repo.resolve()))

    def test_same_snapshot_diff_deterministic(self):
        self.build()
        doc = json.loads((self.out / 'map.json').read_text())
        newer = copy.deepcopy(doc)
        newer['meta']['built_at'] = 'later'
        newer['nodes'].reverse()
        diff = bp.snapshot_diff(doc, newer)
        self.assertTrue(all(v == 0 for v in diff['summary'].values()))
        self.assertEqual(bp.snapshot_diff(doc, newer), bp.snapshot_diff(doc, newer))

    def test_foreign_previous_rejected_without_write(self):
        self.build()
        before = self.published()
        prev = json.loads(before['map.json'])
        prev['meta']['repo'] = 'another/repo'
        path = self.root / 'foreign.json'
        path.write_text(json.dumps(prev))
        with self.assertRaisesRegex(bp.BuildFailure, 'another repository'):
            self.build(previous_map=path)
        self.assertEqual(before, self.published())

    def test_commonjs_umd_and_python_script_imports_are_real(self):
        self.put('a.js', "/* require('./ghost') */\nconst fixture = \"require('./ghost')\";\n(function(){const b=require('./b.js');})();\n")
        self.put('gone.py', 'from helper import (\n thing,\n)\n')
        self.put('helper.py', 'thing = 1\n')
        self.spec['layers'][0]['globs'].append('helper.py')
        self.write_spec()
        second = self.commit()
        self.build(second)
        doc = json.loads((self.out / 'map.json').read_text())
        self.assertIn({'from': 'a.js', 'to': 'b.js', 'type': 'import', 'cross_layer': True}, doc['file_edges'])
        self.assertIn({'from': 'gone.py', 'to': 'helper.py', 'type': 'import', 'cross_layer': False}, doc['file_edges'])
        self.assertEqual(doc['diagnostics']['unresolved'], [])

    def test_unsupported_constructs_reported_not_guessed(self):
        self.put('a.js', 'require(variable);\n')
        self.put('gone.py', 'from .helper import thing\n')
        second = self.commit()
        self.build(second)
        doc = json.loads((self.out / 'map.json').read_text())
        self.assertEqual(len(doc['diagnostics']['unsupported']), 2)
        self.assertEqual(doc['file_edges'], [])

    def test_ambiguous_python_local_import_rejects_without_guessing(self):
        self.build()
        before = self.published()
        self.put('gone.py', 'from helper import thing\n')
        self.put('one/helper.py', 'thing = 1\n')
        self.put('two/helper.py', 'thing = 2\n')
        self.spec['layers'][0]['globs'] += ['one/**', 'two/**']
        self.write_spec()
        second = self.commit()
        with self.assertRaisesRegex(bp.BuildFailure, 'ambiguous Python helper'):
            self.build(second)
        self.assertEqual(before, self.published())

    def test_vendor_generated_and_node_modules_excluded(self):
        for d in ['vendor', 'dist', '.next', 'node_modules', '.venv', 'artifacts']:
            self.put(d + '/unmapped.js', "require('./missing');")
        second = self.commit()
        report = self.build(second)
        self.assertEqual(report['meta']['counts']['files'], 3)
