"""Re-export provenance survives JS queries and fails closed on tampering."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'tests')]
from python_symbols import extract_symbols
from test_function_contract import fixture
from test_query_packets import run_worker
from app.contracts import validate_snapshot, validate_evidence_packet, ContractError


class ReexportPackets(unittest.TestCase):
    def snapshot(self):
        sources = {'a.py': 'from pkg import work\ndef run(): work()\n',
                   'pkg/__init__.py': 'from .impl import work\n',
                   'pkg/impl.py': 'from typing import overload\n@overload\ndef work(x: int): ...\ndef work(x=None): pass\n'}
        imports = [('a.py', 'pkg/__init__.py'), ('pkg/__init__.py', 'pkg/impl.py')]
        s = fixture()
        s['inventory'] = [{'path': p, 'sha256': 'd' * 64, 'lineCount': len(text.splitlines())} for p, text in sources.items()]
        s['map']['nodes'] = [s['map']['nodes'][0]] + [{'id': p, 'kind': 'file', 'path': p, 'layer': 'group'} for p in sources]
        s['map']['file_edges'] = [{'from': a, 'to': b, 'type': 'import'} for a, b in imports]
        s['map']['symbol_graph'] = extract_symbols(sources, imports)
        return s

    def test_certain_only_keeps_static_hops_and_implementation(self):
        s = self.snapshot()
        validate_snapshot(s)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'snapshot.json'
            p.write_text(json.dumps(s))
            done, replies = run_worker(p, [{'requestId': str(mode), 'query': 'what does run call', 'certainOnly': mode} for mode in (False, True)])
        self.assertEqual(done.returncode, 0, done.stderr)
        for reply in replies:
            self.assertTrue(reply['ok'], reply)
            packet = reply['packet']
            validate_evidence_packet(packet, s)
            self.assertEqual(packet['selectedEdges'][0]['to'], 'pkg/impl.py#work@4')
            self.assertEqual(packet['selectedEdges'][0]['sites'][0]['reexports'][0]['path'], 'pkg/__init__.py')
            bad = copy.deepcopy(packet)
            bad['selectedEdges'][0]['sites'][0]['reexports'][0]['start'] = 2
            with self.assertRaises(ContractError):
                validate_evidence_packet(bad, s)

    def test_reexport_contract_rejects_bad_chains(self):
        for update in ({'path': 'a.py'}, {'targetPath': 'missing.py'}, {'targetName': 'stub'}, {'start': 99}, {'end': 0}):
            with self.subTest(update=update):
                s = self.snapshot()
                s['map']['symbol_graph']['edges'][0]['sites'][0]['reexports'][0].update(update)
                with self.assertRaises(ContractError):
                    validate_snapshot(s)

    def test_reexport_contract_requires_observed_import(self):
        s = self.snapshot()
        s['map']['file_edges'].pop()
        with self.assertRaises(ContractError):
            validate_snapshot(s)
