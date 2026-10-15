'use strict';
// Manual paired replay: unchanged query engine, frozen grids, changed snapshots.
const fs = require('node:fs'), path = require('node:path');
const {createHash} = require('node:crypto');
const {createQueryService} = require('../web/query-service.js');
const Scorer = require('../web/scorer.js');
const {generate, classify, counts, timing} = require('../scripts/bench_variations.cjs');
const {performance} = require('node:perf_hooks');
const out = path.resolve(__dirname, '../artifacts/ts-paths');
const read = p => JSON.parse(fs.readFileSync(p));
const config = read(path.resolve(__dirname, '../eval/variation_templates.json'));
const snapshots = ['before', 'after'].map(v => read(`${out}/${v}/salesroom/snapshot.json`));
const services = snapshots.map(createQueryService);
const scorers = snapshots.map(s => Scorer.createScorer(s.map));
const grid = generate(config, 'salesroom', snapshots[0]);
const frozen = read(path.resolve(__dirname, '../eval/question_parser_salesroom.json')).rows;
// Remove only identity/revision metadata; retain the entire semantic answer.
function semantic(p) {
  return JSON.parse(JSON.stringify(p, (k, v) => ['requestId', 'snapshotId', 'mapSha256', 'scorerSha256'].includes(k) ? undefined : v));
}
const report = {};
for (const [name, rows] of [['frozen', frozen], ['variation', grid]]) {
  const results = [[], []], changes = [], times = [[], []];
  for (const row of rows) {
    const packets = services.map((s, i) => {
      const start = performance.now();
      const p = s.query({requestId: row.id, query: row.question});
      times[i].push(performance.now() - start);
      const choiceOp = p.status === 'needs-choice' && p.operation === 'NOT_SURE' ? scorers[i].score(row.question).requestedOperation : p.operation;
      const outcome = classify({...row, negative: name === 'frozen' ? row.expected === 'no-match' : row.negative}, p, choiceOp);
      results[i].push({id: row.id, question: row.question, outcome});
      return semantic(p);
    });
    if (JSON.stringify(packets[0]) !== JSON.stringify(packets[1])) {
      const outcomes = results.map(rs => rs.at(-1).outcome);
      const wrong = x => ['wrong', 'overconfident'].includes(x);
      changes.push({id: row.id, question: row.question, outcomes,
        classification: wrong(outcomes[1]) && !wrong(outcomes[0]) ? 'newly wrong' :
          !['correct', 'choose-correct'].includes(outcomes[0]) && ['correct', 'choose-correct'].includes(outcomes[1]) ? 'newly right' :
            wrong(outcomes[0]) && wrong(outcomes[1]) ? 'changed; pre-existing wrong' : 'changed but both acceptable',
        preexistingWrong: wrong(outcomes[0]) && wrong(outcomes[1]),
        before: packets[0], after: packets[1]});
    }
  }
  const newlyWrong = results[1].filter((r, i) => ['wrong', 'overconfident'].includes(r.outcome) && !['wrong', 'overconfident'].includes(results[0][i].outcome)).length;
  report[name] = {cases: rows.length, changed: changes.length, newlyWrong, counts: results.map(counts), latency: times.map(timing),
    gridSha256: createHash('sha256').update(JSON.stringify(rows)).digest('hex')};
  fs.writeFileSync(`${out}/${name}-changes.json`, JSON.stringify(changes, null, 2));
  fs.writeFileSync(`${out}/${name}-outcomes.json`, JSON.stringify(results));
}
fs.writeFileSync(`${out}/query-report.json`, JSON.stringify(report, null, 2));
console.log(JSON.stringify(report, null, 2));
if (Object.values(report).some(r => r.newlyWrong)) process.exitCode = 1;
