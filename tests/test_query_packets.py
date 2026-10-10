"""Cross-language contract checks: packets from the shared JS query service, run
through the trusted worker on a real importer publication, must satisfy the
frozen Python evidence contract. Synthetic local fixture; mechanics only."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from app.contracts import ContractError, validate_evidence_packet  # noqa: E402
from app.snapshots import SnapshotError, build_workspace_snapshot  # noqa: E402
from app.workspace_snapshot import load_publication, write_snapshot  # noqa: E402
from test_workspace_snapshot import acquire  # noqa: E402

NODE = shutil.which('node')
FILES = {
    'app/main.py': 'from app import util\nfrom lib import core\n',
    'app/util.py': 'X = 1\n',
    'lib/__init__.py': '',
    'app/__init__.py': '',
    'lib/util.py': 'Y = 2\n',
    'lib/core.py': 'from lib import a\n',
    'lib/a.py': 'from lib import b\n',
    'lib/b.py': 'from lib import a\n',
    'tools/cli.py': 'from lib import core\n',
    'README.md': '# fixture\n',
}


def run_worker(snapshot_path, requests):
    lines = ''.join(json.dumps(r) + '\n' for r in requests)
    done = subprocess.run([NODE, str(ROOT / 'scripts/query_worker.cjs'), str(snapshot_path)],
                          input=lines, capture_output=True, text=True, timeout=60)
    return done, [json.loads(line) for line in done.stdout.splitlines() if line.strip()]


@unittest.skipUnless(NODE, 'node is required for the shared query worker')
class QueryPacketContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        root = Path(cls._tmp.name)
        result, cls.commit, _ = acquire(root, FILES)
        cls.out = root / 'out'
        build_workspace_snapshot(result, cls.out)
        cls.snapshot = load_publication(cls.out)
        cls.path = root / 'snapshot.json'
        write_snapshot(cls.snapshot, cls.path)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_envelope_is_a_valid_unreviewed_preview_bound_to_query_code(self):
        s = self.snapshot
        self.assertEqual('dag-gps-workspace/v1', s['schema'])
        self.assertEqual('dependency-preview', s['state'])
        self.assertEqual({'status': 'proposed', 'reviewed': False}, s['grouping'])
        self.assertEqual(self.commit, s['source']['commit'])
        self.assertEqual(s['scorerSha256'], s['queryCode']['web/scorer.js'])
        self.assertIn('README.md', {f['path'] for f in s['inventory']})

    def test_every_worker_packet_satisfies_the_frozen_evidence_contract(self):
        requests = [
            {'requestId': 'locate', 'query': 'lib/core.py'},
            {'requestId': 'choice', 'query': 'util.py'},
            {'requestId': 'chosen', 'query': 'util.py', 'chosenNodeId': 'lib/util.py'},
            {'requestId': 'none', 'query': 'zzqx_nothing.py'},
            {'requestId': 'down', 'query': 'what depends on lib/core.py'},
            {'requestId': 'up', 'query': 'dependencies of lib/core.py'},
            {'requestId': 'path', 'query': 'path from app/main.py to lib/b.py'},
            {'requestId': 'nopath', 'query': 'path from lib/b.py to app/main.py'},
            {'requestId': 'stale', 'query': 'lib/core.py', 'snapshotId': 'other'},
        ]
        done, replies = run_worker(self.path, requests)
        self.assertEqual(0, done.returncode, done.stderr)
        self.assertEqual(len(requests), len(replies))
        statuses = {}
        for reply in replies:
            self.assertTrue(reply['ok'], reply)
            packet = reply['packet']
            validate_evidence_packet(packet, self.snapshot)
            statuses[packet['requestId']] = (packet['status'], packet['operation'], packet['highlightState'])
        self.assertEqual(('matched', 'LOCATE', 'relevant'), statuses['locate'])
        self.assertEqual('needs-choice', statuses['choice'][0])
        self.assertEqual('matched', statuses['chosen'][0])
        self.assertEqual(('matched', 'DOWNSTREAM', 'potential-impact'), statuses['down'])
        self.assertEqual(('matched', 'UPSTREAM', 'relevant'), statuses['up'])
        self.assertEqual(('matched', 'PATH', 'relevant'), statuses['path'])
        self.assertEqual('no-path', statuses['nopath'][0])
        self.assertEqual('stale', statuses['stale'][0])

    def test_packet_from_one_snapshot_is_rejected_against_another(self):
        _, replies = run_worker(self.path, [{'requestId': 'x', 'query': 'what depends on lib/core.py'}])
        packet = replies[0]['packet']
        other = json.loads(json.dumps(self.snapshot))
        other['snapshotId'] = 'f' * 64
        with self.assertRaises(ContractError):
            validate_evidence_packet(packet, other)

    def test_worker_refuses_snapshot_bound_to_different_query_code(self):
        tampered = json.loads(self.path.read_text())
        tampered['queryCode']['web/router.js'] = '0' * 64
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / 's.json'
            path.write_text(json.dumps(tampered))
            done, replies = run_worker(path, [{'requestId': 'x', 'query': 'lib/core.py'}])
        self.assertEqual(2, done.returncode)
        self.assertIn('differs from the bytes bound', done.stderr)
        self.assertEqual([], replies)

    def test_bad_request_line_reports_error_without_killing_worker(self):
        done, replies = run_worker(self.path, [{'query': 'no id'}, {'requestId': 'ok', 'query': 'lib/core.py'}])
        self.assertEqual(0, done.returncode)
        self.assertFalse(replies[0]['ok'])
        self.assertTrue(replies[1]['ok'])

    def test_load_rejects_tampered_publication(self):
        with tempfile.TemporaryDirectory() as raw:
            copy = Path(raw) / 'pub'
            shutil.copytree(self.out, copy)
            preview = copy / 'preview.json'
            preview.write_bytes(preview.read_bytes().replace(b'"import"', b'"imporx"', 1))
            with self.assertRaises(SnapshotError):
                load_publication(copy)


if __name__ == '__main__':
    unittest.main()
