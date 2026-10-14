'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {createQueryService} = require('../web/query-service.js');
function fixture(ext) {
  const paths = ['src/cache.' + ext, 'src/db.' + ext, 'src/client.' + ext];
  return {schema: 'dag-gps-workspace/v1', projectId: 'review', snapshotId: 'review',
    mapSha256: 'a', scorerSha256: 'b', source: {manifestSha256: 'c'},
    inventory: paths.map(path => ({path, sha256: 'd'})), map: {
      nodes: [{id: 'cache', label: 'cache', kind: 'layer'}, ...paths.map(path => ({id: path, path, label: path, kind: 'file'}))],
      edges: [], file_edges: [{from: paths[2], to: paths[1], type: 'import'}, {from: paths[1], to: paths[0], type: 'import'}],
      symbol_graph: {nodes: [], edges: [], unresolved: []}}};
}
for (const ext of ['py', 'ts']) {
  const ask = (s, query) => createQueryService(s).query({requestId: 'review', query});
  test(ext + ': file stems dispatch to dependents, including hints and controls', () => {
    const s = fixture(ext);
    for (const query of ['who invokes db', 'where is db called from', 'who invokes db file', 'who invokes src/db.' + ext, 'what uses db']) {
      const p = ask(s, query);
      assert.equal(p.status, 'matched', query); assert.equal(p.operation, 'DOWNSTREAM', query);
      assert.equal(p.seedNodeId, 'src/db.' + ext);
      assert.equal(p.witnesses.length, 1);
    }
    s.map.nodes.push({id: 'other/db.' + ext, path: 'other/db.' + ext, kind: 'file'});
    const p = ask(s, 'who invokes db');
    assert.equal(p.status, 'needs-choice'); assert.equal(p.alternatives.length, 2);
  });
  test(ext + ': every file hint wins collisions and retains single-kind fallback', () => {
    for (const hint of ['file', 'module', 'script']) {
      const s = fixture(ext);
      assert.deepEqual(ask(s, 'where is cache ' + hint).selectedNodeIds, ['src/cache.' + ext], hint);
      s.map.nodes = s.map.nodes.filter(n => n.kind === 'layer'); s.map.file_edges = [];
      assert.deepEqual(ask(s, 'where is cache ' + hint).selectedNodeIds, ['cache']);
      assert.notEqual(ask(s, 'where is missing/cache.' + ext + ' ' + hint).status, 'matched');
      const fileOnly = fixture(ext); fileOnly.map.nodes = fileOnly.map.nodes.filter(n => n.kind === 'file');
      assert.deepEqual(ask(fileOnly, 'where is cache ' + hint).selectedNodeIds, ['src/cache.' + ext]);
    }
    assert.deepEqual(ask(fixture(ext), 'where is cache folder').selectedNodeIds, ['cache']);
  });
  test(ext + ': synonym provenance survives traversal and both route endpoints', () => {
    for (const query of ['what uses database', 'what does database depend on', 'from database to cache file', 'from client to database', 'from cache file to database']) {
      const p = ask(fixture(ext), query);
      assert.match(p.reason, /matched via synonym database→db/, query);
    }
  });
}
test('genuine symbol callers retain dispatch and explicit missing symbols do not become files', () => {
  const s = fixture('py');
  s.map.symbol_graph.nodes.push({id: 'src/db.py#db@1', kind: 'symbol', name: 'db', qualname: 'db', path: 'src/db.py', start: 1, end: 2});
  const ask = query => createQueryService(s).query({requestId: 'r', query});
  assert.equal(ask('who invokes function db').operation, 'CALLERS');
  for (const hint of ['file', 'module', 'script']) {
    const p = ask('who invokes db ' + hint);
    assert.equal(p.operation, 'DOWNSTREAM', hint);
    assert.equal(p.seedNodeId, 'src/db.py', hint);
  }
  assert.equal(ask('who invokes missing_function').status, 'no-match');
  assert.equal(ask('who invokes function client').status, 'no-match');
});
