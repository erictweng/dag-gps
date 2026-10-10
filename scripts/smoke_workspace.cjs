#!/usr/bin/env node
// M2.3 workspace UI smoke. Usage: node scripts/smoke_workspace.cjs PRIVATE_URL REPO_URL BAD_REPO_URL OUT_DIR
// Drives the real page: import -> ask (type + Enter) -> highlight -> choice -> Escape -> file/graph selection
// -> failed import recovery, at 1280/1920/390 px, with axe, no external requests and no page errors.
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const PW = process.env.PLAYWRIGHT_DIR || '/Users/aibert/projects/quest-coder-assist/node_modules/playwright';
const AXE = process.env.AXE_CORE_PATH || '/Users/aibert/projects/quest-coder-assist/node_modules/axe-core/axe.min.js';
const {chromium} = require(PW);
const [url, repoUrl, badRepoUrl, outDir, fixtureRoot] = process.argv.slice(2);

(async () => {
  fs.mkdirSync(outDir, {recursive: true});
  const origin = new URL(url).origin;
  const browser = await chromium.launch();
  const context = await browser.newContext({viewport: {width: 1280, height: 900}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  const report = {checks: [], external: [], errors: [], axe: [], widths: [], screenshots: []};
  let contextRequests = 0;
  page.on('request', r => { if (r.url().endsWith('/context')) contextRequests++; });
  page.on('request', r => { if (!r.url().startsWith(origin)) report.external.push(r.url()); });
  page.on('console', m => { if (m.type() === 'error') report.errors.push(m.text()); });
  page.on('pageerror', e => report.errors.push(String(e)));
  const check = (name, value) => { report.checks.push({name, value}); };
  const states = () => page.evaluate(() => {
    const out = {seed: [], on: [], dim: 0, plain: 0, edgesOn: 0};
    for (const g of document.querySelectorAll('#graph .node')) {
      const s = g.getAttribute('data-state');
      if (s === 'seed') out.seed.push(g.dataset.id); else if (s === 'on') out.on.push(g.dataset.id);
      else if (s === 'dim') out.dim++; else out.plain++;
    }
    out.edgesOn = document.querySelectorAll('#graph .edge[data-state=on]').length;
    return out;
  });
  const statusText = () => page.textContent('#answer-status');
  async function askTyped(q) {
    await page.fill('#question', '');
    await page.locator('#question').pressSequentially(q, {delay: 2});
    const before = await page.evaluate(() => document.getElementById('answer-status').textContent + '|' + document.getElementById('answer-reason').textContent);
    await page.keyboard.press('Enter');
    await page.waitForFunction(prev => document.getElementById('answer-status').textContent + '|' +
      document.getElementById('answer-reason').textContent !== prev, before);
  }

  await page.goto(url);
  assert.equal(new URL(page.url()).hash, '', 'session key removed from the address bar');

  async function openImport() {
    if (!(await page.evaluate(() => document.getElementById('import-box').open))) await page.click('#import-box summary');
  }
  // Import through the UI (the box opens itself when there are no projects).
  await page.waitForFunction(() => document.getElementById('project-info').textContent.length > 0);
  check('empty-state', await page.textContent('#project-info'));
  await openImport();
  await page.fill('#repo-url', repoUrl);
  await page.click('#import-form button');
  await page.waitForFunction(() => /^Imported|^Import failed/.test(document.getElementById('import-status').textContent), null, {timeout: 120000});
  const imported = await page.textContent('#import-status');
  assert.ok(imported.startsWith('Imported'), imported);
  await page.waitForSelector('#graph svg .node');
  const nodeCount = await page.locator('#graph .node').count();
  check('imported', {imported, nodeCount, lanes: await page.locator('#graph .lane-label').allTextContents()});
  assert.ok(nodeCount >= 5);
  assert.ok((await page.locator('#graph .lane-label').allTextContents()).some(t => t.startsWith('lib')), 'lanes use folder labels');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'question', 'focus moves to the question after import');

  // Confident match: exact packet selection highlighted, everything else dimmed.
  await askTyped('what depends on lib/util.py');
  let s = await states();
  check('dependents', {status: await statusText(), s});
  assert.match(await statusText(), /^Found · downstream · potentially affected/);
  assert.deepEqual(s.seed, ['lib/util.py']);
  assert.deepEqual(new Set(s.on), new Set(['lib/core.py', 'app/main.py', 'tools/cli.py']));
  assert.ok(s.dim > 0 && s.plain === 0 && s.edgesOn >= 3);
  const results = await page.locator('#results li').allInnerTexts();
  assert.ok(results.some(t => t.includes('via app/main.py → lib/core.py → lib/util.py')), 'witness chain shown');
  report.screenshots.push(path.join(outDir, 'dependents-1280.png'));
  await page.screenshot({path: report.screenshots.at(-1), fullPage: true});

  // M3: source reads are revision-bound; agent export is opt-in, never automatic.
  await page.locator('#results button').first().click();
  await page.click('#view-source');
  await page.waitForSelector('#source-lines li');
  assert.match(await page.textContent('#source-meta'), /Commit.*SHA-256/);
  assert.match(await page.textContent('#source-lines'), /from lib import core|Z = 1/);
  assert.ok(await page.isDisabled('#prepare-context'));
  assert.equal(contextRequests, 0, 'no context request before explicit consent');
  assert.equal(await page.inputValue('#context-json'), '');
  await page.check('#agent-consent');
  const exported = page.waitForResponse(r => r.url().endsWith('/context') && r.request().method() === 'POST');
  await page.click('#prepare-context');
  const bundle = await (await exported).json();
  await page.waitForFunction(() => document.getElementById('context-json').value.length > 0);
  assert.deepEqual(JSON.parse(await page.inputValue('#context-json')), bundle);
  const f = bundle.context.files.find(f => f.start !== null);
  const citation = {path: f.path, sha256: f.sha256, start: f.start, end: f.start};
  const hostileText = '<img src=x onerror=globalThis.__dagInjected=1> Observed source.';
  const explanation = {schema: 'dag-gps-explanation/v1', requestId: bundle.packet.requestId,
    projectId: bundle.packet.projectId, snapshotId: bundle.packet.snapshotId,
    packetSha256: bundle.context.packetSha256, agent: {name: 'Fixture agent', model: null},
    paragraphs: [{text: hostileText, inferred: false, citations: [citation]},
      {text: 'This may be a shared dependency.', inferred: true, citations: []}],
    suggestedRelationships: [{from: 'app/main.py', to: 'lib/util.py', type: 'possible coupling',
      reason: 'A suggestion, not an observed import.', citations: [citation]}],
    limitations: ['Synthetic test only.'], usage: {inputTokens: null, outputTokens: null}};
  const edgeCount = await page.locator('#graph .edge').count();
  await page.fill('#explanation-json', JSON.stringify(explanation));
  await page.click('#attach-explanation');
  await page.waitForSelector('#explanation-list article');
  assert.match(await page.textContent('#explanation-list'), /Agent inference/);
  assert.match(await page.textContent('#explanation-list'), /Suggested \(unverified\) relationships/);
  assert.match(await page.textContent('#explanation-list'), /unknown/);
  assert.ok((await page.textContent('#explanation-list')).includes(hostileText));
  assert.equal(await page.locator('#explanation-list img').count(), 0);
  assert.equal(await page.evaluate(() => globalThis.__dagInjected || null), null);
  assert.equal(await page.locator('#graph .edge').count(), edgeCount);
  await page.locator('#explanation-list .citation').first().click();
  await page.waitForFunction(p => document.getElementById('source-meta').textContent.includes(p), f.path);
  assert.equal(await page.getAttribute('#source-lines', 'start'), String(f.start));
  await page.fill('#explanation-json', JSON.stringify({...explanation, packetSha256: '0'.repeat(64)}));
  const rejected = page.waitForResponse(r => r.url().endsWith('/explanations') && r.status() === 422);
  await page.click('#attach-explanation');
  await rejected;
  await page.waitForFunction(() => document.getElementById('agent-error').textContent.length > 0);
  assert.equal(await page.locator('#explanation-list article').count(), 1);
  assert.equal(await page.locator('#graph .edge').count(), edgeCount);
  report.errors = report.errors.filter(e => !/Failed to load resource:.*422/.test(e));
  await page.fill('#explanation-json', '{invalid');
  await page.click('#attach-explanation');
  await page.waitForFunction(() => document.getElementById('agent-error').textContent.length > 0);
  // Corrupt disk records are reported only as a warning count, never rendered.
  if (fixtureRoot) {
    const directory = path.join(fixtureRoot, 'projects', bundle.packet.projectId, 'explanations', bundle.packet.snapshotId);
    fs.writeFileSync(path.join(directory, 'invalid.json'), JSON.stringify({schema: 'HOSTILE_INVALID_RECORD'}));
    await page.click('#prepare-context');
    await page.waitForFunction(() => document.getElementById('explanation-warning').textContent.includes('1 invalid'));
    assert.ok(!(await page.textContent('body')).includes('HOSTILE_INVALID_RECORD'));
  }
  // Revoking consent clears exports; keyboard copy has a selectable-text fallback.
  await page.evaluate(() => Object.defineProperty(navigator, 'clipboard', {value: undefined, configurable: true}));
  await page.focus('#copy-context');
  await page.keyboard.press('Enter');
  await page.waitForFunction(() => document.getElementById('copy-status').textContent.includes('JSON selected'));
  assert.equal(await page.evaluate(() => document.activeElement.id), 'context-json');
  assert.ok(await page.evaluate(() => document.getElementById('context-json').selectionEnd > 0));
  await page.uncheck('#agent-consent');
  assert.ok(await page.isDisabled('#prepare-context'));
  assert.equal(await page.inputValue('#context-json'), '');

  let releaseContext;
  const contextGate = new Promise(resolve => { releaseContext = resolve; });
  await page.route('**/context', async route => {
    const response = await route.fetch();
    await contextGate;
    await route.fulfill({response});
  });
  await page.check('#agent-consent');
  const pendingContext = page.waitForRequest(r => r.url().endsWith('/context'));
  await page.click('#prepare-context');
  await pendingContext;
  await page.uncheck('#agent-consent');
  const returnedContext = page.waitForResponse(r => r.url().endsWith('/context'));
  releaseContext();
  await returnedContext;
  await page.waitForTimeout(50);
  assert.equal(await page.inputValue('#context-json'), '', 'late export stays hidden after consent is revoked');
  assert.ok(await page.isHidden('#context-export'));
  await page.unroute('**/context');
  check('m3-agent-evidence', {source: f.path, edgeCount, inert: true, consent: true});
  report.screenshots.push(path.join(outDir, 'agent-evidence-1280.png'));
  await page.screenshot({path: report.screenshots.at(-1), fullPage: true});

  // Ambiguous: nothing highlighted or dimmed until the user chooses.
  await askTyped('helpers.py');
  s = await states();
  check('ambiguous', {status: await statusText(), s});
  assert.match(await statusText(), /choose one/);
  assert.equal(s.seed.length + s.on.length + s.dim, 0, 'no dimming around a guess');
  assert.equal(await page.locator('#choices button').count(), 2);
  await page.locator('#choices button').nth(1).click();
  await page.waitForFunction(() => document.querySelectorAll('#graph .node[data-state=on], #graph .node[data-state=seed]').length === 1);
  check('chosen', {status: await statusText(), s: await states()});

  // Escape clears every highlight and returns focus to the question.
  await page.keyboard.press('Escape');
  s = await states();
  check('escape', s);
  assert.equal(s.seed.length + s.on.length + s.dim, 0);
  assert.equal(await page.evaluate(() => document.activeElement.id), 'question');

  // Keyboard file selection from the list: details + direct-link highlight.
  await page.fill('#file-filter', 'core');
  await page.locator('#file-list button', {hasText: 'lib/core.py'}).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('#detail:not([hidden])');
  check('file-detail', {path: await page.textContent('#detail-path'), group: await page.textContent('#detail-group'),
    focus: await page.evaluate(() => document.activeElement.id), s: await states(),
    out: await page.locator('#detail-out li').allInnerTexts(), inc: await page.locator('#detail-in li').allInnerTexts()});
  assert.equal(await page.textContent('#detail-path'), 'lib/core.py');
  assert.equal(await page.textContent('#detail-group'), 'lib');
  assert.equal(await page.evaluate(() => document.activeElement.id), 'detail-heading');
  assert.deepEqual((await states()).seed, ['lib/core.py']);
  // Detail action runs a real query.
  await page.click('#detail-dependencies');
  await page.waitForFunction(() => /upstream/.test(document.getElementById('answer-status').textContent));
  // Graph click selects a node.
  await page.keyboard.press('Escape');
  await page.locator('#graph .node[data-id="tools/cli.py"]').click();
  await page.waitForFunction(() => document.getElementById('detail-path').textContent === 'tools/cli.py');
  // Unmapped inventory file: details without a fake graph highlight.
  await page.fill('#file-filter', 'README');
  await page.locator('#file-list button', {hasText: 'README.md'}).click();
  assert.equal(await page.textContent('#detail-group'), 'Not mapped');
  assert.equal((await states()).dim, 0);
  await page.fill('#file-filter', '');

  // Unmapped text is still readable; large files paginate without duplicate lines.
  await page.fill('#file-filter', 'long.txt');
  await page.locator('#file-list button').click();
  await page.click('#view-source');
  await page.waitForFunction(() => document.querySelectorAll('#source-lines li').length === 200);
  await page.click('#source-more');
  await page.waitForFunction(() => document.querySelectorAll('#source-lines li').length === 240);
  assert.ok(await page.isHidden('#source-more'));
  await page.fill('#file-filter', 'binary.dat');
  await page.locator('#file-list button').click();
  const expectedMetadata = page.waitForResponse(r => r.url().endsWith('/source') && r.status() === 400);
  await page.click('#view-source');
  await expectedMetadata;
  await page.waitForFunction(() => document.getElementById('source-error').textContent === 'metadata only');
  // Chromium logs the expected 400 as a resource error; exclude just that expected status.
  report.errors = report.errors.filter(e => !/Failed to load resource:.*400/.test(e));
  await page.fill('#file-filter', '');

  // Hostile names stay inert text.
  const hostile = await page.locator('#file-list button', {hasText: 'onerror'}).count();
  check('hostile', {rows: hostile, injected: await page.evaluate(() => globalThis.__dagInjected || null),
    images: await page.locator('img').count()});
  assert.ok(hostile >= 1);
  assert.equal(await page.evaluate(() => globalThis.__dagInjected || null), null);
  assert.equal(await page.locator('img').count(), 0);

  // Failed import keeps the loaded project usable and the form retryable.
  await openImport();
  await page.fill('#repo-url', badRepoUrl);
  await page.click('#import-form button');
  await page.waitForFunction(() => /^Import failed/.test(document.getElementById('import-status').textContent), null, {timeout: 60000});
  check('failed-import', {status: await page.textContent('#import-status'), nodes: await page.locator('#graph .node').count(),
    buttonEnabled: await page.isEnabled('#import-form button')});
  assert.equal(await page.locator('#graph .node').count(), nodeCount);
  assert.ok(await page.isEnabled('#import-form button'));
  await askTyped('lib/core.py');
  assert.match(await statusText(), /^Found/);

  // CSP actually blocks inline script in the real page.
  const cspBlocked = await page.addScriptTag({content: 'globalThis.__dagInline = 1;'}).then(() => false, () => true);
  check('csp-blocks-inline', {blocked: cspBlocked, flag: await page.evaluate(() => globalThis.__dagInline || null)});
  assert.equal(cspBlocked, true);
  report.errors = report.errors.filter(e => !/Content Security Policy/.test(e));

  // Widths, reduced motion and axe. axe-core is injected, so this audit context bypasses CSP;
  // the app page above ran under the real CSP.
  const auditContext = await browser.newContext({viewport: {width: 1280, height: 900}, reducedMotion: 'reduce', bypassCSP: true});
  const audit = await auditContext.newPage();
  audit.on('request', r => { if (!r.url().startsWith(origin)) report.external.push(r.url()); });
  audit.on('pageerror', e => report.errors.push(String(e)));
  await audit.goto(url);
  await audit.waitForSelector('#graph svg .node');
  await audit.fill('#question', 'what depends on lib/util.py');
  await audit.keyboard.press('Enter');
  await audit.waitForSelector('#graph .node[data-state=seed]');
  await audit.locator('#results button').first().click();
  await audit.check('#agent-consent');
  await audit.click('#prepare-context');
  await audit.waitForFunction(() => document.getElementById('context-json').value.length > 0);
  const auditBundle = JSON.parse(await audit.inputValue('#context-json'));
  const auditExplanation = {...explanation, requestId: auditBundle.packet.requestId,
    packetSha256: auditBundle.context.packetSha256};
  await audit.fill('#explanation-json', JSON.stringify(auditExplanation));
  await audit.click('#attach-explanation');
  await audit.waitForSelector('#explanation-list article');
  await audit.locator('#explanation-list .citation').first().click();
  await audit.waitForSelector('#source-lines li');
  for (const [width, height] of [[1920, 1080], [1280, 900], [390, 844]]) {
    await audit.setViewportSize({width, height});
    await audit.waitForTimeout(150);
    const overflow = await audit.evaluate(() => ({doc: document.documentElement.scrollWidth, view: innerWidth}));
    report.widths.push({width, overflow});
    assert.ok(overflow.doc <= overflow.view, 'no horizontal page overflow at ' + width);
    const shot = path.join(outDir, 'workspace-' + width + '.png');
    await audit.screenshot({path: shot, fullPage: true});
    report.screenshots.push(shot);
    if (fs.existsSync(AXE)) {
      if (!(await audit.evaluate(() => typeof axe !== 'undefined'))) await audit.addScriptTag({path: AXE});
      const result = await audit.evaluate(() => axe.run(document, {runOnly: {type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21aa']}}));
      report.axe.push({width, violations: result.violations.map(v => ({id: v.id, nodes: v.nodes.slice(0, 3).map(n => n.target)}))});
    } else report.axe.push({width, missing: AXE});
  }
  report.reducedMotion = await audit.evaluate(() => matchMedia('(prefers-reduced-motion: reduce)').matches);
  fs.writeFileSync(path.join(outDir, 'report.json'), JSON.stringify(report, null, 2) + '\n');
  await browser.close();
  assert.deepEqual(report.external, [], 'no external requests');
  assert.deepEqual(report.errors, [], 'no page/console errors');
  for (const a of report.axe) {
    assert.ok(!a.missing, 'axe-core unavailable: ' + a.missing);
    assert.deepEqual(a.violations, [], 'axe violations at ' + a.width + ': ' + JSON.stringify(a.violations));
  }
  console.log(JSON.stringify({ok: true, checks: report.checks.length, widths: report.widths, axe: report.axe}));
})().catch(error => { console.error(error); process.exit(1); });
