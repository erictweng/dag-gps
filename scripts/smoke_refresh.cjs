#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'), fs=require('node:fs'), path=require('node:path');
const {execFileSync}=require('node:child_process'), {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const ROOT=path.resolve(__dirname,'..'), fixture=require('../artifacts/refresh-fixture.json');
(async()=>{
 const browser=await chromium.launch();
 try{
  const context=await browser.newContext({viewport:{width:1920,height:1080},acceptDownloads:true});
  const page=await context.newPage(), errors=[], requests=[], checks=[], screenshots=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{if(!r.url().startsWith('file:')&&!r.url().startsWith('blob:'))requests.push(r.url());});
  const file=p=>pathToFileURL(path.join(ROOT,p)).href;
  async function ask(q){await page.locator('#ask').fill(q);await page.locator('#ask').press('Enter');return page.evaluate(()=>dagGps.state());}
  async function shot(name){await page.locator('#btn-fit').click();await page.waitForTimeout(250);const target=path.join(ROOT,'artifacts/refresh-'+name+'.png');await page.screenshot({path:target,fullPage:true});screenshots.push(target);}
  function check(name){checks.push(name);}
  await page.goto(file('dist/dag-gps/index.html'));
  let s=await ask('locate scripts/build_map.py');
  assert.equal(s.answer.yes,true);assert.equal(s.route.from,'scripts/build_map.py');assert.equal(s.expanded,'pipeline');
  await page.locator('#refresh-info summary').click();
  assert.match(await page.locator('#refresh-detail').innerText(),/f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93/);
  assert.match(await page.locator('#refresh-detail').innerText(),/cannot detect current remote freshness/);
  await shot('self-file');check('real second repository Ask resolves scripts/build_map.py and precise audited source');
  await page.locator('#btn-back').click();
  s=await ask('dependencies of Regression tests');assert.equal(s.route.from,'tests');
  assert.deepEqual(s.route.ids.slice().sort(),['browser','pipeline','tests']);
  await shot('self-dependencies');check('real second graph follows tests consumer → pipeline/browser dependencies');
  await page.locator('#btn-fit').click();
  await page.locator('#t-tests').check();
  await page.locator('[data-go="pipeline"]').first().click();
  await page.locator('[data-expand="pipeline"]').click();
  assert.equal((await page.evaluate(()=>dagGps.state())).expanded,'pipeline');
  await page.locator('#btn-back').click();check('second repo real click inspect/expand/back, fit and test toggle');
  await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(250);
  await ask('locate web/aliases.js');await page.locator('#btn-fit').click();await page.waitForTimeout(250);
  await shot('self-1280');
  assert.ok(await page.locator('#ask-submit').isVisible());
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  check('1280 full-page provenance, Ask, canvas and sidebar without horizontal document clipping');
  await page.setViewportSize({width:1920,height:1080});
  await page.goto(file('dist/quest-refresh/index.html'));await page.locator('#refresh-info summary').click();
  assert.match(await page.locator('#refresh-summary').innerText(),/\+0 \/ −0 files/);
  s=await ask('where is magic link?');assert.equal(s.route.from,'auth');await shot('quest');
  check('quest pinned snapshot unchanged diff and existing real architecture Ask');
  // User-selected alias import binds only actual before-snapshot paths.
  await page.goto(file('dist/refresh-fixture/index.html'));
  const before=JSON.parse(fs.readFileSync(path.join(fixture.out_dir,'map.json'),'utf8'));
  const payload=JSON.stringify({version:1,repo:before.meta.repo,aliases:[{alias:'valid station',nodeId:'a.cjs'},{alias:'retired station',nodeId:'gone.py'}]});
  await page.locator('#alias-manager summary').click();
  await page.locator('#alias-import').setInputFiles({name:'aliases.json',mimeType:'application/json',buffer:Buffer.from(payload)});
  await page.locator('#alias-import-confirm').click();
  s=await ask('valid station');assert.equal(s.route.from,'a.cjs');assert.equal(s.expanded,'consumer');
  s=await ask('retired station');assert.equal(s.route.from,'gone.py');
  const namespace=await page.evaluate(()=>localStorage.key(0));
  // Rebuild the SAME published URL from a second committed snapshot, then reload.
  execFileSync('python3',['scripts/build_project.py','--repo',fixture.repo,'--ref',fixture.after_commit,'--layers',fixture.layers,'--out-dir',fixture.out_dir],{cwd:ROOT});
  await page.reload();
  s=await ask('valid station');assert.equal(s.route.from,'a.cjs');assert.equal(s.expanded,'dependency');
  assert.equal(s.answer.targets.locate_target.top3[0].components.learnedAlias,30);
  s=await ask('retired station');assert.equal(s.answer.yes,false);assert.equal(s.route,null);
  await page.locator('#alias-manager summary').click();
  assert.match(await page.locator('#alias-status').innerText(),/Loaded 2 saved aliases/);
  assert.match(await page.locator('#alias-list').innerText(),/ORPHAN/);
  assert.match(await page.locator('#alias-list').innerText(),/gone.py/);
  assert.match(await page.locator('#refresh-summary').innerText(),/1 assignments/);
  await page.locator('#refresh-info summary').click();await shot('alias-migration');
  const after=JSON.parse(fs.readFileSync(path.join(fixture.out_dir,'map.json'),'utf8'));
  const diff=JSON.parse(fs.readFileSync(path.join(fixture.out_dir,'diff.json'),'utf8'));
  assert.equal(after.meta.repo,before.meta.repo);
  assert.deepEqual(diff.added_files,['new.cjs']);assert.deepEqual(diff.deleted_files,['gone.py']);
  assert.deepEqual(diff.assignment_changes,[{id:'a.cjs',from:'consumer',to:'dependency'}]);
  assert.equal(diff.baseline.commit,fixture.before_commit);assert.equal(diff.snapshot.commit,fixture.after_commit);
  check('synthetic real git snapshots: added/deleted files, typed connections, reassignment; valid aliases retain exact IDs/new layer, deleted alias ORPHAN not rebound');
  const downloadPromise=page.waitForEvent('download');await page.locator('#alias-export').click();
  const download=await downloadPromise;await download.saveAs(path.join(ROOT,'artifacts/refresh-alias-export.json'));
  const exported=JSON.parse(fs.readFileSync(path.join(ROOT,'artifacts/refresh-alias-export.json'),'utf8'));
  assert.deepEqual(exported.aliases,JSON.parse(payload).aliases);
  check('export backup includes valid and orphan bindings; import fallback displayed for file:// portability');
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const report={checks,checkCount:checks.length,screenshots,pageErrors:errors,externalRequests:requests,
    fixtureDiff:diff,aliasNamespace:namespace,secondRepo:JSON.parse(fs.readFileSync(path.join(ROOT,'dist/dag-gps/map.json'),'utf8')).meta};
  fs.writeFileSync(path.join(ROOT,'artifacts/refresh-browser.json'),JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify(report,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
