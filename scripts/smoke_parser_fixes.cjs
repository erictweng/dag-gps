'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_DIR || '/Users/aibert/projects/quest-coder-assist/node_modules/playwright');
(async () => {
  const input = JSON.parse(fs.readFileSync(0, 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
  const report = {cases: [], errors: [], external: []};
  page.on('pageerror', e => report.errors.push(String(e)));
  const origin = new URL(input.url).origin;
  page.on('request', r => { if (!r.url().startsWith(origin)) report.external.push(r.url()); });
  try {
    await page.goto(input.url);
    await page.waitForSelector('#project-select option', {state: 'attached'});
    for (const [repo, query, status, expected] of [
      ['honcho', 'where is src/reconciler/backfill.py.', 'matched', ['src/reconciler/backfill.py']],
      ['salesroom', 'where is events', 'needs-choice', ['src/lib/events.ts', 'folder-339c0fd4c4ebbcb5']],
      ['honcho', 'where is backfill', 'needs-choice', ['src/reconciler/backfill.py', 'src/reconciler/backfill.py#Backfill@33']],
      ['honcho', 'where is db', 'matched', ['src/db.py']],
      ['honcho', 'where is configuration', 'needs-choice', ['src/schemas/configuration.py']],
      ['salesroom', 'where is folder events', 'matched', ['folder-339c0fd4c4ebbcb5']]
    ]) {
      if (await page.inputValue('#project-select') !== input.projects[repo]) {
        const loaded = page.waitForResponse(r => r.url().includes('/snapshot') && r.request().method() === 'GET');
        await page.selectOption('#project-select', input.projects[repo]);
        await loaded;
      }
      await page.waitForSelector('#graph .node');
      await page.fill('#question', query);
      const response = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
      await page.press('#question', 'Enter');
      const packet = await (await response).json();
      assert.equal(packet.status, status, query);
      const ids = status === 'matched' ? packet.selectedNodeIds : packet.alternatives.map(a => a.nodeId);
      for (const id of expected) assert.ok(ids.includes(id), query + ': ' + id);
      await page.waitForFunction(() => !document.querySelector('#answer-status').textContent.includes('Asking'));
      // Wait for the actual answer rendering, not merely HTTP completion.
      await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent.includes(reason), packet.reason);
      const screenshot = path.join(input.out, String(report.cases.length + 1) + '-' + repo + '.png');
      await page.screenshot({path: screenshot, fullPage: true});
      report.cases.push({repo, query, status: packet.status, operation: packet.operation,
        selected: packet.selectedNodeIds, alternatives: packet.alternatives, screenshot});
    }
    assert.equal(report.cases.length, 6);
    assert.deepEqual(report.errors, []); assert.deepEqual(report.external, []);
    fs.writeFileSync(path.join(input.out, 'report.json'), JSON.stringify(report, null, 2) + '\n');
    console.log('Real-app checks: 6/6, no page errors or external requests');
  } finally { await browser.close(); }
})().catch(e => { console.error(e.message); process.exitCode = 1; });
