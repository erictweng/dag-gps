'use strict';
const fs = require('node:fs');
const {createQueryService} = require('../web/query-service.js');
const cases = require('../eval/question_parser_review_regressions.json');
const rows = [];
for (const repo of ['honcho', 'salesroom']) {
  const service = createQueryService(JSON.parse(fs.readFileSync('artifacts/question-parser/' + repo + '/snapshot.json')));
  for (const row of cases[repo]) {
    const packet = service.query({requestId: 'review', query: row.query});
    const pass = packet.status === 'matched' && packet.operation === row.operation &&
      (packet.seedNodeId || packet.selectedNodeIds[0]) === row.target && (!row.reason || packet.reason.includes(row.reason));
    rows.push({repo, ...row, pass, packet});
  }
}
const report = {passed: rows.filter(r => r.pass).length, failed: rows.filter(r => !r.pass).length, rows};
fs.writeFileSync(process.argv[2] || 'artifacts/question-parser/review-fixes/regressions.json', JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({passed: report.passed, failed: report.failed}));
if (report.failed) process.exitCode = 1;
