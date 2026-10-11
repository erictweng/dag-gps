"""Symbol extension and cross-language packets, synthetic source only."""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from python_symbols import extract_symbols
from app.contracts import ContractError, validate_snapshot, validate_evidence_packet
from app.workspace_snapshot import query_code_digests
from test_query_packets import run_worker


def fixture():
    text = 'def leaf(): pass\ndef run():\n    leaf()\n    unknown()\n'
    return {'schema': 'dag-gps-workspace/v1', 'projectId': 'fixture', 'snapshotId': 'fixture',
            'mapSha256': 'a'*64, 'scorerSha256': query_code_digests()['web/scorer.js'],
            'queryCode': query_code_digests(),
            'source': {'kind': 'git-commit', 'repo': 'test/fixture', 'commit': 'b'*40,
                       'worktreeId': None, 'manifestSha256': 'c'*64},
            'state': 'dependency-preview', 'grouping': {'status': 'proposed', 'reviewed': False},
            'inventory': [{'path': 'a.py', 'sha256': 'd'*64, 'lineCount': 4}],
            'map': {'meta': {'repo': 'test/fixture', 'snapshot_commit': 'b'*40},
                    'nodes': [{'id': 'group', 'kind': 'layer', 'label': 'group'},
                              {'id': 'a.py', 'kind': 'file', 'path': 'a.py', 'layer': 'group'}],
                    'edges': [], 'file_edges': [], 'symbol_graph': extract_symbols({'a.py': text}, [])}}


class FunctionContractTests(unittest.TestCase):
    def test_extension_catalog_and_range_guards(self):
        s = fixture()
        catalog = validate_snapshot(s)
        self.assertIn('a.py#run@2', catalog['nodeIds'])
        for mutate in (
            lambda g: g.update(schema='future'),
            lambda g: g['nodes'][0].update(end=99),
            lambda g: g['edges'][0]['sites'][0].update(path='missing.py'),
            lambda g: g['edges'][0].update(to='invented'),
            lambda g: g['unresolved'][0].update(to='a.py#leaf@1'),
            lambda g: g['counts'].update(resolved=99),
        ):
            bad = copy.deepcopy(s)
            mutate(bad['map']['symbol_graph'])
            with self.assertRaises(ContractError):
                validate_snapshot(bad)

    def test_packets_and_site_tampering(self):
        s = fixture()
        queries = ['where is run defined', 'what calls leaf', 'what does run call',
                   'how does run reach leaf', 'how does leaf reach run', 'trace from run', 'a.py']
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'snapshot.json'
            p.write_text(json.dumps(s))
            done, replies = run_worker(p, [{'requestId': str(i), 'query': q} for i, q in enumerate(queries)])
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(len(replies), len(queries))
        for reply in replies:
            self.assertTrue(reply['ok'], reply)
            validate_evidence_packet(reply['packet'], s)
        self.assertEqual([r['packet']['operation'] for r in replies],
                         ['LOCATE', 'CALLERS', 'CALLEES', 'FLOW', 'FLOW', 'TRACE', 'LOCATE'])
        self.assertEqual(replies[4]['packet']['status'], 'no-path')
        bad = copy.deepcopy(replies[1]['packet'])
        bad['selectedEdges'][0]['sites'][0]['start'] = 1
        with self.assertRaises(ContractError):
            validate_evidence_packet(bad, s)

    def test_legacy_map_still_valid_without_extension(self):
        s = fixture()
        del s['map']['symbol_graph']
        self.assertEqual(validate_snapshot(s)['nodeIds'], {'group', 'a.py'})
