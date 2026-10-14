#!/usr/bin/env node
'use strict';
const fs = require('node:fs'), {performance} = require('node:perf_hooks');
const {createConceptIndex, createQueryService} = require('../web/query-service.js');
const reports = {};
for (const repo of ['honcho', 'salesroom']) {
  const snapshot = JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json'));
  const rows = JSON.parse(fs.readFileSync('eval/question_parser' + (repo === 'salesroom' ? '_salesroom' : '') + '.json')).rows;
  const index = createConceptIndex(snapshot.map), service = createQueryService(snapshot);
  for (let i = 0; i < 5; i++) for (const row of rows) index.search(row.question);
  const times = [], whole = [];
  for (let i = 0; i < 20; i++) for (const row of rows) {
    let t = performance.now(); index.search(row.question); times.push(performance.now() - t);
    t = performance.now(); service.query({requestId: row.id, query: row.question}); whole.push(performance.now() - t);
  }
  const p95 = values => values.sort((a, b) => a - b)[Math.ceil(values.length * 0.95) - 1];
  reports[repo] = {...index.stats, samples: times.length, queryP95Ms: p95(times), serviceP95Ms: p95(whole),
    snapshotBytes: fs.statSync('artifacts/question-parser/' + repo + '/snapshot.json').size};
}
fs.writeFileSync('artifacts/question-parser/performance.json', JSON.stringify(reports, null, 2));
console.log(JSON.stringify(reports, null, 2));
