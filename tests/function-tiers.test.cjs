'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const Q = require('../web/query-service.js'), G = require('../web/graph-view.js');
function fixture() {
  const tiers = ['resolved', 'instance-local', 'typed', 'through-decorator'];
  const names = ['a', 'b', 'c', 'd', 'e'];
  const nodes = names.map((name, i) => ({id: name, name, qualname: name, kind: 'symbol', path: 'a.py', start: i + 1, end: i + 1}));
  nodes[4].entryPoint = ['app.task'];
  const edges = tiers.map((confidence, i) => ({from: names[i], to: names[i + 1], type: 'call', confidence,
    ...(confidence === 'through-decorator' ? {decorators: ['app.task']} : {}),
    sites: [{path: 'a.py', start: i + 1, end: i + 1, expression: names[i + 1],
      ...(confidence !== 'resolved' ? {confidence} : {})}]}));
  return {schema: 'dag-gps-workspace/v1', projectId: 'p', snapshotId: 's', mapSha256: 'm', scorerSha256: 's',
    source: {manifestSha256: 'h'}, inventory: [{path: 'a.py', sha256: 'h'}],
    map: {nodes: [{id: 'group', kind: 'layer'}, {id: 'a.py', kind: 'file', path: 'a.py', layer: 'group'}], edges: [], file_edges: [],
      symbol_graph: {nodes, edges, unresolved: [], certainAdditions: [[0, 1, 0], [0, 2, 0], [0, 3, 0]]}}};
}
test('all call tiers traverse by default and each witness exposes its weakest link', () => {
  const p = Q.querySnapshot(fixture(), {requestId: 'r', query: 'trace from function a'});
  assert.deepEqual(p.selectedNodeIds, ['a', 'b', 'c', 'd', 'e']);
  assert.deepEqual(p.witnesses.map(w => w.confidence), ['resolved', 'instance-local', 'typed', 'through-decorator']);
  assert.deepEqual(p.entryPoints, [{nodeId: 'e', decorators: ['app.task']}]);
});
test('certain-only excludes weaker edges and reconstructs original unknown sites', () => {
  const p = Q.querySnapshot(fixture(), {requestId: 'r', query: 'trace from function a', certainOnly: true});
  assert.deepEqual(p.selectedNodeIds, ['a', 'b']);
  assert.equal(p.unresolvedCallCount, 1);
  assert.equal(p.unresolvedCalls[0].expression, 'c');
  assert.equal(p.unresolvedCalls[0].confidence, 'unresolved');
  assert.throws(() => Q.querySnapshot(fixture(), {requestId: 'r', query: 'trace from a', certainOnly: 'yes'}));
});
test('CALLERS traverses decorated targets without synthesizing registration callers', () => {
  const p = Q.querySnapshot(fixture(), {requestId: 'r', query: 'what calls e'});
  assert.deepEqual(p.selectedNodeIds, ['e', 'd']);
  assert.equal(p.witnesses[0].confidence, 'through-decorator');
  assert.deepEqual(p.selectedEdges[0].decorators, ['app.task']);
});
test('focused drawing retains tier metadata and uses exactly packet call edges', () => {
  const s = fixture(), p = Q.querySnapshot(s, {requestId: 'r', query: 'trace from function a'});
  const layout = G.layoutMap(s.map, {focusedSymbols: new Set(p.selectedNodeIds), focusedEdges: p.selectedEdges});
  assert.deepEqual(layout.edges.map(e => e.confidence), ['resolved', 'instance-local', 'typed', 'through-decorator']);
  const certain = Q.querySnapshot(s, {requestId: 'r', query: 'trace from function a', certainOnly: true});
  const filtered = G.layoutMap(s.map, {focusedSymbols: new Set(p.selectedNodeIds), focusedEdges: certain.selectedEdges});
  assert.equal(filtered.edges.length, 1);
});
