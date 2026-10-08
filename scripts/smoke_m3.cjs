#!/usr/bin/env node
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {pathToFileURL} = require('node:url');
const {chromium} = require(process.env.PLAYWRIGHT_DIR || '/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const ROOT = path.resolve(__dirname, '..');
const map = require('../maps/quest-coder/map.json');
const canonical = [
  {name:'locate', question:'where is magic link?', op:'LOCATE', from:'auth', ids:['auth']},
  {name:'dependencies', question:'dependencies of pyodide', op:'UPSTREAM', from:'browser-run', ids:['browser-run','game-domain']},
  {name:'dependents', question:'what depends on runner service', op:'DOWNSTREAM', from:'runner-service', ids:['runner-service','api','tests','tooling','app-shell','party-ui','screens','solve-ui']},
  {name:'path', question:'path from API routes to runner service', op:'PATH', from:'api', to:'runner-service', route:['api','runner-service']},
  {name:'file', question:'locate app/api/health/route.ts', op:'LOCATE', from:'app/api/health/route.ts', ids:['app/api/health/route.ts'], expanded:'api'},
];
(async()=>{
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport:{width:1920,height:1080}});
    const errors = [], requests = [], states = [];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('console',m=>{if(m.type()==='error') errors.push(m.text());});
    page.on('request',r=>{if(!r.url().startsWith('file:')) requests.push(r.url());});
    await page.goto(pathToFileURL(path.join(ROOT,'dist/quest-coder.html')).href);
    async function ask(question, click=false) {
      await page.locator('#ask').fill('');
      await page.locator('#ask').pressSequentially(question);
      if(click) await page.locator('#ask-submit').click();
      else await page.locator('#ask').press('Enter');
      return page.evaluate(()=>dagGps.state());
    }
    async function lit() {
      return page.locator('g.node:not(.faded)').evaluateAll(gs=>gs.map(g=>g.dataset.id).sort());
    }
    async function emph() {
      return page.locator('path.edge.emph').evaluateAll(ps=>ps.map(p=>p.dataset.e));
    }
    fs.mkdirSync(path.join(ROOT,'artifacts'),{recursive:true});
    for(const [i,c] of canonical.entries()) {
      const s = await ask(c.question, i%2===1);
      assert.equal(s.answer.operation.choice,c.op); assert.equal(s.route.op,c.op);
      assert.equal(s.route.from,c.from); assert.equal(s.focused,c.from);
      if(c.to) assert.equal(s.route.to,c.to);
      assert.deepEqual(s.route.path,c.route || null);
      assert.deepEqual(await lit(),(c.ids || c.route).slice().sort());
      assert.equal((await emph()).length,s.route.edges.length);
      if(c.expanded) assert.equal(s.expanded,c.expanded);
      assert.match(await page.locator('#answer').innerText(),/not calibrated correctness/);
      assert.ok(Number.isFinite(s.latencyMs));
      assert.equal(await page.locator('#answer [data-override]').count(),c.op==='PATH'?6:3);
      const screenshot = path.join(ROOT,`artifacts/m3-${c.name}.png`);
      await page.screenshot({path:screenshot});
      states.push({question:c.question,operation:c.op,target:c.from,path:s.route.path,latencyMs:s.latencyMs,screenshot});
    }
    // Stale highlights cleared, never act on uniform/tied speculative choices.
    for(const q of ['quantum teleporter','where is top bar']) {
      const s = await ask(q);
      assert.equal(s.answer.operation.choice,'NOT_SURE');assert.equal(s.route,null);assert.equal(s.focused,null);
      assert.equal(await page.locator('g.sel,g.rel-up,g.rel-down,g.endpoint-to').count(),0);
      assert.equal((await emph()).length,0);
      assert.equal(await page.locator('#answer [data-override]').count(),3);
    }
    // Explicit single-target override works while keeping scorer no/NOT_SURE honest.
    const choice = await page.locator('#answer [data-override]').first().getAttribute('data-override');
    await page.locator('#answer [data-override]').first().click();
    let s = await page.evaluate(()=>dagGps.state());
    assert.equal(s.route.from,choice);assert.equal(s.answer.yes,false);
    assert.match(await page.locator('#route-status').innerText(),/Explicit user override/);
    s = await ask('path from database to editor');
    assert.equal(s.answer.operation.choice,'PATH');assert.equal(s.answer.yes,true);
    assert.equal(s.route.path,null);assert.deepEqual(s.route.edges,[]);
    assert.match(await page.locator('#route-status').innerText(),/No directed route found/);
    assert.deepEqual(await lit(),['persistence','solve-ui']);assert.equal((await emph()).length,0);
    assert.equal(await page.locator('g.endpoint-to[data-id="solve-ui"]').count(),1);
    await page.screenshot({path:path.join(ROOT,'artifacts/m3-no-path.png')});
    // Both file endpoints matched independently, drawn as real IDs across layers.
    s = await ask('path from app/api/friends/route.ts to lib/friends-store.ts');
    assert.equal(s.answer.operation.choice,'PATH');assert.equal(s.view,'route');
    assert.deepEqual(s.route.path,['app/api/friends/route.ts','lib/friends-store.ts']);
    assert.deepEqual(await lit(),s.route.path.slice().sort());assert.equal((await emph()).length,1);
    assert.ok(s.route.edges.every(e=>map.file_edges.some(x=>x.from===e.from&&x.to===e.to&&x.type===e.type)));
    await page.screenshot({path:path.join(ROOT,'artifacts/m3-file-path.png')});
    await page.locator('g.node[data-id="lib/friends-store.ts"]').click();
    assert.equal((await page.evaluate(()=>dagGps.state())).focused,'lib/friends-store.ts');
    assert.match(await page.locator('#panel').innerText(),/lib\/friends-store.ts/);
    await page.locator('#btn-back').click();assert.equal((await page.evaluate(()=>dagGps.state())).view,'layers');
    s = await ask('path from API routes to lib/friends-store.ts');
    assert.equal(s.answer.operation.choice,'PATH');assert.equal(s.route.path,null);
    assert.deepEqual(s.route.edges,[]);assert.match(await page.locator('#route-status').innerText(),/mixed layer\/file endpoints unsupported/);
    // Abstained PATH: neither endpoint is acted on until both explicitly selected.
    s = await ask('path from mystery engine to database');
    assert.equal(s.answer.yes,false);assert.equal(s.route,null);
    await page.locator('[data-head="from_target"]').first().click();
    assert.equal((await page.evaluate(()=>dagGps.state())).route,null);
    await page.locator('[data-head="to_target"]').first().click();
    assert.ok((await page.evaluate(()=>dagGps.state())).route);
    // Boundary rejects corrupt scorer output without using its IDs.
    await page.evaluate(()=>{ const original=DagGpsScorer.validateResult; DagGpsScorer.validateResult=()=>{throw new Error('injected invalid contract');}; globalThis.restoreValidator=()=>{DagGpsScorer.validateResult=original;}; });
    s = await ask('where is magic link?');assert.equal(s.route,null);assert.equal(s.focused,null);
    assert.match(await page.locator('#answer').innerText(),/Invalid scorer result — no action/);
    await page.evaluate(()=>restoreValidator());
    // Long input treated as text; smaller screen keeps Ask visible and usable.
    await page.setViewportSize({width:1280,height:800});
    s = await ask('where is magic link?',true);assert.equal(s.route.from,'auth');
    await page.screenshot({path:path.join(ROOT,'artifacts/m3-1280.png')});
    assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
    const report={canonical:states,canonicalCount:states.length,checks:['unknown','ambiguous','stale clearing','single override','reverse unreachable','cross-layer file path','file inspect/back','mixed endpoints','both explicit PATH overrides','invalid boundary','1280 Ask'],pageErrors:errors,externalRequests:requests};
    fs.writeFileSync(path.join(ROOT,'artifacts/m3-browser.json'),JSON.stringify(report,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
