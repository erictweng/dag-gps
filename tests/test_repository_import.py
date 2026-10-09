import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest import mock
import zlib

from app.repositories import (
    RepositoryAcquisitionError,
    RepositoryCancelled,
    RepositoryTimeout,
    _acquire_repository_for_test,
    _run_git,
    acquire_repository,
    parse_github_repository,
)


class RepositoryUrlTests(unittest.TestCase):
    def test_accepts_only_canonical_root(self):
        self.assertEqual(
            parse_github_repository('https://github.com/pallets/itsdangerous'),
            {'owner': 'pallets', 'repo': 'itsdangerous'},
        )

    def test_rejects_noncanonical_or_ambiguous_urls(self):
        bad = [
            'http://github.com/a/b', 'git://github.com/a/b', 'ssh://github.com/a/b',
            'file:///a/b', 'https://github.com.evil.invalid/a/b',
            'https://user@github.com/a/b', 'https://github.com:443/a/b',
            'https://GITHUB.com/a/b', 'https://github.com/a/b/',
            'https://github.com//a/b', 'https://github.com/a//b',
            'https://github.com/a/b/blob/main/x.py', 'https://github.com/a/b/tree/main',
            'https://github.com/a/b?x=1', 'https://github.com/a/b#readme',
            'https://github.com/a/b.git', 'https://github.com/a/%62',
            'https://github.com/./b', 'https://github.com/a/..',
            ' https://github.com/a/b', 'https://github.com/a/b\n',
            'https://github.com/a/b c', '', None,
        ]
        for value in bad:
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_github_repository(value)


class RepositoryAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        self.cache = self.root / 'cache'
        self.source.mkdir()
        self._git('init', '-q', '-b', 'main')
        self._git('config', 'user.name', 'Fixture')
        self._git('config', 'user.email', 'fixture@example.invalid')
        (self.source / 'value.txt').write_text('one\n', encoding='utf-8')
        self._git('add', 'value.txt')
        self._git('commit', '-q', '-m', 'one')
        self.old_commit = self._git('rev-parse', 'HEAD').strip()
        self.url = 'https://github.com/example/synthetic'

    def tearDown(self):
        self.temp.cleanup()

    def _git(self, *args):
        return subprocess.check_output(['git', *args], cwd=self.source, text=True)

    def _acquire(self, commit=None, **kwargs):
        return _acquire_repository_for_test(
            self.url, self.cache, str(self.source), commit=commit, **kwargs
        )

    def _loosen_cache_objects(self, git_dir):
        git_dir = Path(git_dir)
        pack_dir = git_dir / 'objects' / 'pack'
        packs = list(pack_dir.glob('*.pack'))
        if not packs:
            return
        self.assertEqual(len(packs), 1)
        pack = packs[0]
        data = pack.read_bytes()
        pack.unlink()
        pack.with_suffix('.idx').unlink()
        subprocess.run(
            ['git', '--git-dir', str(git_dir), 'unpack-objects', '-r'],
            input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        )

    def _blob_sha(self, git_dir):
        output = subprocess.check_output(
            ['git', '--git-dir', str(git_dir), 'ls-tree', self.old_commit, 'value.txt'],
            text=True,
        )
        return output.split()[2]

    def _byte_inventory(self, path):
        return {
            str(item.relative_to(path)): (item.stat().st_size, hashlib.sha256(item.read_bytes()).hexdigest())
            for item in sorted(path.rglob('*')) if item.is_file() and not item.is_symlink()
        }

    def test_default_head_is_resolved_once_and_exact_commit_returned(self):
        first = self._acquire()
        self.assertEqual(first['commit'], self.old_commit)
        self.assertFalse(first['cache_hit'])
        self.assertEqual(first['repo_id'], 'example/synthetic')
        self.assertEqual(first['url'], self.url)
        self.assertTrue(Path(first['git_dir']).is_relative_to(self.cache.resolve()))

        (self.source / 'value.txt').write_text('two\n', encoding='utf-8')
        self._git('commit', '-qam', 'two')
        new_commit = self._git('rev-parse', 'HEAD').strip()
        second = self._acquire()
        self.assertEqual(second['commit'], new_commit)
        self.assertNotEqual(first['git_dir'], second['git_dir'])

    def test_branch_move_after_resolution_does_not_change_fetched_commit(self):
        moved = []

        def progress(event):
            if event['stage'] == 'fetching' and not moved:
                (self.source / 'value.txt').write_text('moved\n', encoding='utf-8')
                self._git('commit', '-qam', 'move-after-resolution')
                moved.append(self._git('rev-parse', 'HEAD').strip())

        result = self._acquire(progress=progress)
        self.assertTrue(moved)
        self.assertEqual(result['commit'], self.old_commit)
        self.assertNotEqual(result['commit'], moved[0])

    def test_explicit_old_pin_and_same_sha_reuse(self):
        first = self._acquire(self.old_commit)
        second = self._acquire(self.old_commit)
        self.assertEqual(first['commit'], self.old_commit)
        self.assertTrue(second['cache_hit'])
        self.assertEqual(first['git_dir'], second['git_dir'])
        kind = subprocess.check_output(
            ['git', '--git-dir', first['git_dir'], 'cat-file', '-t', self.old_commit], text=True
        ).strip()
        self.assertEqual(kind, 'commit')

    def test_malformed_pin_is_not_normalized(self):
        for pin in [self.old_commit.upper(), self.old_commit[:12], ' ' + self.old_commit, '0' * 39, None]:
            if pin is None:
                continue
            with self.subTest(pin=pin):
                with self.assertRaises(ValueError):
                    self._acquire(pin)

    def test_tag_object_is_not_accepted_as_commit_pin(self):
        self._git('tag', '-a', 'annotated', '-m', 'tag')
        tag_sha = self._git('rev-parse', 'annotated').strip()
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'not a commit'):
            self._acquire(tag_sha)

    def test_empty_or_unavailable_remote_fails_clearly_without_prompt(self):
        empty = self.root / 'empty.git'
        subprocess.check_call(['git', 'init', '--bare', '-q', str(empty)])
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'HEAD'):
            _acquire_repository_for_test(self.url, self.cache, str(empty))
        missing = self.root / 'missing.git'
        with self.assertRaises(RepositoryAcquisitionError):
            _acquire_repository_for_test(self.url, self.cache, str(missing), commit=self.old_commit)

    def test_poisoned_owned_cache_is_rejected_and_missing_marker_is_not_deleted(self):
        result = self._acquire(self.old_commit)
        metadata = Path(result['git_dir']).parent / 'metadata.json'
        metadata.write_text('{}', encoding='utf-8')
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'poisoned'):
            self._acquire(self.old_commit)

        shutil.rmtree(self.cache)
        self.cache.mkdir()
        foreign = self.cache / 'do-not-delete'
        foreign.write_text('caller data', encoding='utf-8')
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'not an owned cache'):
            self._acquire(self.old_commit)
        self.assertEqual(foreign.read_text(encoding='utf-8'), 'caller data')

    def test_unsafe_local_config_poison_is_rejected(self):
        result = self._acquire(self.old_commit)
        subprocess.check_call([
            'git', '--git-dir', result['git_dir'], 'config', 'core.hooksPath', '/tmp/host-hooks'
        ])
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'unsafe config'):
            self._acquire(self.old_commit)

    def test_local_config_include_is_rejected_without_opening_external_fifo(self):
        result = self._acquire(self.old_commit)
        fifo = self.root / 'external-config-fifo'
        os.mkfifo(fifo)
        config = Path(result['git_dir']) / 'config'
        with config.open('a', encoding='utf-8') as handle:
            handle.write(f'\n[include]\n\tpath = {fifo}\n')

        reader_opened = threading.Event()
        stop = threading.Event()

        def detect_reader():
            while not stop.is_set():
                try:
                    descriptor = os.open(fifo, os.O_WRONLY | os.O_NONBLOCK)
                except OSError as error:
                    if error.errno != errno.ENXIO:
                        return
                    time.sleep(0.01)
                    continue
                reader_opened.set()
                try:
                    os.write(descriptor, b'this is deliberately invalid git config\n')
                finally:
                    os.close(descriptor)
                return

        detector = threading.Thread(target=detect_reader)
        detector.start()
        try:
            with self.assertRaisesRegex(RepositoryAcquisitionError, 'unsafe config'):
                self._acquire(self.old_commit)
        finally:
            stop.set()
            detector.join(timeout=1)
        self.assertFalse(detector.is_alive())
        self.assertFalse(reader_opened.is_set(), 'external include target was opened')

    def test_replacement_refs_grafts_and_alternates_are_rejected(self):
        for poison in ('replace-ref', 'grafts', 'alternates', 'http-alternates'):
            with self.subTest(poison=poison):
                shutil.rmtree(self.cache, ignore_errors=True)
                result = self._acquire(self.old_commit)
                git_dir = Path(result['git_dir'])
                (self.source / 'value.txt').write_text(poison + '\n', encoding='utf-8')
                self._git('commit', '-qam', poison)
                replacement = self._git('rev-parse', 'HEAD').strip()
                subprocess.check_call([
                    'git', '--git-dir', str(git_dir), 'fetch', '--quiet', '--no-tags',
                    '--no-write-fetch-head', str(self.source), replacement,
                ])
                if poison == 'replace-ref':
                    poisoned = git_dir / 'refs' / 'replace' / self.old_commit
                    poisoned.parent.mkdir(parents=True)
                    poisoned.write_text(replacement + '\n', encoding='ascii')
                elif poison == 'grafts':
                    poisoned = git_dir / 'info' / 'grafts'
                    poisoned.write_text(self.old_commit + ' ' + replacement + '\n', encoding='ascii')
                else:
                    poisoned = git_dir / 'objects' / 'info' / poison
                    poisoned.write_text(str(self.source / '.git' / 'objects') + '\n', encoding='utf-8')
                with self.assertRaisesRegex(RepositoryAcquisitionError, 'poisoned'):
                    self._acquire(self.old_commit)
                self.assertTrue(poisoned.exists())

    def test_reachable_blob_hash_corruption_is_rejected_but_clean_reuse_passes(self):
        result = self._acquire(self.old_commit)
        self.assertTrue(self._acquire(self.old_commit)['cache_hit'])
        git_dir = Path(result['git_dir'])
        self._loosen_cache_objects(git_dir)
        blob = self._blob_sha(git_dir)
        object_path = git_dir / 'objects' / blob[:2] / blob[2:]
        replacement = b'changed but same-sized data\n'
        payload = b'blob ' + str(len(replacement)).encode() + b'\0' + replacement
        object_path.unlink()
        object_path.write_bytes(zlib.compress(payload))
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'integrity'):
            self._acquire(self.old_commit)

    def test_cache_symlinks_are_rejected_before_git_reads_or_quota_deletes(self):
        cases = ('object-fanout', 'pack-directory', 'config', 'metadata')
        for case in cases:
            with self.subTest(case=case):
                shutil.rmtree(self.cache, ignore_errors=True)
                result = self._acquire(self.old_commit)
                git_dir = Path(result['git_dir'])
                entry = git_dir.parent
                external = self.root / ('external-' + case)
                external.mkdir(exist_ok=True)
                sentinel = external / 'sentinel'
                sentinel.write_text('preserve me', encoding='utf-8')
                if case == 'object-fanout':
                    self._loosen_cache_objects(git_dir)
                    blob = self._blob_sha(git_dir)
                    victim = git_dir / 'objects' / blob[:2]
                    shutil.move(victim, external / 'fanout')
                    victim.symlink_to(external / 'fanout', target_is_directory=True)
                elif case == 'pack-directory':
                    victim = git_dir / 'objects' / 'pack'
                    shutil.rmtree(victim)
                    victim.symlink_to(external, target_is_directory=True)
                elif case == 'config':
                    victim = git_dir / 'config'
                    victim.unlink()
                    victim.symlink_to(sentinel)
                else:
                    victim = entry / 'metadata.json'
                    victim.unlink()
                    victim.symlink_to(sentinel)
                with self.assertRaisesRegex(RepositoryAcquisitionError, 'symbolic link|poisoned'):
                    self._acquire(self.old_commit)
                self.assertEqual(sentinel.read_text(encoding='utf-8'), 'preserve me')

    def test_stale_staging_directory_file_and_symlink_fail_closed(self):
        result = self._acquire(self.old_commit)
        target_size = sum(
            item.stat().st_size for item in Path(result['git_dir']).parent.rglob('*')
            if item.is_file() and not item.is_symlink()
        )
        outside = self.root / 'outside-staging'
        outside.write_text('unrelated bytes', encoding='utf-8')
        for kind in ('directory', 'file', 'symlink'):
            with self.subTest(kind=kind):
                stale = self.cache / ('.staging-stale-' + kind)
                if kind == 'directory':
                    stale.mkdir()
                    (stale / 'payload').write_bytes(b'x' * 4096)
                elif kind == 'file':
                    stale.write_bytes(b'x' * 4096)
                else:
                    stale.symlink_to(outside)
                with self.assertRaisesRegex(RepositoryAcquisitionError, 'staging|unowned|symbolic link'):
                    self._acquire(
                        self.old_commit,
                        limits={'max_cache_bytes': target_size + 1, 'max_entries': 32},
                    )
                self.assertTrue(stale.exists() or stale.is_symlink())
                self.assertEqual(outside.read_text(encoding='utf-8'), 'unrelated bytes')
                if stale.is_symlink() or stale.is_file():
                    stale.unlink()
                else:
                    shutil.rmtree(stale)

    def test_missing_object_is_detected_before_cache_reuse(self):
        result = self._acquire(self.old_commit)
        subprocess.check_call(['git', '--git-dir', result['git_dir'], 'prune', '--expire=now'])
        shutil.rmtree(Path(result['git_dir']) / 'objects')
        (Path(result['git_dir']) / 'objects').mkdir()
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'poisoned'):
            self._acquire(self.old_commit)

    def test_concurrent_writer_is_refused(self):
        self.cache.mkdir()
        (self.cache / '.dag-gps-repository-cache-v1').write_text('1\n', encoding='ascii')
        (self.cache / '.writer.lock').mkdir()
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'writer'):
            self._acquire(self.old_commit)

    def test_quota_evicts_only_owned_entries_and_rejects_oversized_target(self):
        first = self._acquire(self.old_commit)
        (self.source / 'value.txt').write_text('three\n', encoding='utf-8')
        self._git('commit', '-qam', 'three')
        newer = self._git('rev-parse', 'HEAD').strip()
        second = self._acquire(newer, limits={'max_entries': 1, 'max_cache_bytes': 10_000_000})
        self.assertFalse(Path(first['git_dir']).exists())
        self.assertTrue(Path(second['git_dir']).exists())
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'quota'):
            self._acquire(newer, limits={'max_entries': 4, 'max_cache_bytes': 1})

    def test_rejected_tighter_quota_preserves_existing_target_bytes(self):
        result = self._acquire(self.old_commit)
        entry = Path(result['git_dir']).parent
        before = self._byte_inventory(entry)
        self.assertTrue(before)
        with self.assertRaisesRegex(RepositoryAcquisitionError, 'quota'):
            self._acquire(
                self.old_commit,
                limits={'max_entries': 32, 'max_cache_bytes': 1},
            )
        self.assertTrue(entry.is_dir())
        self.assertEqual(self._byte_inventory(entry), before)

    def test_no_imported_hooks_are_run(self):
        marker = self.root / 'hook-ran'
        hooks = self.source / '.git' / 'hooks'
        hook = hooks / 'post-checkout'
        hook.write_text('#!/bin/sh\ntouch "$MARKER"\n', encoding='utf-8')
        hook.chmod(0o755)
        with mock.patch.dict(os.environ, {'MARKER': str(marker)}):
            self._acquire(self.old_commit)
        self.assertFalse(marker.exists())

    def test_production_api_has_no_local_transport_backdoor(self):
        with mock.patch('app.repositories._acquire') as inner:
            inner.return_value = {'ok': True}
            acquire_repository(self.url, self.cache, commit=self.old_commit)
            transport = inner.call_args.kwargs['transport_url']
            self.assertEqual(transport, self.url)
            self.assertFalse(inner.call_args.kwargs['allow_file_protocol'])


class GitProcessTests(unittest.TestCase):
    def test_production_git_does_not_use_inherited_path(self):
        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / 'git'
            marker = Path(temp) / 'executed'
            fake.write_text(
                '#!/bin/sh\nprintf fake-git\nprintf x > "$MARKER"\n', encoding='utf-8'
            )
            fake.chmod(0o755)
            with mock.patch.dict(os.environ, {'PATH': temp, 'MARKER': str(marker)}):
                result = _run_git(['--version'], timeout=2)
            self.assertFalse(marker.exists())
            self.assertRegex(result.stdout, r'^git version ')

    def test_safe_environment_disables_prompts_and_inherited_config(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / 'git'
            script.write_text(
                '#!/bin/sh\nprintf "%s|%s|%s|%s" "$GIT_TERMINAL_PROMPT" "$GIT_CONFIG_NOSYSTEM" '
                '"$GIT_CONFIG_GLOBAL" "$GIT_OPTIONAL_LOCKS"\n', encoding='utf-8'
            )
            script.chmod(0o755)
            result = _run_git([], executable=str(script), timeout=2)
            self.assertEqual(result.stdout, '0|1|/dev/null|0')

    def test_deadline_kills_process_group(self):
        with tempfile.TemporaryDirectory() as temp:
            marker = Path(temp) / 'survived'
            script = Path(temp) / 'git'
            script.write_text(
                '#!/bin/sh\n(sleep 1; touch "$MARKER") &\nsleep 20\n', encoding='utf-8'
            )
            script.chmod(0o755)
            with mock.patch.dict(os.environ, {'MARKER': str(marker)}):
                with self.assertRaises(RepositoryTimeout):
                    _run_git([], executable=str(script), timeout=0.1)
            time.sleep(1.2)
            self.assertFalse(marker.exists())

    def test_cancellation_kills_process_group(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / 'git'
            script.write_text('#!/bin/sh\nsleep 20\n', encoding='utf-8')
            script.chmod(0o755)
            cancelled = threading.Event()
            timer = threading.Timer(0.1, cancelled.set)
            timer.start()
            try:
                with self.assertRaises(RepositoryCancelled):
                    _run_git([], executable=str(script), timeout=5, cancel=cancelled)
            finally:
                timer.cancel()


if __name__ == '__main__':
    unittest.main()
