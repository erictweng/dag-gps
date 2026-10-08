const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const {createScorer, validateHead, validateResult, OPERATIONS} = require('../web/scorer.js');
const map = require('../maps/quest-coder/map.json');
const scorer = createScorer(map);
const ids = map.nodes.map(n => n.id);

for (const [q, op, id] of [
  ['Please locate magic link', 'LOCATE', 'auth'],
  ['Which module uses the runner service?', 'DOWNSTREAM', 'runner-service'],
  ['Who imports run gateway?', 'DOWNSTREAM', 'run-gateway'],
  ['What would break if database changed?', 'DOWNSTREAM', 'persistence'],
  ['What is party service built on?', 'UPSTREAM', 'social-services'],
  ['Dependencies of pyodide?', 'UPSTREAM', 'browser-run'],
  ['What does lib/runner-client.ts import?', 'UPSTREAM', 'lib/runner-client.ts'],
  ['Find lib/progress-store.ts', 'LOCATE', 'lib/progress-store.ts'],
  ['Where is the UI kit?', 'LOCATE', 'design-system'],
  ['Locate app/api/health/route.ts', 'LOCATE', 'app/api/health/route.ts'],
  ['Where are route handlers?', 'LOCATE', 'api'],
  ['Locate hidden tests', 'LOCATE', 'content'],
]) test(`paraphrase: ${q}`, () => {
  const r = scorer.score(q);
  assert.equal(r.operation.choice, op); assert.equal(r.targets.locate_target.choice, id);
  assert.equal(r.yes, true); assert.equal(validateResult(r, map), true);
});

test('endpoint heads independent, and no route traversal in M2', () => {
  const r = scorer.score('Trace a route from magic link to db');
  assert.equal(r.operation.choice, 'PATH');
  assert.equal(r.targets.from_target.choice, 'auth');
  assert.equal(r.targets.to_target.choice, 'persistence');
  assert.equal(scorer.score('Trace from db to frobnicator').operation.choice, 'NOT_SURE');
  assert.equal(scorer.score('show path database').operation.choice, 'NOT_SURE');
});
for (const q of ['', '  ', 'please show me', 'quantum teleporter', 'where is top bar', 'auth and database',
  'path from mystery engine to database']) test(`abstains: ${JSON.stringify(q)}`, () => {
  const r = scorer.score(q); assert.equal(r.operation.choice, 'NOT_SURE'); assert.equal(r.yes, false);
  assert.equal(validateResult(r, map), true);
});
test('unknown lexical terms cannot acquire a structural match', () => {
  const r = scorer.score('zzzzunknown');
  assert.ok(Object.values(r.targets.locate_target.probabilities).every(p => p === 1 / ids.length));
  assert.ok(r.targets.locate_target.top3.every(a => a.components.structural === 0));
});
test('labels, aliases, descriptions, paths are individually explainable evidence', () => {
  const fixture = {nodes: [
    {id:'a', label:'Unique label', aliases:['secret alias'], desc:'unusual description', path:'lib/unique.ts'},
    {id:'b', label:'Other', desc:'', path:''}
  ]};
  const s = createScorer(fixture);
  for (const [q, component] of [['unique label','label'], ['secret alias','alias'],
    ['unusual description','description'], ['lib/unique.ts','path']]) {
    const h = s.score(q).targets.locate_target;
    assert.equal(h.choice, 'a'); assert.ok(h.top3[0].components[component] > 0);
  }
});
test('deterministic results; output distributions include exactly the observed IDs', () => {
  for (const q of ['login', 'quantum pizza', 'from editor to db']) {
    const a = scorer.score(q); assert.deepEqual(a, scorer.score(q));
    assert.deepEqual(Object.keys(a.operation.probabilities), OPERATIONS);
    for (const h of Object.values(a.targets)) assert.deepEqual(Object.keys(h.probabilities), ids);
  }
});
for (const [name, mutate] of [
  ['unknown choice', h => {h.choice='invented';}],
  ['extra ID', h => {h.probabilities.invented=0;}],
  ['missing ID', h => {delete h.probabilities[ids[1]];}],
  ['NaN', h => {h.probabilities[ids[0]]=NaN;}],
  ['Infinity', h => {h.probabilities[ids[0]]=Infinity;}],
  ['negative', h => {h.probabilities[ids[0]]=-0.1;}],
  ['above one', h => {h.probabilities[ids[0]]=1.1;}],
  ['sum', h => {h.probabilities[ids[0]]+=0.1;}],
  ['non argmax', h => {h.choice=ids[0];h.confidence=h.probabilities[ids[0]];}],
  ['fake confidence', h => {h.confidence=0.123;}],
]) test(`contract rejects ${name}`, () => {
  const h = structuredClone(scorer.score('login').targets.locate_target);
  mutate(h); assert.throws(() => validateHead(h, ids));
});
test('full result validator rejects incompatible heads, false acceptance and unknown alternatives', () => {
  const r = scorer.score('login');
  for (const mutate of [
    x => {x.targets.to_target=x.targets.locate_target;},
    x => {x.yes=false;},
    x => {x.targets.locate_target.yes=false;},
    x => {x.targets.locate_target.top3[1].id='unknown';},
    x => {x.targets.locate_target.top3[0].components.label=NaN;},
  ]) {const bad=structuredClone(r);mutate(bad);assert.throws(()=>validateResult(bad,map));}
});
test('maps reject unknown endpoints, duplicate IDs, empty table and malformed queries', () => {
  assert.throws(() => createScorer({nodes:[]}));
  assert.throws(() => createScorer({nodes:[{id:'a'},{id:'a'}]}));
  assert.throws(() => createScorer({nodes:[{id:'a'}],edges:[{from:'a',to:'b'}]}));
  assert.throws(() => scorer.score(null));
});
test('browser global has Node-identical results without require, window or network', () => {
  const sandbox={};vm.createContext(sandbox);
  vm.runInContext(fs.readFileSync(require.resolve('../web/scorer.js'),'utf8'), sandbox);
  const browser = sandbox.DagGpsScorer.createScorer(map);
  for (const q of ['login','from editor to db','what depends on runner service','unknown foo'])
    assert.equal(JSON.stringify(browser.score(q)), JSON.stringify(scorer.score(q)));
});
test('built map persists layer aliases exactly, with original candidate IDs', () => {
  const spec = require('../maps/quest-coder/layers.json');
  for (const layer of spec.layers) assert.deepEqual(map.nodes.find(n=>n.id===layer.id).aliases,layer.aliases);
  assert.equal(ids.length,290);
});
