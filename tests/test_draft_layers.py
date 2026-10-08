"""Onboarding fixtures are synthetic unless explicitly pinned real snapshots."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_map import assign_layers, build, source_files
from build_project import BuildFailure, build_project, repo_identity
from draft_layers import draft_layers
from onboarding import DRAFT_SCHEMA, SPEC_SCHEMA, group_files, validate_spec
from render_layer_editor import render_editor


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        for path, text in {'main.js': 'require("./src/a.js");\n', 'src/a.js': 'require("../helpers/b.js");\n',
                           'helpers/b.js': '', 'app/[id]/route.ts': '', 'dist/ignored.js': '',
                           'node_modules/ignored.js': ''}.items():
            p = self.repo / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(text)
        self.git('init', '-q')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def spec(self, draft):
        return {'schema': SPEC_SCHEMA, 'repo': draft['repo'], 'layers': copy.deepcopy(draft['layers']),
                'onboarding': {'repo': draft['repo'], 'commit': draft['commit'], 'source_files': draft['source_files'],
                               'tops': draft['tops'], 'reviewed': True, 'reference_warnings': []}}

    def write_spec(self, spec):
        p = self.root / 'layers.json'
        p.write_text(json.dumps(spec))
        return str(p)

    def test_draft_deterministic_and_unapproved(self):
        a = draft_layers(self.repo, self.commit)
        self.assertEqual(a, draft_layers(self.repo, self.commit))
        self.assertFalse(a['reviewed'])
        self.assertEqual(a['schema'], DRAFT_SCHEMA)
        self.assertEqual(len(a['source_files']), 4)
        self.assertEqual(a['diagnostics']['unmapped'], [])
        self.assertEqual(a['diagnostics']['duplicate_assignments'], {})

    def test_pinned_source_ignores_mutable_worktree(self):
        a = draft_layers(self.repo, self.commit)
        (self.repo / 'main.js').write_text('require("./missing.js");')
        (self.repo / 'new.js').write_text('')
        self.assertEqual(a, draft_layers(self.repo, self.commit))

    def test_flat_root_and_helper_reason_visible(self):
        groups = group_files(['main.js', 'helpers/a.py', 'shared/b.js'])
        self.assertTrue(any('Flat root' in g['reason'] for g in groups))
        self.assertTrue(any('sharing is not inferred' in g['reason'] for g in groups))

    def test_stable_folder_ids_independent_of_file_order_and_rename(self):
        a = group_files(['src/a.js', 'src/b.js'])
        b = group_files(['src/b.js', 'src/a.js', 'src/c.js'])
        self.assertEqual(a[0]['id'], b[0]['id'])
        a[0]['label'] = 'Renamed'
        self.assertEqual(a[0]['id'], b[0]['id'])

    def test_exact_brackets_are_literal_not_fnmatch(self):
        d = draft_layers(self.repo, self.commit)
        owners, unmapped, double = assign_layers(d['source_files'], d['layers'])
        self.assertIn('app/[id]/route.ts', owners)
        self.assertEqual((unmapped, double), ([], {}))

    def test_exclusions_match_generic_builder(self):
        d = draft_layers(self.repo, self.commit)
        self.assertEqual(d['source_files'], source_files(str(self.repo), self.commit))
        self.assertFalse(any(p.startswith(('dist/', 'node_modules/')) for p in d['source_files']))

    def test_cycle_draft_retains_source_edges_and_is_not_approved(self):
        (self.repo / 'helpers/b.js').write_text('require("../src/a.js");\n')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'cycle')
        d = draft_layers(self.repo, 'HEAD')
        self.assertTrue(d['diagnostics']['layer_cycle'])
        self.assertTrue(d['diagnostics']['file_cycles'])
        self.assertEqual(len(d['file_edges']), 3)
        self.assertFalse(d['reviewed'])

    def test_unresolved_draft_returns_actionable_failure_without_publication(self):
        (self.repo / 'main.js').write_text('require("./generated.json");')
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.test', 'commit', '-qm', 'missing')
        d = draft_layers(self.repo, 'HEAD')
        self.assertTrue(d['diagnostics']['unresolved'])
        self.assertTrue(any(not c['ok'] for c in d['checks']))

    def test_reviewed_export_builds_and_legacy_globs_still_work(self):
        d = draft_layers(self.repo, self.commit)
        out = self.root / 'out'
        r = build_project(str(self.repo), self.commit, self.write_spec(self.spec(d)), out)
        self.assertEqual(r['meta']['counts']['files'], 4)
        legacy = {'layers': [{'id': 'all', 'label': 'All', 'globs': ['**']} ]}
        # Existing root-aware glob semantics need path-depth patterns, not a new ** rule.
        legacy['layers'][0]['globs'] = ['*.js', 'src/**', 'helpers/**', 'app/**']
        build_project(str(self.repo), self.commit, self.write_spec(legacy), out)

    def test_draft_and_unreviewed_fail_preserving_all_outputs(self):
        d = draft_layers(self.repo, self.commit)
        out = self.root / 'out'
        build_project(str(self.repo), self.commit, self.write_spec(self.spec(d)), out)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        s = self.spec(d)
        s['onboarding']['reviewed'] = False
        for bad in [d, s]:
            with self.assertRaises(ValueError):
                build_project(str(self.repo), self.commit, self.write_spec(bad), out)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_invalid_ownership_preserves_all_outputs(self):
        d = draft_layers(self.repo, self.commit)
        out = self.root / 'out'
        build_project(str(self.repo), self.commit, self.write_spec(self.spec(d)), out)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        for mode in ['missing', 'double', 'unknown', 'empty']:
            s = self.spec(d)
            if mode == 'missing': s['layers'][0]['files'].clear()
            if mode == 'double': s['layers'][1]['files'].extend(s['layers'][0]['files'])
            if mode == 'unknown': s['layers'][0]['files'].append('unknown.js')
            if mode == 'empty': s['layers'].append({'id': 'empty', 'label': 'Empty', 'files': []})
            with self.assertRaises(ValueError):
                build_project(str(self.repo), self.commit, self.write_spec(s), out)
            self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})

    def test_wrong_repo_commit_scope_inventory_rejected(self):
        d = draft_layers(self.repo, self.commit)
        s = self.spec(d)
        s['repo'] = 'other/repo'
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            validate_spec(s, d['source_files'], d['repo'], d['commit'], d['tops'])
        for field, value in [('repo', 'other'), ('commit', 'a'*40), ('source_files', []), ('tops', [])]:
            s = self.spec(d)
            s['onboarding'][field] = value
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                validate_spec(s, d['source_files'], d['repo'], d['commit'], d['tops'])

    def test_duplicate_id_and_files_globs_conflict_rejected(self):
        d = draft_layers(self.repo, self.commit)
        for change in ['id', 'globs', 'duplicate']:
            s = self.spec(d)
            if change == 'id': s['layers'][1]['id'] = s['layers'][0]['id']
            if change == 'globs': s['layers'][0]['globs'] = ['**']
            if change == 'duplicate': s['layers'][0]['files'] *= 2
            with self.assertRaises(ValueError):
                validate_spec(s, d['source_files'], d['repo'], d['commit'], d['tops'])

    def test_renderer_escape_script_closing_text_and_bound_size(self):
        d = draft_layers(self.repo, self.commit)
        d['layers'][0]['label'] = '</script><script>alert(1)</script>'
        html = render_editor(d)
        self.assertNotIn('</script><script>alert(1)', html)
        self.assertIn('\\u003c/script>', html)
        d['layers'][0]['label'] = 'x' * (8*1024*1024)
        with self.assertRaisesRegex(ValueError, '8 MiB'):
            render_editor(d)

    def test_cycle_approved_spec_rejected_preserves_output(self):
        d = draft_layers(self.repo, self.commit)
        out = self.root / 'out'
        build_project(str(self.repo), self.commit, self.write_spec(self.spec(d)), out)
        before = {p.name: p.read_bytes() for p in out.iterdir()}
        # Reverse grouping edge created by moving entry point into helpers while src depends on it.
        s = self.spec(d)
        root = next(l for l in s['layers'] if 'main.js' in l['files'])
        helpers = next(l for l in s['layers'] if 'helpers/b.js' in l['files'])
        helpers['files'].append('main.js')
        s['layers'].remove(root)
        with self.assertRaises(BuildFailure):
            build_project(str(self.repo), self.commit, self.write_spec(s), out)
        self.assertEqual(before, {p.name: p.read_bytes() for p in out.iterdir()})


if __name__ == '__main__':
    unittest.main()
