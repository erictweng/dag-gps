"""Explanation storage beside a revision: validate-before-write, re-validate on read."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from app.contracts import validate_evidence_packet
from app.explanation_store import list_explanations, store_explanation
from app.explanations import ExplanationError, packet_digest
from test_agent_explanations import explanation
from test_workspace_contract import fixture

PID, SID = 'p-' + '0' * 20, 'a' * 64


def store_fixture():
    snapshot, packet = fixture()
    text = json.dumps([snapshot, packet]).replace('"synthetic-unit"', '"%s"' % PID)
    text = text.replace('"synthetic-revision-a"', '"%s"' % SID)
    snapshot, packet = json.loads(text)
    validate_evidence_packet(packet, snapshot)
    return snapshot, packet


class ExplanationStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.snapshot, self.packet = store_fixture()
        self.value = explanation(self.packet)

    def tearDown(self):
        self._tmp.cleanup()

    def test_store_then_list_round_trip(self):
        store_explanation(self.root, self.snapshot, self.packet, self.value)
        items = list_explanations(self.root, self.snapshot)
        self.assertEqual(1, len(items))
        self.assertTrue(items[0]['valid'])
        self.assertEqual(self.value, items[0]['record']['explanation'])
        self.assertEqual([], list(self.root.glob('projects/*/explanations/*/.*.tmp')))

    def test_invalid_explanation_is_never_written(self):
        bad = copy.deepcopy(self.value)
        bad['packetSha256'] = '0' * 64
        with self.assertRaises(ExplanationError):
            store_explanation(self.root, self.snapshot, self.packet, bad)
        self.assertEqual([], list_explanations(self.root, self.snapshot))

    def test_context_must_belong_to_packet_and_restricts_citations(self):
        context = {'schema': 'dag-gps-context/v1', 'snapshotId': SID, 'requestId': self.packet['requestId'],
                   'packetSha256': packet_digest(self.packet), 'files': [{'path': 'b.py'}]}
        with self.assertRaises(ExplanationError):  # cites a.py, context only has b.py
            store_explanation(self.root, self.snapshot, self.packet, self.value, context)
        foreign = dict(context, packetSha256='1' * 64, files=[{'path': 'a.py'}])
        with self.assertRaises(ExplanationError):
            store_explanation(self.root, self.snapshot, self.packet, self.value, foreign)
        ok = dict(context, files=[{'path': 'a.py'}])
        record = store_explanation(self.root, self.snapshot, self.packet, self.value, ok)
        self.assertEqual(['a.py'], record['contextFiles'])

    def test_tampered_record_is_reported_invalid_not_displayed(self):
        store_explanation(self.root, self.snapshot, self.packet, self.value)
        path = next(self.root.glob('projects/*/explanations/*/*.json'))
        record = json.loads(path.read_text())
        record['explanation']['paragraphs'][0]['citations'][0]['sha256'] = 'f' * 64
        path.write_text(json.dumps(record))
        items = list_explanations(self.root, self.snapshot)
        self.assertEqual([False], [i['valid'] for i in items])
        self.assertIsNone(items[0]['record'])

    def test_other_revision_does_not_see_records_and_ids_are_validated(self):
        store_explanation(self.root, self.snapshot, self.packet, self.value)
        other = dict(self.snapshot, snapshotId='b' * 64)
        self.assertEqual([], list_explanations(self.root, other))
        with self.assertRaises(ExplanationError):
            list_explanations(self.root, dict(self.snapshot, projectId='../../etc'))


if __name__ == '__main__':
    unittest.main()
