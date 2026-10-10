import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

from app.repositories import _acquire_repository_for_test
import app.snapshots as snapshots
from app.snapshots import SnapshotCancelled, SnapshotError, build_workspace_snapshot


URL = 'https://github.com/example/inventory-fixture'


def git(repo, *args, input_data=None):
    return subprocess.run(['/usr/bin/git', '-C', str(repo), *args], input=input_data,
                          text=True, check=True, capture_output=True).stdout.strip()


def repository(root, files):
    repo = root / 'source'
    repo.mkdir(parents=True)
    git(repo, 'init', '--quiet')
    git(repo, 'config', 'user.email', 'fixture@example.invalid')
    git(repo, 'config', 'user.name', 'Fixture')
    for name, value in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(value, encoding='utf-8')
    git(repo, 'add', '.')
    git(repo, 'commit', '--quiet', '-m', 'fixture')
    return repo, git(repo, 'rev-parse', 'HEAD')


def acquire(root, files):
    repo, commit = repository(root, files)
    result = _acquire_repository_for_test(URL, root / 'git-cache', str(repo), commit)
    return result, commit, repo


def tree_hash(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob('*')) if p.is_file()}


def exact_tree(path):
    result = {}
    for parent, dirs, files in os.walk(path, followlinks=False):
        for name in sorted(dirs + files):
            item = Path(parent) / name
            key = item.relative_to(path).as_posix()
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                result[key] = ('symlink', os.readlink(item))
            elif stat.S_ISDIR(info.st_mode):
                result[key] = ('directory', None)
            elif stat.S_ISREG(info.st_mode):
                result[key] = ('file', hashlib.sha256(item.read_bytes()).hexdigest())
            else:
                result[key] = ('special', info.st_mode)
    return result


class WorkspaceSnapshotTests(unittest.TestCase):
    def test_rejection_preserves_previous_publication_bytes(self):
        # Git-tree symlinks are now inventoried (see GitTreeLinkTests); a bound
        # violation is the rejected input that must leave the old publication intact.
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            good, _, _ = acquire(root / 'good', {'src/main.py': 'print("data")\n'})
            out = root / 'published'
            build_workspace_snapshot(good, out)
            before = tree_hash(out)

            repo, commit = repository(root / 'bad', {'safe.py': 'x = 1\n', 'big.py': '1234567890\n'})
            bad = _acquire_repository_for_test(URL, root / 'bad-cache', str(repo), commit)
            with self.assertRaisesRegex(SnapshotError, 'per-file'):
                build_workspace_snapshot(bad, out, limits={'max_file_bytes': 8})
            self.assertEqual(before, tree_hash(out))

    def test_inventory_hashes_exact_bytes_and_labels_binary_unsupported(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, commit, _ = acquire(root, {
                'src/app.py': 'from . import missing\n',
                'assets/logo.bin': b'\x00\xff\x10',
                'README.md': '# data\n',
            })
            built = build_workspace_snapshot(result, root / 'published')
            inventory = json.loads(Path(built['inventory_path']).read_text())
            self.assertEqual(inventory['source']['commit'], commit)
            by_path = {item['path']: item for item in inventory['files']}
            self.assertEqual(by_path['assets/logo.bin']['sha256'], hashlib.sha256(b'\x00\xff\x10').hexdigest())
            self.assertEqual(by_path['assets/logo.bin']['contentKind'], 'binary')
            self.assertEqual(by_path['assets/logo.bin']['extraction']['status'], 'unsupported')
            self.assertIsNone(by_path['assets/logo.bin']['lineCount'])
            self.assertEqual(by_path['README.md']['extraction']['status'], 'unsupported')

    def test_member_file_and_expanded_bounds_fail_before_publication(self):
        cases = [
            ({'a': '1', 'b': '2'}, {'max_members': 1}, 'member'),
            ({'big.py': '12345'}, {'max_file_bytes': 4}, 'per-file'),
            ({'a.py': '123', 'b.py': '456'}, {'max_expanded_bytes': 5}, 'expanded'),
        ]
        for files, limits, message in cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                result, _, _ = acquire(root, files)
                with self.assertRaisesRegex(SnapshotError, message):
                    build_workspace_snapshot(result, root / 'published', limits=limits)
                self.assertFalse((root / 'published').exists())


    def test_export_attributes_do_not_change_authoritative_blob_bytes(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            raw_bytes = b'$Format:%H$\n'
            result, _, _ = acquire(root, {'.gitattributes': 'value.txt export-subst\n', 'value.txt': raw_bytes})
            built = build_workspace_snapshot(result, root / 'out')
            inventory = json.loads(Path(built['inventory_path']).read_text())
            item = next(x for x in inventory['files'] if x['path'] == 'value.txt')
            self.assertEqual(item['sha256'], hashlib.sha256(raw_bytes).hexdigest())

    def test_cancellation_and_faulted_readback_preserve_previous_directory(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            first, _, _ = acquire(root / 'one', {'a.py': 'x=1\n'})
            out = root / 'out'
            build_workspace_snapshot(first, out)
            before = tree_hash(out)
            second, _, _ = acquire(root / 'two', {'b.py': 'x=2\n'})
            event = threading.Event(); event.set()
            with self.assertRaises(SnapshotCancelled):
                build_workspace_snapshot(second, out, cancel=event)
            self.assertEqual(before, tree_hash(out))
            with self.assertRaisesRegex(SnapshotError, 'readback'):
                build_workspace_snapshot(second, out, _fault='readback')
            self.assertEqual(before, tree_hash(out))
            fresh = root / 'fresh'
            with self.assertRaisesRegex(SnapshotError, 'readback'):
                build_workspace_snapshot(second, fresh, _fault='readback')
            self.assertFalse(fresh.exists())

    def test_idempotence_binds_source_options_and_limits_and_keeps_overlays_separate(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _, _ = acquire(root, {'src/a.py': 'x=1\n'})
            out = root / 'out'
            first = build_workspace_snapshot(result, out)
            overlay = out.parent / 'manual-overlays' / 'notes.json'
            overlay.parent.mkdir(); overlay.write_text('{"human":true}\n')
            hashes = tree_hash(out)
            second = build_workspace_snapshot(result, out)
            self.assertTrue(second['cache_hit'])
            self.assertEqual(hashes, tree_hash(out))
            self.assertEqual(overlay.read_text(), '{"human":true}\n')
            changed = build_workspace_snapshot(result, out, extractor_options={'tops': ['src']})
            self.assertNotEqual(first['snapshot_id'], changed['snapshot_id'])
            limited = build_workspace_snapshot(result, out, extractor_options={'tops': ['src']},
                                               limits={'max_members': 999})
            self.assertNotEqual(changed['snapshot_id'], limited['snapshot_id'])
            self.assertEqual(overlay.read_text(), '{"human":true}\n')

    def test_publication_target_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _, _ = acquire(root, {'a.py': 'x=1\n'})
            real = root / 'real'; real.mkdir()
            link = root / 'linked'; link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(SnapshotError, 'symbolic link'):
                build_workspace_snapshot(result, link)
            self.assertEqual(list(real.iterdir()), [])

    def test_duplicate_or_unsafe_tree_names_are_rejected_by_parser(self):
        from app.snapshots import _parse_tree
        duplicate = b'100644 blob ' + b'a' * 40 + b' 1\ta.py\0' + b'100644 blob ' + b'b' * 40 + b' 1\ta.py\0'
        with self.assertRaisesRegex(SnapshotError, 'Duplicate'):
            _parse_tree(duplicate, 10)
        unsafe = b'100644 blob ' + b'a' * 40 + b' 1\t../escape.py\0'
        with self.assertRaisesRegex(SnapshotError, 'unsafe'):
            _parse_tree(unsafe, 10)
    def test_existing_receipt_requires_exact_complete_outputs_and_preserves_all_bytes(self):
        cases = ('empty', 'missing', 'extra', 'malformed-digest', 'unrelated-file')
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                result, _, _ = acquire(root, {'a.py': 'x=1\n'})
                out = root / 'out'; out.mkdir()
                outputs = {
                    'inventory.json': hashlib.sha256(b'inventory').hexdigest(),
                    'preview.json': hashlib.sha256(b'preview').hexdigest(),
                    'index.html': hashlib.sha256(b'html').hexdigest(),
                }
                for name, value in (('inventory.json', b'inventory'),
                                    ('preview.json', b'preview'), ('index.html', b'html')):
                    (out / name).write_bytes(value)
                selected = dict(outputs)
                if case == 'empty':
                    selected = {}
                elif case == 'missing':
                    selected.pop('preview.json')
                elif case == 'extra':
                    selected['other.json'] = hashlib.sha256(b'other').hexdigest()
                    (out / 'other.json').write_bytes(b'other')
                elif case == 'malformed-digest':
                    selected['preview.json'] = 'not-a-sha256'
                elif case == 'unrelated-file':
                    (out / 'user-owned.txt').write_bytes(b'preserve me')
                receipt = {
                    'schema': snapshots.RECEIPT_SCHEMA,
                    'cacheKey': 'a' * 64,
                    'snapshotId': 'b' * 64,
                    'source': {'kind': 'git-commit', 'url': URL,
                               'repo': 'example/inventory-fixture', 'commit': 'c' * 40},
                    'outputs': selected,
                    'producer': {'schema': 'dag-gps-producer/v1', 'files': {}},
                    'manualOverlays': 'separate; never overwritten or marked reviewed',
                }
                (out / 'receipt.json').write_text(json.dumps(receipt), encoding='utf-8')
                before = exact_tree(out)
                with self.assertRaises(SnapshotError):
                    build_workspace_snapshot(result, out)
                self.assertEqual(before, exact_tree(out))

    def test_oversized_receipt_rejects_from_size_before_any_read(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _, _ = acquire(root, {'a.py': 'x=1\n'})
            out = root / 'out'; out.mkdir()
            for name in ('inventory.json', 'preview.json', 'index.html'):
                (out / name).write_bytes(b'{}')
            limit = snapshots.MAX_RECEIPT_BYTES
            (out / 'receipt.json').write_bytes(b' ' * (limit + 1))
            before = exact_tree(out)
            opened = []
            real_os_open, real_io_open = os.open, io.open

            def record(path):
                try:
                    if Path(os.fsdecode(path)).name == 'receipt.json':
                        opened.append(os.fsdecode(path))
                except TypeError:
                    pass  # integer file descriptors

            def guarded_os_open(path, *args, **kwargs):
                record(path)
                return real_os_open(path, *args, **kwargs)

            def guarded_io_open(path, *args, **kwargs):
                record(path)
                return real_io_open(path, *args, **kwargs)

            with mock.patch('os.open', guarded_os_open), \
                    mock.patch('io.open', guarded_io_open), \
                    mock.patch('builtins.open', guarded_io_open):
                with self.assertRaisesRegex(SnapshotError, 'receipt exceeds'):
                    build_workspace_snapshot(result, out)
            self.assertEqual([], opened)
            self.assertEqual(before, exact_tree(out))

    def test_receipt_at_limit_is_read_with_bounded_no_follow_open(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _, _ = acquire(root, {'a.py': 'x=1\n'})
            out = root / 'out'
            first = build_workspace_snapshot(result, out)
            self.assertLessEqual((out / 'receipt.json').stat().st_size, snapshots.MAX_RECEIPT_BYTES)
            again = build_workspace_snapshot(result, out)
            self.assertTrue(again['cache_hit'])
            self.assertEqual(first['snapshot_id'], again['snapshot_id'])

    def test_internal_output_links_reject_without_mutating_publication_or_external_file(self):
        for kind in ('symlink', 'hardlink', 'receipt-symlink'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as raw:
                root = Path(raw)
                result, _, _ = acquire(root, {'a.py': 'x=1\n'})
                out = root / 'out'
                build_workspace_snapshot(result, out)
                outside = root / 'outside'; outside.write_bytes(b'outside sentinel\n')
                victim = out / ('receipt.json' if kind == 'receipt-symlink' else 'inventory.json')
                victim.unlink()
                if kind in ('symlink', 'receipt-symlink'):
                    victim.symlink_to(outside)
                else:
                    os.link(outside, victim)
                before = exact_tree(out); outside_before = outside.read_bytes()
                with self.assertRaises(SnapshotError):
                    build_workspace_snapshot(result, out)
                self.assertEqual(before, exact_tree(out))
                self.assertEqual(outside_before, outside.read_bytes())

    def test_portable_trailing_and_reserved_components_reject(self):
        from app.snapshots import _parse_tree
        oid = b'a' * 40
        for path in (b'a.', b'a ', b'CON', b'con.txt', b'dir/LPT9.py'):
            with self.subTest(path=path):
                raw = b'100644 blob ' + oid + b' 1\t' + path + b'\0'
                with self.assertRaisesRegex(SnapshotError, 'portable'):
                    _parse_tree(raw, 10)
        collision = (b'100644 blob ' + oid + b' 1\ta\0' +
                     b'100644 blob ' + b'b' * 40 + b' 1\ta.\0')
        with self.assertRaisesRegex(SnapshotError, 'portable'):
            _parse_tree(collision, 10)

    def test_graph_sidecar_bound_preserves_prior_and_absent_publications(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            good, _, _ = acquire(root / 'good', {'a.py': 'x=1\n'})
            out = root / 'out'; build_workspace_snapshot(good, out)
            before = exact_tree(out)
            bad, _, _ = acquire(root / 'bad', {'b.py': 'x=2\n'})

            def oversized(command, **kwargs):
                Path(command[3]).write_bytes(b'x' * 65)
                return subprocess.CompletedProcess(command, 0, b'', b'')

            with mock.patch.object(snapshots, '_run_trusted', side_effect=oversized):
                with self.assertRaisesRegex(SnapshotError, 'graph output'):
                    build_workspace_snapshot(bad, out, limits={'max_graph_output_bytes': 64})
                self.assertEqual(before, exact_tree(out))
                fresh = root / 'fresh'
                with self.assertRaisesRegex(SnapshotError, 'graph output'):
                    build_workspace_snapshot(bad, fresh, limits={'max_graph_output_bytes': 64})
                self.assertFalse(fresh.exists())
            self.assertFalse(any(p.name.startswith('.workspace-stage-') for p in root.iterdir()))

    def test_receipt_and_identity_bind_generated_producer_fingerprints(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, _, _ = acquire(root, {'a.py': 'x=1\n'})
            out = root / 'out'
            first = build_workspace_snapshot(result, out)
            receipt = json.loads((out / 'receipt.json').read_text())
            self.assertEqual(receipt['producer'], snapshots._producer_manifest())
            changed = json.loads(json.dumps(receipt['producer']))
            changed['files']['scripts/import_graph.py'] = 'f' * 64
            with mock.patch.object(snapshots, '_producer_manifest', return_value=changed):
                second = build_workspace_snapshot(result, out)
            self.assertFalse(second['cache_hit'])
            self.assertNotEqual(first['snapshot_id'], second['snapshot_id'])
    def test_isolated_copied_producer_mutation_changes_identity_and_misses_cache(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            acquisition, _, _ = acquire(root / 'fixture', {'src/a.py': 'x=1\n'})
            copied = root / 'producer'
            project = Path(__file__).resolve().parents[1]
            for relative in ('app/__init__.py',) + snapshots._PRODUCER_FILES:
                destination = copied / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(project / relative, destination)
            code = (
                'import json,sys; '
                'from app.snapshots import build_workspace_snapshot; '
                'print(json.dumps(build_workspace_snapshot(json.loads(sys.argv[1]),sys.argv[2])))'
            )
            env = dict(os.environ)
            env['PYTHONPATH'] = str(copied)
            output = root / 'published'
            first = json.loads(subprocess.run(
                [sys.executable, '-c', code, json.dumps(acquisition), str(output)],
                cwd=copied, env=env, check=True, text=True, capture_output=True).stdout)
            extractor = copied / 'scripts/import_graph.py'
            extractor.write_bytes(extractor.read_bytes() + b'\n# isolated producer drift\n')
            second = json.loads(subprocess.run(
                [sys.executable, '-c', code, json.dumps(acquisition), str(output)],
                cwd=copied, env=env, check=True, text=True, capture_output=True).stdout)
            self.assertNotEqual(first['snapshot_id'], second['snapshot_id'])
            self.assertFalse(second['cache_hit'])
            receipt = json.loads((output / 'receipt.json').read_text())
            self.assertEqual(receipt['producer']['files']['scripts/import_graph.py'],
                             hashlib.sha256(extractor.read_bytes()).hexdigest())


class GitTreeLinkTests(unittest.TestCase):
    """Git-tree symlinks (120000) and gitlinks (160000) are listed, never followed or fetched."""

    def _link_repo(self, root):
        repo, _ = repository(root, {'skills/tool.py': 'import os\n', 'main.py': 'x = 1\n'})
        (repo / '.agents').mkdir()
        (repo / '.agents' / 'skills').symlink_to('../skills')
        (repo / 'evil.py').symlink_to('/etc/passwd')
        git(repo, 'add', '.agents/skills', 'evil.py')
        git(repo, 'commit', '--quiet', '-m', 'links')
        return repo, git(repo, 'rev-parse', 'HEAD')

    def test_git_tree_symlinks_are_inventoried_as_unsupported_and_never_followed(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, commit = self._link_repo(root / 'r')
            self.assertIn('120000', git(repo, 'ls-tree', '-r', commit))
            result = _acquire_repository_for_test(URL, root / 'cache', str(repo), commit)
            out = root / 'published'
            built = build_workspace_snapshot(result, out)
            inventory = json.loads(Path(built['inventory_path']).read_text())
            preview = json.loads(Path(built['preview_path']).read_text())
            by_path = {item['path']: item for item in inventory['files']}
            for path, target in (('.agents/skills', '../skills'), ('evil.py', '/etc/passwd')):
                entry = by_path[path]
                self.assertEqual('symlink', entry['contentKind'])
                self.assertEqual('120000', entry['gitMode'])
                self.assertIsNone(entry['lineCount'])
                self.assertEqual(len(target), entry['bytes'])
                self.assertEqual(hashlib.sha256(target.encode()).hexdigest(), entry['sha256'])
                self.assertEqual(target, entry['linkTarget'])
                self.assertEqual('unsupported', entry['extraction']['status'])
                self.assertIn('never followed', entry['extraction']['reason'])
            self.assertEqual(2, inventory['counts']['symlinks'])
            self.assertEqual(0, inventory['counts']['submodules'])
            # No graph node or edge touches a link path, even one named *.py.
            mapped = {n.get('path') for n in preview['map']['nodes']}
            self.assertNotIn('evil.py', mapped)
            self.assertNotIn('.agents/skills', mapped)
            for edge in preview['map']['file_edges']:
                self.assertFalse({edge['from'], edge['to']} & {'evil.py', '.agents/skills'})
            # Nothing on the host is ever a link, and the host target is never read.
            self.assertNotIn('symlink', {kind for kind, _ in exact_tree(out).values()})
            secret = next((line for line in Path('/etc/passwd').read_text(errors='replace').splitlines()
                           if line.startswith('root:')), None)
            if secret:
                for item in out.rglob('*'):
                    if item.is_file():
                        self.assertNotIn(secret, item.read_text(errors='replace'))

    def test_git_submodule_is_inventoried_and_not_fetched(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, _ = repository(root / 'r', {'a.py': 'x = 1\n'})
            gitlink = 'ab' * 20
            git(repo, 'update-index', '--add', '--cacheinfo', f'160000,{gitlink},vendor/lib')
            git(repo, 'commit', '--quiet', '-m', 'submodule')
            commit = git(repo, 'rev-parse', 'HEAD')
            result = _acquire_repository_for_test(URL, root / 'cache', str(repo), commit)
            built = build_workspace_snapshot(result, root / 'published')
            inventory = json.loads(Path(built['inventory_path']).read_text())
            entry = {item['path']: item for item in inventory['files']}['vendor/lib']
            self.assertEqual('submodule', entry['contentKind'])
            self.assertEqual('160000', entry['gitMode'])
            self.assertEqual(gitlink, entry['submoduleCommit'])
            self.assertEqual(hashlib.sha256(gitlink.encode()).hexdigest(), entry['sha256'])
            self.assertEqual(0, entry['bytes'])
            self.assertIsNone(entry['lineCount'])
            self.assertEqual('unsupported', entry['extraction']['status'])
            self.assertEqual(1, inventory['counts']['submodules'])

    def test_links_count_against_member_and_byte_bounds(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, commit = self._link_repo(root / 'r')
            result = _acquire_repository_for_test(URL, root / 'cache', str(repo), commit)
            with self.assertRaisesRegex(SnapshotError, 'member'):
                build_workspace_snapshot(result, root / 'a', limits={'max_members': 3})
            with self.assertRaisesRegex(SnapshotError, 'per-file'):  # '/etc/passwd' is 11 bytes
                build_workspace_snapshot(result, root / 'b', limits={'max_file_bytes': 10})

    def test_publication_receipt_and_snapshot_load_with_links(self):
        from app.contracts import validate_snapshot
        from app.workspace_snapshot import load_publication
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            repo, commit = self._link_repo(root / 'r')
            result = _acquire_repository_for_test(URL, root / 'cache', str(repo), commit)
            build_workspace_snapshot(result, root / 'published')
            snapshot = load_publication(root / 'published')
            validate_snapshot(snapshot)
            kinds = {f['path']: f['contentKind'] for f in snapshot['inventory']}
            self.assertEqual('symlink', kinds['.agents/skills'])


if __name__ == '__main__':
    unittest.main()
