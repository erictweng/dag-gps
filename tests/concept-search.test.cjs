'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const Q = require('../web/query-service.js');
function fixture() {
  const nodes = Array.from({length: 40}, (_, i) => ({id: 'src/file' + i + '.py', path: 'src/file' + i + '.py', kind: 'file', label: 'file' + i}));
  const text = Object.fromEntries(nodes.map((n, i) => [n.id, {name: n.label, path: n.path,
    docstring: i === 0 ? 'Persists zebra records in durable storage.' : 'Other unrelated task ' + i}]));
  return {schema: 'dag-gps-workspace/v1', projectId: 'p', snapshotId: 's', mapSha256: 'a', scorerSha256: 'b',
    source: {manifestSha256: 'c'}, inventory: [], map: {nodes, edges: [], file_edges: [],
      search_text: {schema: 'dag-gps-search-text/v1', nodes: text, omitted: 0}}};
}
test('BM25 always asks even for one strong candidate and shows matched fields', () => {
  const service = Q.createQueryService(fixture());
  const p = service.query({requestId: 'r', query: 'where is zebra storage'});
  assert.equal(p.status, 'needs-choice'); assert.deepEqual(p.selectedNodeIds, []);
  assert.equal(p.alternatives[0].nodeId, 'src/file0.py');
  assert.match(p.alternatives[0].reason, /zebra \[docstring\]/);
  assert.ok(p.alternatives.length <= 8);
  assert.deepEqual(service.query({requestId: 'r', query: 'where is zebra storage'}), p);
  assert.equal(service.query({requestId: 'r', query: 'where is zebra storage', chosenNodeId: p.alternatives[0].nodeId}).status, 'matched');
});
test('BM25 respects literal priority, missing filenames, unknown terms and legacy snapshots', () => {
  const s = fixture(), service = Q.createQueryService(s);
  assert.equal(service.query({requestId: 'r', query: 'src/file1.py'}).status, 'matched');
  assert.equal(service.query({requestId: 'r', query: 'zebra_missing.py'}).status, 'no-match');
  assert.equal(service.query({requestId: 'r', query: 'zebra unicorn'}).status, 'no-match');
  delete s.map.search_text;
  const legacy = Q.createQueryService(s);
  assert.equal(legacy.conceptStats.available, false);
  assert.equal(legacy.query({requestId: 'r', query: 'where is zebra storage'}).status, 'no-match');
});
test('BM25 floor rejects common corpus words and names/paths work without docstrings', () => {
  const s = fixture(), service = Q.createQueryService(s);
  assert.equal(service.query({requestId: 'r', query: 'other unrelated task'}).status, 'no-match');
  s.map.nodes[0].label = 'ZebraStorage';
  delete s.map.search_text.nodes['src/file0.py'];
  assert.equal(Q.createQueryService(s).query({requestId: 'r', query: 'zebra storage'}).status, 'needs-choice');
});
