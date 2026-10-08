#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const {createScorer}=require('../web/scorer.js'), A=require('../web/aliases.js');
const map=require('../maps/quest-coder/map.json'), ROOT=path.resolve(__dirname,'..');
const entry=(alias,nodeId='runner-service')=>({alias,nodeId});
const payload=aliases=>JSON.stringify({version:1,repo:map.meta.repo,aliases});
(async()=>{
 const browser=await chromium.launch();
 try {
  const context=await browser.newContext({viewport:{width:1920,height:1080},acceptDownloads:true});
  const page=await context.newPage(), errors=[], requests=[], checks=[], screenshots=[];
  function observe(p){p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text());});p.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('blob:'))requests.push(r.url());});}
  observe(page);
  const url=pathToFileURL(path.join(ROOT,'dist/quest-coder.html')).href;
  await page.goto(url);
  const state=()=>page.evaluate(()=>dagGps.state());
  const saved=()=>page.evaluate(()=>localStorage.getItem('dag-gps:aliases:v1:'+encodeURIComponent('erictweng/quest-coder')));
  function check(name,details={}){checks.push({check:name,...details});}
  async function shot(name){const f=path.join(ROOT,'artifacts/alias-'+name+'.png');await page.screenshot({path:f});screenshots.push(f);}
  async function ask(q){await page.locator('#ask').fill('');await page.locator('#ask').pressSequentially(q);await page.locator('#ask').press('Enter');return state();}
  async function remember(q,alias,target='runner-service'){
   await ask(q);await page.locator('[data-override="'+target+'"]').click();
   await page.locator('#alias-text').fill(alias);await page.locator('#alias-review').click();
   assert.ok((await page.locator('#alias-confirmation').innerText()).includes(alias));
   assert.ok((await page.locator('#alias-confirmation').innerText()).includes(target));
   await page.locator('#alias-confirm').click();
  }
  async function openManager(){if(!await page.locator('#alias-manager').evaluate(e=>e.open))await page.locator('#alias-manager summary').click();}
  async function upload(text,mode='merge'){
   await openManager();await page.locator('#alias-mode').selectOption(mode);
   await page.locator('#alias-import').setInputFiles({name:'aliases.json',mimeType:'application/json',buffer:Buffer.from(text)});
   await page.waitForFunction(()=>document.getElementById('alias-preview').textContent.length>0);
  }
  let s=await ask('Python judge');const baseline=s.answer;
  assert.equal(s.route.from,'runner-service');assert.equal(await saved(),null);
  await page.locator('[data-override="runner-service"]').click();
  assert.equal(await saved(),null);assert.match(await page.locator('#remember-offer').innerText(),/Remember this name/i);
  await page.locator('#alias-text').fill('');await page.locator('#alias-review').click();
  assert.match(await page.locator('#alias-confirmation').innerText(),/Invalid alias entry/);assert.equal(await page.locator('#alias-confirm').count(),0);assert.equal(await saved(),null);
  await page.locator('#alias-text').fill('Python judge');await page.locator('#alias-review').click();
  await page.locator('#alias-text').fill('changed name');assert.equal(await page.locator('#alias-confirm').count(),0);assert.equal(await saved(),null);
  await page.locator('#alias-text').fill('Python judge');await page.locator('#alias-review').click();
  assert.equal(await saved(),null);await shot('consent');await page.locator('#alias-cancel').click();assert.equal(await saved(),null);
  check('synthetic Python judge baseline already correct; override/review/cancel never saves',{baselineTarget:baseline.targets.locate_target.choice});
  await page.locator('#alias-review').click();await page.locator('#alias-confirm').click();
  assert.deepEqual(A.validate(await saved(),map.meta.repo),[entry('Python judge')]);
  s=await ask('Python judge');assert.equal(s.route.from,'runner-service');assert.equal(s.answer.targets.locate_target.top3[0].components.learnedAlias,30);
  await page.reload();s=await ask('Python judge');assert.equal(s.route.from,'runner-service');assert.equal(s.answer.targets.locate_target.top3[0].components.learnedAlias,30);
  await shot('persisted');check('confirmed Python judge -> runner-service persists on same-file reload, learned evidence explicit');
  await openManager();await page.locator('[data-alias-remove]').click();s=await ask('Python judge');assert.deepEqual(s.answer,baseline);check('remove restores exact baseline');
  await remember('where is runner.py?','quest helper','runner/quest_runner.py');
  s=await ask('quest helper');assert.equal(s.route.from,'runner/quest_runner.py');assert.equal(s.expanded,'runner-service');await shot('file');
  await openManager();await page.locator('#alias-list [data-alias-remove]').click();assert.deepEqual(A.validate(await saved(),map.meta.repo),[]);
  check('confirmed file nickname preserves real full path and layer; remove restores no-alias store');
  s=await ask('Python judge station');assert.equal(s.answer.yes,false);assert.equal(s.route,null);
  await remember('Python judge station','Python judge station');s=await ask('Python judge station');assert.equal(s.answer.yes,true);assert.equal(s.route.from,'runner-service');
  check('harder synthetic abstention -> explicit correction -> accepted runner-service');
  await openManager();const downloadPromise=page.waitForEvent('download');await page.locator('#alias-export').click();
  const download=await downloadPromise, exportPath=path.join(ROOT,'artifacts/alias-export.json');await download.saveAs(exportPath);
  const exported=fs.readFileSync(exportPath,'utf8');assert.deepEqual(A.validate(exported,map.meta.repo),[entry('Python judge station')]);check('real browser download export roundtrip',{file:exportPath});
  page.once('dialog',d=>d.dismiss());await page.locator('#alias-clear').click();assert.equal(A.validate(await saved(),map.meta.repo).length,1);
  page.once('dialog',d=>d.accept());await page.locator('#alias-clear').click();assert.deepEqual(A.validate(await saved(),map.meta.repo),[]);
  s=await ask('Python judge station');assert.equal(s.answer.yes,false);check('clear cancel preserves; confirm clears persisted aliases and restores abstention');
  await upload(exported);assert.deepEqual(A.validate(await saved(),map.meta.repo),[]);await shot('import-preview');await page.locator('#alias-import-confirm').click();
  assert.deepEqual(A.validate(await saved(),map.meta.repo),[entry('Python judge station')]);check('import preview does not save until explicit confirmation (default merge)');
  await remember('Python judge','Python judge','runner-service');
  await upload(exported);await page.locator('#alias-import-confirm').click();assert.equal(A.validate(await saved(),map.meta.repo).length,2);
  await upload(exported,'replace');assert.equal(A.validate(await saved(),map.meta.repo).length,2);await page.locator('#alias-import-cancel').click();assert.equal(A.validate(await saved(),map.meta.repo).length,2);
  await upload(exported,'replace');await page.locator('#alias-import-confirm').click();assert.deepEqual(A.validate(await saved(),map.meta.repo),[entry('Python judge station')]);check('merge keeps existing, duplicates idempotent; replace explicit/cancellable');
  const before=await saved();
  for(const bad of ['{',payload([entry('valid'),entry('')]),payload([entry('x')]).replace('"version":1','"version":2'),payload([entry('x')]).replace(map.meta.repo,'wrong/repo'),payload([entry('x'.repeat(161))]),' '.repeat(A.MAX_BYTES+1)]){
   await page.locator('#alias-preview').evaluate(e=>e.textContent='');await upload(bad);
   assert.match(await page.locator('#alias-preview').innerText(),/Import rejected; nothing changed/);assert.equal(await saved(),before);assert.equal(await page.locator('#alias-import-confirm').count(),0);
  }
  check('six invalid imports atomic: malformed JSON/entry/version/repo/alias length/file size');
  const evil='<img src=x onerror="window.aliasPwned=1">';
  await upload(payload([entry(evil,'auth'),entry('old nickname','deleted-node'),entry('Python judge station','browser-run'),entry('route.ts')]),'merge');
  assert.match(await page.locator('#alias-preview').innerText(),/1 orphan/);assert.equal(await page.locator('#alias-preview img').count(),0);
  await page.locator('#alias-import-confirm').click();assert.equal(await page.locator('#alias-list img').count(),0);assert.equal(await page.evaluate(()=>window.aliasPwned),undefined);
  assert.match(await page.locator('#alias-list').innerText(),/ORPHAN/);await shot('manager');
  check('markup escaped in preview/manage; stale node quarantined visibly, no rebinding');
  s=await ask('Python judge station');assert.equal(s.answer.yes,false);assert.equal(s.route,null);
  assert.deepEqual(s.answer.targets.locate_target.suggestions.map(a=>a.id).sort(),['browser-run','runner-service']);await shot('conflict');
  await page.locator('[data-override="runner-service"]').click();const collisionSaved=await saved();await page.locator('#alias-text').fill('Python judge station');await page.locator('#alias-review').click();
  assert.match(await page.locator('#alias-confirmation').innerText(),/Conflict/);await page.locator('#alias-confirm').click();assert.equal(await saved(),collisionSaved);
  s=await ask('Python judge station');assert.equal(s.answer.yes,false);check('conflict requires choice, explicit duplicate save cannot inflate score/overwrite');
  s=await ask('route.ts');assert.equal(s.answer.yes,false);assert.equal(s.answer.targets.locate_target.match.mode,'filename');
  assert.equal(s.answer.targets.locate_target.suggestions.length,13);check('exact ambiguous filename outranks imported nickname');
  for(const q of ['quantum teleporter','old nickname','Python judge station elsewhere']){s=await ask(q);assert.equal(s.answer.yes,false);assert.equal(s.route,null);assert.equal(await page.locator('#remember-offer').count(),0);}
  check('unrelated, orphan-only and extended nickname queries abstain without learning offers');
  s=await ask('path from runner.py to database');await page.locator('[data-head="from_target"][data-override="runner/quest_runner.py"]').click();
  assert.equal(await page.locator('#alias-text').count(),0);assert.match(await page.locator('#answer').innerText(),/Alias learning disabled for PATH/);check('PATH override cannot remember full route question');
  // Shipped scorer overlay parity, not a replacement scorer injection.
  const list=A.validate(await saved(),map.meta.repo).filter(e=>map.nodes.some(n=>n.id===e.nodeId));
  const queries=['Python judge station','route.ts','quantum teleporter','old nickname','Python judge'];
  const actual=await page.evaluate(({map,list,queries})=>queries.map(q=>DagGpsScorer.createScorer(map,list).score(q)),{map,list,queries});
  function parity(a,b) {
   if(typeof b==='number') assert.ok(Number.isFinite(a)&&Math.abs(a-b)<=1e-12);
   else if(b&&typeof b==='object'){assert.deepEqual(Object.keys(a),Object.keys(b));for(const k of Object.keys(b))parity(a[k],b[k]);}
   else assert.equal(a,b);
  }
  parity(actual,queries.map(q=>createScorer(map,list).score(q)));check('shipped overlay scorer parity',{cases:queries.length});
  await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(200);await ask('Python judge station');
  await page.locator('#btn-fit').click();await page.waitForTimeout(200);await shot('1280');
  check('1280 viewport: existing Fit button keeps canvas and alias choices inspectable',{state:await state()});
  // Separate real browser contexts with denied and quota storage; navigation must remain usable.
  for(const failure of ['denied','quota']){
   const c=await browser.newContext({viewport:{width:1920,height:1080}});
   await c.addInitScript(kind=>{if(kind==='denied')Object.defineProperty(window,'localStorage',{get(){throw new Error('storage denied');}});
     else Storage.prototype.setItem=function(){throw new Error('quota exceeded');};},failure);
   const p=await c.newPage();observe(p);await p.goto(url);
   await p.locator('#ask').fill('Python judge station');await p.locator('#ask').press('Enter');await p.locator('[data-override="runner-service"]').click();
   await p.locator('#alias-text').fill('Python judge station');await p.locator('#alias-review').click();await p.locator('#alias-confirm').click();
   assert.match(await p.locator('#answer').innerText(),/Unsaved/);
   await p.locator('#alias-manager summary').click();assert.match(await p.locator('#alias-status').innerText(),/Unsaved/);
   await p.locator('#ask').fill('Python judge station');await p.locator('#ask').press('Enter');assert.equal((await p.evaluate(()=>dagGps.state())).route.from,'runner-service');
   const f=path.join(ROOT,'artifacts/alias-storage-'+failure+'.png');await p.screenshot({path:f});screenshots.push(f);
   await c.close();check('storage '+failure+' reports unsaved and keeps session navigation functional');
  }
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const report={synthetic:true,checks,checkCount:checks.length,screenshots,pageErrors:errors,externalRequests:requests,overlayParityCases:queries.length};
  fs.writeFileSync(path.join(ROOT,'artifacts/alias-browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
