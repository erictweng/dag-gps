#!/usr/bin/env node
'use strict';
// Generated fixtures are a regression benchmark, NOT measured user accuracy.
const fs = require('node:fs');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const {createScorer, validateResult, OPERATIONS} = require('../web/scorer.js');
const ROOT = path.resolve(__dirname, '..');

function shortestPath(map, from, to) {
  const adj = new Map(map.nodes.map(n => [n.id, new Set()]));
  for (const e of [...map.edges, ...map.file_edges]) if (e.type !== 'realtime') adj.get(e.from).add(e.to);
  const queue = [[from]], seen = new Set([from]);
  for (const route of queue) {
    if (route.at(-1) === to) return route;
    for (const next of [...adj.get(route.at(-1))].sort()) if (!seen.has(next)) {
      seen.add(next); queue.push([...route, next]);
    }
  }
  return null;
}
function validateCases(rows, map) {
  if (!Array.isArray(rows) || !rows.length) throw new Error('Empty evaluation');
  const known = new Set(map.nodes.map(n => n.id));
  const seen = new Set();
  for (const r of rows) {
    if (typeof r.question !== 'string' || !OPERATIONS.includes(r.operation) || !r.id || seen.has(r.id) ||
        r.provenance !== 'generated-worker-draft') throw new Error('Invalid generated eval row');
    seen.add(r.id);
    if (r.operation !== 'NOT_SURE') {
      const targets = r.operation === 'PATH' ? [r.from_target, r.to_target] : [r.target];
      if (targets.some(id => !known.has(id))) throw new Error(`Unknown expected ID in ${r.id}`);
      if (r.operation === 'PATH' && JSON.stringify(shortestPath(map, ...targets)) !== JSON.stringify(r.expected_route))
        throw new Error(`Expected route differs from dependency graph: ${r.id}`);
    }
  }
  return rows;
}
function loadCases(filename, map) {
  return validateCases(fs.readFileSync(filename, 'utf8').trim().split('\n').map(line => JSON.parse(line)), map);
}
function fraction(correct, total) {return {correct, total, rate: total ? correct / total : null};}
function evaluate(map, rows, timingRepeats = 20) {
  const scorer = createScorer(map);
  const results = rows.map(row => {
    const output = scorer.score(row.question);validateResult(output,map);return {row,output};
  });
  let op=0,top1=0,top3=0,targets=0,acceptedTargets=0,acceptedTop1=0,paths=0,endpoints=0,pair=0;
  let positives=0,negatives=0,positiveAbstentions=0,negativeAbstentions=0;
  const failures=[];
  for (const {row:r, output:o} of results) {
    const correctOp = o.operation.choice === r.operation;
    op += correctOp;
    if (r.operation === 'NOT_SURE') {
      negatives++; negativeAbstentions += !o.yes;
    } else {
      positives++;positiveAbstentions += !o.yes;
      const expected = r.operation === 'PATH' ? [['from_target',r.from_target],['to_target',r.to_target]] : [['locate_target',r.target]];
      let both=true;
      for (const [name,id] of expected) {
        targets++;const h=o.targets[name];const one=h?.choice===id;
        top1+=one;top3+=Boolean(h?.top3.some(a=>a.id===id));both=both&&one;
        if(o.yes){acceptedTargets++;acceptedTop1+=one;}
        if(r.operation==='PATH')endpoints+=one;
      }
      if(r.operation==='PATH'){paths++;pair+=both&&correctOp;}
      if(!both || !correctOp) failures.push({id:r.id,question:r.question,expected:r.operation,
        actual:o.operation.choice,expectedTargets:expected.map(e=>e[1]),actualTargets:Object.values(o.targets).map(h=>h.choice)});
    }
    if(r.operation==='NOT_SURE'&&!correctOp)failures.push({id:r.id,question:r.question,expected:r.operation,actual:o.operation.choice});
  }
  // Warm all queries before timing. Timing includes contract validation inside score().
  for(let i=0;i<5;i++)for(const r of rows)scorer.score(r.question);
  const times=[];
  for(let i=0;i<timingRepeats;i++)for(const r of rows){const start=performance.now();scorer.score(r.question);times.push(performance.now()-start);}
  times.sort((a,b)=>a-b);
  const p95=times[Math.ceil(times.length*.95)-1];
  const negativeGroups = Object.fromEntries([...new Set(results.filter(x=>x.row.operation==='NOT_SURE').map(x=>x.row.kind))].sort().map(kind=>{
    const group=results.filter(x=>x.row.operation==='NOT_SURE'&&x.row.kind===kind);
    return [kind,{abstained:group.filter(x=>!x.output.yes).length,total:group.length}];
  }));
  return {dataset:'generated-worker-draft; not user-ground-truth',candidates:map.nodes.length,cases:rows.length,
    positiveOperationAccuracy:fraction(op-negativeAbstentions,positives),negativeGroups,
    operationAccuracy:fraction(op,rows.length), targetTop1:fraction(top1,targets),targetTop3:fraction(top3,targets),
    acceptedTargetTop1:fraction(acceptedTop1,acceptedTargets),
    abstentionRate:fraction(positiveAbstentions+negativeAbstentions,rows.length),
    positiveAbstentionRate:fraction(positiveAbstentions,positives),negativeAbstentionRate:fraction(negativeAbstentions,negatives),
    negativeFalseAcceptRate:fraction(negatives-negativeAbstentions,negatives),
    pathEndpointAccuracy:fraction(endpoints,paths*2),pathPairAndOperationAccuracy:fraction(pair,paths),
    latency:{samples:times.length,p95WarmMs:p95,targetMs:10,passed:p95<10},failures};
}
if(require.main===module){
  const map=JSON.parse(fs.readFileSync(path.join(ROOT,'maps/quest-coder/map.json'),'utf8'));
  const rows=loadCases(path.join(ROOT,'eval/eval.jsonl'),map);
  if(rows.length<30)throw new Error('Benchmark needs at least 30 cases');
  const report=evaluate(map,rows);
  console.log(JSON.stringify(report,null,2));
  if(!report.latency.passed)process.exitCode=1;
}
module.exports={loadCases,validateCases,evaluate,shortestPath};
