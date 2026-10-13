#!/usr/bin/env node
'use strict';
const fs = require('node:fs');
const crypto = require('node:crypto');
const {performance} = require('node:perf_hooks');
const {createQueryService} = require(process.argv[6] ? require('node:path').resolve(process.argv[6]) : '../web/query-service.js');
const datasetBytes = fs.readFileSync(process.argv[5] || 'eval/question_parser.json');
const dataset = JSON.parse(datasetBytes);
const snapshot = JSON.parse(fs.readFileSync(process.argv[2] || 'artifacts/question-parser/baseline-snapshot.json'));
const out = process.argv[3] || 'artifacts/question-parser/baseline.json';
if (snapshot.source.commit !== dataset.pin) throw Error('Wrong source pin');
const known = new Set([...snapshot.map.nodes, ...(snapshot.map.symbol_graph?.nodes || [])].map(n => n.id));
const start = performance.now(), service = createQueryService(snapshot), buildMs = performance.now() - start;
const results = dataset.rows.map(row => {
  if (row.targets.some(id => !known.has(id))) throw Error('Unknown expected target: ' + row.id);
  const p = service.query({requestId: row.id, query: row.question});
  const targets = p.seedNodeId ? [p.seedNodeId] : p.selectedNodeIds;
  const targetRight = targets.some(id => row.targets.includes(id));
  const matchCorrect = row.expected === 'match' && p.status === 'matched' && targetRight && p.operation === row.operation;
  const chooseCorrect = row.expected === 'choose' && p.status === 'needs-choice' && p.alternatives.some(a => row.targets.includes(a.nodeId));
  const noMatchCorrect = row.expected === 'no-match' && p.status === 'no-match';
  const wrong = p.status === 'matched' && row.expected !== 'no-match' && (!targetRight || p.operation !== row.operation);
  const overconfident = p.status === 'matched' && row.expected === 'no-match';
  return {id: row.id, split: row.split, question: row.question, expected: row.expected, status: p.status,
    targets, alternatives: p.alternatives.map(a => a.nodeId), matchCorrect, chooseCorrect, noMatchCorrect, wrong, overconfident};
});
const splits = Object.fromEntries(['dev', 'holdout'].map(split => {
  const rows = results.filter(r => r.split === split);
  return [split, Object.fromEntries(['matchCorrect', 'chooseCorrect', 'noMatchCorrect', 'wrong', 'overconfident'].map(k => [k, rows.filter(r => r[k]).length]).concat([
    ['cases', rows.length], ['matchTotal', rows.filter(r => r.expected === 'match').length],
    ['chooseTotal', rows.filter(r => r.expected === 'choose').length], ['noMatchTotal', rows.filter(r => r.expected === 'no-match').length]]))];
}));
const report = {datasetSha256: crypto.createHash('sha256').update(datasetBytes).digest('hex'), pin: dataset.pin,
  buildMs, splits, results};
fs.mkdirSync(require('node:path').dirname(out), {recursive: true});
fs.writeFileSync(out, JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({buildMs, splits}, null, 2));
if (process.argv[4]) {
  const baseline = JSON.parse(fs.readFileSync(process.argv[4]));
  if (baseline.datasetSha256 !== report.datasetSha256) throw Error('Frozen questions changed');
  const old = new Map(baseline.results.map(r => [r.id, r]));
  if (results.some(r => (r.wrong && !old.get(r.id).wrong) || (r.overconfident && !old.get(r.id).overconfident)))
    throw Error('New wrong/overconfident answer versus baseline');
}
