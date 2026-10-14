'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const {generate, classify, timing, counts} = require('../scripts/bench_variations.cjs');
const config = require('../eval/variation_templates.json');
const snapshot = repo => ({map: {nodes: config.repos[repo].targets, symbol_graph: {nodes: []}}});

test('variation construction deterministic, source-grounded quotas and negative counts', () => {
  for (const repo of ['honcho', 'salesroom']) {
    const a = generate(config, repo, snapshot(repo)), b = generate(config, repo, snapshot(repo));
    assert.deepEqual(a, b);
    const targets = config.repos[repo].targets;
    for (const [kind, min] of [['file', 30], ['layer', repo === 'honcho' ? 15 : 10], ['symbol', repo === 'honcho' ? 30 : 0]])
      assert.ok(targets.filter(t => t.kind === kind).length >= min);
    assert.equal(a.filter(r => r.negative).length, 240);
    assert.equal(new Set(a.map(r => r.id)).size, a.length);
    assert.ok(targets.every(t => t.sourceCheck));
    const known = new Set(targets.map(t => t.id));
    const pairs = config.repos[repo].pairs;
    for (const r of a.filter(r => !r.negative)) {
      assert.ok(r.targets.length === 1 ? known.has(r.targets[0]) : pairs.some(p => p.from === r.targets[0] && p.to === r.targets[1] && p.operation === r.operation));
      assert.ok(!r.question.includes('{x}') && !r.question.includes('{y}'));
      if (r.targets.length === 1) {
        const kind = targets.find(t => t.id === r.targets[0]).kind;
        assert.ok((kind === 'symbol' ? ['LOCATE', 'CALLERS', 'CALLEES', 'TRACE'] : ['LOCATE', 'UPSTREAM', 'DOWNSTREAM']).includes(r.operation));
      }
    }
  }
});
test('all declared independent axes exist including mismatching kinds and synonyms', () => {
  const rows = generate(config, 'honcho', snapshot('honcho'));
  for (const axis of ['case', 'punctuation', 'filler', 'kind', 'target-form', 'typo']) assert.ok(rows.some(r => r.axis === axis));
  for (const value of ['matching', 'mismatching']) assert.ok(rows.some(r => r.kindAgreement === value));
  assert.ok(rows.some(r => r.form.startsWith('synonym:')));
  assert.ok(rows.some(r => r.question.startsWith('wheres ')));
  assert.ok(rows.some(r => r.question.startsWith('where’s ')));
});
test('confident grading checks seed, operation and directed path, not incidental selected nodes', () => {
  const row = {targets: ['a'], operation: 'UPSTREAM'};
  const packet = {status: 'matched', operation: 'UPSTREAM', selectedNodeIds: ['a', 'b']};
  assert.equal(classify(row, packet), 'correct');
  assert.equal(classify(row, {...packet, selectedNodeIds: ['b', 'a']}), 'wrong');
  assert.equal(classify(row, {...packet, operation: 'DOWNSTREAM'}), 'wrong');
  assert.equal(classify(row, {...packet, seedNodeId: 'b'}), 'wrong');
  const route = {targets: ['a', 'b'], operation: 'PATH'};
  assert.equal(classify(route, {...packet, operation: 'PATH', witnesses: [{nodeIds: ['a', 'c', 'b']}]}), 'correct');
  assert.equal(classify(route, {...packet, operation: 'PATH', witnesses: [{nodeIds: ['b', 'a']}]}), 'wrong');
});
test('choice, abstention, unsupported and negative classification stay separate', () => {
  const row = {targets: ['a'], operation: 'LOCATE'};
  const p = {status: 'needs-choice', operation: 'NOT_SURE', alternatives: [{nodeId: 'a'}]};
  assert.equal(classify(row, p, 'LOCATE'), 'choose-correct');
  assert.equal(classify(row, p, 'PATH'), 'unresolved');
  assert.equal(classify(row, {...p, alternatives: []}, 'LOCATE'), 'unresolved');
  assert.equal(classify(row, {status: 'no-match'}), 'no-match');
  assert.equal(classify(row, {status: 'unsupported'}), 'unresolved');
  assert.equal(classify({...row, negative: true}, {status: 'matched'}), 'overconfident');
  assert.equal(classify({...row, negative: true}, p), 'unresolved');
});
test('distinct successes deduplicate question strings, percentiles use nearest rank', () => {
  const c = counts([{question: 'a', outcome: 'correct'}, {question: 'a', outcome: 'choose-correct'}, {question: 'b', outcome: 'wrong'}]);
  assert.equal(c.distinctSuccessful, 1); assert.equal(c.total, 3);
  assert.equal(timing([1, 2, 3, 4, 5]).p95, 5); assert.equal(timing([1, 2, 3]).p50, 2);
});
