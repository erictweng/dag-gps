"""Consultant counterexamples: lexical ownership, bounded packets, legacy parity."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'tests')]
from python_symbols import extract_symbols
from test_function_contract import fixture
from app.contracts import validate_snapshot, validate_evidence_packet, MAX_PACKET_BYTES


class FunctionReviewTests(unittest.TestCase):
    def test_wildcard_invalidates_local_and_imported_lookup(self):
        for source in ('def leaf(): pass\nfrom b import *\ndef run(): leaf()\n',
                       'from a import leaf\ndef run(): leaf()\n'):
            sources = {'c.py': source, 'a.py': 'def leaf(): pass\nfrom b import *\n',
                       'b.py': 'def leaf(): pass\n'}
            graph = extract_symbols(sources, [('c.py', 'a.py'), ('c.py', 'b.py'), ('a.py', 'b.py')])
            self.assertEqual(graph['edges'], [])

    def test_definition_expressions_bind_in_enclosing_scope(self):
        for definition in ('def inner(x=(leaf := callback)): pass',
                           '@(leaf := callback)\n    def inner(): pass',
                           'def inner(x: (leaf := callback)): pass',
                           'def inner() -> (leaf := callback): pass'):
            with self.subTest(definition=definition):
                graph = extract_symbols({'a.py': 'def leaf(): pass\ndef run(callback):\n    ' + definition + '\n    leaf()\n'}, [])
                self.assertEqual(graph['edges'], [])

    def test_definition_calls_use_outer_parameters_not_inner_parameters(self):
        graph = extract_symbols({'a.py': 'def leaf(): pass\ndef run():\n    def inner(leaf=leaf()): pass\n'}, [])
        self.assertEqual([(e['from'], e['to']) for e in graph['edges']], [('a.py#run@2', 'a.py#leaf@1')])

    def test_deferred_lambda_and_class_body_are_not_invocation_edges(self):
        for source in ('def leaf(): pass\ndef run(): return lambda: leaf()\n',
                       'def leaf(): pass\nclass A:\n    leaf()\ndef run(): A()\n',
                       'def leaf(): pass\ndef run(): return (leaf() for x in [])\n'):
            with self.subTest(source=source):
                graph = extract_symbols({'a.py': source}, [])
                self.assertFalse(any(e['to'] == 'a.py#leaf@1' for e in graph['edges']))
                self.assertTrue(any(c['expression'] == 'leaf' for c in graph['unresolved']))

    def test_large_trace_packets_validate_across_languages(self):
        for sites in (1, 20):
            with self.subTest(sites=sites):
                source = ''.join('def f%d():\n%s' % (i, ('    f%d()\n' % (i + 1)) * sites if i < 149 else '    pass\n') for i in range(150))
                snapshot = fixture()
                snapshot['map']['symbol_graph'] = extract_symbols({'a.py': source}, [])
                snapshot['inventory'][0]['lineCount'] = len(source.splitlines())
                validate_snapshot(snapshot)
                code = "const Q=require('./web/query-service.js');let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>console.log(JSON.stringify(Q.querySnapshot(JSON.parse(s),{requestId:'r',query:'trace from f0'}))));"
                result = subprocess.run(['node', '-e', code], cwd=ROOT, input=json.dumps(snapshot), text=True, capture_output=True, check=True)
                packet = json.loads(result.stdout)
                self.assertLessEqual(len(json.dumps(packet, ensure_ascii=False).encode()), MAX_PACKET_BYTES)
                validate_evidence_packet(packet, snapshot)
                self.assertIn(packet['status'], ('matched', 'unsupported'))
                if packet['status'] == 'unsupported':
                    self.assertEqual(packet['selectedNodeIds'], [])
                    self.assertEqual(packet['witnesses'], [])

    def test_legacy_file_and_group_parity_with_and_without_extension(self):
        code = r"""
const cp=require('child_process'),vm=require('vm'),path=require('path');
const box={module:{exports:{}},require:n=>require(path.resolve('web',n))};
vm.runInNewContext(cp.execFileSync('git',['show','eb72a73:web/query-service.js'],{encoding:'utf8'}),box);
const Q=require('./web/query-service.js'),map=require('./maps/quest-coder/map.json');
const s={schema:'dag-gps-workspace/v1',projectId:'p',snapshotId:'s',mapSha256:'a',scorerSha256:'b',source:{manifestSha256:'c'},map,inventory:map.nodes.filter(n=>n.path).map(n=>({path:n.path,sha256:'d'}))};
const queries=['where is lib/runner-client.ts defined','where is runner-service defined'];
for(const extension of [false,true]) {
 if(extension) map.symbol_graph={nodes:[],edges:[],unresolved:[]};
 for(const query of queries) {
  const request={requestId:'r',query};
  const before=box.module.exports.querySnapshot(s,request),after=Q.querySnapshot(s,request);
  if(JSON.stringify(before)!==JSON.stringify(after)) throw Error(JSON.stringify({extension,query,before,after}));
 }
 // Caller vocabulary now preserves traversal rather than the old LOCATE fallthrough.
 for(const target of ['lib/runner-client.ts','runner-service']) {
  const p=Q.querySnapshot(s,{requestId:'r',query:'what calls '+target});
  const expected=Q.querySnapshot(s,{requestId:'r',query:'downstream of '+target});
  if(p.operation!=='DOWNSTREAM' || JSON.stringify(p.selectedNodeIds)!==JSON.stringify(expected.selectedNodeIds) ||
    JSON.stringify(p.witnesses)!==JSON.stringify(expected.witnesses)) throw Error('Caller traversal mismatch: '+target);
 }
}
"""
        result = subprocess.run(['node', '-e', code], cwd=ROOT, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
