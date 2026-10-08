#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{execFileSync}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const {analyzeImpact}=require('../web/impact.js'),map=require('../maps/quest-coder/map.json'),spec=require('../maps/quest-coder/tours.json'),ROOT=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch(),checks=[],errors=[],requests=[],screenshots=[];
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>{if(!/^(file|blob):/.test(r.url()))requests.push(r.url());});
  await page.goto(pathToFileURL(path.join(ROOT,'dist/quest-refresh/index.html')).href);
  const state=()=>page.evaluate(()=>dagGps.state());
  async function ask(q){await page.locator('#ask').fill('');await page.locator('#ask').pressSequentially(q);await page.locator('#ask').press('Enter');}
  async function shot(name){const f=path.join(ROOT,'artifacts/impact-'+name+'.png');await page.screenshot({path:f});screenshots.push(f);}
  const original=await page.evaluate(()=>JSON.stringify([MAP.nodes,MAP.file_edges]));
  // First target from explicit natural Ask, not a test hook.
  await ask('what could be affected if I change lib/runner-client.ts?');
  let s=await state();assert.equal(s.impact.fileId,'lib/runner-client.ts');assert.equal(s.route,null);
  const expected=analyzeImpact(map,spec,'lib/runner-client.ts');
  for(const key of ['directConsumers','transitiveConsumers','linkedTests','boundaryImpacts'])assert.deepEqual(s.impact[key],expected[key]);
  assert.deepEqual(s.impact.tourReferences.map(r=>[r.tourId,r.step,r.path,r.start,r.end]),expected.tourReferences.map(r=>[r.tourId,r.step,r.path,r.start,r.end]));
  assert.equal(s.impact.linkedTests.length,0);assert.match(await page.locator('#impact-coverage').innerText(),/Coverage unknown/);
  const ids=[...new Set([s.impact.fileId,...s.impact.directConsumers.concat(s.impact.transitiveConsumers,s.impact.boundaryImpacts).flatMap(r=>r.chain)])].sort();
  assert.deepEqual(await page.locator('#viewport g.node').evaluateAll(ns=>ns.map(n=>n.dataset.id).sort()),ids);
  assert.deepEqual(await page.locator('#viewport .sel').evaluateAll(ns=>ns.map(n=>n.dataset.id)),['lib/runner-client.ts']);
  assert.match(await page.locator('#legend').innerText(),/Potentially affected/);await shot('runner-client');checks.push('natural Ask, exact real IDs, separate boundaries and no invented linked tests');
  await page.locator('[data-impact-result="transitiveConsumers"]').first().click();
  assert.match(await page.locator('#impact-chain').innerText(),/lib\/party-boss-server.ts → lib\/runner-client.ts/);
  assert.equal(await page.locator('#viewport .edge.emph').count(),2);
  assert.deepEqual(await page.locator('#viewport g.node').evaluateAll(ns=>ns.map(n=>n.dataset.id).sort()),['app/api/party/boss/route.ts','lib/party-boss-server.ts','lib/runner-client.ts']);
  await page.locator('[data-impact-inspect]').click();assert.equal((await state()).focused,'app/api/party/boss/route.ts');assert.equal((await state()).impact.fileId,'lib/runner-client.ts');
  await shot('chain');await page.locator('#impact-return').click();checks.push('shortest transitive chain, exact edge emphasis, inspect real node, recoverable summary');
  // Source backed actual import lines, not fabricated witness endpoints.
  for(const row of expected.directConsumers){const text=execFileSync('git',['-C',(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),'show',spec.commit+':'+row.id],{encoding:'utf8'});assert.match(text,/import .*runner-client/);}
  checks.push('all runner-client direct witnesses verified against pinned source');
  await page.locator('[data-impact-result="boundaryImpacts"]').first().click();assert.match(await page.locator('#impact-chain').innerText(),/HTTP\/RPC/);assert.match(await page.locator('#impact-chain').innerText(),/\(http\)/);await shot('boundary');await page.locator('#impact-return').click();checks.push('separate boundary result gives typed real-edge witness and full overview recovery');
  await page.locator('[data-impact-tour]').first().click();assert.equal((await state()).tour.id,'submit');assert.equal((await state()).tour.index,2);assert.equal(await page.locator('#tour-evidence').evaluate(d=>d.open),true);assert.match(await page.locator('#evidence-title').innerText(),/lib\/runner-client.ts/);
  await shot('tour-evidence');await page.locator('#evidence-close').click();await page.locator('#impact-return').click();assert.equal((await state()).tour,null);assert.equal((await state()).impact.fileId,'lib/runner-client.ts');checks.push('exact tour citation opens step and offline evidence; return summary');
  // Extractor v2 adds the source-audited `from runner import quest_runner`
  // in test_trusted_boundary.py:14; twelve real tests despite tests toggle off.
  await ask('locate runner/quest_runner.py');await page.locator('[data-impact="runner/quest_runner.py"]').click();
  s=await state();assert.equal(s.showTests,false);assert.equal(s.impact.fileId,'runner/quest_runner.py');assert.equal(s.impact.directConsumers.length,16);assert.equal(s.impact.linkedTests.length,12);assert.equal(await page.locator('[data-impact-result="linkedTests"]').count(),12);assert.equal(s.impact.coverage,'unknown');
  for(const r of s.impact.linkedTests){assert.equal(await page.locator('#viewport g.node').evaluateAll((ns,id)=>ns.some(n=>n.dataset.id===id),r.id),true);const src=execFileSync('git',['-C',(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),'show',spec.commit+':'+r.id],{encoding:'utf8'});assert.match(src,r.id==='runner/tests/test_trusted_boundary.py'?/^from runner import quest_runner$/m:/from runner.quest_runner import/);}
  await shot('linked-tests');await page.locator('[data-impact-result="linkedTests"]').first().click();assert.match(await page.locator('#impact-chain').innerText(),/runner\/quest_runner.py/);checks.push('Inspect button second real file: 16 imports, 12 source-backed hidden tests; coverage unknown');
  await ask('impact of route.ts');assert.equal((await state()).impact,null);assert.equal((await state()).focused,null);assert.equal(await page.locator('[data-impact-choice]').count(),13);assert.equal(await page.locator('#viewport .sel, #viewport .rel-down, #viewport .emph').count(),0);
  await shot('ambiguous');await page.locator('[data-impact-choice="app/api/run/route.ts"]').click();assert.equal((await state()).impact.fileId,'app/api/run/route.ts');checks.push('all 13 ambiguous basenames require real click before analysis');
  await ask('impact of nonexistent-zebra.ts');assert.equal((await state()).impact,null);assert.equal((await state()).route,null);assert.equal((await state()).focused,null);assert.equal(await page.locator('[data-impact-choice]').count(),0);assert.equal(await page.locator('#viewport .sel, #viewport .rel-down, #viewport .emph').count(),0);await shot('unknown');checks.push('unknown clears summary and all stale highlights, no speculative choice');
  await ask('impact of runner.py');assert.equal((await state()).impact,null);assert.ok(await page.locator('[data-impact-choice]').count()>0);checks.push('missing filename suggestions never auto-analyze');
  await ask('impact of API routes');assert.equal((await state()).impact,null);checks.push('layer target never analyzes as a file');
  await ask('impact of path from API routes to runner service');assert.equal((await state()).impact,null);checks.push('non-single-target query fails closed without page error');
  await ask('what depends on lib/runner-client.ts?');assert.equal((await state()).route.op,'DOWNSTREAM');assert.equal((await state()).impact,null);checks.push('existing depends-on remains DOWNSTREAM, not impact');
  await ask('impact of lib/runner-client.ts');await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(250);await page.locator('aside').evaluate(e=>e.scrollTop=0);await shot('1280');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.locator('#impact-close').focus();await page.keyboard.press('Enter');assert.equal((await state()).impact,null);checks.push('1280 no horizontal clipping and keyboard Close impact');
  assert.equal(await page.evaluate(()=>JSON.stringify([MAP.nodes,MAP.file_edges])),original);
  await page.goto(pathToFileURL(path.join(ROOT,'dist/dag-gps/index.html')).href);await ask('impact of scripts/build_map.py');assert.equal((await state()).impact.fileId,'scripts/build_map.py');assert.equal((await state()).impact.toursStatus,'unavailable');assert.match(await page.locator('#impact-panel').innerText(),/No curated tours available/);await shot('self-no-tours');checks.push('second pinned map: no tours honest and usable impact');
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  fs.writeFileSync(path.join(ROOT,'artifacts/impact-browser.json'),JSON.stringify({checks,screenshots,pageErrors:errors,externalRequests:requests},null,2));console.log(JSON.stringify({checks:checks.length,screenshots:screenshots.length,pageErrors:errors.length,externalRequests:requests.length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
