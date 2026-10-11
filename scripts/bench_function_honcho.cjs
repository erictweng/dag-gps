'use strict';
const fs = require('fs'), {performance} = require('perf_hooks');
const {createQueryService} = require('../web/query-service.js');
const out = 'artifacts/function-layer/honcho/';
const snapshot = JSON.parse(fs.readFileSync(out + 'snapshot.json'));
const questions = JSON.parse(fs.readFileSync(out + 'questions.json'));
const start = performance.now(), service = createQueryService(snapshot), indexMs = performance.now() - start;
const samples = [];
for (let round = 0; round < 110; round++) for (const query of questions) {
  const t = performance.now();
  service.query({requestId: 'bench', query});
  if (round >= 10) samples.push(performance.now() - t);
}
samples.sort((a,b) => a-b);
const result = {indexMs, samples: samples.length, p95Ms: samples[Math.ceil(samples.length * .95)-1],
  maxMs: samples.at(-1), boundary: 'Warm deterministic JS query service only; excludes Python contract validation, transport and DOM. 10 warmup and 100 measured rounds per question.'};
fs.writeFileSync(out + 'query-benchmark.json', JSON.stringify(result, null, 2));
console.log(JSON.stringify(result));
