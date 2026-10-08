#!/usr/bin/env node
'use strict';
// Test shipped inlined scorer parity alongside enabled M3 Ask.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {createScorer, validateResult} = require('../web/scorer.js');
const {loadCases} = require('./eval_scorer.cjs');
const ROOT = path.resolve(__dirname,'..');
const {chromium} = require(process.env.PLAYWRIGHT_DIR || '/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
(async()=>{
  const map=JSON.parse(fs.readFileSync(path.join(ROOT,'maps/quest-coder/map.json'),'utf8'));
  const rows=loadCases(path.join(ROOT,'eval/eval.jsonl'),map);
  const scorer=createScorer(map);
  const expected=rows.map(r=>scorer.score(r.question));
  const browser=await chromium.launch();
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080}});
    const errors=[],requests=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url());});
    await page.goto(pathToFileURL(path.join(ROOT,'dist/quest-coder.html')).href);
    assert.equal(await page.locator('#ask').isEnabled(),true);
    const result=await page.evaluate(({map,rows})=>{
      const s=globalThis.DagGpsScorer.createScorer(map);
      const results=rows.map(r=>s.score(r.question));
      for(let i=0;i<5;i++)for(const r of rows)s.score(r.question);
      const times=[];
      for(let i=0;i<20;i++)for(const r of rows){const start=performance.now();s.score(r.question);times.push(performance.now()-start);}
      times.sort((a,b)=>a-b);
      return {results,p95WarmMs:times[Math.ceil(times.length*.95)-1],samples:times.length};
    },{map,rows});
    // Different V8/libm releases can differ by a few ULPs; decisions/IDs/keys must be exact.
    function parity(actual, wanted, location='result') {
      if(typeof wanted==='number') {
        assert.ok(Number.isFinite(actual) && Math.abs(actual-wanted)<=1e-12,`Numeric parity: ${location}`);
      } else if(wanted && typeof wanted==='object') {
        assert.deepEqual(Object.keys(actual).sort(),Object.keys(wanted).sort(),`Keys: ${location}`);
        for(const key of Object.keys(wanted))parity(actual[key],wanted[key],`${location}.${key}`);
      } else assert.equal(actual,wanted,location);
    }
    for(const output of result.results)validateResult(output,map);
    parity(result.results,expected);
    assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
    assert.ok(result.p95WarmMs<10,`browser p95 ${result.p95WarmMs}ms >=10ms`);
    const report={cases:rows.length,nodeBrowserParity:true,askEnabled:true,pageErrors:errors,externalRequests:requests,
      p95WarmMs:result.p95WarmMs,samples:result.samples};
    fs.mkdirSync(path.join(ROOT,'artifacts'),{recursive:true});
    fs.writeFileSync(path.join(ROOT,'artifacts/m2-browser.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
