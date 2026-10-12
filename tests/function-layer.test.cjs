'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const Q = require('../web/query-service.js');
const G = require('../web/graph-view.js');
function snapshot() {
  const symbols = ['one', 'two', 'two'].map((name, i) => ({id: 's' + i, kind: 'symbol', name, qualname: name,
    path: i === 2 ? 'b.py' : 'a.py', start: i + 1, end: i + 1, label: name}));
  return {schema: 'dag-gps-workspace/v1', projectId: 'p', snapshotId: 's', mapSha256: 'a', scorerSha256: 'b',
    source: {manifestSha256: 'c'}, inventory: ['a.py', 'b.py'].map(path => ({path, sha256: 'd'})),
    map: {nodes: [{id: 'g', kind: 'layer', label: 'g'}, ...['a.py', 'b.py'].map(path => ({id: path, path, kind: 'file', layer: 'g'}))],
      edges: [], file_edges: [], symbol_graph: {schema: 'dag-gps-symbols/v1', nodes: symbols,
        edges: [{from: 's0', to: 's1', type: 'call', confidence: 'resolved', sites: [{path: 'a.py', start: 1, end: 1}]}],
        unresolved: [{from: 's0', to: null, confidence: 'unresolved', path: 'a.py', start: 1, end: 1}]}}};
}
test('symbol operation and target heads abstain on duplicates; choice keeps operation', () => {
  const s = Q.createQueryService(snapshot());
  const p = s.query({requestId: 'r', query: 'what calls two'});
  assert.equal(p.operation, 'CALLERS'); assert.equal(p.status, 'needs-choice');
  assert.deepEqual(p.selectedNodeIds, []); assert.equal(p.alternatives.length, 2);
  const chosen = s.query({requestId: 'r', query: 'what calls two', chosenNodeId: 's1'});
  assert.equal(chosen.operation, 'CALLERS'); assert.deepEqual(chosen.selectedNodeIds, ['s1', 's0']);
  assert.throws(() => s.query({requestId: 'r', query: 'what calls two', chosenNodeId: 's0'}));
});
test('flow witness cites observed sites, no-path has no edges, unresolved stays data', () => {
  const s = Q.createQueryService(snapshot());
  const p = s.query({requestId: 'r', query: 'how does one reach s1'});
  assert.equal(p.status, 'matched'); assert.equal(p.witnesses[0].edges[0].sites[0].start, 1);
  assert.equal(p.unresolvedCallCount, 1);
  const no = s.query({requestId: 'r', query: 'how does s1 reach one'});
  assert.equal(no.status, 'no-path'); assert.deepEqual(no.selectedEdges, []);
});
test('symbol drill-down expands only selected files and preserves legacy layout', () => {
  const map = snapshot().map;
  const l = G.layoutMap(map, {expandedGroups: new Set(['g']), expandedFiles: new Set(['a.py'])});
  assert.ok(l.nodes.some(n => n.id === 's0')); assert.ok(!l.nodes.some(n => n.id === 's2'));
  assert.equal(l.edges.length, 1);
  assert.equal(G.layoutMap(map).mode, 'groups');
  const focused = G.layoutMap(map, {focusedSymbols: new Set(['s0', 's1'])});
  assert.deepEqual(focused.nodes.map(n => n.id), ['s0', 's1']);
  assert.deepEqual(focused.lanes.map(n => n.id), ['a.py']);
  delete map.symbol_graph;
  assert.equal(G.layoutMap(map).mode, 'files');
});

test('recursive calls remain edges without fake acyclic witnesses', () => {
  const s = snapshot();
  s.map.symbol_graph.edges.push({...s.map.symbol_graph.edges[0], to: 's0'});
  const p = Q.querySnapshot(s, {requestId: 'r', query: 'what calls one'});
  assert.equal(p.selectedEdges.length, 1);
  assert.equal(p.selectedEdges[0].to, 's0');
  assert.deepEqual(p.witnesses, []);
});

test('both ambiguous flow endpoints can be chosen without losing the first choice', () => {
  const service = Q.createQueryService(snapshot());
  const first = service.query({requestId: 'r', query: 'how does two reach two'});
  const second = service.query({requestId: 'r', query: first.alternatives[0].query});
  assert.equal(second.status, 'needs-choice');
  const final = service.query({requestId: 'r', query: second.alternatives[1].query});
  assert.equal(final.status, 'no-path');
  assert.deepEqual(final.selectedNodeIds, ['s1', 's2']);
});
