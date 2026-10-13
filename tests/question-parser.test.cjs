'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const S = require('../web/scorer.js');
const Q = require('../web/query-service.js');
const map = {nodes: [
  {id: 'db', kind: 'file', path: 'src/db.py', label: 'db.py'},
  {id: 'src', kind: 'layer', label: 'src'},
  {id: 'database', kind: 'layer', label: 'database'}
], edges: [], file_edges: []};
const snapshot = {schema: 'dag-gps-workspace/v1', projectId: 'test', snapshotId: 'test',
  mapSha256: 'a', scorerSha256: 'b', source: {manifestSha256: 'c'}, map, inventory: []};

test('rules normalize case, punctuation, contractions and run-ons', () => {
  const s = S.createScorer(map);
  for (const q of ['where is DB', "where's the db", 'wheres the db', 'WHAT’S DB?!',
    'whats db', "who's db", "how's db", 'where is SRC/DB.PY', 'where is db stuff']) {
    const r = s.score(q);
    assert.equal(r.yes, true, q); assert.equal(r.targets.locate_target.choice, 'db', q);
  }
});
test('kind words and filler do not dilute coverage', () => {
  const s = S.createScorer(map);
  for (const word of ['folder', 'directory', 'dir', 'package'])
    assert.equal(s.score('where is the src ' + word).targets.locate_target.choice, 'src');
  for (const word of ['file', 'module', 'script', ...S.FILLER]) {
    const h = s.score('where is db ' + word).targets.locate_target;
    assert.equal(h.yes, true, word); assert.equal(h.match.coverage, 1);
  }
  assert.equal(s.score('where is the database layer').yes, true);
  assert.equal(s.score('db extraterrestrial nonsense').yes, false);
});
test('case-folded file collisions require choice; paths are not repaired', () => {
  const s = S.createScorer({...map, nodes: [...map.nodes, {id: 'DB', kind: 'file', path: 'src/DB.py'}]});
  assert.equal(s.score('src/db.py').yes, false);
  assert.equal(s.score('./src/db.py').yes, false);
});
test('normalization composes with explicitly supplied alias overlays', () => {
  const q = Q.createQueryService(snapshot, {learnedAliases: [{alias: 'my datastore', nodeId: 'db'}]});
  const p = q.query({requestId: 'alias', query: "WHERE'S MY DATASTORE?!"});
  assert.equal(p.status, 'matched'); assert.deepEqual(p.selectedNodeIds, ['db']);
  assert.match(p.reason, /learned alias/);
});
test('operation patterns retain dependency direction', () => {
  assert.equal(S.createScorer(map).score('what does src/db.py depend on').requestedOperation, 'UPSTREAM');
  assert.equal(S.createScorer(map).score('what uses src/db.py').requestedOperation, 'DOWNSTREAM');
});
