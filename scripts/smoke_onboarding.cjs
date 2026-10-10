#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url'),{execFileSync,spawnSync}=require('node:child_process');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const ROOT=path.resolve(__dirname,'..'),E=require('../web/layer-editor.js');
const QUEST='749d8b5de490cc2e6a0c98c713fab3ab856da799',SELF='a5b02554e479b5184204ab6aa7c7190d6605fe91';
function py(args,name){const r=spawnSync('python3',args,{cwd:ROOT,encoding:'utf8'});fs.writeFileSync(path.join(ROOT,'artifacts/onboarding-'+name+'.log'),(r.stdout||'')+(r.stderr||''));assert.equal(r.status,0,'python '+args.join(' ')+'\n'+r.stderr);return r;}
function prepare(){fs.mkdirSync(path.join(ROOT,'artifacts'),{recursive:true});
 py(['scripts/draft_layers.py','--repo',(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),'--ref',QUEST,'--tops','app','components','lib','proxy.ts','scripts','browser-runtime','runner','--out','artifacts/onboarding-quest-draft.json'],'quest-draft');
 py(['scripts/draft_layers.py','--repo','.','--ref',SELF,'--out','artifacts/onboarding-self-all-source-draft.json'],'self-all-source');
 const full=JSON.parse(fs.readFileSync(path.join(ROOT,'artifacts/onboarding-self-all-source-draft.json')));
 assert.deepEqual(full.diagnostics.unresolved,[['scripts/smoke_refresh.cjs','UNRESOLVED:../artifacts/refresh-fixture.json']]);
 // Declared supported scan excludes ONE generator consumer with an untracked runtime fixture.
 // Full 48-file assignment inventory remains. No extractor guessing or generated fixture injected.
 const tops=full.source_files.filter(p=>p!=='scripts/smoke_refresh.cjs');
 py(['scripts/draft_layers.py','--repo','.','--ref',SELF,'--tops',...tops,'--out','maps/dag-gps/onboarding-draft.json'],'self-draft');
 for(const [name,draft]of [['quest','artifacts/onboarding-quest-draft.json'],['dag-gps','maps/dag-gps/onboarding-draft.json']])py(['scripts/render_layer_editor.py','--draft',draft,'--out','dist/onboarding-'+name+'.html'],'render-'+name);
}
(async()=>{
 prepare();const browser=await chromium.launch(),checks=[],screenshots=[],errors=[],requests=[],repos=[];
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080},acceptDownloads:true});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>{if(!/^(file|blob):/.test(r.url()))requests.push(r.url());});page.on('dialog',d=>d.accept());
  const file=p=>pathToFileURL(path.join(ROOT,p)).href;
  async function shot(name){const target=path.join(ROOT,'artifacts/onboarding-'+name+'.png');await page.screenshot({path:target,fullPage:true});screenshots.push(target);}
  async function download(button,target){const pending=page.waitForEvent('download');await page.locator(button).click();const d=await pending;await d.saveAs(path.join(ROOT,target));return JSON.parse(fs.readFileSync(path.join(ROOT,target),'utf8'));}
  async function saved(){return download('#save-draft','artifacts/onboarding-current-draft.json');}
  async function selectLayer(id){await page.locator('#layers').selectOption([id]);}
  async function selectFile(p){await page.locator('#search').fill(p);await page.getByRole('checkbox',{name:'Select '+p,exact:true}).check();}
  async function reset(){await page.locator('#reset').click();assert.equal(await page.locator('#review').isChecked(),false);}
  for(const cfg of [
   {name:'dag-gps',repo:'.',draft:'maps/dag-gps/onboarding-draft.json',file:'web/impact.js',renameFolder:'scripts',ask:'scripts/build_map.py',demo:'dist/onboarding-dag-gps'},
   {name:'quest',repo:(process.env.DAG_GPS_QUEST_REPO||'/Users/aibert/projects/quest-coder'),draft:'artifacts/onboarding-quest-draft.json',file:'lib/runner-client.ts',renameFolder:'lib',ask:'lib/runner-client.ts',demo:'dist/onboarding-quest'}]){
   const base=JSON.parse(fs.readFileSync(path.join(ROOT,cfg.draft))),owner=base.layers.find(l=>l.files.includes(cfg.file)),renameLayer=base.layers.find(l=>l.label===cfg.renameFolder);
   assert.equal(E.findings(base).valid,true);assert.equal(base.reviewed,false);
   await page.goto(file('dist/onboarding-'+cfg.name+'.html'));assert.match(await page.locator('#provenance').innerText(),new RegExp(base.commit));assert.equal(await page.locator('#export').isEnabled(),false);
   await shot(cfg.name+'-initial-1920');checks.push(cfg.name+': pinned unapproved folder draft, complete inventory and export disabled without review');
   await selectLayer(renameLayer.id);await page.locator('#label').fill('Pipeline sample label');await page.locator('#rename').click();let d=await saved();assert.equal(d.layers.find(l=>l.id===renameLayer.id).label,'Pipeline sample label');assert.equal(d.layers.length,base.layers.length);await page.locator('#undo').click();d=await saved();assert.equal(d.layers.find(l=>l.id===renameLayer.id).label,renameLayer.label);
   await selectLayer(owner.id);await selectFile(cfg.file);assert.equal(await page.locator('#files label.file').count(),1);await page.locator('#split-label').fill('Review sample split');await page.locator('#split').click();
   d=await saved();const split=d.layers.find(l=>l.id===owner.id+'-split-1');assert.deepEqual(split.files,[cfg.file]);assert.ok(d.reference_warnings.length);assert.deepEqual(d.file_edges,base.file_edges);
   if(cfg.name==='quest'){assert.ok(E.findings(d).cycles.length);assert.match(await page.locator('#findings').innerText(),/LAYER CYCLE/);assert.match(await page.locator('#findings').innerText(),/lib\/runner-client.ts/);assert.equal(await page.locator('#export').isEnabled(),false);await shot('quest-real-cycle-evidence');checks.push('quest: deliberate real runner-client split exposes grouping cycle with actual source pairs; export blocked, file links intact');}
   await page.locator('#layers').selectOption([owner.id,split.id]);await page.locator('#merge').click();d=await saved();assert.equal(E.findings(d).valid,true);assert.deepEqual(d.file_edges,base.file_edges);assert.ok(d.reference_warnings.some(w=>w.includes(split.id)));
   checks.push(cfg.name+': real search/file selection, stable-ID rename/undo, split/merge, manual migration warnings and retained file links');
   // Real move and recovery; empty layers and conflicts remain visible, not silently removed.
   await selectFile(cfg.file);const other=base.layers.find(l=>l.id!==owner.id&&l.files.length>0);await page.locator('#target').selectOption(other.id);await page.locator('#move').click();d=await saved();assert.ok(d.layers.find(l=>l.id===other.id).files.includes(cfg.file));assert.equal(E.findings(d).double.length,0);await page.locator('#undo').click();d=await saved();assert.ok(d.layers.find(l=>l.id===owner.id).files.includes(cfg.file));
   // Deletion is deliberately not an automatic reassignment and must block export.
   await selectLayer(owner.id);await page.locator('#delete').click();d=await saved();assert.ok(E.findings(d).unmapped.includes(cfg.file));assert.equal(await page.locator('#export').isEnabled(),false);await page.locator('#undo').click();checks.push(cfg.name+': real move/undo and delete/unmapped/undo; no silent reassignment');
   // Malformed imports are atomically refused; markup remains literal text.
   await page.locator('#import').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{invalid')});await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Import rejected'));const before=await saved();
   const wrong={...before,repo:'wrong/repo'};await page.locator('#import').setInputFiles({name:'wrong.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(wrong))});await page.waitForFunction(()=>document.getElementById('status').textContent.includes('Repository/commit mismatch'));assert.deepEqual(await saved(),before);
   const malicious=E.copy(base);malicious.layers[0].label='</script><img src="https://invalid.example/x" onerror="window.onboardingPwned=1">';await page.locator('#import').setInputFiles({name:'markup.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(malicious))});await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Edit applied'));assert.equal(await page.evaluate(()=>window.onboardingPwned),undefined);assert.equal(await page.locator('img').count(),0);assert.equal((await saved()).layers[0].label,malicious.layers[0].label);
   await reset();d=await saved();assert.deepEqual(d,base);checks.push(cfg.name+': malformed/repo-mismatched import rejected without edit; malicious markup remains data; reset restores pinned proposal');
   // Final exported demo: actual UI label edit, reviewed checkbox, actual browser download.
   await selectLayer(renameLayer.id);await page.locator('#label').fill(cfg.name==='quest'?'Library folder (worker review sample)':'Build scripts (worker review sample)');await page.locator('#rename').click();await page.locator('#review').check();assert.equal(await page.locator('#export').isEnabled(),true);
   await page.setViewportSize({width:1280,height:800});await shot(cfg.name+'-review-1280');assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await page.setViewportSize({width:1920,height:1080});await shot(cfg.name+'-review-1920');
   const exportedPath='artifacts/onboarding-'+cfg.name+'-layers.json',exported=await download('#export',exportedPath);assert.equal(exported.onboarding.reviewed,true);assert.equal(exported.layers.find(l=>l.id===renameLayer.id).id,renameLayer.id);
   await page.locator('#import').setInputFiles(path.join(ROOT,exportedPath));await page.waitForFunction(()=>document.getElementById('status').textContent.startsWith('Edit applied'));assert.equal(await page.locator('#review').isChecked(),false);assert.equal(await page.locator('#export').isEnabled(),false);checks.push(cfg.name+': 1280/1920 no clipping, explicit review and actual download, reviewed reimport clears confirmation');
   py(['scripts/build_project.py','--repo',cfg.repo,'--ref',base.commit,'--layers',exportedPath,'--tops',...base.tops,'--without-tours','--out-dir',cfg.demo],'build-'+cfg.name);
   const map=JSON.parse(fs.readFileSync(path.join(ROOT,cfg.demo,'map.json')));assert.equal(map.meta.snapshot_commit,base.commit);assert.equal(map.meta.counts.files,base.source_files.length);assert.deepEqual(map.file_edges.map(e=>[e.from,e.to,e.type]),base.file_edges.map(e=>[e.from,e.to,e.type]));assert.deepEqual(map.diagnostics.unmapped,[]);assert.deepEqual(map.diagnostics.duplicate_assignments,{});assert.equal(map.diagnostics.layer_cycle,null);
   // Corrupt a copy of the downloaded spec, verify rejected rebuild preserves all published bytes.
   const outputs=['map.json','index.html','diff.json','report.json'],prior=outputs.map(p=>fs.readFileSync(path.join(ROOT,cfg.demo,p)));const bad=E.copy(exported);bad.layers[1].files.push(bad.layers[0].files[0]);const badPath='artifacts/onboarding-invalid-'+cfg.name+'.json';fs.writeFileSync(path.join(ROOT,badPath),JSON.stringify(bad));const rejected=spawnSync('python3',['scripts/build_project.py','--repo',cfg.repo,'--ref',base.commit,'--layers',badPath,'--tops',...base.tops,'--without-tours','--out-dir',cfg.demo],{cwd:ROOT,encoding:'utf8'});assert.notEqual(rejected.status,0);fs.writeFileSync(path.join(ROOT,'artifacts/onboarding-rejected-'+cfg.name+'.log'),rejected.stderr);outputs.forEach((p,i)=>assert.deepEqual(fs.readFileSync(path.join(ROOT,cfg.demo,p)),prior[i]));
   await page.goto(file(cfg.demo+'/index.html'));await page.locator('#ask').fill('locate '+cfg.ask);await page.locator('#ask').press('Enter');let s=await page.evaluate(()=>dagGps.state());assert.equal(s.answer.yes,true);assert.equal(s.route.from,cfg.ask);assert.equal(s.expanded,exported.layers.find(l=>l.files.includes(cfg.ask)).id);await shot(cfg.name+'-built-ask');checks.push(cfg.name+': downloaded JSON built offline map, exact real-file Ask, invalid ownership rebuild preserves all four artifacts');
   repos.push({repo:base.repo,commit:base.commit,files:base.source_files.length,layers:exported.layers.length,fileEdges:map.file_edges.length,layerEdges:map.edges.length,trust:map.trust,exportedPath,demo:cfg.demo,semanticApproval:'Worker automated review sample only; Eric semantic approval pending'});
  }
  // Visible full-discovery failure retained as a separate diagnostic draft, never falsely approved.
  py(['scripts/render_layer_editor.py','--draft','artifacts/onboarding-self-all-source-draft.json','--out','dist/onboarding-dag-gps-all-source.html'],'render-self-failure');await page.goto(file('dist/onboarding-dag-gps-all-source.html'));assert.match(await page.locator('#findings').innerText(),/UNRESOLVED.*refresh-fixture/);assert.equal(await page.locator('#export').isEnabled(),false);await shot('self-all-source-blocked');checks.push('new self full discovery fails closed on real runtime-generated JSON reference; explicit 47-JS-input supported scope retains full 48-file inventory');
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const report={checks,checkCount:checks.length,screenshots,pageErrors:errors,externalRequests:requests,repos,semanticApproval:'Eric approval still required; automation is not a human architecture judgement'};fs.writeFileSync(path.join(ROOT,'artifacts/onboarding-browser.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({checks:checks.length,screenshots:screenshots.length,errors:errors.length,requests:requests.length,repos:repos.map(({trust,...rest})=>rest)},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
