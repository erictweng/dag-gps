"""Collision choice/replay packets satisfy the unmodified Python contract."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'tests')]
from python_symbols import extract_symbols
from test_function_contract import fixture
from test_query_packets import run_worker
from app.contracts import validate_snapshot, validate_evidence_packet


class CollisionPacketTests(unittest.TestCase):
    def test_every_operation_and_ui_choice_packet_validates(self):
        snapshot = fixture()
        snapshot['map']['symbol_graph'] = extract_symbols(
            {'a.py': 'def leaf(): pass\ndef a(): leaf()\ndef run(): a()\n'}, [])
        validate_snapshot(snapshot)
        queries = ['where is a', 'what uses a', 'what does a use', 'who invokes a',
                   'what does a call', 'trace from a', 'upstream of a', 'downstream of a',
                   'path from a to a.py', 'path from a.py to a', 'how does a reach a.py',
                   'path from function a to function leaf', 'downstream of function leaf']
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot.json'
            path.write_text(json.dumps(snapshot))
            requests = [{'requestId': str(i), 'query': query} for i, query in enumerate(queries)]
            done, replies = run_worker(path, requests)
            self.assertEqual(done.returncode, 0, done.stderr)
            choices = []
            for reply in replies:
                self.assertTrue(reply['ok'], reply)
                packet = reply['packet']
                validate_evidence_packet(packet, snapshot)
                for alternative in packet['alternatives']:
                    choices.append({'requestId': 'choice-' + str(len(choices)),
                                    'query': alternative['query'], 'chosenNodeId': alternative['nodeId']})
            self.assertGreater(len(choices), 0)
            done, chosen = run_worker(path, choices)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(len(chosen), len(choices))
            for reply in chosen:
                self.assertTrue(reply['ok'], reply)
                validate_evidence_packet(reply['packet'], snapshot)
                self.assertNotEqual(reply['packet']['status'], 'needs-choice')
