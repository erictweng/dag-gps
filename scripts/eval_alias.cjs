#!/usr/bin/env node
'use strict';
// Synthetic worker-draft regression only; not Eric queries or held-out accuracy.
const fs=require('node:fs'),path=require('node:path'),{performance}=require('node:perf_hooks');
const {createScorer}=require('../web/scorer.js');const map=require('../maps/quest-coder/map.json');
const a=(alias,nodeId='runner-service')=>({alias,nodeId});
const rows=[
 {question:'Python judge',aliases:[a('Python judge')],yes:true,target:'runner-service'},
 {question:'Python judge station',aliases:[a('Python judge station')],yes:true,target:'runner-service'},
 {question:'where is Python judge station?',aliases:[a('Python judge station')],yes:true,target:'runner-service'},
 {question:'dependencies of Python judge station',aliases:[a('Python judge station')],yes:true,target:'runner-service',op:'UPSTREAM'},
 {question:'what depends on Python judge station',aliases:[a('Python judge station')],yes:true,target:'runner-service',op:'DOWNSTREAM'},
 {question:'my health point',aliases:[a('my health point','app/api/health/route.ts')],yes:true,target:'app/api/health/route.ts'},
 {question:'quest_runner.py',aliases:[a('quest_runner.py')],yes:true,target:'runner/quest_runner.py'},
 {question:'app/api/health/route.ts',aliases:[a('app/api/health/route.ts')],yes:true,target:'app/api/health/route.ts'},
 {question:'route.ts',aliases:[a('route.ts')],yes:false},
 {question:'Python judge station',aliases:[a('Python judge station'),a('Python judge station','browser-run')],yes:false},
 {question:'quantum teleporter',aliases:[a('Python judge station')],yes:false},
 {question:'Python judge station elsewhere',aliases:[a('Python judge station')],yes:false},
 {question:'Python judge station',aliases:[],yes:false},
 {question:'path from unknown place to Python judge station',aliases:[a('Python judge station')],yes:false},
 {question:'path from API routes to Python judge station',aliases:[a('Python judge station')],yes:true,target:'api',to:'runner-service',op:'PATH'}
];
const results=rows.map(row=>{
 const s=createScorer(map,row.aliases),r=s.score(row.question),h=r.targets.locate_target||r.targets.from_target;
 const pass=r.yes===row.yes&&(!row.yes||(h.choice===row.target&&r.operation.choice===(row.op||'LOCATE')&&(!row.to||r.targets.to_target.choice===row.to)));
 const times=[];for(let i=0;i<30;i++){const t=performance.now();s.score(row.question);times.push(performance.now()-t);}
 return {...row,actual:{yes:r.yes,op:r.operation.choice,target:h.choice,to:r.targets.to_target?.choice},pass,times};
});
const times=results.flatMap(r=>r.times).sort((a,b)=>a-b), report={synthetic:true,source:'worker-draft regression, not user evidence',cases:rows.length,passed:results.filter(r=>r.pass).length,
 negativeFalseAcceptance:results.filter(r=>!r.yes&&r.actual.yes).length,wrongAccepted:results.filter(r=>r.actual.yes&&!r.pass).length,
 samples:times.length,p95Ms:times[Math.ceil(times.length*.95)-1],results:results.map(({times,...r})=>r)};
fs.mkdirSync(path.resolve(__dirname,'../artifacts'),{recursive:true});fs.writeFileSync(path.resolve(__dirname,'../artifacts/alias-eval.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
if(report.passed!==report.cases||report.negativeFalseAcceptance||report.wrongAccepted)process.exitCode=1;
