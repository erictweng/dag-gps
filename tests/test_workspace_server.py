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
    'long.py': 'X = 1\n' * 240,
    'binary.dat': b'\x00\xff',
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
        try:
            try:
                conn.request(method, path, body=data, headers=headers)
            except BrokenPipeError:
                # A bounded server may send 413 and close before the client has
                # finished uploading. Read that response rather than racing it.
                pass
            response = conn.getresponse()
            payload = response.read()
        finally:
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

    # ---- M3 revision-bound source and agent intake -------------------------
    def agent_request(self):
        job = self.imported()
        return '/api/projects/' + job['projectId'], {
            'snapshotId': job['snapshotId'], 'requestId': 'm3-test',
            'query': 'what depends on lib/util.py'}

    def context_and_explanation(self):
        base, request = self.agent_request()
        status, _, value = self.request('POST', base + '/context', dict(request, consent=True))
        self.assertEqual(200, status, value)
        context, packet = value['context'], value['packet']
        source = context['files'][0]
        citation = {k: source[k] for k in ('path', 'sha256', 'start', 'end')}
        explanation = {'schema': 'dag-gps-explanation/v1', 'requestId': packet['requestId'],
            'projectId': packet['projectId'], 'snapshotId': packet['snapshotId'],
            'packetSha256': context['packetSha256'], 'agent': {'name': 'test', 'model': None},
            'paragraphs': [{'text': '<img src=x onerror=alert(1)>', 'inferred': False, 'citations': [citation]},
                           {'text': 'An inference.', 'inferred': True, 'citations': []}],
            'suggestedRelationships': [], 'limitations': [],
            'usage': {'inputTokens': None, 'outputTokens': None}}
        payload = {'snapshotId': request['snapshotId'],
                   'request': {k: v for k, v in request.items() if k != 'snapshotId'},
                   'explanation': explanation, 'useContext': True}
        return base, payload, value

    def test_m3_source_success_and_invalid_paths_ranges(self):
        base, request = self.agent_request()
        body = {'snapshotId': request['snapshotId'], 'path': 'lib/util.py'}
        status, _, value = self.request('POST', base + '/source', body)
        self.assertEqual(200, status, value)
        self.assertEqual(['X = 1'], value['lines'])
        self.assertEqual(request['snapshotId'], value['snapshotId'])
        for extra in ({'path': '../etc/passwd'}, {'path': '/etc/passwd'}, {'path': 'x?y'},
                      {'start': True}, {'start': 0}, {'start': 2}, {'end': '1'}, {'surprise': 1}):
            status, _, error = self.request('POST', base + '/source', dict(body, **extra))
            self.assertEqual(400, status, error)
            self.assertNotIn(self._tmp.name, json.dumps(error))
        self.assertEqual(404, self.request('POST', base + '/source', dict(body, path='missing.py'))[0])

    def test_m3_context_requires_literal_consent(self):
        base, request = self.agent_request()
        for consent in (None, False, 1, 'true', [], {}):
            body = dict(request) if consent is None else dict(request, consent=consent)
            status, _, error = self.request('POST', base + '/context', body)
            self.assertEqual(403, status, error)
            self.assertEqual('Explicit consent required to export source to an agent', error['error'])
        self.context_and_explanation()

    def test_m3_routes_reject_unknown_foreign_snapshot_and_session(self):
        base, request = self.agent_request()
        for route, body in [('source', {'snapshotId': request['snapshotId'], 'path': 'lib/util.py'}),
                            ('context', dict(request, consent=True)),
                            ('explanations', {'snapshotId': request['snapshotId'], 'request': {'requestId': 'x', 'query': 'x'}, 'explanation': {}})]:
            for endpoint, data in [(base, dict(body, snapshotId='f'*64)), ('/api/projects/p-'+'0'*20, body)]:
                self.assertEqual(404, self.request('POST', endpoint+'/'+route, data)[0])
            self.assertEqual(401, self.request('POST', base+'/'+route, body, token=None)[0])
        self.assertEqual(404, self.request('GET', base+'/snapshots/'+'f'*64+'/explanations')[0])

    def test_m3_explanation_validates_before_storing_and_lists(self):
        base, payload, value = self.context_and_explanation()
        status, _, record = self.request('POST', base + '/explanations', payload)
        self.assertEqual(200, status, record)
        listing = base + '/snapshots/' + payload['snapshotId'] + '/explanations'
        status, _, listed = self.request('GET', listing)
        self.assertEqual(200, status)
        self.assertTrue(any(x['valid'] and x['record']['explanation'] == payload['explanation'] for x in listed['explanations']))
        before = listed
        for field, bad in [('packetSha256', '0'*64), ('snapshotId', 'f'*64), ('projectId', 'p-'+'0'*20), ('requestId', 'foreign')]:
            altered = json.loads(json.dumps(payload))
            altered['explanation'][field] = bad
            status, _, error = self.request('POST', base + '/explanations', altered)
            self.assertEqual(422, status, error)
            self.assertEqual(before, self.request('GET', listing)[2])
        # A caller cannot provide a fabricated authority packet (exact allowlist).
        self.assertEqual(400, self.request('POST', base+'/explanations', dict(payload, packet=value['packet']))[0])
        altered = json.loads(json.dumps(payload))
        altered['request']['packet'] = value['packet']
        self.assertEqual(400, self.request('POST', base+'/explanations', altered)[0])
        self.assertEqual(before, self.request('GET', listing)[2])

    def test_m3_pagination_metadata_and_exact_allowlists(self):
        base, request = self.agent_request()
        body = {'snapshotId': request['snapshotId'], 'path': 'long.py'}
        status, _, source = self.request('POST', base+'/source', body)
        self.assertEqual(200, status, source)
        self.assertEqual(200, len(source['lines']))
        self.assertEqual(201, source['nextStart'])
        status, _, source = self.request('POST', base+'/source', dict(body, start=source['nextStart']))
        self.assertEqual(200, status)
        self.assertEqual(40, len(source['lines']))
        self.assertIsNone(source['nextStart'])
        status, _, error = self.request('POST', base+'/source', dict(body, path='binary.dat'))
        self.assertEqual(400, status)
        self.assertEqual('metadata only', error['error'])
        self.assertEqual(200, self.request('POST', base+'/source', dict(body, path='README.md'))[0])
        for sid in (None, [], {}, 12, True):
            self.assertEqual(404, self.request('POST', base+'/source', dict(body, snapshotId=sid))[0])
        self.assertEqual(400, self.request('POST', base+'/context', dict(request, consent=True, packet={}))[0])
        self.assertEqual(400, self.request('POST', base+'/context', dict(request, consent=True, continuation='invalid'))[0])
        for route in ('source', 'context', 'explanations'):
            self.assertEqual(403, self.request('POST', base+'/'+route, {}, origin='https://evil.example')[0])
            self.assertEqual(403, self.request('POST', base+'/'+route, {}, host='evil.example')[0])

    def test_m3_context_restricts_citation_ranges_and_recomputed_packet(self):
        base, request = self.agent_request()
        request.update(query='long.py', requestId='long-context')
        status, _, bundle = self.request('POST', base+'/context', dict(request, consent=True))
        self.assertEqual(200, status, bundle)
        _, payload, _ = self.context_and_explanation()
        payload['request'] = {k: v for k, v in request.items() if k != 'snapshotId'}
        ex = payload['explanation']
        ex['requestId'] = request['requestId']
        ex['packetSha256'] = bundle['context']['packetSha256']
        f = bundle['context']['files'][0]
        ex['paragraphs'][0]['citations'] = [dict(path=f['path'], sha256=f['sha256'], start=81, end=81)]
        self.assertEqual(422, self.request('POST', base+'/explanations', payload)[0])
        ex['paragraphs'][0]['citations'][0].update(start=None, end=None)
        self.assertEqual(200, self.request('POST', base+'/explanations', payload)[0])
        payload['request']['query'] = 'README.md'
        self.assertEqual(422, self.request('POST', base+'/explanations', payload)[0])
        payload['useContext'] = 'true'
        self.assertEqual(400, self.request('POST', base+'/explanations', payload)[0])

    def test_m3_invalid_stored_records_are_not_returned_as_text(self):
        base, request = self.agent_request()
        job = self.imported()
        directory = self.server.store.root / 'projects' / job['projectId'] / 'explanations' / job['snapshotId']
        directory.mkdir(parents=True, exist_ok=True)
        corrupt = directory / 'corrupt.json'
        corrupt.write_text('{"schema":"hostile secret text"}')
        try:
            status, _, listed = self.request('GET', base+'/snapshots/'+job['snapshotId']+'/explanations')
            self.assertEqual(200, status)
            invalid = [item for item in listed['explanations'] if not item['valid']]
            self.assertEqual(1, len(invalid))
            self.assertIsNone(invalid[0]['record'])
            self.assertNotIn('hostile secret text', json.dumps(listed))
        finally:
            corrupt.unlink()

    def test_m3_route_specific_body_limits(self):
        base, payload, _ = self.context_and_explanation()
        raw = json.dumps(payload).encode() + b' ' * (70 * 1024)
        self.assertEqual(200, self.request('POST', base+'/explanations', raw=raw)[0])
        self.assertEqual(413, self.request('POST', base+'/explanations', raw=b' '* (512*1024+1))[0])
        for route in ('source', 'context', 'query'):
            self.assertEqual(413, self.request('POST', base+'/'+route, raw=raw)[0])

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
