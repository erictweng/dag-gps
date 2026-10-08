#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const spec=require('../maps/quest-coder/tours.json'),ROOT=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch();const checks=[],errors=[],requests=[],screenshots=[];
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('blob:'))requests.push(r.url());});
  await page.goto(pathToFileURL(path.join(ROOT,'dist/quest-refresh/index.html')).href);
  const state=()=>page.evaluate(()=>dagGps.state());
  async function ask(q){await page.locator('#ask').fill('');await page.locator('#ask').pressSequentially(q);await page.locator('#ask').press('Enter');}
  async function shot(name){let f=path.join(ROOT,'artifacts/tour-'+name+'.png');await page.screenshot({path:f});screenshots.push(f);}
  const originalEdges=await page.evaluate(()=>JSON.stringify([MAP.edges,MAP.file_edges]));
  for(const tour of spec.tours){
   await page.locator('#tour-select').selectOption(tour.id);
   assert.equal((await state()).tour.id,tour.id);
   await page.locator('#tour-overview summary').click();
   assert.ok((await page.locator('#tour-overview').innerText()).includes(spec.commit));
   assert.ok(await page.locator('#tour-overview [data-tour-locate]').count()>0);
   await page.locator('#tour-layers').click();
   const layerIds=[...new Set(tour.steps.flatMap(s=>s.nodeIds.map(id=>require('../maps/quest-coder/map.json').nodes.find(n=>n.id===id)).map(n=>n.kind==='layer'?n.id:n.layer)))].sort();
   assert.deepEqual(await page.locator('.tour-involved').evaluateAll(ns=>ns.map(n=>n.dataset.id).sort()),layerIds);
   assert.equal((await state()).view,'layers');
   await shot(tour.id+'-layers');await page.locator('#tour-step-view').click();
   for(let i=0;i<tour.steps.length;i++){
    const step=tour.steps[i];assert.equal((await state()).tour.index,i);
    const links=tour.links.filter(l=>l.status==='source-supported'&&(step.nodeIds.includes(l.from)||step.nodeIds.includes(l.to)));
    assert.equal((await state()).visibleEdges,links.length);
    assert.deepEqual(await page.locator('#viewport g.node').evaluateAll(ns=>ns.map(n=>n.dataset.id).sort()),[...new Set(step.nodeIds.concat(links.flatMap(l=>[l.from,l.to])))].sort());
    assert.equal(await page.locator('#tour-progress').innerText(),`Step ${i+1} of ${tour.steps.length}`);
    assert.equal(await page.locator('.tour-step-title').innerText(),step.title);
    assert.deepEqual(await page.locator('.tour-current').evaluateAll(ns=>ns.map(n=>n.dataset.id).sort()),step.nodeIds.slice().sort());
    const citations=page.locator('#tour-panel > .tour-citation');assert.equal(await citations.count(),step.evidence.length);
    for(let j=0;j<step.evidence.length;j++){
     const e=step.evidence[j];await citations.nth(j).click();
     assert.equal(await page.locator('#tour-evidence').evaluate(d=>d.open),true);
     assert.equal(await page.locator('#evidence-title').innerText(),`${e.path}:${e.start}–${e.end} · ${e.symbol}`);
     const actual=await page.locator('#evidence-source').innerText();
     const pinned=require('node:child_process').execFileSync('git',['-C',(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),'show',spec.commit+':'+e.path],{encoding:'utf8'}).split(/\r?\n/).slice(e.start-1,e.end).map((l,k)=>`${e.start+k} | ${l}`).join('\n');
     assert.equal(actual,pinned);
     assert.ok((await page.locator('#evidence-permalink').getAttribute('href')).includes('/blob/'+spec.commit+'/'));
     if(i===0&&j===0)await shot(tour.id+'-evidence');
     await page.locator('#evidence-close').click();assert.equal(await citations.nth(j).evaluate(e=>e===document.activeElement),true);
    }
    checks.push({check:'ordered step and every exact pinned citation',tour:tour.id,step:i+1,evidence:step.evidence.length});
    if(i===0){await page.locator('aside').evaluate(el=>el.scrollTop=0);await shot(tour.id);}
    if(i<tour.steps.length-1)await page.locator('#tour-next').click();
   }
   await page.locator('#tour-panel > details').last().locator('summary').click();
   const linkCitations=page.locator('#tour-panel > details').last().locator('.tour-citation');
   const linkEvidence=tour.links.flatMap(l=>l.evidence);
   assert.equal(await linkCitations.count(),linkEvidence.length);
   for(let j=0;j<linkEvidence.length;j++){
    const e=linkEvidence[j];await linkCitations.nth(j).click();
    const pinned=require('node:child_process').execFileSync('git',['-C',(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),'show',spec.commit+':'+e.path],{encoding:'utf8'}).split(/\r?\n/).slice(e.start-1,e.end).map((l,k)=>`${e.start+k} | ${l}`).join('\n');
    assert.equal(await page.locator('#evidence-source').innerText(),pinned);
    const index=(await state()).tour.index;await page.keyboard.press('ArrowRight');assert.equal((await state()).tour.index,index);
    await page.keyboard.press('Escape');assert.equal(await page.locator('#tour-evidence').evaluate(d=>d.open),false);
    assert.equal(await linkCitations.nth(j).evaluate(e=>e===document.activeElement),true);
   }
   checks.push({check:'every typed runtime-link citation and modal keyboard guard',tour:tour.id,evidence:linkEvidence.length});
   assert.equal(await page.locator('#tour-next').isDisabled(),true);
   await page.locator('#tour-prev').click();assert.equal((await state()).tour.index,tour.steps.length-2);
   await page.locator('#tour-reset').click();assert.equal((await state()).tour.index,0);assert.equal(await page.locator('#tour-prev').isDisabled(),true);
   await page.locator('#tour-panel > .tour-citation').first().click();await page.locator('#evidence-locate').click();
   assert.equal((await state()).focused,tour.steps[0].evidence[0].path);
   assert.ok((await page.locator('#panel').innerText()).includes(tour.steps[0].evidence[0].path));
   await page.locator('#tour-next').click();assert.equal((await state()).tour.index,1);
   await page.locator('#tour-exit').click();assert.equal((await state()).tour,null);
   await ask(tour.queries[0]);assert.equal((await state()).tour.id,tour.id);
   await page.locator('#ask').press('ArrowRight');assert.equal((await state()).tour.index,0);
   await page.locator('#ask').press('Escape');assert.equal((await state()).tour.id,tour.id);
   await page.locator('body').click({position:{x:2,y:2}});await page.keyboard.press('ArrowRight');assert.equal((await state()).tour.index,1);
   await page.keyboard.press('ArrowLeft');assert.equal((await state()).tour.index,0);
   await page.keyboard.press('Escape');assert.equal((await state()).tour,null);
   checks.push({check:'previous/reset/locate/natural Ask/typing guard/keyboard/exit',tour:tour.id});
  }
  assert.equal(await page.evaluate(()=>JSON.stringify([MAP.edges,MAP.file_edges])),originalEdges);
  await page.evaluate(()=>localStorage.setItem('dag-gps:aliases:v1:'+encodeURIComponent('erictweng/quest-coder'),JSON.stringify({version:1,repo:'erictweng/quest-coder',aliases:[{alias:'walk me through submitting code',nodeId:'auth'}]})));
  await page.reload();await ask('walk me through submitting code');assert.equal((await state()).tour.id,'submit');assert.equal((await state()).answer,null);
  await page.evaluate(()=>localStorage.removeItem('dag-gps:aliases:v1:'+encodeURIComponent('erictweng/quest-coder')));
  checks.push({check:'learned alias cannot hijack explicit walkthrough resolver'});
  await ask('walk me through submitting code');
  assert.ok(await page.locator('#dag .edge').count()>0);
  assert.ok(await page.locator('#legend').innerText().then(t=>t.includes('tour')));
  await ask('where is magic link?');assert.equal((await state()).tour,null);assert.equal((await state()).route.from,'auth');
  await ask('locate lib/session.ts');assert.equal((await state()).route.from,'lib/session.ts');
  checks.push({check:'runtime links separate from immutable imports; ordinary Ask restored'});
  await ask('walk me through submitting code');await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(200);await shot('submit-1280');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await page.setViewportSize({width:390,height:844});await page.waitForTimeout(350);await shot('submit-phone');assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  checks.push({check:'1280 and phone no horizontal clipping'});
  // Injection stays inert in text, source excerpts, attributes and metadata.
  const malicious='</script><img src=x onerror="window.injected=true">';
  const html=fs.readFileSync(path.join(ROOT,'dist/quest-refresh/index.html'),'utf8');
  const literal=html.match(/var TOUR_DATA = (.+);\nvar MAP/)[1];const data=JSON.parse(literal);
  data.tours[0].title=malicious;data.tours[0].steps[0].evidence[0].excerpt=malicious;
  const safe=JSON.stringify(data).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');
  const injectionFile=path.join(ROOT,'artifacts/tour-malicious.html');fs.writeFileSync(injectionFile,html.replace(literal,safe));
  await page.goto(pathToFileURL(injectionFile).href);await page.locator('#tour-select').selectOption('run-basic');assert.equal(await page.locator('#tour-panel h2').innerText(),malicious);
  await page.locator('#tour-panel > .tour-citation').first().click();assert.ok((await page.locator('#evidence-source').innerText()).includes(malicious));
  assert.equal(await page.evaluate(()=>Boolean(window.injected)),false);assert.equal(await page.locator('#tour-panel img, #tour-evidence img').count(),0);
  checks.push({check:'malicious titles and excerpts remain inert text'});
  await page.goto(pathToFileURL(path.join(ROOT,'dist/dag-gps/index.html')).href);
  assert.equal(await page.locator('#tour-select').isDisabled(),true);assert.match(await page.locator('#tour-select').innerText(),/No curated tours/);
  await ask('walk me through submitting code');assert.equal((await state()).tour,null);
  await ask('locate scripts/build_map.py');assert.equal((await state()).route.from,'scripts/build_map.py');
  checks.push({check:'self repo zero tours honest; normal Ask works'});
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const report={checks,screenshots,pageErrors:errors,externalRequests:requests};fs.writeFileSync(path.join(ROOT,'artifacts/tour-browser.json'),JSON.stringify(report,null,2));
  console.log(JSON.stringify({checks:checks.length,orderedSteps:spec.tours.reduce((n,t)=>n+t.steps.length,0),screenshots:screenshots.length,pageErrors:errors.length,externalRequests:requests.length}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
