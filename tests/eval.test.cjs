const test = require('node:test');
const assert = require('node:assert/strict');
const path = require('node:path');
const {loadCases, validateCases, shortestPath, evaluate} = require('../scripts/eval_scorer.cjs');
const map = require('../maps/quest-coder/map.json');
const rows = loadCases(path.join(__dirname,'../eval/eval.jsonl'),map);
test('generated benchmark covers all operations and inspected graph routes', () => {
  assert.equal(rows.length,47);
  assert.deepEqual([...new Set(rows.map(r=>r.operation))].sort(), ['DOWNSTREAM','LOCATE','NOT_SURE','PATH','UPSTREAM']);
  assert.equal(rows.filter(r=>r.operation==='NOT_SURE').length,10);
  assert.equal(rows.filter(r=>r.operation==='PATH').length,7);
  assert.equal(shortestPath(map,'persistence','solve-ui'),null);
  assert.deepEqual(shortestPath(map,'solve-ui','persistence'),['solve-ui','api','persistence']);
});
test('invalid expectations and invented routes fail rather than inflate benchmark', () => {
  for(const mutate of [
    r=>{r[0].target='fictional';},
    r=>{r[1].id=r[0].id;},
    r=>{r[0].operation='MAGIC';},
    r=>{r.find(x=>x.operation==='PATH').expected_route=['solve-ui','persistence'];},
    r=>{r[0].provenance='user-ground-truth';},
  ]) {const bad=structuredClone(rows);mutate(bad);assert.throws(()=>validateCases(bad,map));}
  assert.throws(()=>validateCases([],map));
});
test('metrics deterministic apart from separately measured latency; negatives separate', () => {
  const a=evaluate(map,rows,1),b=evaluate(map,rows,1);
  delete a.latency;delete b.latency;assert.deepEqual(a,b);
  assert.equal(a.targetTop1.total,44);
  assert.equal(a.positiveAbstentionRate.total,37);
  assert.equal(a.negativeAbstentionRate.total,10);
  assert.equal(a.pathEndpointAccuracy.total,14);
});
