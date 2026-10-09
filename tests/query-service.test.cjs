'use strict';
// Shared query packet regressions on explicit synthetic snapshots (mechanics only,
// not real-user accuracy evidence).
const test = require('node:test');
const assert = require('node:assert/strict');
const {createQueryService, querySnapshot, LIMITS} = require('../web/query-service.js');

const HEX = c => c.repeat(64);
function snapshot(files, fileEdges, extra = {}) {
  const layers = [...new Set(files.map(p => (p.includes('/') ? p.split('/')[0] : '(root)')))];
  const layerId = name => 'folder-' + name.replace(/[^a-z]/g, '');
  const nodes = [
    ...layers.map(name => ({id: layerId(name), kind: 'layer', label: name, desc: 'Same parent folder.'})),
    ...files.map(p => ({id: p, kind: 'file', label: p.split('/').at(-1), path: p,
      layer: layerId(p.includes('/') ? p.split('/')[0] : '(root)')})),
  ];
  return {
    schema: 'dag-gps-workspace/v1', projectId: 'github:test/fixture', snapshotId: 'snap-a',
    mapSha256: HEX('a'), scorerSha256: HEX('b'), state: 'dependency-preview',
    source: {kind: 'git-commit', repo: 'test/fixture', commit: '1'.repeat(40), worktreeId: null, manifestSha256: HEX('c')},
    grouping: {status: 'proposed', reviewed: false},
    inventory: files.map(p => ({path: p, sha256: HEX('d'), lineCount: 3})),
    map: {meta: {repo: 'test/fixture', snapshot_commit: '1'.repeat(40)}, nodes, edges: [],
      file_edges: fileEdges.map(([from, to]) => ({from, to, type: 'import'})),
      layers: Object.fromEntries(layers.map(n => [layerId(n), {files: files.filter(p => layerId(p.includes('/') ? p.split('/')[0] : '(root)') === layerId(n))}]))},
    limitations: [],
    ...extra,
  };
}
const FILES = ['app/main.py', 'app/util.py', 'lib/util.py', 'lib/core.py', 'lib/a.py', 'lib/b.py', 'tools/cli.py'];
const EDGES = [['app/main.py', 'app/util.py'], ['app/main.py', 'lib/core.py'], ['lib/core.py', 'lib/a.py'],
  ['lib/a.py', 'lib/b.py'], ['lib/b.py', 'lib/a.py'], ['tools/cli.py', 'lib/core.py']];
const snap = snapshot(FILES, EDGES);
const ask = (query, extra = {}) => querySnapshot(snap, {requestId: 'r1', query, ...extra});

test('literal full path selects exactly that file with revision-bound source ref', () => {
  const p = ask('lib/core.py');
  assert.equal(p.status, 'matched');
  assert.equal(p.operation, 'LOCATE');
  assert.deepEqual(p.selectedNodeIds, ['lib/core.py']);
  assert.equal(p.snapshotId, 'snap-a');
  assert.deepEqual(p.sourceRefs, [{path: 'lib/core.py', sha256: HEX('d'), snapshotId: 'snap-a',
    evidenceKind: 'observed-source', start: null, end: null}]);
  assert.equal(p.truncated, false);
  assert.equal(p.continuation, null);
});

test('duplicate basename needs an explicit choice and highlights nothing', () => {
  const p = ask('util.py');
  assert.equal(p.status, 'needs-choice');
  assert.deepEqual(p.selectedNodeIds, []);
  assert.deepEqual(p.selectedEdges, []);
  assert.deepEqual(p.alternatives.map(a => a.nodeId).sort(), ['app/util.py', 'lib/util.py']);
});

test('explicit choice resolves only known IDs', () => {
  const p = ask('util.py', {chosenNodeId: 'lib/util.py'});
  assert.equal(p.status, 'matched');
  assert.deepEqual(p.selectedNodeIds, ['lib/util.py']);
  assert.throws(() => ask('util.py', {chosenNodeId: 'nope.py'}), /Unknown chosen node/);
});

test('unknown query is no-match without guessed highlights', () => {
  const p = ask('zzqx_nothing_here.py');
  assert.ok(['no-match', 'needs-choice'].includes(p.status));
  assert.deepEqual(p.selectedNodeIds, []);
});

test('request against another snapshot is stale and empty', () => {
  const p = ask('lib/core.py', {snapshotId: 'snap-b'});
  assert.equal(p.status, 'stale');
  assert.deepEqual(p.selectedNodeIds, []);
});

test('dependents are potential impact with a directed witness ending at the seed for every consumer', () => {
  const p = ask('what depends on lib/core.py');
  assert.equal(p.status, 'matched');
  assert.equal(p.operation, 'DOWNSTREAM');
  assert.equal(p.highlightState, 'potential-impact');
  assert.equal(p.seedNodeId, 'lib/core.py');
  assert.deepEqual(new Set(p.selectedNodeIds), new Set(['lib/core.py', 'app/main.py', 'tools/cli.py']));
  for (const id of p.selectedNodeIds.filter(id => id !== 'lib/core.py')) {
    const w = p.witnesses.find(x => x.nodeIds[0] === id);
    assert.ok(w, 'witness for ' + id);
    assert.equal(w.nodeIds.at(-1), 'lib/core.py');
    w.edges.forEach((e, i) => assert.deepEqual([e.from, e.to], [w.nodeIds[i], w.nodeIds[i + 1]]));
  }
});

test('dependencies traverse a genuine cycle once and keep both cycle edges', () => {
  const p = ask('dependencies of lib/core.py');
  assert.equal(p.operation, 'UPSTREAM');
  assert.deepEqual(new Set(p.selectedNodeIds), new Set(['lib/core.py', 'lib/a.py', 'lib/b.py']));
  assert.equal(p.highlightState, 'relevant');
  const keys = p.selectedEdges.map(e => e.from + '>' + e.to);
  assert.ok(keys.includes('lib/core.py>lib/a.py') && keys.includes('lib/a.py>lib/b.py'));
});

test('path returns a contiguous directed witness; reverse direction is no-path', () => {
  const p = ask('path from app/main.py to lib/b.py');
  assert.equal(p.status, 'matched');
  assert.deepEqual(p.selectedNodeIds, ['app/main.py', 'lib/core.py', 'lib/a.py', 'lib/b.py']);
  assert.equal(p.witnesses.length, 1);
  assert.equal(p.witnesses[0].edges.length, 3);
  const back = ask('path from lib/b.py to app/main.py');
  assert.equal(back.status, 'no-path');
  assert.deepEqual(back.selectedEdges, []);
  assert.deepEqual(back.witnesses, []);
});

test('group-to-file path is unsupported with a disclosed limitation', () => {
  const p = ask('path from tools to lib/core.py');
  if (p.status === 'unsupported') assert.ok(p.limitations.some(l => /group and a file/.test(l)));
  else assert.ok(['needs-choice', 'no-match'].includes(p.status));
  assert.deepEqual(p.selectedEdges, []);
});

test('large dependents page through resumable continuations covering every consumer exactly', () => {
  const n = 450;
  const files = ['core/hub.py', ...Array.from({length: n}, (_, i) => 'pkg/user_' + i + '.py')];
  const big = snapshot(files, files.slice(1).map(f => [f, 'core/hub.py']));
  const service = createQueryService(big);
  const seen = new Set();
  let continuation, pages = 0;
  do {
    const p = service.query({requestId: 'page-' + pages, query: 'what depends on core/hub.py', continuation});
    assert.ok(p.selectedNodeIds.length <= LIMITS.selectedNodes);
    assert.ok(p.witnesses.length <= LIMITS.witnesses);
    assert.equal(p.truncated, p.continuation !== null);
    p.selectedNodeIds.filter(id => id !== 'core/hub.py').forEach(id => seen.add(id));
    continuation = p.continuation;
    pages++;
  } while (continuation && pages < 10);
  assert.equal(seen.size, n);
  assert.equal(pages, 3);
  assert.throws(() => service.query({requestId: 'x', query: 'what depends on core/hub.py', continuation: 'offset:99999'}), /past the end/);
  assert.throws(() => service.query({requestId: 'x', query: 'q', continuation: 'page=2'}), /Invalid continuation/);
});

test('packets are deterministic for the same snapshot and request', () => {
  assert.deepEqual(ask('what depends on lib/core.py'), ask('what depends on lib/core.py'));
});

test('rejects untrusted or malformed snapshots and requests', () => {
  assert.throws(() => querySnapshot({...snap, schema: 'x'}, {requestId: 'r', query: 'a'}), /dag-gps-workspace/);
  assert.throws(() => querySnapshot(snap, {query: 'a'}), /requestId/);
  assert.throws(() => querySnapshot(snap, {requestId: 'r', query: 'x'.repeat(LIMITS.queryChars + 1)}), /bounded/);
});
