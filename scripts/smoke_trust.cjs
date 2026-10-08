#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),{pathToFileURL}=require('node:url');
const {chromium}=require(process.env.PLAYWRIGHT_DIR||'/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
const ROOT=path.resolve(__dirname,'..');
(async()=>{
 const browser=await chromium.launch(),checks=[],errors=[],requests=[],screenshots=[];
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});page.on('request',r=>{if(!/^(file|blob):/.test(r.url()))requests.push(r.url());});
  const go=async p=>page.goto(pathToFileURL(path.join(ROOT,p)).href);
  async function ask(q){await page.locator('#ask').fill('');await page.locator('#ask').pressSequentially(q);await page.locator('#ask').press('Enter');}
  async function shot(n){const f=path.join(ROOT,'artifacts/trust-'+n+'.png');await page.screenshot({path:f});screenshots.push(f);}
  await go('dist/quest-refresh/index.html');
  assert.match(await page.locator('#trust-summary').innerText(),/182 \/ 272 files scanned/);
  await page.locator('#trust-summary').click();
  assert.match(await page.locator('#trust-meta').innerText(),/749d8b5de490cc2e6a0c98c713fab3ab856da799/);
  assert.match(await page.locator('#trust-meta').innerText(),/Tours current/);

  checks.push('immutable snapshot, exact extraction scope/denominator and distinct evidence tiers visible');
  await page.locator('#trust-filter').selectOption('unsupported_dynamic_construct');
  assert.equal(await page.locator('.trust-finding').count(),8);
  await page.locator('#trust-path').fill('browser-runtime/run-worker.mjs');
  assert.equal(await page.locator('.trust-finding').count(),1);assert.match(await page.locator('.trust-finding').innerText(),/nonliteral import/);
  await page.locator('#trust-limits-box > summary').click();assert.match(await page.locator('#trust-limits').innerText(),/resolved lexical import ≠ curated source-supported runtime walkthrough ≠ inferred\/unverified/);await shot('evidence-tiers');await page.locator('#trust-limits-box > summary').click();await page.locator('aside').evaluate(e=>e.scrollTop=0);await shot('findings-1920');
  await page.locator('[data-trust-locate]').click();
  assert.equal((await page.evaluate(()=>dagGps.state())).focused,'browser-runtime/run-worker.mjs');
  await page.locator('#trust-summary').click();
  assert.match(await page.locator('#panel .trust-warning').innerText(),/nonliteral import/);
  checks.push('unsupported finding filters by real path and real-click navigation shows concrete contextual reason');
  await ask('locate browser-runtime/run-worker.mjs');
  assert.equal(await page.locator('#answer .trust-warning').getAttribute('data-trust-scope'),'context');assert.match(await page.locator('#answer .trust-warning').innerText(),/nonliteral import/);await shot('context-answer');
  await ask('impact of browser-runtime/run-worker.mjs');
  assert.equal(await page.locator('#impact-panel .trust-warning').getAttribute('data-trust-scope'),'context');assert.match(await page.locator('#impact-panel .trust-warning').innerText(),/browser-runtime\/run-worker.mjs/);await shot('context-impact');
  checks.push('real Ask and impact show traceable extraction finding, never a runtime percentage');
  await ask('impact of lib/runner-client.ts');
  const s=await page.evaluate(()=>dagGps.state());assert.equal(s.impact.directConsumers.length,3);assert.equal(s.impact.transitiveConsumers.length,1);assert.equal(s.impact.linkedTests.length,0);
  assert.match(await page.locator('#impact-panel .trust-warning').innerText(),/scripts\/deployment_smoke.mjs.*[\s\S]*\/api\/private-pack/);assert.match(await page.locator('#impact-coverage').innerText(),/Coverage unknown/);await shot('boundary-context');
  checks.push('unchanged runner-client impact retains source-audited counts and contextual finding on its real boundary witness');
  await ask('locate lib/runner-client.ts');assert.match(await page.locator('#answer .trust-warning').innerText(),/Repository-level uncertainty/);await shot('general-answer');await page.locator('#answer [data-trust-context]').click();
  assert.match(await page.locator('#trust-meta').innerText(),/Context paths: lib\/runner-client.ts/);
  await page.locator('#trust-filter').selectOption('resolved_source');assert.ok((await page.locator('.trust-finding').count())>0);assert.match(await page.locator('#trust-findings').innerText(),/resolved_lexical_import/);
  await page.locator('#trust-reset').click();await page.locator('#trust-filter').selectOption('external_dependency');await page.locator('#trust-path').fill('react');assert.match(await page.locator('#trust-findings').innerText(),/Not an unresolved local error/);await shot('external');
  checks.push('answer findings open scoped navigation; external imports separate from local resolution errors');
  await page.locator('#trust-filter').selectOption('unresolved_local_reference');await page.locator('#trust-path').fill('');assert.match(await page.locator('#trust-findings').innerText(),/\/api\/private-pack/);await shot('unresolved-http');
  await page.locator('#trust-filter').selectOption('non_source_target');await page.locator('#trust-path').fill('globals.css');assert.match(await page.locator('#trust-findings').innerText(),/has no source node/);await shot('non-source');
  checks.push('literal unresolved HTTP and resolved non-code targets carry concrete reasons, not import errors');
  await page.locator('#trust-path').fill('unknown-zebra-path');assert.match(await page.locator('#trust-findings').innerText(),/0 matching findings.*not proof of completeness/);
  await page.locator('#trust-summary').click();await ask('locate nonexistent-zebra.ts');assert.match(await page.locator('#answer .trust-warning').innerText(),/Repository-level uncertainty/);assert.equal((await page.evaluate(()=>dagGps.state())).focused,null);await shot('unknown');
  checks.push('unknown/unsupported paths have honest no-match and general limitation, no fabricated evidence');
  await ask('locate browser-runtime/run-worker.mjs');await page.setViewportSize({width:1280,height:800});await page.waitForTimeout(250);await shot('1280');
  assert.equal(await page.locator('aside').evaluate(e=>e.scrollWidth<=e.clientWidth+1),true);checks.push('1280 contextual warning and controls fit without horizontal sidebar clipping');
  await page.setViewportSize({width:1920,height:1080});await go('dist/quest-no-tours/index.html');
  assert.equal(await page.locator('#tour-select').isDisabled(),true);assert.match(await page.locator('#tour-select').getAttribute('title'),/Explicit --without-tours/);
  await ask('walk me through submitting code');assert.equal((await page.evaluate(()=>dagGps.state())).tour,null);assert.equal(await page.locator('[data-tour-evidence]').count(),0);
  await page.locator('#trust-summary').click();assert.match(await page.locator('#trust-meta').innerText(),/Tours omitted.*Explicit --without-tours/);await shot('omitted-tours');
  checks.push('explicit no-tour build has no stale evidence or natural-query tour; omission reason visible');
  await go('dist/dag-gps/index.html');await page.locator('#trust-summary').click();assert.match(await page.locator('#trust-meta').innerText(),/f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93/);assert.match(await page.locator('#trust-meta').innerText(),/Tours unavailable/);await page.locator('#trust-filter').selectOption('unsupported_dynamic_construct');assert.ok(await page.locator('.trust-finding').count());await shot('self-scope');
  checks.push('old self pin stays explicit, unsupported dynamic constructs and unavailable tours disclosed');
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  const result={checks,check_count:checks.length,screenshots,errors,externalRequests:requests};fs.writeFileSync(path.join(ROOT,'artifacts/trust-browser.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
