#!/usr/bin/env node
'use strict';
// Separate worker-draft lookup challenge set; NOT held-out or user ground truth.
const fs = require('node:fs');
const path = require('node:path');
const {performance} = require('node:perf_hooks');
const {createScorer, validateResult, OPERATIONS} = require('../web/scorer.js');
const ROOT=path.resolve(__dirname,'..');
function loadCases(map) {
  const rows=fs.readFileSync(path.join(ROOT,'eval/lookup.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
  const known=new Set(map.nodes.map(n=>n.id)),ids=new Set();
  for(const r of rows) {
    if(ids.has(r.id)||!r.id||typeof r.question!=='string'||!OPERATIONS.includes(r.operation)||
      !['Exact match','Likely match','Needs your choice','No match'].includes(r.label)) throw new Error('Invalid lookup row');
    ids.add(r.id);
    for(const id of [r.target,r.from_target,r.to_target,r.suggestion].filter(Boolean)) if(!known.has(id)) throw new Error('Invented lookup target');
  }
  return rows;
}
function answerLabel(r) {
  const heads=Object.values(r.targets),labels=heads.map(h=>h.match.label);
  if(!r.yes&&heads.every(h=>h.yes)) return 'No match';
  return labels.includes('No match')?'No match':labels.includes('Needs your choice')?'Needs your choice':labels.includes('Likely match')?'Likely match':'Exact match';
}
function evaluate(map,rows,repeats=20) {
  const scorer=createScorer(map);
  let operationCorrect=0,labelCorrect=0,targetCorrect=0,targetTop3=0,targetTotal=0,acceptedWrong=0,acceptedTotal=0,negativeAccepted=0,negativeTotal=0,suggestionFound=0,suggestionTotal=0;
  const failures=[],results=[];
  for(const row of rows) {
    const r=scorer.score(row.question);validateResult(r,map);
    const expected=row.operation==='PATH'?[['from_target',row.from_target],['to_target',row.to_target]]:row.target?[['locate_target',row.target]]:[];
    let targetsRight=true;
    for(const [key,id] of expected) {
      targetTotal++;targetCorrect+=r.targets[key]?.choice===id;
      targetTop3+=Boolean(r.targets[key]?.top3.some(a=>a.id===id));
      targetsRight=targetsRight&&r.targets[key]?.choice===id;
    }
    operationCorrect+=r.operation.choice===row.operation;
    labelCorrect+=answerLabel(r)===row.label;
    if(row.operation==='NOT_SURE'){negativeTotal++;negativeAccepted+=r.yes;}
    if(r.yes){acceptedTotal++;acceptedWrong+=r.operation.choice!==row.operation||!targetsRight;}
    if(row.suggestion){suggestionTotal++;suggestionFound+=Object.values(r.targets).some(h=>h.suggestions.some(a=>a.id===row.suggestion));}
    const output={id:row.id,kind:row.kind,question:row.question,expectedOperation:row.operation,operation:r.operation.choice,expectedLabel:row.label,label:answerLabel(r),accepted:r.yes,
      targets:Object.fromEntries(Object.entries(r.targets).map(([k,h])=>[k,{choice:h.choice,label:h.match.label,reason:h.reason,suggestions:h.suggestions.map(a=>a.id)}]))};
    if(r.operation.choice!==row.operation||answerLabel(r)!==row.label||!targetsRight||(row.suggestion&&!Object.values(r.targets).some(h=>h.suggestions.some(a=>a.id===row.suggestion)))) failures.push(output);
    results.push(output);
  }
  for(let i=0;i<5;i++)for(const row of rows)scorer.score(row.question);
  const times=[];
  for(let i=0;i<repeats;i++)for(const row of rows){const t=performance.now();scorer.score(row.question);times.push(performance.now()-t);}
  times.sort((a,b)=>a-b);
  const f=(correct,total)=>({correct,total,rate:total?correct/total:null});
  return {dataset:'lookup worker-draft challenge/regression; not held-out, not user-ground-truth',cases:rows.length,
    operationAccuracy:f(operationCorrect,rows.length),labelAccuracy:f(labelCorrect,rows.length),targetTop1:f(targetCorrect,targetTotal),targetTop3:f(targetTop3,targetTotal),
    suggestionRecall:f(suggestionFound,suggestionTotal),negativeFalseAccept:f(negativeAccepted,negativeTotal),acceptedWrong:f(acceptedWrong,acceptedTotal),
    latency:{samples:times.length,p95WarmMs:times[Math.ceil(times.length*.95)-1]},failures,results};
}
if(require.main===module){
  const map=require('../maps/quest-coder/map.json'),report=evaluate(map,loadCases(map));
  fs.mkdirSync(path.join(ROOT,'artifacts'),{recursive:true});
  fs.writeFileSync(path.join(ROOT,'artifacts/lookup-eval.json'),JSON.stringify(report,null,2)+'\n');
  const {results,...summary}=report;console.log(JSON.stringify(summary,null,2));
  if(report.negativeFalseAccept.correct||report.acceptedWrong.correct||report.latency.p95WarmMs>=10)process.exitCode=1;
}
module.exports={loadCases,evaluate,answerLabel};
