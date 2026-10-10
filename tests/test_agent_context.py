"""Local importer + real worker regressions; no model or network required."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from app.context import ContextError, build_context, read_source
from app.contracts import ContractError
from app.snapshots import build_workspace_snapshot
from app.workspace_snapshot import canonical_json, load_publication, write_snapshot
from test_workspace_snapshot import acquire, git, repository

NODE = shutil.which('node')
FILES = {
    'app/main.py': 'from lib import core\n# main\n# third\n',
    'app/util.py': 'X = 1\n',
    'app/__init__.py': '',
    'lib/core.py': '# café\nVALUE = 1\n# tail\n',
    'lib/util.py': 'Y = 2\n',
    'lib/__init__.py': '',
    'asset.bin': b'\x00\xff',
    'lines.txt': b'alpha\r\nbeta\ngamma',
    'unicode.txt': 'é\n雪\nlast\n',
}


class PublicationFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.root = Path(cls.tmp.name)
        acquired, cls.commit, cls.repo = acquire(cls.root, FILES)
        cls.git_dir = acquired['git_dir']
        out = cls.root / 'out'
        build_workspace_snapshot(acquired, out)
        cls.snapshot = load_publication(out)
        cls.snapshot_path = cls.root / 'snapshot.json'
        write_snapshot(cls.snapshot, cls.snapshot_path)


class SourceTests(PublicationFixture):
    def read(self, path='lines.txt', **kwargs):
        return read_source(self.git_dir, self.snapshot, path, **kwargs)

    def test_exact_lines_hash_and_inclusive_range(self):
        result = self.read(start=2, end=3)
        self.assertEqual(result, {
            'schema': 'dag-gps-source/v1', 'snapshotId': self.snapshot['snapshotId'],
            'path': 'lines.txt', 'sha256': hashlib.sha256(FILES['lines.txt']).hexdigest(),
            'lineCount': 3, 'start': 2, 'end': 3, 'lines': ['beta', 'gamma'],
            'truncated': False, 'nextStart': None,
        })
        self.assertEqual(['alpha', 'beta', 'gamma'], self.read()['lines'])
        self.assertFalse(self.read(start=1, end=1)['truncated'])

    def test_ranges_reject_non_int_and_out_of_bounds(self):
        for args in ({'start': 0}, {'end': 0}, {'start': 3, 'end': 2},
                     {'start': 4}, {'end': 4}, {'start': 1.0}, {'end': '2'},
                     {'start': True}, {'end': False}):
            with self.subTest(args=args), self.assertRaises(ContextError):
                self.read(**args)

    def test_paths_are_literal_inventory_members(self):
        for path in ('missing.txt', '../x', '/lines.txt', 'LINES.txt', 'lines.txt/',
                     './lines.txt', 'lines.txt\x00', None):
            with self.subTest(path=path), self.assertRaises(ContextError):
                self.read(path)

    def test_binary_and_unknown_kind_are_metadata_only(self):
        with self.assertRaisesRegex(ContextError, 'metadata only'):
            self.read('asset.bin')
        snapshot = copy.deepcopy(self.snapshot)
        next(f for f in snapshot['inventory'] if f['path'] == 'lines.txt')['contentKind'] = 'unknown'
        with self.assertRaisesRegex(ContextError, 'metadata only'):
            read_source(self.git_dir, snapshot, 'lines.txt')

    def test_git_symlink_and_submodule_entries_are_metadata_only(self):
        for kind in ('symlink', 'submodule'):
            with self.subTest(kind=kind):
                snapshot = copy.deepcopy(self.snapshot)
                entry = next(f for f in snapshot['inventory'] if f['path'] == 'lines.txt')
                entry.update(contentKind=kind, lineCount=None)
                with self.assertRaisesRegex(ContextError, 'metadata only'):
                    read_source(self.git_dir, snapshot, 'lines.txt')

    def test_stale_digest_and_line_count_rejected(self):
        for key, value in (('sha256', '0' * 64), ('lineCount', 2)):
            snapshot = copy.deepcopy(self.snapshot)
            next(f for f in snapshot['inventory'] if f['path'] == 'lines.txt')[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ContextError, 'stale|tampered'):
                read_source(self.git_dir, snapshot, 'lines.txt')

    def test_missing_git_directory_and_commit(self):
        with self.assertRaises(ContextError):
            read_source(self.root / 'absent', self.snapshot, 'lines.txt')
        with self.assertRaises(ContextError):
            read_source(self.snapshot_path, self.snapshot, 'lines.txt')
        snapshot = copy.deepcopy(self.snapshot)
        snapshot['source']['commit'] = '0' * 40
        snapshot['map']['meta']['snapshot_commit'] = '0' * 40
        with self.assertRaises(ContextError):
            read_source(self.git_dir, snapshot, 'lines.txt')

    def test_line_cap_and_continuation(self):
        first = self.read(max_lines=2)
        self.assertEqual(['alpha', 'beta'], first['lines'])
        self.assertEqual((True, 3, 1, 2), tuple(first[k] for k in ('truncated', 'nextStart', 'start', 'end')))
        self.assertEqual(['gamma'], self.read(start=first['nextStart'])['lines'])

    def test_byte_cap_counts_utf8_and_original_delimiters(self):
        result = self.read('unicode.txt', max_bytes=3)
        self.assertEqual(['é'], result['lines'])
        self.assertEqual(2, result['nextStart'])
        self.assertTrue(result['truncated'])
        self.assertEqual(['alpha'], self.read(max_bytes=7)['lines'])
        too_small = self.read(max_bytes=1)
        self.assertEqual([], too_small['lines'])
        self.assertEqual((None, None, True, 1), tuple(too_small[k] for k in ('start', 'end', 'truncated', 'nextStart')))

    def test_empty_file_has_no_fabricated_line_range(self):
        result = self.read('app/__init__.py')
        self.assertEqual(([], 0, None, None, False, None),
                         tuple(result[k] for k in ('lines', 'lineCount', 'start', 'end', 'truncated', 'nextStart')))
        with self.assertRaises(ContextError):
            self.read('app/__init__.py', start=1)

    def test_snapshot_validation_precedes_io(self):
        bad = copy.deepcopy(self.snapshot)
        bad['schema'] = 'invalid'
        with mock.patch('app.context._run_git') as git:
            with self.assertRaises(ContractError):
                read_source('/absent', bad, 'lines.txt')
            git.assert_not_called()

    def test_worktree_edits_and_host_symlink_do_not_affect_blob(self):
        path = self.repo / 'lines.txt'
        original = path.read_bytes()
        path.unlink()
        path.symlink_to('/etc/passwd')
        try:
            self.assertEqual(['alpha', 'beta', 'gamma'], self.read()['lines'])
        finally:
            path.unlink()
            path.write_bytes(original)

    def test_git_symlink_returns_target_blob_not_host_contents(self):
        with tempfile.TemporaryDirectory() as raw:
            repo, _ = repository(Path(raw), {'lines.txt': 'placeholder'})
            (repo / 'lines.txt').unlink()
            (repo / 'lines.txt').symlink_to('/etc/passwd')
            git(repo, 'add', 'lines.txt')
            git(repo, 'commit', '--quiet', '-m', 'symlink fixture')
            snapshot = copy.deepcopy(self.snapshot)
            commit = git(repo, 'rev-parse', 'HEAD')
            snapshot['source']['commit'] = commit
            snapshot['map']['meta']['snapshot_commit'] = commit
            entry = next(f for f in snapshot['inventory'] if f['path'] == 'lines.txt')
            entry.update(sha256=hashlib.sha256(b'/etc/passwd').hexdigest(), lineCount=1)
            result = read_source(repo / '.git', snapshot, 'lines.txt')
            self.assertEqual(['/etc/passwd'], result['lines'])
            self.assertEqual(entry['sha256'], result['sha256'])

    def test_blob_verification_cap_fails_closed(self):
        with mock.patch('app.context.MAX_BLOB_BYTES', 2):
            with self.assertRaisesRegex(ContextError, 'safety limit'):
                self.read()

    def test_limits_are_strict_integers(self):
        for name in ('max_lines', 'max_bytes'):
            for value in (0, -1, True, 1.5, '2'):
                with self.subTest(name=name, value=value), self.assertRaises(ContextError):
                    self.read(**{name: value})

    def test_no_network_or_model_imports(self):
        tree = ast.parse((ROOT / 'app/context.py').read_text())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or '')
        self.assertFalse(set(name.split('.')[0] for name in imports) &
                         {'urllib', 'http', 'socket', 'openai', 'anthropic', 'requests'})


@unittest.skipUnless(NODE, 'node required for real evidence packets')
class ContextTests(PublicationFixture):
    def packet(self, query='what depends on lib/core.py', **kwargs):
        done = subprocess.run([NODE, str(ROOT / 'scripts/query_worker.cjs'), str(self.snapshot_path)],
                              input=json.dumps(dict(requestId='context-test', query=query, **kwargs)) + '\n',
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(0, done.returncode, done.stderr)
        reply = json.loads(done.stdout)
        self.assertTrue(reply['ok'], reply)
        return reply['packet']

    def test_real_packet_seed_first_and_bounded_excerpts(self):
        packet = self.packet()
        before = copy.deepcopy(packet)
        result = build_context(self.git_dir, self.snapshot, packet, lines_per_file=1)
        self.assertEqual('dag-gps-context/v1', result['schema'])
        self.assertEqual(hashlib.sha256(canonical_json(packet)).hexdigest(), result['packetSha256'])
        nodes = {n['id']: n for n in self.snapshot['map']['nodes']}
        expected = [packet['seedNodeId']] + [n for n in packet['selectedNodeIds'] if n != packet['seedNodeId']]
        self.assertEqual([nodes[n]['path'] for n in expected if nodes[n]['kind'] == 'file'],
                         [f['path'] for f in result['files']])
        self.assertTrue(all(len(f['lines']) <= 1 and f['start'] == 1 for f in result['files']))
        self.assertTrue(result['truncated'])
        self.assertTrue(any('line 1' in s for s in result['limitations']))
        self.assertEqual(before, packet)

    def test_packet_validation_is_first_and_revision_bound(self):
        packet = self.packet()
        snapshot = copy.deepcopy(self.snapshot)
        snapshot['snapshotId'] = 'other-revision'
        with mock.patch('app.context._run_git') as git:
            with self.assertRaises(ContractError):
                build_context('/absent', snapshot, packet, budget_bytes=-1)
            git.assert_not_called()

    def test_non_matched_packets_do_not_read_source(self):
        for query, kwargs, status in [('util.py', {}, 'needs-choice'),
                                      ('zzqx_nothing.py', {}, 'no-match'),
                                      ('lib/core.py', {'snapshotId': 'other'}, 'stale')]:
            packet = self.packet(query, **kwargs)
            self.assertEqual(status, packet['status'])
            with mock.patch('app.context._run_git') as git:
                result = build_context('/absent', self.snapshot, packet)
                self.assertEqual([], result['files'])
                git.assert_not_called()

    def test_budget_overflow_and_max_files_are_explicit(self):
        packet = self.packet()
        result = build_context(self.git_dir, self.snapshot, packet, budget_bytes=1)
        self.assertEqual([], result['files'])
        self.assertEqual(len(packet['selectedNodeIds']), len(result['omitted']))
        self.assertTrue(all('budget' in f['reason'] for f in result['omitted']))
        self.assertTrue(result['truncated'])
        result = build_context(self.git_dir, self.snapshot, packet, max_files=1)
        self.assertEqual(1, len(result['files']))
        self.assertTrue(result['omitted'])
        self.assertTrue(result['truncated'])
        result = build_context(self.git_dir, self.snapshot, packet, budget_bytes=250)
        self.assertLessEqual(sum(len(canonical_json(f)) for f in result['files']), 250)

    def test_non_text_selected_file_is_omitted(self):
        packet = self.packet('lib/core.py')
        snapshot = copy.deepcopy(self.snapshot)
        next(f for f in snapshot['inventory'] if f['path'] == 'lib/core.py')['contentKind'] = 'binary'
        result = build_context(self.git_dir, snapshot, packet)
        self.assertEqual([], result['files'])
        self.assertEqual([{'path': 'lib/core.py', 'reason': 'metadata only'}], result['omitted'])
        self.assertTrue(result['truncated'])

    def test_invalid_context_limits(self):
        packet = self.packet()
        for name in ('budget_bytes', 'max_files', 'lines_per_file'):
            for value in (-1, True, 1.5):
                with self.subTest(name=name, value=value), self.assertRaises(ContextError):
                    build_context(self.git_dir, self.snapshot, packet, **{name: value})


if __name__ == '__main__':
    unittest.main()


class GitDirLookupTests(unittest.TestCase):
    def test_git_dir_for_matches_acquisition_cache_entry_and_rejects_escape(self):
        from app.context import git_dir_for
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            result, commit, _ = acquire(root, {'a.py': 'x = 1\n'})
            snapshot = {'source': {'repo': 'example/inventory-fixture', 'commit': commit}}
            found = git_dir_for(root / 'git-cache', snapshot)
            self.assertEqual(Path(result['git_dir']).resolve(), found.resolve())
            with self.assertRaises(ContextError):
                git_dir_for(root / 'git-cache', {'source': {'repo': 'example/inventory-fixture', 'commit': 'f' * 40}})
            with self.assertRaises(ContextError):
                git_dir_for(root / 'git-cache', {'source': {'repo': 'x', 'commit': '../../etc'}})
