"""M2.2 local workspace service: loopback boundary, opaque IDs, import jobs and
contract-validated query packets. Synthetic local Git fixtures (mechanics only)."""
import http.client
import json
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from app.contracts import validate_evidence_packet  # noqa: E402
from app.repositories import _acquire_repository_for_test  # noqa: E402
from app.server import WorkspaceServer  # noqa: E402
from test_workspace_snapshot import repository  # noqa: E402

NODE = shutil.which('node')
URL = 'https://github.com/example/server-fixture'
FILES = {
    'app/__init__.py': '', 'lib/__init__.py': '',
    'app/main.py': 'from lib import core\n',
    'lib/core.py': 'from lib import util\n',
    'lib/util.py': 'X = 1\n',
    'README.md': '# fixture\n',
}


@unittest.skipUnless(NODE, 'node is required for the query worker')
class WorkspaceServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        cls.repo, cls.commit = repository(root / 'fixture', FILES)
        transports = {URL: str(cls.repo)}

        def acquire(url, cache_root, commit=None, *, progress=None, cancel=None):
            if url not in transports:
                raise RuntimeError('fixture transport unavailable')
            return _acquire_repository_for_test(url, cache_root, transports[url], commit,
                                                progress=progress, cancel=cancel)

        cls.server = WorkspaceServer(root / 'workspace', port=0, acquire=acquire)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.port
        cls.token = cls.server.session_token

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls._tmp.cleanup()

    def request(self, method, path, body=None, *, host=None, origin=None, token='default',
                content_type='application/json', raw=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.port, timeout=30)
        headers = {'Host': host or '127.0.0.1:%d' % self.port}
        if origin:
            headers['Origin'] = origin
        if token == 'default':
            token = self.token
        if token is not None:
            headers['X-DAG-GPS-Session'] = token
        data = raw if raw is not None else (json.dumps(body).encode() if body is not None else None)
        if data is not None:
            headers['Content-Type'] = content_type
            headers['Content-Length'] = str(len(data))
        conn.request(method, path, body=data, headers=headers)
        response = conn.getresponse()
        payload = response.read()
        conn.close()
        try:
            parsed = json.loads(payload) if payload else None
        except ValueError:
            parsed = payload.decode('utf-8', 'replace')
        return response.status, dict(response.getheaders()), parsed

    def imported(self):
        if not hasattr(type(self), '_job'):
            status, _, job = self.request('POST', '/api/imports', {'url': URL, 'commit': self.commit})
            self.assertEqual(202, status, job)
            deadline = time.time() + 60
            while time.time() < deadline:
                status, _, state = self.request('GET', '/api/imports/' + job['jobId'])
                if state['state'] in ('ready', 'failed'):
                    break
                time.sleep(0.1)
            type(self)._job = state
        self.assertEqual('ready', type(self)._job['state'], type(self)._job)
        return type(self)._job

    # ---- loopback boundary -------------------------------------------------
    def test_refuses_non_loopback_bind(self):
        with self.assertRaises(ValueError):
            WorkspaceServer(Path(self._tmp.name) / 'x', host='0.0.0.0', port=0)

    def test_rejects_unexpected_host_header_dns_rebinding(self):
        status, _, body = self.request('GET', '/api/projects', host='attacker.example:%d' % self.port)
        self.assertEqual(403, status)
        status, _, _ = self.request('GET', '/', host='attacker.example')
        self.assertEqual(403, status)

    def test_rejects_cross_origin_requests(self):
        status, _, _ = self.request('POST', '/api/imports', {'url': URL}, origin='https://evil.example')
        self.assertEqual(403, status)
        status, headers, _ = self.request('GET', '/api/projects', origin='http://127.0.0.1:%d' % self.port)
        self.assertEqual(200, status)
        self.assertNotIn('Access-Control-Allow-Origin', headers)

    def test_api_requires_session_capability(self):
        self.assertEqual(401, self.request('GET', '/api/projects', token=None)[0])
        self.assertEqual(401, self.request('GET', '/api/projects', token='wrong')[0])
        self.assertEqual(401, self.request('POST', '/api/imports', {'url': URL}, token=None)[0])

    def test_unknown_routes_and_traversal_are_not_served(self):
        for path in ('/../app/server.py', '/app/server.py', '/web/scorer.js?x', '/api/projects/../../etc',
                     '/api/projects/p-zzzz/snapshots/abc', '/api/imports/../../x', '/.git/config'):
            status, _, _ = self.request('GET', path)
            self.assertIn(status, (400, 404), path)

    def test_body_limits_and_content_type(self):
        status, _, _ = self.request('POST', '/api/imports', raw=b'{' + b' ' * (70 * 1024) + b'}')
        self.assertEqual(413, status)
        status, _, _ = self.request('POST', '/api/imports', raw=b'url=x', content_type='application/x-www-form-urlencoded')
        self.assertEqual(415, status)
        status, _, _ = self.request('POST', '/api/imports', raw=b'{not json')
        self.assertEqual(400, status)

    def test_invalid_repository_url_is_rejected_before_any_job(self):
        for url in ('https://github.com.evil.invalid/a/b', 'git@github.com:a/b.git', 'file:///etc', 'https://github.com/a/b/blob/main/x.py'):
            status, _, body = self.request('POST', '/api/imports', {'url': url})
            self.assertEqual(400, status, url)
            self.assertIn('error', body)

    def test_ui_page_is_static_with_strict_headers(self):
        status, headers, body = self.request('GET', '/', token=None)
        self.assertEqual(200, status)
        self.assertIn("default-src 'none'", headers['Content-Security-Policy'])
        self.assertEqual('nosniff', headers['X-Content-Type-Options'])
        self.assertIn('DAG GPS', body)
        self.assertNotIn(self.token, body)

    # ---- import + query ----------------------------------------------------
    def test_import_job_reports_inventory_before_ready_and_lists_project(self):
        job = self.imported()
        stages = [event['stage'] for event in job['events']]
        self.assertIn('inventory-ready', stages)
        self.assertLess(stages.index('inventory-ready'), stages.index('ready'))
        self.assertRegex(job['projectId'], r'^p-[0-9a-f]{20}$')
        self.assertRegex(job['snapshotId'], r'^[0-9a-f]{64}$')
        status, _, projects = self.request('GET', '/api/projects')
        self.assertEqual(200, status)
        mine = [p for p in projects['projects'] if p['projectId'] == job['projectId']]
        self.assertEqual(1, len(mine))
        self.assertEqual(self.commit, mine[0]['current']['commit'])

    def test_snapshot_and_query_packet_are_revision_bound_and_contract_valid(self):
        job = self.imported()
        base = '/api/projects/%s' % job['projectId']
        status, _, snapshot = self.request('GET', base + '/snapshots/' + job['snapshotId'])
        self.assertEqual(200, status)
        self.assertEqual(job['snapshotId'], snapshot['snapshotId'])
        status, _, packet = self.request('POST', base + '/query', {
            'snapshotId': job['snapshotId'], 'requestId': 'client-1', 'query': 'what depends on lib/util.py'})
        self.assertEqual(200, status, packet)
        validate_evidence_packet(packet, snapshot)
        self.assertEqual('client-1', packet['requestId'])
        self.assertEqual('potential-impact', packet['highlightState'])
        self.assertEqual({'lib/util.py', 'lib/core.py', 'app/main.py'}, set(packet['selectedNodeIds']))

    def test_query_rejects_unknown_or_foreign_revision(self):
        job = self.imported()
        base = '/api/projects/%s' % job['projectId']
        status, _, _ = self.request('POST', base + '/query', {
            'snapshotId': 'f' * 64, 'requestId': 'r', 'query': 'lib/core.py'})
        self.assertEqual(404, status)
        status, _, _ = self.request('POST', '/api/projects/p-%s/query' % ('0' * 20), {
            'snapshotId': job['snapshotId'], 'requestId': 'r', 'query': 'lib/core.py'})
        self.assertEqual(404, status)

    def test_query_validates_request_fields(self):
        job = self.imported()
        base = '/api/projects/%s/query' % job['projectId']
        for body in ({'snapshotId': job['snapshotId'], 'query': 'x'},
                     {'snapshotId': job['snapshotId'], 'requestId': 'r', 'query': 'x' * 5000},
                     {'snapshotId': job['snapshotId'], 'requestId': 'r', 'query': 'x', 'continuation': 'bad'},
                     {'snapshotId': job['snapshotId'], 'requestId': 'r', 'query': 'x', 'extra': 1}):
            status, _, reply = self.request('POST', base, body)
            self.assertEqual(400, status, body)

    def test_unknown_import_job_is_404(self):
        self.assertEqual(404, self.request('GET', '/api/imports/j-' + '0' * 24)[0])


if __name__ == '__main__':
    unittest.main()
