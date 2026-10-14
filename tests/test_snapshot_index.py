"""Indexed validation regressions; unchanged full-validator fixtures also replayed."""
import copy
import json
import os
import threading
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

from app import contracts
from app.server import WorkspaceStore
from app.query_worker import WorkerPool, QueryBusy, QueryWorker, QueryWorkerError
from test_workspace_contract import fixture


class SnapshotIndexTests(unittest.TestCase):
    def test_packet_checks_do_not_revalidate_snapshot(self):
        snapshot, packet = fixture()
        index = contracts.validate_snapshot(snapshot)
        with mock.patch.object(contracts, 'validate_snapshot', side_effect=AssertionError('full scan')):
            self.assertIs(contracts.validate_evidence_packet_against(packet, index), packet)

    def test_packet_tampering_equivalence(self):
        snapshot, packet = fixture()
        index = contracts.validate_snapshot(snapshot)
        mutations = [lambda p: p.update(snapshotId='foreign'),
                     lambda p: p.update(selectedNodeIds=['missing']),
                     lambda p: p['sourceRefs'][0].update(start=0),
                     lambda p: p['sourceRefs'][0].update(sha256='0' * 64)]
        for mutate in mutations:
            bad = copy.deepcopy(packet)
            mutate(bad)
            with self.assertRaises(contracts.ContractError) as old:
                contracts.validate_evidence_packet(bad, snapshot)
            with self.assertRaises(contracts.ContractError) as new:
                contracts.validate_evidence_packet_against(bad, index)
            self.assertEqual(str(old.exception), str(new.exception))

    def test_foreign_index_is_rejected(self):
        snapshot, _ = fixture()
        index = contracts.validate_snapshot(snapshot)
        with self.assertRaisesRegex(contracts.ContractError, 'different snapshot'):
            index.for_snapshot(copy.deepcopy(snapshot))

    def test_unresolved_order_count_and_bounded_prefix(self):
        from test_function_contract import fixture as symbol_fixture
        snapshot = symbol_fixture()
        extension = snapshot['map']['symbol_graph']
        call = extension['unresolved'][0]
        extension['unresolved'] = [dict(call, expression='unknown%d()' % n,
                                       **{'from': 'a.py#run@2' if n % 2 else 'a.py#leaf@1'}) for n in range(501)]
        extension['counts']['unresolved'] = 501
        index = contracts.validate_snapshot(snapshot)
        for certain in [False, True]:
            first, count = index.unresolved_for(['a.py#run@2', 'a.py#leaf@1'], certain)
            self.assertEqual(count, 501)
            self.assertEqual(first, extension['unresolved'][:100])
            self.assertTrue(all(len(rows) <= 100 for _, rows in index.unresolved[int(certain)].values()))


class SnapshotCacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = WorkspaceStore(Path(self.tmp.name))
        self.snapshots = []
        for n in range(5):
            snapshot, _ = fixture()
            snapshot.update(projectId='p-' + 'a' * 20, snapshotId=str(n) * 64)
            self.store.project_dir(snapshot['projectId']).mkdir(exist_ok=True)
            path = self.store.root / ('snapshot%d.json' % n)
            path.write_text(json.dumps(snapshot))
            self.store.record(snapshot, path)
            self.snapshots.append(snapshot)

    def load(self, n=0):
        s = self.snapshots[n]
        return self.store.snapshot(s['projectId'], s['snapshotId'])

    def test_hit_and_disk_tamper(self):
        path, first = self.load()
        self.assertIs(self.load()[1], first)
        bad = copy.deepcopy(first)
        bad['map']['nodes'][0]['kind'] = 'invalid'
        path.write_text(json.dumps(bad))
        with self.assertRaises(contracts.ContractError):
            self.load()
        path.write_text(json.dumps(self.snapshots[0]))
        self.assertIsNot(self.load()[1], first)

    def test_alternation_eviction_and_concurrent_load(self):
        first = self.load()[1]
        other = self.load(1)[1]
        self.assertIs(self.load()[1], first)
        self.assertIs(self.load(1)[1], other)
        for n in [2, 3, 4]:
            self.load(n)
        self.assertIsNot(self.load()[1], first)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.load()[1], range(32)))
        self.assertTrue(all(s is results[0] for s in results))
        self.assertEqual(len(self.store._snapshots), 4)

    def test_equal_size_restored_mtime_edit_invalidates(self):
        path, before = self.load()
        stat = path.stat()
        path.write_text(path.read_text().replace('dependency-preview', 'inventory-ready   '))
        os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        self.assertEqual(path.stat().st_size, stat.st_size)
        with self.assertRaises(contracts.ContractError):
            self.load()

    def test_concurrent_cold_load_validates_once(self):
        import app.server as server
        with mock.patch.object(server, 'validate_snapshot', wraps=contracts.validate_snapshot) as validate:
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(lambda _: self.load()[1], range(32)))
            self.assertEqual(validate.call_count, 1)
            self.assertTrue(all(s is results[0] for s in results))

    def test_file_replacement_and_identity_mismatch(self):
        from app.server import ApiError
        path, _ = self.load()
        other = path.with_suffix('.replacement')
        bad = dict(self.snapshots[0], projectId='p-' + 'b' * 20)
        other.write_text(json.dumps(bad))
        other.replace(path)
        with self.assertRaisesRegex(ApiError, 'identity mismatch'):
            self.load()


class IndexedWorkerTests(unittest.TestCase):
    def setUp(self):
        from test_function_contract import fixture as symbol_fixture
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = WorkspaceStore(Path(self.tmp.name))
        self.snapshots = []
        for n in range(2):
            s = symbol_fixture()
            s.update(projectId='p-' + 'c' * 20, snapshotId=str(n) * 64)
            path = self.store.root / ('s%d.json' % n)
            path.write_text(json.dumps(s))
            self.store.project_dir(s['projectId']).mkdir(exist_ok=True)
            self.store.record(s, path)
            self.snapshots.append(s)
        self.pool = WorkerPool(size=2)
        self.addCleanup(self.pool.close)

    def load(self, n=0):
        s = self.snapshots[n]
        return self.store.snapshot(s['projectId'], s['snapshotId'], with_index=True)

    def ask(self, n=0):
        path, s, index = self.load(n)
        packet = self.pool.query(path, s, dict(requestId=str(n), query='a.py'), index=index)
        contracts.validate_evidence_packet_against(packet, index)
        return packet

    def test_alternating_concurrent_real_workers(self):
        with ThreadPoolExecutor(max_workers=4) as executor:
            packets = list(executor.map(self.ask, [0, 1] * 12))
        self.assertEqual([p['snapshotId'] for p in packets], [str(n) * 64 for n in [0, 1] * 12])
        self.assertEqual(len(self.pool._workers), 2)

    def test_same_id_changed_generation_uses_new_worker(self):
        first = self.ask()
        path, snapshot, _ = self.load()
        changed = copy.deepcopy(snapshot)
        changed['inventory'][0]['sha256'] = 'e' * 64
        path.write_text(json.dumps(changed))
        second = self.ask()
        self.assertNotEqual(first['sourceRefs'], second['sourceRefs'])
        self.assertEqual(second['sourceRefs'][0]['sha256'], 'e' * 64)

    def test_startup_rejects_file_changed_after_validation(self):
        path, snapshot, index = self.load()
        path.write_text(path.read_text() + ' ')
        with QueryWorker(path, snapshot, index=index) as worker:
            with self.assertRaisesRegex(QueryWorkerError, 'changed since validation'):
                worker.query(dict(requestId='x', query='a.py'))

    def test_busy_worker_cannot_be_evicted_and_idle_worker_can(self):
        self.pool.size = 1
        path, snapshot, index = self.load()
        worker = self.pool.get(path, snapshot, index=index)
        entered, release = threading.Event(), threading.Event()
        def wait(_):
            entered.set()
            self.assertTrue(release.wait(5))
            return {}
        with mock.patch.object(worker, 'query', side_effect=wait), ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.pool.query, path, snapshot, {}, index=index)
            self.assertTrue(entered.wait(5))
            try:
                other_path, other, other_index = self.load(1)
                with self.assertRaises(QueryBusy):
                    self.pool.query(other_path, other, {}, index=other_index)
            finally:
                release.set()
            future.result()
        self.ask(1)
        self.assertEqual(len(self.pool._workers), 1)


if __name__ == '__main__':
    unittest.main()
