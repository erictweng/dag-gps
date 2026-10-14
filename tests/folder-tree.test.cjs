const test = require('node:test');
const assert = require('node:assert/strict');
const {createRouter} = require('../web/router.js');
const {createQueryService} = require('../web/query-service.js');
const {layoutMap} = require('../web/graph-view.js');
function fixture(count = 2) {
  const nodes = [
    {id: 'src', kind: 'layer', label: 'src', parent: null, depth: 0},
    {id: 'components', kind: 'layer', label: 'src/components', parent: 'src', depth: 1},
    {id: 'outside', kind: 'layer', label: 'outside', parent: null, depth: 0},
    {id: 'a', kind: 'file', path: 'src/components/a.py', layer: 'components'},
    {id: 'b', kind: 'file', path: 'src/components/b.py', layer: 'components'},
    {id: 'dep', kind: 'file', path: 'outside/dep.py', layer: 'outside'},
    ...Array.from({length: count}, (_, i) => ({id: 'x'+i, kind: 'file', path: `outside/x${i}.py`, layer: 'outside'}))];
  const file_edges = [{from: 'a', to: 'b', type: 'import'}, {from: 'b', to: 'dep', type: 'import'},
    ...Array.from({length: count}, (_, i) => ({from: 'x'+i, to: 'a', type: 'import'}))];
  return {schema: 'dag-gps-workspace/v1', projectId: 'test', snapshotId: 'test', mapSha256: 'a'.repeat(64),
    scorerSha256: 'b'.repeat(64), source: {manifestSha256: 'c'.repeat(64)},
    inventory: nodes.filter(n => n.kind === 'file').map(n => ({path: n.path, sha256: 'd'.repeat(64)})),
    map: {meta: {folderTree: 1}, nodes, file_edges, edges: []}};
}
const ask = (service, query, rest = {}) => service.query({requestId:'test', query, ...rest});
test('router descendants, outside-only reachability and shortest file route', () => {
  const router = createRouter(fixture().map);
  assert.deepEqual(router.descendants('src'), ['a','b']);
  assert.deepEqual(router.reachable('src', true), ['x0','x1']);
  assert.deepEqual(router.reachable('src', false), ['dep']);
  assert.deepEqual(router.shortestPath('src', 'outside'), ['b','dep']);
});
test('folder matching and real-file witnesses, not synthetic folder edges', () => {
  const service = createQueryService(fixture());
  for (const q of ['where is src', 'where is the src', 'where is src folder', 'where is folder src']) {
    const p = ask(service, q); assert.equal(p.status, 'matched', q);
    assert.deepEqual(new Set(p.selectedNodeIds), new Set(['src','components','a','b']), q);
  }
  const p = ask(service, 'what uses src/components');
  assert.equal(p.operation, 'DOWNSTREAM');
  assert.deepEqual(new Set(p.selectedNodeIds), new Set(['components','x0','x1']));
  assert.ok(p.witnesses.every(w => w.nodeIds.at(-1) === 'a' && w.edges.length));
  const up = ask(service, 'what does src use');
  assert.deepEqual(up.selectedNodeIds, ['src','dep']);
  assert.deepEqual(up.witnesses[0].nodeIds, ['b','dep']);
  const path = ask(service, 'path from src to outside');
  assert.deepEqual(path.witnesses[0].nodeIds, ['b','dep']);
});
test('folder paging returns all external files within 200 nodes', () => {
  const service = createQueryService(fixture(450));
  const seen = new Set(); let continuation; let pages = 0;
  do {
    const p = ask(service, 'what uses src', {continuation});
    assert.equal(p.status, 'matched'); assert.ok(p.selectedNodeIds.length <= 200);
    p.selectedNodeIds.filter(id => id !== 'src').forEach(id => seen.add(id));
    assert.ok(p.witnesses.every(w => w.nodeIds.at(-1) === 'a'));
    continuation = p.continuation; pages++;
    assert.ok(pages <= 3);
  } while (continuation);
  assert.equal(seen.size, 450); assert.equal(pages, 3);
});
test('same-name folder collisions require a choice', () => {
  const snapshot = fixture();
  snapshot.map.nodes.push({id:'other-components', kind:'layer', label:'outside/components', parent:'outside', depth:1});
  const p = ask(createQueryService(snapshot), 'where is components');
  assert.equal(p.status, 'needs-choice');
  assert.deepEqual(new Set(p.alternatives.map(a => a.nodeId)), new Set(['components','other-components']));
});

test('every same-kind folder choice preserves traversal even with an exact root name', () => {
  const snapshot = fixture();
  snapshot.map.nodes.push({id:'nested-src', kind:'layer', label:'outside/src', parent:'outside', depth:1});
  snapshot.map.nodes.find(n=>n.id==='dep').layer='nested-src';
  const service = createQueryService(snapshot);
  const p = ask(service, 'what uses src');
  assert.equal(p.status, 'needs-choice');
  for (const alternative of p.alternatives) {
    const chosen = ask(service, 'what uses src', {chosenNodeId:alternative.nodeId});
    assert.equal(chosen.status, 'matched');
    assert.equal(chosen.operation, 'DOWNSTREAM');
    assert.equal(chosen.seedNodeId, alternative.nodeId);
  }
});

test('flat overview omits empty ancestors; LOCATE pages all descendants', () => {
  const snapshot = fixture(1600), service = createQueryService(snapshot);
  const layout = layoutMap(snapshot.map);
  assert.ok(!layout.nodes.some(n=>n.id==='src'));
  assert.ok(layout.nodes.some(n=>n.id==='components'));
  const seen = new Set(); let continuation;
  do {
    const p = ask(service, 'where is outside', {continuation});
    assert.ok(p.selectedNodeIds.length<=200);
    p.selectedNodeIds.forEach(id=>seen.add(id)); continuation=p.continuation;
  } while(continuation);
  assert.equal(seen.size,1602);
});

test('folder routes keep directed cycles, no-path and legacy flat semantics', () => {
  const snapshot = fixture();
  snapshot.map.file_edges.push({from:'b',to:'a',type:'import'});
  const router = createRouter(snapshot.map);
  assert.deepEqual(router.reachable('src',false),['dep']);
  assert.equal(router.shortestPath('components','src')[0],'a');
  const overlap = ask(createQueryService(snapshot),'path from src/components to src');
  assert.deepEqual(overlap.witnesses, [{nodeIds:['a'],edges:[]}]);
  snapshot.map.file_edges=[];
  assert.equal(ask(createQueryService(snapshot),'path from src to outside').status,'no-path');
  delete snapshot.map.meta.folderTree;
  assert.deepEqual(ask(createQueryService(snapshot),'where is src').selectedNodeIds,['src']);
});

test('article before full folder path cannot select a shorter ancestor', () => {
  const snapshot = fixture();
  snapshot.map.nodes.find(n=>n.id==='components').label = 'src/src';
  const service = createQueryService(snapshot);
  for (const q of ['the src/src', 'what does the src/src use']) {
    const p = ask(service,q);
    assert.equal(p.seedNodeId || p.selectedNodeIds[0], 'components', q);
  }
});
function dotted() {
  const s = fixture();
  s.map.nodes.push({id: 'gh', kind: 'layer', label: '.github', parent: null, depth: 0},
    {id: 'ghs', kind: 'layer', label: '.github/scripts', parent: 'gh', depth: 1},
    {id: 'gate', kind: 'file', path: '.github/scripts/gate.js', layer: 'ghs'},
    {id: 'gatetest', kind: 'file', path: 'outside/gate-user.js', layer: 'outside'});
  s.map.file_edges.push({from: 'gatetest', to: 'gate', type: 'import'});
  s.inventory = s.map.nodes.filter(n => n.kind === 'file').map(n => ({path: n.path, sha256: 'd'.repeat(64)}));
  return s;
}
test('hidden dotted folders are addressable by their literal name', () => {
  const service = createQueryService(dotted());
  for (const q of ['where is .github', 'where is folder .github', 'where is the .github folder']) {
    const p = ask(service, q); assert.equal(p.status, 'matched', q);
    assert.ok(p.selectedNodeIds.includes('gh') && p.selectedNodeIds.includes('gate'), q);
  }
  const up = ask(service, 'what uses .github');
  assert.equal(up.status, 'matched'); assert.equal(up.operation, 'DOWNSTREAM');
  assert.deepEqual(new Set(up.selectedNodeIds), new Set(['gh', 'gatetest']));
});
test('a dotted folder name shared by two folders still asks which one', () => {
  const s = dotted();
  s.map.nodes.push({id: 'gh2', kind: 'layer', label: 'outside/.github', parent: 'outside', depth: 1},
    {id: 'inner', kind: 'file', path: 'outside/.github/x.yml.js', layer: 'gh2'});
  s.inventory = s.map.nodes.filter(n => n.kind === 'file').map(n => ({path: n.path, sha256: 'd'.repeat(64)}));
  const p = ask(createQueryService(s), 'where is .github');
  assert.equal(p.status, 'needs-choice');
});
