"""Playground's eight behaviors plus bounded persistence/security regressions."""
import concurrent.futures
import http.client
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))
from app.query_log import QueryLog, read_entries, MAX_LINE
from app.server import WorkspaceServer, _load_session, label_for_status
from app.repositories import _acquire_repository_for_test
from test_workspace_snapshot import repository
from scripts.export_query_log import export


class LogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.log = QueryLog(self.root)

    def question(self, text='where is core', request_id='same-id'):
        return self.log.question('p', {'snapshotId': 's', 'source': {'commit': 'c'}},
                                 {'requestId': request_id, 'query': text},
                                 {'operation': 'LOCATE', 'status': 'matched',
                                  'selectedNodeIds': ['core'], 'alternatives': []}, 1.25)

    def test_labels_cover_every_status(self):
        self.assertEqual('match', label_for_status('matched'))
        self.assertEqual('no match', label_for_status('no-match'))
        for status in ('needs-choice', 'no-path', 'unsupported', 'stale'):
            self.assertEqual('unsure', label_for_status(status))

    def test_session_file_persists_key_privately(self):
        path = self.root / 'nested' / 'session'
        self.assertEqual(_load_session(path), _load_session(path))
        self.assertEqual(0o600, path.stat().st_mode & 0o777)
        self.assertNotEqual(_load_session(None), _load_session(None))

    def test_invalid_allowed_host_rejected(self):
        for host in ('evil.com/x', '*.ts.net', 'https://host', 'host:443', ''):
            with self.assertRaises(ValueError):
                WorkspaceServer(self.root, port=0, allowed_hosts=(host,))

    def test_session_refuses_permissions_and_malformed_without_replacing(self):
        path = self.root / 'session'
        for mode, content in ((0o644, 'a' * 43), (0o640, 'a' * 43),
                              (0o600, 'bad'), (0o600, 'a' * 129), (0o600, '\xff')):
            path.write_text(content)
            path.chmod(mode)
            with self.assertRaises(ValueError):
                _load_session(path)
            self.assertEqual(content, path.read_text())
            self.assertEqual(mode, path.stat().st_mode & 0o777)
        link = self.root / 'link'
        link.symlink_to(path)
        with self.assertRaises(ValueError):
            _load_session(link)

    def test_rotation_retains_two_bounded_generations_and_verdict(self):
        self.log.max_bytes = 1200
        first = self.question()
        self.log.verdict('p', first, 'unsure')
        for _ in range(12):
            last = self.question()
        self.assertTrue(Path(str(self.log.path) + '.1').is_file())
        self.assertNotIn(first, [q['entryId'] for q in self.log.entries('p')])
        self.log.verdict('p', last, 'no match')
        self.assertEqual('no match', next(q for q in QueryLog(self.root).entries('p') if q['entryId'] == last)['verdict'])
        for path in (self.log.path, Path(str(self.log.path) + '.1')):
            self.assertLessEqual(path.stat().st_size, 1200)
        with self.assertRaises(KeyError):
            self.log.verdict('p', first, 'match')

    def test_concurrent_logging_unique_ids_not_interleaved(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
            ids = list(pool.map(lambda i: self.question('question %d' % i), range(120)))
        rows = [json.loads(line) for line in self.log.path.read_text().splitlines()]
        self.assertEqual(120, len(rows))
        self.assertEqual(120, len(set(ids)))
        self.assertEqual(120, len(self.log.entries('p')))

    def test_verdict_idempotency_and_project_isolation(self):
        entry_id = self.question()
        first = self.log.verdict('p', entry_id, 'unsure')
        before = self.log.path.read_bytes()
        self.assertEqual(first, self.log.verdict('p', entry_id, 'unsure'))
        self.assertEqual(before, self.log.path.read_bytes())
        with self.assertRaises(KeyError):
            self.log.verdict('other', entry_id, 'match')
        self.assertEqual([], self.log.entries('other'))

    def test_line_bound_and_torn_line(self):
        self.question('\U0001f600' * 2048, '\U0001f600' * 2048)
        self.assertLessEqual(self.log.path.stat().st_size, MAX_LINE)
        with self.log.path.open('ab') as handle:
            handle.write(b'{broken')
        self.assertEqual(1, len(read_entries(self.log.path)))
        self.question('after torn line')
        self.assertEqual(2, len(read_entries(self.log.path)))

    def test_worst_case_unicode_stays_bounded(self):
        self.log.question('p', {'snapshotId': 's', 'source': {'commit': 'c'}},
                          {'requestId': '\U0001f600' * 2048, 'query': '\U0001f600' * 2048},
                          {'operation': 'LOCATE', 'status': 'needs-choice',
                           'selectedNodeIds': ['\U0001f600' * 256] * 10,
                           'alternatives': [{'nodeId': '\U0001f600' * 256}] * 10}, 1)
        self.assertLessEqual(self.log.path.stat().st_size, MAX_LINE)

    def test_export_requires_single_project_commit(self):
        self.question()
        with self.log.lock:
            row = {
                'kind': 'question', 'entryId': 'other', 'projectId': 'other', 'commit': 'different'}
            self.log._append(row)
        with self.assertRaises(ValueError):
            export(self.log.path)
        self.assertEqual(1, len(export(self.log.path, 'p', 'c')['rows']))

    def test_export_cli_is_draft_and_refuses_overwrite(self):
        entry_id = self.question()
        self.log.verdict('p', entry_id, 'no match')
        out = self.root / 'export.json'
        command = [sys.executable, str(ROOT / 'scripts/export_query_log.py'), str(self.log.path), '--out', str(out)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        data = json.loads(out.read_text())
        self.assertTrue(data['reviewRequired'])
        self.assertEqual('c', data['pin'])
        row = data['rows'][0]
        self.assertEqual(('where is core', 'match', 'no match'), (row['question'], row['autoLabel'], row['verdict']))
        self.assertIsNone(row['expected'])
        self.assertEqual([], row['targets'])
        self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
        self.assertEqual(data, json.loads(out.read_text()))


@unittest.skipUnless(shutil.which('node'), 'node required')
class QuestionServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        root = Path(cls.tmp.name)
        repo, commit = repository(root / 'fixture', {
            'lib/__init__.py': '', 'lib/core.py': 'def go():\n    return 1\n',
            'app/main.py': 'from lib import core\ncore.go()\n'})
        def acquire(url, cache_root, commit=None, **kw):
            return _acquire_repository_for_test(url, cache_root, str(repo), commit, **kw)
        cls.root = root / 'workspace'
        cls.session_file = root / 'session'
        cls.server = WorkspaceServer(cls.root, port=0, acquire=acquire,
                                     session_file=cls.session_file, allowed_hosts=('mini.ts.net', 'second.ts.net'))
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.token = cls.server.session_token
        _, _, job = cls.call('POST', '/api/imports', {'url': 'https://github.com/example/log-fixture', 'commit': commit})
        deadline = time.time() + 60
        while time.time() < deadline:
            _, _, job = cls.call('GET', '/api/imports/' + job['jobId'])
            if job['state'] in ('ready', 'failed'):
                break
            time.sleep(.05)
        assert job['state'] == 'ready', job
        cls.job = job
        cls.base = '/api/projects/' + job['projectId']

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.tmp.cleanup()

    @classmethod
    def call(cls, method, path, body=None, host=None, origin=None, token=True):
        connection = http.client.HTTPConnection('127.0.0.1', cls.server.port, timeout=30)
        headers = {'Host': host or '127.0.0.1:%d' % cls.server.port}
        if token:
            headers['X-DAG-GPS-Session'] = cls.token
        if origin:
            headers['Origin'] = origin
        if body is not None:
            headers['Content-Type'] = 'application/json'
        try:
            connection.request(method, path, json.dumps(body) if body is not None else None, headers)
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), json.loads(response.read())
        finally:
            connection.close()

    def ask(self, query, **extra):
        body = dict(snapshotId=self.job['snapshotId'], requestId='same-request', query=query)
        body.update(extra)
        status, headers, packet = self.call('POST', self.base + '/query', body)
        self.assertEqual(200, status, packet)
        return headers.get('X-DAG-GPS-Question-ID'), packet

    def questions(self):
        status, _, data = self.call('GET', self.base + '/questions')
        self.assertEqual(200, status)
        return {q['entryId']: q for q in data['questions']}

    def test_every_question_is_logged_with_automatic_label(self):
        for query in ('where is lib/core.py', 'where is the quantum flux capacitor', 'explain everything'):
            entry_id, packet = self.ask(query)
            row = self.questions()[entry_id]
            self.assertEqual(query, row['query'])
            self.assertEqual(packet['status'], row['status'])
            self.assertEqual(label_for_status(packet['status']), row['label'])
            self.assertEqual(self.job['commit'], row['commit'])
            self.assertGreaterEqual(row['latencyMs'], 0)
            self.assertIsNone(row['verdict'])

    def test_paging_is_not_a_new_question(self):
        self.ask('what depends on lib/core.py')
        before = len(self.questions())
        entry_id, _ = self.ask('what depends on lib/core.py', continuation='offset:0')
        self.assertIsNone(entry_id)
        self.assertEqual(before, len(self.questions()))

    def test_verdict_overrides_and_validates(self):
        entry_id, _ = self.ask('where is lib/core.py')
        for label in ('unsure', 'no match'):
            self.assertEqual(200, self.call('POST', self.base + '/verdict', {'entryId': entry_id, 'label': label})[0])
        row = self.questions()[entry_id]
        self.assertEqual('match', row['label'])
        self.assertEqual('no match', row['verdict'])
        self.assertTrue(row['verdictAt'])
        for bad in ({'entryId': entry_id, 'label': []}, {'entryId': entry_id, 'label': 'maybe'},
                    {'entryId': entry_id}, {'entryId': '../bad', 'label': 'match'},
                    {'entryId': entry_id, 'label': 'match', 'x': 1}):
            self.assertEqual(400, self.call('POST', self.base + '/verdict', bad)[0])
        self.assertEqual(404, self.call('POST', self.base + '/verdict', {'entryId': 'q-' + '0' * 32, 'label': 'match'})[0])
        self.assertEqual(401, self.call('POST', self.base + '/verdict', {'entryId': entry_id, 'label': 'match'}, token=False)[0])

    def test_log_requires_session_and_is_per_project(self):
        self.assertEqual(401, self.call('GET', self.base + '/questions', token=False)[0])
        self.assertEqual([], self.call('GET', '/api/projects/p-' + '0' * 20 + '/questions')[2]['questions'])

    def test_tailnet_host_and_https_origin_allowed_others_rejected(self):
        for host in ('mini.ts.net', 'second.ts.net'):
            self.assertEqual(200, self.call('GET', '/api/projects', host=host, origin='https://' + host)[0])
        for host, origin in (('other.ts.net', None), ('prefix.mini.ts.net', None),
                             ('mini.ts.net', 'http://mini.ts.net'), ('mini.ts.net', 'https://evil.com')):
            self.assertEqual(403, self.call('GET', '/api/projects', host=host, origin=origin)[0])

    def test_no_secrets_or_source_in_log_and_restart(self):
        entry_id, _ = self.ask('where is lib/core.py')
        self.call('POST', self.base + '/verdict', {'entryId': entry_id, 'label': 'unsure'})
        data = (self.root / 'query-log.jsonl').read_text()
        for secret in (self.token, '127.0.0.1', 'return 1', 'X-DAG-GPS-Session'):
            self.assertNotIn(secret, data)
        self.assertEqual(self.token, _load_session(self.session_file))
        self.assertEqual('unsure', next(q for q in QueryLog(self.root).entries(self.job['projectId']) if q['entryId'] == entry_id)['verdict'])


if __name__ == '__main__':
    unittest.main()
