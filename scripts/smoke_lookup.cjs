#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const {createScorer,validateResult}=require('../web/scorer.js');
const {loadCases}=require('./eval_lookup.cjs');
const map=require('../maps/quest-coder/map.json'),ROOT=path.resolve(__dirname,'..');
function parity(a,b,location='result') {
  if(typeof b==='number')assert.ok(Number.isFinite(a)&&Math.abs(a-b)<=1e-12,location);
  else if(b&&typeof b==='object') {assert.deepEqual(Object.keys(a),Object.keys(b),location);for(const k of Object.keys(b))parity(a[k],b[k],location+'.'+k);}
  else assert.equal(a,b,location);
}
(async()=>{
  const browser=await chromium.launch();
  try{
    const page=await browser.newPage({viewport:{width:1920,height:1080}}),errors=[],requests=[],checks=[],screenshots=[];
    page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
    page.on('request',r=>{if(!r.url().startsWith('file:'))requests.push(r.url());});
    await page.goto(pathToFileURL(path.join(ROOT,'dist/quest-coder.html')).href);
    fs.mkdirSync(path.join(ROOT,'artifacts'),{recursive:true});
    async function ask(q,label,click=false) {
      await page.locator('#ask').fill('');await page.locator('#ask').pressSequentially(q);
      if(click)await page.locator('#ask-submit').click();else await page.locator('#ask').press('Enter');
      assert.equal(await page.locator('.match-label').innerText(),label);
      const text=await page.locator('#answer').innerText();assert.ok(!text.includes('%'));assert.equal(await page.locator('#answer progress').count(),0);
      const s=await page.evaluate(()=>dagGps.state());validateResult(s.answer,map);
      checks.push({question:q,label,accepted:s.answer.yes,route:s.route,reason:s.answer.reason});return s;
    }
    async function screenshot(name){const file=path.join(ROOT,'artifacts/lookup-'+name+'.png');await page.screenshot({path:file});screenshots.push(file);}
    async function noAction(s){assert.equal(s.route,null);assert.equal(s.focused,null);assert.equal(await page.locator('g.sel,g.rel-up,g.rel-down,g.endpoint-to,path.edge.emph').count(),0);}
    let s=await ask('locate app/api/health/route.ts','Exact match');assert.equal(s.route.from,'app/api/health/route.ts');await screenshot('exact');
    s=await ask('where is runner.py?','Needs your choice',true);await noAction(s);
    assert.match(await page.locator('#answer').innerText(),/No exact file named runner\.py/);
    const missingButtons=await page.locator('#answer [data-override]').allTextContents();
    assert.ok(missingButtons.length>1);assert.ok(missingButtons.every(t=>/Override: runner\//.test(t)));await screenshot('missing');
    await page.locator('[data-override="runner/quest_runner.py"]').click();s=await page.evaluate(()=>dagGps.state());
    assert.equal(s.route.from,'runner/quest_runner.py');assert.equal(s.answer.yes,false);
    assert.equal(await page.locator('g.sel[data-id="runner/quest_runner.py"]').count(),1);
    assert.match(await page.locator('#route-status').innerText(),/Explicit user override/);checks.push({check:'explicit missing filename override selects actual file'});await screenshot('override');
    s=await ask('quantum teleporter','No match');await noAction(s);assert.equal(await page.locator('[data-override]').count(),0);await screenshot('unknown');
    s=await ask('route.ts','Needs your choice');await noAction(s);
    const expected=map.nodes.filter(n=>n.kind==='file'&&n.path.endsWith('/route.ts')).map(n=>n.id).sort();
    const shown=await page.locator('[data-override]').evaluateAll(bs=>bs.map(b=>b.dataset.override).sort());assert.deepEqual(shown,expected);await screenshot('ambiguous');
    // Choose a duplicate outside top3, proving all duplicates remain actionable explicitly.
    const outside=s.answer.targets.locate_target.suggestions.find(a=>!s.answer.targets.locate_target.top3.some(t=>t.id===a.id));assert.ok(outside);
    await page.locator('#match-details summary').click();assert.ok((await page.locator('#match-details').innerText()).includes(outside.id));
    await page.locator(`[data-override="${outside.id}"]`).click();s=await page.evaluate(()=>dagGps.state());assert.equal(s.route.from,outside.id);checks.push({check:'duplicate outside top3 chosen explicitly',file:outside.id});
    s=await ask('quest_runer.py','Needs your choice');await noAction(s);
    assert.match(await page.locator('[data-override="runner/quest_runner.py"]').innerText(),/Minor spelling/);await screenshot('typo');
    s=await ask('quest_runner','Likely match');assert.equal(s.route.from,'runner/quest_runner.py');await screenshot('stem');
    s=await ask('file bounded_sub','Likely match',true);assert.equal(s.route.from,'runner/bounded_subprocess.py');
    s=await ask('where does grading live?','Likely match');assert.equal(s.route.from,'runner-service');
    assert.match(await page.locator('#answer').innerText(),/Aliases: grader/);
    s=await ask('where is authentication?','Likely match');assert.equal(s.route.from,'auth');
    await page.locator('#match-details summary').click();assert.equal(await page.locator('#match-details').getAttribute('open'),'');
    assert.match(await page.locator('#match-details').innerText(),/not calibrated correctness probabilities/);
    assert.match(await page.locator('#match-details').innerText(),/runner-up margin/);assert.match(await page.locator('#match-details').innerText(),/raw/);
    await screenshot('details');checks.push({check:'raw heuristic details accessible with real click'});
    s=await ask('path from app/api/friends/route.ts to friends-store','Likely match');assert.deepEqual(s.route.path,['app/api/friends/route.ts','lib/friends-store.ts']);
    s=await ask('path from runner.py to database','Needs your choice');await noAction(s);
    await page.locator('[data-head="from_target"][data-override="runner/quest_runner.py"]').click();assert.equal((await page.evaluate(()=>dagGps.state())).route,null);
    await page.locator('[data-head="to_target"][data-override="persistence"]').click();s=await page.evaluate(()=>dagGps.state());
    assert.equal(s.route.from,'runner/quest_runner.py');assert.equal(s.route.to,'persistence');assert.equal(s.route.path,null);assert.deepEqual(s.route.edges,[]);
    checks.push({check:'abstained PATH requires both explicit overrides and mixed route remains honest'});
    s=await ask('path from mystery engine to database','No match');await noAction(s);assert.equal(await page.locator('[data-head="from_target"]').count(),0);
    s=await ask('file authentication.py','No match');await noAction(s);assert.equal(await page.locator('[data-override]').count(),0);
    await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(200);s=await ask('where is runner.py?','Needs your choice',true);await noAction(s);await screenshot('1280');
    const storage=await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}));assert.deepEqual(storage,{local:0,session:0});checks.push({check:'no alias learning or browser persistence WITHOUT explicit consent (including override alone)'});
    // Verify the shipped source, not an injected replacement, on all separate lookup rows.
    const rows=loadCases(map),expectedOutputs=rows.map(r=>createScorer(map).score(r.question));
    const browserOutputs=await page.evaluate(({map,rows})=>rows.map(r=>DagGpsScorer.createScorer(map).score(r.question)),{map,rows});
    browserOutputs.forEach(r=>validateResult(r,map));parity(browserOutputs,expectedOutputs);
    assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
    const report={checks,checkCount:checks.length,screenshots,lookupParityCases:rows.length,pageErrors:errors,externalRequests:requests,storage};
    fs.writeFileSync(path.join(ROOT,'artifacts/lookup-browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
  }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
