const test = require('node:test');
const assert = require('node:assert/strict');
const {createRouter} = require('../web/router.js');
const map = require('../maps/quest-coder/map.json');
function fixture(edges) { return {nodes: ['a','b','c','d','e'].map(id => ({id,kind:'layer'})),edges}; }
const edge = (from,to,type='import') => ({from,to,type});
test('BFS shortest route with lexical tie-breaking independent of edge order', () => {
  const es = [edge('a','c'),edge('c','d'),edge('a','b'),edge('b','d'),edge('b','e'),edge('e','d')];
  for (const edges of [es,es.slice().reverse()]) assert.deepEqual(createRouter(fixture(edges)).shortestPath('a','d'),['a','b','d']);
  assert.deepEqual(createRouter(fixture(es)).route('UPSTREAM','a'),createRouter(fixture(es.slice().reverse())).route('UPSTREAM','a'));
  const m = fixture(es), before = JSON.stringify(m);
  createRouter(m).route('PATH','a','d'); assert.equal(JSON.stringify(m),before);
});
test('cycles terminate and traversal excludes source', () => {
  const r = createRouter(fixture([edge('a','b'),edge('b','c'),edge('c','a')]));
  assert.deepEqual(r.reachable('a',false),['b','c']);
  assert.deepEqual(r.reachable('a',true),['c','b']);
  assert.deepEqual(r.shortestPath('a','c'),['a','b','c']);
});
test('unreachable, self path, unknown IDs and ignored realtime', () => {
  const r = createRouter(fixture([edge('a','b','realtime')]));
  assert.equal(r.shortestPath('a','b'),null);
  assert.deepEqual(r.shortestPath('a','a'),['a']);
  assert.deepEqual(r.reachable('a',false),[]);
  assert.throws(()=>r.shortestPath('unknown','a'));
  assert.throws(()=>r.shortestPath('a','unknown'));
  assert.throws(()=>r.route('NOT_SURE','a'));
  assert.throws(()=>createRouter(fixture([edge('a','unknown')])));
});
test('LOCATE highlights only target; dependencies forward; dependents reverse', () => {
  const r = createRouter(fixture([edge('a','b'),edge('b','c'),edge('d','a'),edge('a','e','realtime')]));
  assert.deepEqual(r.route('LOCATE','a').ids,['a']); assert.deepEqual(r.route('LOCATE','a').edges,[]);
  assert.deepEqual(r.route('UPSTREAM','a').ids,['a','b','c']);
  assert.deepEqual(r.route('DOWNSTREAM','a').ids,['a','d']);
  assert.deepEqual(r.route('UPSTREAM','a').edges,[edge('a','b'),edge('b','c')]);
});
test('no route never fabricates edges and mixed endpoints unsupported', () => {
  const r = createRouter(map);
  const result = r.route('PATH','persistence','solve-ui');
  assert.equal(result.path,null);assert.deepEqual(result.edges,[]);
  assert.match(result.status,/No directed route found/);
  const mixed = r.route('PATH','api','app/api/health/route.ts');
  assert.equal(mixed.path,null);assert.deepEqual(mixed.edges,[]);assert.match(mixed.status,/mixed layer\/file/);
});
test('file routes keep real cross-layer file IDs and original typed edges', () => {
  const r = createRouter(map), e = map.file_edges.find(e=>e.cross_layer);
  const result = r.route('PATH',e.from,e.to);
  assert.deepEqual(result.path,[e.from,e.to]);assert.equal(result.kind,'file');
  assert.ok(result.edges.length);assert.ok(result.edges.every(x=>map.file_edges.includes(x)));
});
