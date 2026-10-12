"""Cross-language tier packets and full legacy certain-only parity."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts'), str(ROOT / 'tests')]
from python_symbols import extract_symbols
from test_function_contract import fixture
from app.contracts import validate_snapshot, validate_evidence_packet, ContractError

SOURCE = '''def leaf(): pass
@wrap
def decorated(): leaf()
class A:
 def work(self): decorated()
 def run(self):
  self.work()
  x = A()
  x.work()
def run(agent: A):
 agent.work()
 unknown()
'''


class TierPackets(unittest.TestCase):
    def snapshot(self):
        s = fixture()
        s['inventory'][0]['lineCount'] = len(SOURCE.splitlines())
        s['map']['symbol_graph'] = extract_symbols({'a.py': SOURCE}, [])
        return s

    def query(self, s, certain=False):
        code = "const Q=require('./web/query-service.js');let s='';process.stdin.on('data',d=>s+=d);process.stdin.on('end',()=>console.log(JSON.stringify(Q.querySnapshot(JSON.parse(s),{requestId:'r',query:'trace from run',chosenNodeId:'a.py#run@10',certainOnly:" + str(certain).lower() + "}))));"
        p = subprocess.run(['node', '-e', code], cwd=ROOT, input=json.dumps(s), text=True, capture_output=True, check=True)
        return json.loads(p.stdout)

    def test_weakest_witness_and_tampering(self):
        s = self.snapshot()
        validate_snapshot(s)
        p = self.query(s)
        validate_evidence_packet(p, s)
        self.assertEqual({w['confidence'] for w in p['witnesses']}, {'typed', 'through-decorator'})
        self.assertTrue(any('decorators' in e for e in p['selectedEdges']))
        bad = copy.deepcopy(p)
        bad['witnesses'][-1]['confidence'] = 'resolved'
        with self.assertRaises(ContractError):
            validate_evidence_packet(bad, s)
        self.assertEqual(len(self.query(s, True)['selectedNodeIds']), 1)
        validate_evidence_packet(self.query(s, True), s)

    def test_full_certain_packet_parity_with_baseline(self):
        s = self.snapshot()
        namespace = {}
        old = subprocess.check_output(['git', 'show', '62010f6:scripts/python_symbols.py'], cwd=ROOT, text=True)
        exec(compile(old, '<baseline>', 'exec'), namespace)
        baseline = copy.deepcopy(s)
        baseline['map']['symbol_graph'] = namespace['extract_symbols']({'a.py': SOURCE}, [])
        code = r"""
const cp=require('child_process'),vm=require('vm'),path=require('path');
const box={module:{exports:{}},TextEncoder,require:n=>require(path.resolve('web',n))};
vm.runInNewContext(cp.execFileSync('git',['show','62010f6:web/query-service.js'],{encoding:'utf8'}),box);
let text='';process.stdin.on('data',d=>text+=d);process.stdin.on('end',()=>{
 const [before,after]=JSON.parse(text),Q=require('./web/query-service.js');
 for(const query of ['trace from A.run','what calls A.work','what does A.run call','trace from a.py:run','how does A.run reach leaf','where is decorated defined']){
  const req={requestId:'r',query};
  const a=box.module.exports.querySnapshot(before,req),b=Q.querySnapshot(after,{...req,certainOnly:true});
  delete b.certainOnly;
  require('assert').deepStrictEqual(JSON.parse(JSON.stringify(a)),b,query);
 }
 console.log('6 complete packets identical (except explicit certainOnly mode marker)');
});
"""
        p = subprocess.run(['node', '-e', code], cwd=ROOT, input=json.dumps([baseline, s]), text=True, capture_output=True)
        self.assertEqual(p.returncode, 0, p.stderr)

    def test_additions_and_confidence_count_integrity(self):
        s = self.snapshot()
        for mutation in (lambda g: g['counts'].update(typed=99),
                         lambda g: g['edges'][0].update(confidence='bogus'),
                         lambda g: g['certainAdditions'].pop()):
            bad = copy.deepcopy(s)
            mutation(bad['map']['symbol_graph'])
            with self.assertRaises(ContractError):
                validate_snapshot(bad)
