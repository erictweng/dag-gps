import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from app.repositories import _acquire_repository_for_test
from app.snapshots import SnapshotError, build_workspace_snapshot

URL = 'https://github.com/example/preview-fixture'


def git(repo, *args):
    return subprocess.run(['/usr/bin/git', '-C', str(repo), *args], text=True,
                          check=True, capture_output=True).stdout.strip()


def acquired(root, files):
    repo = root / 'source'; repo.mkdir(parents=True)
    git(repo, 'init', '--quiet'); git(repo, 'config', 'user.email', 'fixture@example.invalid'); git(repo, 'config', 'user.name', 'Fixture')
    for name, text in files.items():
        path = repo / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding='utf-8')
    git(repo, 'add', '.'); git(repo, 'commit', '--quiet', '-m', 'fixture')
    commit = git(repo, 'rev-parse', 'HEAD')
    return _acquire_repository_for_test(URL, root / 'cache', str(repo), commit), commit


class WorkspacePreviewTests(unittest.TestCase):
    def test_unresolved_extraction_is_partial_inventory_visible_and_never_reviewed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {'src/main.js': "import x from './missing.js';\nconsole.log(x);\n", 'notes.txt': 'visible\n'})
            built = build_workspace_snapshot(result, root / 'out')
            preview = json.loads(Path(built['preview_path']).read_text())
            inventory = json.loads(Path(built['inventory_path']).read_text())
            self.assertEqual(preview['state'], 'partial')
            self.assertFalse(preview['grouping']['reviewed'])
            self.assertEqual(preview['grouping']['status'], 'proposed')
            self.assertNotIn('approved', preview['grouping'])
            self.assertEqual(inventory['counts']['files'], 2)
            self.assertTrue(preview['diagnostics']['unresolved'])

    def test_file_and_layer_cycles_keep_all_edges_and_block_grouping_publication(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {
                'one/a.js': "import '../two/b.js';\n",
                'two/b.js': "import '../one/a.js';\n",
            })
            built = build_workspace_snapshot(result, root / 'out')
            preview = json.loads(Path(built['preview_path']).read_text())
            pairs = {(e['from'], e['to']) for e in preview['map']['file_edges']}
            self.assertEqual(pairs, {('one/a.js', 'two/b.js'), ('two/b.js', 'one/a.js')})
            self.assertTrue(preview['diagnostics']['file_cycles'])
            self.assertTrue(preview['diagnostics']['layer_cycle'])
            self.assertTrue(preview['publicationBlocked'])

    def test_supported_js_and_python_edges_have_source_witness_paths(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {
                'web/a.js': "import './b.js';\n", 'web/b.js': 'export const b = 1;\n',
                'pkg/__init__.py': 'from . import util\n', 'pkg/util.py': 'VALUE = 1\n',
            })
            built = build_workspace_snapshot(result, root / 'out')
            preview = json.loads(Path(built['preview_path']).read_text())
            pairs = {(e['from'], e['to']) for e in preview['map']['file_edges']}
            self.assertIn(('web/a.js', 'web/b.js'), pairs)
            self.assertIn(('pkg/__init__.py', 'pkg/util.py'), pairs)
            for edge in preview['map']['file_edges']:
                self.assertEqual(edge['witness']['path'], edge['from'])
                self.assertIsNone(edge['witness']['start'])
                self.assertIsNone(edge['witness']['end'])

    def test_offline_html_escapes_hostile_source_names_and_has_no_remote_resources(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {'src/x</script><img src=x onerror=alert(1)>.js': 'export const x=1;\n'})
            built = build_workspace_snapshot(result, root / 'out')
            html = Path(built['html_path']).read_text()
            self.assertNotIn('</script><img', html)
            self.assertNotRegex(html, r'<(?:script|link|img)[^>]+(?:src|href)=["\']https?://')
            self.assertIn('https://github.com/example/preview-fixture', html)
            self.assertIn('application/json', html)
            self.assertIn('Dependency preview', html)

    def test_source_identity_counts_limits_and_scope_are_visible(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, commit = acquired(root, {'a.py': 'import os\n', 'blob.dat': 'plain\n'})
            built = build_workspace_snapshot(result, root / 'out', limits={'max_members': 9, 'max_file_bytes': 9999})
            preview = json.loads(Path(built['preview_path']).read_text())
            self.assertEqual(preview['source']['repo'], 'example/preview-fixture')
            self.assertEqual(preview['source']['commit'], commit)
            self.assertEqual(preview['inventoryCounts']['files'], 2)
            self.assertEqual(preview['limits']['max_members'], 9)
            self.assertIn('a.py', preview['extraction']['scope']['paths'])
            self.assertGreaterEqual(preview['diagnostics']['counts']['external'], 1)

    def test_unsupported_only_repository_still_publishes_inventory_first(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {'README.md': '# visible\n', 'data.txt': 'facts\n'})
            events = []
            built = build_workspace_snapshot(result, root / 'out', progress=events.append)
            preview = json.loads(Path(built['preview_path']).read_text())
            inventory = json.loads(Path(built['inventory_path']).read_text())
            self.assertEqual(events[0]['stage'], 'inventory-ready')
            self.assertEqual(inventory['counts']['files'], 2)
            self.assertEqual(preview['state'], 'partial')
            self.assertEqual(preview['map']['nodes'], [])
            self.assertEqual(preview['map']['file_edges'], [])

    def test_corrupt_endpoint_or_ownership_rejects_instead_of_hiding(self):
        from app.snapshots import _validate_preview
        base = {'source': {'repo': 'x/y', 'commit': 'a' * 40}, 'grouping': {'status': 'proposed', 'reviewed': False},
                'map': {'nodes': [{'id': 'layer', 'kind': 'layer'}, {'id': 'a.py', 'kind': 'file', 'path': 'a.py', 'layer': 'layer'}],
                        'edges': [], 'file_edges': [{'from': 'a.py', 'to': 'missing.py', 'type': 'import'}], 'layers': {'layer': {'files': ['a.py']}}}}
        with self.assertRaisesRegex(SnapshotError, 'endpoint'):
            _validate_preview(base, {'a.py'})
        base['map']['file_edges'] = []
        base['map']['nodes'][1]['layer'] = 'missing-layer'
        with self.assertRaisesRegex(SnapshotError, 'ownership'):
            _validate_preview(base, {'a.py'})

    def test_html_and_json_readback_hashes_are_reported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {'a.py': 'x=1\n'})
            built = build_workspace_snapshot(result, root / 'out')
            self.assertEqual(set(built['output_sha256']), {'inventory.json', 'preview.json', 'index.html', 'receipt.json'})
            self.assertTrue(all(len(value) == 64 for value in built['output_sha256'].values()))
    def test_offline_html_has_keyboard_file_controls_and_inert_detail_fields(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _ = acquired(root, {
                'src/a.js': "import './b.js';\n",
                'src/b.js': 'export const b=1;\n',
                'README.md': '# unsupported but inspectable\n',
            })
            built = build_workspace_snapshot(result, root / 'out')
            html = Path(built['html_path']).read_text()
            for marker in ('file-detail', 'detail-path', 'detail-sha256', 'detail-kind',
                           'detail-lines', 'detail-reason', 'detail-group', 'detail-links',
                           'id="group-links"'):
                self.assertIn(marker, html)
            # Groups render by folder label; opaque folder-<hash> ids are lookup keys only.
            self.assertIn('groupName(node.layer)', html)
            self.assertNotIn("li.textContent=id+': '", html)
            self.assertIn("button.type='button'", html)
            self.assertIn("addEventListener('keydown'", html)
            self.assertIn('.focus()', html)


if __name__ == '__main__':
    unittest.main()
