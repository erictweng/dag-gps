#!/usr/bin/env node
'use strict';
const fs = require('node:fs'), assert = require('node:assert/strict');
const {generate, counts, timing} = require('./bench_variations.cjs');
const config = require('../eval/variation_templates.json');
const report = require('../eval/variation_results.json');
const checks = {};
for (const repo of ['honcho', 'salesroom']) {
  const snapshot = JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json'));
  const grid = generate(config, repo, snapshot);
  let baseline;
  checks[repo] = {};
  for (const version of ['main', 'parser']) {
    const rows = fs.readFileSync('artifacts/variation-benchmark/' + repo + '-' + version + '.jsonl', 'utf8').trim().split('\n').map(JSON.parse);
    assert.equal(rows.length, grid.length);
    for (let i = 0; i < rows.length; i++) {
      for (const [k, v] of Object.entries(grid[i])) assert.deepEqual(rows[i][k], v);
      assert.equal(rows[i].ms.length, 3);
      assert.ok(rows[i].ms.every(t => Number.isFinite(t) && t >= 0));
    }
    const summary = report.repos[repo][version];
    assert.deepEqual(counts(rows.filter(r => !r.negative)), summary.positive);
    assert.deepEqual(counts(rows.filter(r => r.negative)), summary.negative);
    assert.deepEqual(timing(rows.flatMap(r => r.ms)), summary.latency);
    for (const [name, count] of Object.entries(summary.constructionStratum))
      assert.deepEqual(counts(rows.filter(r => !r.negative && r.constructionStratum === name)), count);
    for (const [op, times] of Object.entries(summary.correctOperationLatency))
      assert.deepEqual(timing(rows.filter(r => r.outcome === 'correct' && r.operation === op).flatMap(r => r.ms)), times);
    const http = JSON.parse(fs.readFileSync('artifacts/variation-benchmark/' + repo + '-' + version + '-http-raw.json'));
    assert.ok(http.length >= 200);
    assert.equal(http.length, summary.http.latency.n);
    const byId = new Map(rows.map(r => [r.id, r]));
    for (const h of http) assert.equal(h.status, byId.get(h.id).status);
    checks[repo][version] = {rows: rows.length, directSamples: summary.latency.n, httpRequests: http.length, outcomeAndLatencyTotalsVerified: true};
    if (version === 'main') baseline = rows;
    else {
      checks[repo].newWrongCases = rows.filter((r, i) => r.outcome === 'wrong' && baseline[i].outcome !== 'wrong').length;
      checks[repo].newWrongExamples = rows.filter((r, i) => r.outcome === 'wrong' && baseline[i].outcome !== 'wrong').slice(0, 5).map(r => ({question: r.question, expected: r.targets, actual: r.selected, operation: r.operation, actualOperation: r.actualOperation}));
    }
  }
}
fs.writeFileSync('artifacts/variation-benchmark/verification.json', JSON.stringify(checks, null, 2) + '\n');
console.log(JSON.stringify(checks, null, 2));
