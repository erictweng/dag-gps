'use strict';
// M2.3 graph view pure logic: deterministic layout and honest highlight rules.
const test = require('node:test');
const assert = require('node:assert/strict');
const {layoutMap, highlightFor, edgeKey, LIMITS} = require('../web/graph-view.js');

function map(files, edges, groupOf = p => (p.includes('/') ? p.split('/')[0] : '(root)')) {
  const groups = [...new Set(files.map(groupOf))];
  return {
    nodes: [...groups.map(g => ({id: 'g-' + g, kind: 'layer', label: g})),
      ...files.map(p => ({id: p, kind: 'file', path: p, label: p.split('/').at(-1), layer: 'g-' + groupOf(p)}))],
    edges: [], file_edges: edges.map(([from, to, type]) => ({from, to, type: type || 'import'})),
  };
}
const FILES = ['app/main.py', 'lib/core.py', 'lib/a.py', 'lib/b.py', 'tools/cli.py', 'lib/leaf.py'];
const EDGES = [['app/main.py', 'lib/core.py'], ['tools/cli.py', 'lib/core.py'], ['lib/core.py', 'lib/a.py'],
  ['lib/a.py', 'lib/b.py'], ['lib/b.py', 'lib/a.py'], ['lib/b.py', 'lib/leaf.py']];

test('consumers sit left of their dependencies; cycle members share a column', () => {
  const L = layoutMap(map(FILES, EDGES));
  const at = Object.fromEntries(L.nodes.map(n => [n.id, n]));
  assert.ok(at['app/main.py'].column < at['lib/core.py'].column);
  assert.ok(at['lib/core.py'].column < at['lib/a.py'].column);
  assert.equal(at['lib/a.py'].column, at['lib/b.py'].column, 'strongly connected files share a column');
  assert.ok(at['lib/b.py'].column < at['lib/leaf.py'].column);
});

test('every file and every non-realtime edge is drawn exactly once, including both cycle edges', () => {
  const L = layoutMap(map(FILES, [...EDGES, ['app/main.py', 'tools/cli.py', 'realtime']]));
  assert.equal(L.mode, 'files');
  assert.deepEqual(L.nodes.map(n => n.id).sort(), [...FILES].sort());
  const keys = L.edges.map(e => edgeKey(e)).sort();
  assert.deepEqual(keys, EDGES.map(([f, t]) => edgeKey({from: f, to: t, type: 'import'})).sort());
  assert.ok(L.edges.find(e => e.from === 'lib/b.py' && e.to === 'lib/a.py').back, 'cycle edge is routed as a back edge');
});

test('groups are labeled horizontal lanes and nodes never overlap', () => {
  const L = layoutMap(map(FILES, EDGES));
  assert.deepEqual(L.lanes.map(l => l.label), ['(root)', 'app', 'lib', 'tools'].filter(g => L.lanes.some(l => l.label === g)));
  for (const n of L.nodes) {
    const lane = L.lanes.find(l => l.id === n.layer);
    assert.ok(n.y >= lane.y && n.y + n.h <= lane.y + lane.h, n.id + ' inside its lane');
  }
  const boxes = L.nodes.map(n => [n.x, n.y, n.x + n.w, n.y + n.h]);
  for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
    const [a, b] = [boxes[i], boxes[j]];
    assert.ok(a[2] <= b[0] || b[2] <= a[0] || a[3] <= b[1] || b[3] <= a[1], 'overlap ' + i + ',' + j);
  }
  assert.ok(L.width > 0 && L.height > 0);
});

test('layout is deterministic regardless of input order', () => {
  const a = layoutMap(map(FILES, EDGES));
  const shuffled = map([...FILES].reverse(), [...EDGES].reverse());
  shuffled.nodes.reverse();
  assert.deepEqual(layoutMap(shuffled), a);
});

test('very large maps fall back to a group overview instead of an unreadable file graph', () => {
  const files = Array.from({length: LIMITS.maxFileNodes + 1}, (_, i) => 'pkg' + (i % 7) + '/f' + i + '.py');
  const m = map(files, []);
  m.edges = [{from: 'g-pkg0', to: 'g-pkg1', type: 'import', weight: 3}];
  const L = layoutMap(m);
  assert.equal(L.mode, 'groups');
  assert.equal(L.nodes.length, 7);
  assert.equal(L.edges.length, 1);
  assert.ok(L.notice.includes(String(files.length)));
});

const packet = extra => Object.assign({status: 'matched', operation: 'DOWNSTREAM', highlightState: 'potential-impact',
  seedNodeId: 'lib/core.py', selectedNodeIds: ['lib/core.py', 'app/main.py'],
  selectedEdges: [{from: 'app/main.py', to: 'lib/core.py', type: 'import'}], alternatives: []}, extra);

test('a confident match highlights its exact nodes/edges and dims the rest', () => {
  const h = highlightFor(packet());
  assert.equal(h.mode, 'highlight');
  assert.equal(h.dim, true);
  assert.equal(h.seed, 'lib/core.py');
  assert.deepEqual([...h.nodes].sort(), ['app/main.py', 'lib/core.py']);
  assert.deepEqual([...h.edges], [edgeKey({from: 'app/main.py', to: 'lib/core.py', type: 'import'})]);
  assert.equal(h.kind, 'potential-impact');
});

test('ambiguous, unmatched, unsupported and stale answers never dim the graph around a guess', () => {
  for (const status of ['needs-choice', 'no-match', 'unsupported', 'stale']) {
    const h = highlightFor(packet({status, selectedNodeIds: [], selectedEdges: [], seedNodeId: undefined,
      alternatives: [{nodeId: 'lib/core.py'}]}));
    assert.equal(h.mode, 'none', status);
    assert.equal(h.dim, false, status);
    assert.equal(h.nodes.size, 0, status);
  }
});

test('no-path marks only the two endpoints without dimming or claiming a route', () => {
  const h = highlightFor({status: 'no-path', operation: 'PATH', highlightState: 'relevant',
    selectedNodeIds: ['a.py', 'b.py'], selectedEdges: [], alternatives: []});
  assert.equal(h.mode, 'mark');
  assert.equal(h.dim, false);
  assert.equal(h.edges.size, 0);
  assert.deepEqual([...h.nodes].sort(), ['a.py', 'b.py']);
});

test('null packet clears', () => {
  assert.deepEqual(highlightFor(null), {mode: 'none', dim: false, nodes: new Set(), edges: new Set(), seed: null, kind: null});
});
