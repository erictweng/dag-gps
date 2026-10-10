"""M2.2 persistent query worker lifecycle: request-ID matching, revision-swap
rejection, timeouts with restart, queue bounds and stderr separation."""
import json
import shutil
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'tests'))

from app.query_worker import QueryWorker, QueryWorkerError, QueryTimeout  # noqa: E402
from app.snapshots import build_workspace_snapshot  # noqa: E402
from app.workspace_snapshot import load_publication, write_snapshot  # noqa: E402
from test_workspace_snapshot import acquire  # noqa: E402

NODE = shutil.which('node')
FILES = {'lib/__init__.py': '', 'lib/core.py': 'from lib import util\n', 'lib/util.py': 'X = 1\n'}


def fake_worker(root, body):
    path = root / 'fake_worker.cjs'
    path.write_text(textwrap.dedent('''
        const rl = require('readline').createInterface({input: process.stdin});
        rl.on('line', line => { const r = JSON.parse(line); %s });
    ''') % body)
    return [NODE, str(path)]


@unittest.skipUnless(NODE, 'node is required')
class QueryWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls._tmp.name)
        result, _, _ = acquire(cls.root, FILES)
        build_workspace_snapshot(result, cls.root / 'pub')
        cls.snapshot = load_publication(cls.root / 'pub')
        cls.path = cls.root / 'snapshot.json'
        write_snapshot(cls.snapshot, cls.path)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_persistent_worker_answers_many_requests_with_one_process(self):
        with QueryWorker(self.path, self.snapshot) as worker:
            first = worker.query({'requestId': 'a', 'query': 'lib/core.py'})
            pid = worker.pid
            second = worker.query({'requestId': 'b', 'query': 'what depends on lib/util.py'})
            self.assertEqual(pid, worker.pid)
        self.assertEqual(('a', 'matched'), (first['requestId'], first['status']))
        self.assertEqual('b', second['requestId'])

    def test_mismatched_request_id_is_rejected(self):
        command = fake_worker(self.root, "r.requestId = 'other'; process.stdout.write(JSON.stringify({ok:true, packet:r}) + '\\n');")
        with QueryWorker(self.path, self.snapshot, command=command) as worker:
            with self.assertRaisesRegex(QueryWorkerError, 'request ID'):
                worker.query({'requestId': 'mine', 'query': 'x'})

    def test_packet_for_another_revision_is_rejected(self):
        with QueryWorker(self.path, self.snapshot) as real:
            good = real.query({'requestId': 'swap', 'query': 'lib/core.py'})
        forged = dict(good, snapshotId='e' * 64)
        command = fake_worker(self.root, "process.stdout.write(JSON.stringify({ok:true, packet:%s}) + '\\n');" % json.dumps(forged))
        with QueryWorker(self.path, self.snapshot, command=command) as worker:
            with self.assertRaisesRegex(QueryWorkerError, 'contract'):
                worker.query({'requestId': 'swap', 'query': 'lib/core.py'})

    def test_timeout_kills_and_restarts_worker(self):
        command = fake_worker(self.root, "if (r.query === 'hang') return; process.stdout.write(JSON.stringify({ok:false, requestId:r.requestId, error:'bad'}) + '\\n');")
        with QueryWorker(self.path, self.snapshot, command=command, timeout=0.5) as worker:
            pid = worker.pid
            with self.assertRaises(QueryTimeout):
                worker.query({'requestId': 'h', 'query': 'hang'})
            with self.assertRaisesRegex(QueryWorkerError, 'bad'):
                worker.query({'requestId': 'n', 'query': 'next'})
            self.assertNotEqual(pid, worker.pid)

    def test_oversized_reply_line_is_rejected(self):
        command = fake_worker(self.root, "process.stdout.write('x'.repeat(3 * 1024 * 1024) + '\\n');")
        with QueryWorker(self.path, self.snapshot, command=command, timeout=5) as worker:
            with self.assertRaisesRegex(QueryWorkerError, 'too large'):
                worker.query({'requestId': 'big', 'query': 'x'})

    def test_stderr_is_separated_and_bounded(self):
        command = fake_worker(self.root, "process.stderr.write('noise '.repeat(50000)); process.stdout.write(JSON.stringify({ok:false, requestId:r.requestId, error:'e'}) + '\\n');")
        with QueryWorker(self.path, self.snapshot, command=command) as worker:
            with self.assertRaises(QueryWorkerError):
                worker.query({'requestId': 's', 'query': 'x'})
            self.assertLessEqual(len(worker.stderr_tail()), 16 * 1024)

    def test_worker_refusing_snapshot_is_reported(self):
        tampered = json.loads(self.path.read_text())
        tampered['queryCode']['web/scorer.js'] = '0' * 64
        path = self.root / 'tampered.json'
        path.write_text(json.dumps(tampered))
        with self.assertRaisesRegex(QueryWorkerError, 'exited'):
            with QueryWorker(path, tampered) as worker:
                worker.query({'requestId': 'x', 'query': 'lib/core.py'})


if __name__ == '__main__':
    unittest.main()
