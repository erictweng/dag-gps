'use strict';
const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs');
const {createQueryService} = require('../web/query-service.js');

// Small committed mechanics fixture: real-repo checks below use unchanged pinned snapshots.
function fixture() {
  const files = ['lib/backfill.py', 'lib/other.py', 'app/main.py'];
  const symbol = (name, path) => ({id: path + ':' + name, kind: 'symbol', symbolKind: 'class', name,
    qualname: name, path, start: 1, end: 2});
  const symbols = [symbol('Backfill', files[0]), symbol('Other', files[1]), symbol('Main', files[2])];
  return {schema: 'dag-gps-workspace/v1', projectId: 'fixture', snapshotId: 'fixture', state: 'dependency-preview',
    mapSha256: 'a'.repeat(64), scorerSha256: 'b'.repeat(64), source: {manifestSha256: 'c'.repeat(64)},
    inventory: files.map(path => ({path, sha256: 'd'.repeat(64)})),
    map: {nodes: [{id: 'folder-backfill', kind: 'layer', label: 'app/backfill'},
      ...files.map(path => ({id: path, path, label: path.split('/').at(-1), kind: 'file'}))], edges: [],
      file_edges: [{from: files[2], to: files[0], type: 'import'}, {from: files[0], to: files[1], type: 'import'}],
      symbol_graph: {nodes: symbols, unresolved: [], edges: [
        {from: symbols[2].id, to: symbols[0].id, type: 'call', confidence: 'resolved', sites: []},
        {from: symbols[0].id, to: symbols[1].id, type: 'call', confidence: 'resolved', sites: []}]}}};
}
const patterns = [
  ['LOCATE', 'where is {x}'], ['DOWNSTREAM', 'what uses {x}'], ['UPSTREAM', 'what does {x} use'],
  ['DOWNSTREAM', 'dependents of {x}'], ['UPSTREAM', 'dependencies of {x}'],
  ['DOWNSTREAM', 'downstream of {x}'], ['UPSTREAM', 'upstream of {x}'],
  ['CALLERS', 'who invokes {x}'], ['CALLERS', 'callers of {x}'],
  ['CALLEES', 'what does {x} call'], ['CALLEES', 'callees of {x}'], ['TRACE', 'trace from {x}'],
  ['PATH', 'path from {x} to {y}'], ['PATH', 'path from {y} to {x}'],
  ['FLOW', 'how does {x} reach {y}'], ['FLOW', 'how does {y} reach {x}']
];
function checkSuite(label, snapshot, name, ids, other) {
  const service = createQueryService(snapshot), ask = (query, extra = {}) => service.query({requestId: 'collision', query, ...extra});
  for (const [op, pattern] of patterns) test(label + ': ' + pattern, () => {
    const query = pattern.replace('{x}', name).replace('{y}', other);
    const p = ask(query);
    assert.equal(p.status, 'needs-choice', query);
    assert.equal(p.operation, op);
    assert.deepEqual(p.selectedNodeIds, []);
    for (const id of ids) {
      const alt = p.alternatives.find(a => a.nodeId === id);
      assert.ok(alt, query + ': missing ' + id);
      const chosen = ask(query, {chosenNodeId: id}), linked = ask(alt.query);
      assert.notEqual(chosen.status, 'needs-choice', alt.query);
      assert.equal(chosen.status, linked.status, alt.query);
      assert.equal(chosen.operation, linked.operation, alt.query);
      assert.deepEqual(chosen.selectedNodeIds, linked.selectedNodeIds, alt.query);
      const ui = ask(alt.query, {chosenNodeId: id});
      assert.equal(ui.status, linked.status, 'UI choice: ' + alt.query);
      assert.equal(ui.operation, linked.operation, 'UI choice: ' + alt.query);
      assert.deepEqual(ui.selectedNodeIds, linked.selectedNodeIds, 'UI choice: ' + alt.query);
      if (op !== 'LOCATE') assert.notEqual(chosen.operation, 'LOCATE', query);
      if (chosen.status === 'matched' && !['LOCATE', 'PATH', 'FLOW'].includes(op))
        assert.equal(chosen.seedNodeId, id, query);
    }
    assert.throws(() => ask(query, {chosenNodeId: 'not-a-candidate'}), /alternative/);
  });
}
const small = fixture();
checkSuite('committed fixture', small, 'backfill', ['lib/backfill.py', 'lib/backfill.py:Backfill', 'folder-backfill'], 'lib/other.py');
test('explicit kind, path and qualified symbol retain traversal edges', () => {
  const q = createQueryService(small), ask = query => q.query({requestId: 'explicit', query});
  for (const [query, seed, endpoint] of [
    ['what uses file backfill', 'lib/backfill.py', 'app/main.py'],
    ['what does lib/backfill.py use', 'lib/backfill.py', 'lib/other.py'],
    ['who invokes class backfill', 'lib/backfill.py:Backfill', 'app/main.py:Main'],
    ['what does lib/backfill.py:Backfill call', 'lib/backfill.py:Backfill', 'lib/other.py:Other'],
    ['upstream of class backfill', 'lib/backfill.py:Backfill', 'lib/other.py:Other'],
    ['downstream of class backfill', 'lib/backfill.py:Backfill', 'app/main.py:Main']]) {
    const p = ask(query); assert.equal(p.status, 'matched', query);
    assert.equal(p.seedNodeId, seed, query); assert.ok(p.selectedNodeIds.includes(endpoint), query);
    assert.ok(p.selectedEdges.length, query);
  }
});
test('PATH choices resolve endpoints separately, with endpoint-local kinds', () => {
  const q = createQueryService(small), ask = (query, extra = {}) => q.query({requestId: 'path', query, ...extra});
  const first = ask('path from backfill to backfill');
  const second = ask(first.alternatives.find(a => a.nodeId === 'lib/backfill.py').query);
  assert.equal(second.status, 'needs-choice');
  assert.equal(ask(first.alternatives.find(a => a.nodeId === 'lib/backfill.py').query,
    {chosenNodeId: 'lib/backfill.py'}).status, 'needs-choice');
  const final = ask(second.alternatives.find(a => a.nodeId === 'lib/backfill.py').query);
  assert.equal(final.status, 'matched'); assert.equal(final.operation, 'PATH');
  assert.deepEqual(final.selectedNodeIds, ['lib/backfill.py']);
  assert.equal(ask('path from file backfill to backfill').status, 'needs-choice');
});
test('collision choices paginate deterministically and preserve the operation', () => {
  const s = fixture();
  for (let i = 0; i < 22; i++) s.map.nodes.push({id: 'extra-' + i, kind: 'layer', label: 'extra-' + i + '/backfill'});
  const q = createQueryService(s), request = {requestId: 'pages', query: 'what uses backfill'};
  const first = q.query(request), second = q.query({...request, continuation: first.continuation});
  assert.equal(first.alternatives.length, 20); assert.equal(second.alternatives.length, 5);
  assert.equal(new Set([...first.alternatives, ...second.alternatives].map(a => a.nodeId)).size, 25);
  assert.equal(second.operation, 'DOWNSTREAM'); assert.equal(second.truncated, false);
  assert.throws(() => q.query({...request, continuation: 'offset:25'}), /past/);
  const chosen = q.query({...request, continuation: first.continuation, chosenNodeId: 'lib/backfill.py'});
  assert.equal(chosen.seedNodeId, 'lib/backfill.py'); assert.equal(chosen.operation, 'DOWNSTREAM');
});
test('PATH does not promote a fuzzy endpoint when resolving the other endpoint', () => {
  const q = createQueryService(small), query = 'path from backfill to lib/otherr.py';
  const first = q.query({requestId: 'fuzzy', query});
  assert.equal(first.status, 'needs-choice');
  const alt = first.alternatives.find(a => a.nodeId === 'lib/backfill.py');
  assert.ok(alt.query.includes('lib/otherr.py'));
  const next = q.query({requestId: 'fuzzy-choice', query, chosenNodeId: 'lib/backfill.py'});
  assert.equal(next.status, 'needs-choice'); assert.deepEqual(next.selectedNodeIds, []);
});
test('explicit symbol PATH retains witnesses, reverse traversal and certain-only filtering', () => {
  const s = fixture();
  s.map.symbol_graph.edges[1].confidence = 'typed';
  s.map.symbol_graph.edges[1].sites = [{confidence: 'typed'}];
  s.map.symbol_graph.edges[0].sites = [{}];
  const q = createQueryService(s), ask = (query, extra = {}) => q.query({requestId: 'symbol', query, ...extra});
  const p = ask('path from class backfill to class other');
  assert.equal(p.status, 'matched'); assert.equal(p.operation, 'PATH');
  assert.deepEqual(p.witnesses[0].nodeIds, ['lib/backfill.py:Backfill', 'lib/other.py:Other']);
  assert.equal(ask('path from class backfill to class other', {certainOnly: true}).status, 'no-path');
  assert.deepEqual(ask('downstream of class other').selectedNodeIds,
    ['lib/other.py:Other', 'lib/backfill.py:Backfill', 'app/main.py:Main']);
});
for (const repo of ['honcho', 'salesroom']) {
  const path = 'artifacts/question-parser/' + repo + '/snapshot.json';
  if (!fs.existsSync(path)) { test(repo + ': pinned collision checks', {skip: 'Optional pinned snapshot absent: ' + path}, () => {}); continue; }
  const s = JSON.parse(fs.readFileSync(path));
  const name = repo === 'honcho' ? 'backfill' : 'events';
  const ids = repo === 'honcho' ? ['src/reconciler/backfill.py', s.map.symbol_graph.nodes.find(n => n.name === 'Backfill').id] :
    ['src/lib/events.ts', s.map.nodes.find(n => n.kind === 'layer' && n.label === 'app/api/events').id];
  checkSuite(repo, s, name, ids, ids[0]);
}
