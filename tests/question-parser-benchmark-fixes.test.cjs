'use strict';
const test = require('node:test'), assert = require('node:assert/strict'), fs = require('node:fs');
const Q = require('../web/query-service.js'), S = require('../web/scorer.js');
const config = require('../eval/variation_templates.json');
const available = ['honcho', 'salesroom'].filter(repo => {
  const path = 'artifacts/question-parser/' + repo + '/snapshot.json';
  if (fs.existsSync(path)) return true;
  test(repo + ': pinned benchmark regressions', {skip: 'Optional pinned snapshot absent: ' + path}, () => {});
  return false;
});
const snapshots = Object.fromEntries(available.map(repo => [repo,
  JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json'))]));
const services = Object.fromEntries(Object.entries(snapshots).map(([repo, s]) => [repo, Q.createQueryService(s)]));
const ask = (repo, query) => services[repo].query({requestId: 'regression', query});
const signature = p => [p.status, p.operation, p.seedNodeId, p.selectedNodeIds, p.alternatives.map(a => a.nodeId)];

for (const repo of Object.keys(snapshots)) {
  test(repo + ': terminal punctuation preserves all operation patterns and tiers', () => {
    const spec = config.repos[repo], file = spec.targets.find(t => t.kind === 'file');
    const symbol = spec.targets.find(t => t.kind === 'symbol');
    const questions = ['where is ' + file.path, 'where is database', 'where is settings',
      'where is src/db.py', 'where is json.dumps', 'where is Class.method', 'where is unknown_qzx'];
    for (const [op, phrases] of Object.entries(config.phrases)) {
      if (['CALLERS', 'CALLEES', 'TRACE', 'FLOW'].includes(op) && !symbol) continue;
      const pair = spec.pairs.find(p => p.operation === op);
      for (const phrase of phrases) questions.push(phrase.replace('{x}', pair?.a || (['CALLERS', 'CALLEES', 'TRACE'].includes(op) ? symbol.id : file.path)).replace('{y}', pair?.b || file.path));
    }
    for (const query of questions) {
      const expected = signature(ask(repo, query + '?'));
      for (const suffix of ['.', '!', '.!?', '?!..   ', ' . ! ?  '])
        assert.deepEqual(signature(ask(repo, query + suffix)), expected, query + suffix);
    }
    assert.equal(S.normalizeQuestion('Class.method.'), 'class.method');
    assert.equal(S.normalizeQuestion('json.dumps.'), 'json.dumps');
    assert.equal(S.normalizeQuestion('src/db.py.'), 'src/db.py');
  });
}

test('salesroom: bare events includes folder and file, kind and full path resolve', {skip: !snapshots.salesroom && 'Optional Salesroom snapshot absent'}, () => {
  const file = 'src/lib/events.ts', folder = snapshots.salesroom.map.nodes.find(n => n.kind === 'layer' && n.label === 'app/api/events').id;
  for (const query of ['events', 'where is events', 'what uses events', 'what does events use']) {
    const p = ask('salesroom', query);
    assert.equal(p.status, 'needs-choice', query);
    for (const id of [file, folder]) assert.ok(p.alternatives.some(a => a.nodeId === id), query + ': ' + id);
    assert.deepEqual(p.selectedNodeIds, []);
  }
  for (const [query, id] of [['where is file events', file], ['where is folder events', folder], ['where is src/lib/events.ts', file], ['where is app/api/events', folder]]) {
    const p = ask('salesroom', query);
    assert.equal(p.status, 'matched', query); assert.equal(p.selectedNodeIds[0], id, query);
  }
});

test('honcho: bare backfill includes file and class, kind and qualified path resolve', {skip: !snapshots.honcho && 'Optional Honcho snapshot absent'}, () => {
  const file = 'src/reconciler/backfill.py', symbol = snapshots.honcho.map.symbol_graph.nodes.find(n => n.name === 'Backfill').id;
  for (const query of ['backfill', 'where is backfill', 'where is backfill defined']) {
    const p = ask('honcho', query);
    assert.equal(p.status, 'needs-choice', query);
    for (const id of [file, symbol]) assert.ok(p.alternatives.some(a => a.nodeId === id), query + ': ' + id);
    for (const id of [file, symbol]) {
      const chosen = services.honcho.query({requestId: 'chosen', query, chosenNodeId: id});
      assert.equal(chosen.status, 'matched'); assert.equal(chosen.selectedNodeIds[0], id);
    }
  }
  for (const [query, id] of [['where is file backfill', file], ['where is class backfill', symbol], ['where is src/reconciler/backfill.py', file], ['locate symbol ' + symbol, symbol]]) {
    const p = ask('honcho', query);
    assert.equal(p.status, 'matched', query); assert.equal(p.selectedNodeIds[0], id, query);
  }
});

for (const repo of Object.keys(snapshots)) test(repo + ': synonym-only targets do not pick between comparable candidates', () => {
  // Exercise the real service with each repo's graph plus a competing literal
  // target. Salesroom has only one db stem naturally, so its natural unique
  // database synonym remains legitimate; this variant tests the ambiguity rule.
  const s = structuredClone(snapshots[repo]);
  s.map.nodes.push({id: 'regression-config', kind: 'file', path: 'regression/config.py', label: 'config.py'});
  s.map.nodes.push({id: 'regression-settings', kind: 'layer', label: 'regression/settings'});
  s.map.nodes.push({id: 'regression-env-file', kind: 'file', path: 'regression/env.py', label: 'env.py'});
  s.map.nodes.push({id: 'regression-env-layer', kind: 'layer', label: 'env'});
  const q = Q.createQueryService(s);
  const environment = q.query({requestId: 'env', query: 'where is environment'});
  assert.equal(environment.status, 'needs-choice');
  for (const id of ['regression-env-file', 'regression-env-layer'])
    assert.ok(environment.alternatives.some(a => a.nodeId === id), repo + ': ' + id);
  const p = q.query({requestId: 'synonym', query: 'where is configuration'});
  const literal = s.map.nodes.some(n => n.kind === 'file' && n.path?.split('/').at(-1) === 'configuration.py');
  if (literal) {
    assert.ok(p.selectedNodeIds.includes('src/schemas/configuration.py') || p.alternatives.some(a => a.nodeId === 'src/schemas/configuration.py'));
    assert.ok(!p.alternatives.some(a => ['regression-config', 'regression-settings'].includes(a.nodeId)), 'literal matches precede synonyms');
  }
  else {
    assert.equal(p.status, 'needs-choice');
    assert.ok(p.alternatives.some(a => a.nodeId === 'regression-config'));
    assert.ok(p.alternatives.some(a => a.nodeId === 'regression-settings'));
  }
  for (const word of ['db', 'database', 'config', 'configuration', 'settings']) {
    const natural = ask(repo, 'where is ' + word);
    assert.ok(['matched', 'needs-choice', 'no-match'].includes(natural.status));
  }
});
