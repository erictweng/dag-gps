'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_DIR || 'playwright');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = []; page.on('pageerror', e => errors.push(String(e)));
    await page.goto(input.url);
    if (!await page.evaluate(() => document.querySelector('#import-box').open)) await page.click('#import-box summary');
    await page.fill('#repo-url', 'https://github.com/' + input.repo);
    await page.fill('#repo-commit', input.pin);
    const start = performance.now();
    await page.click('#import-form button');
    await page.waitForFunction(() => /^Imported|^Import failed/.test(document.querySelector('#import-status').textContent), null, {timeout: 240000});
    const status = await page.textContent('#import-status');
    const importMs = performance.now() - start;
    assert.ok(status.startsWith('Imported'), status);
    await page.waitForFunction(() => !document.querySelector('#import-form button').disabled);
    await page.waitForSelector('#graph .node');
    await page.screenshot({path: path.join(input.out, 'import.png')});
    const results = [];
    for (const [i, query] of (input.importOnly ? [] : ['where is src', 'what uses src/components', 'what does src use']).entries()) {
      await page.click('#clear'); await page.fill('#question', query);
      const response = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
      await page.press('#question', 'Enter');
      const packet = await (await response).json();
      assert.ok(packet.selectedNodeIds, JSON.stringify(packet));
      // Honcho has no src/components; an honest no-match/choice is required.
      if (!(input.repo.includes('honcho') && query.includes('src/components'))) {
        assert.ok(['matched', 'needs-choice'].includes(packet.status), query);
        if (packet.status === 'needs-choice') assert.ok(packet.alternatives.length > 1, query);
      }
      await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent === reason, packet.reason);
      await page.screenshot({path: path.join(input.out, 'question-' + (i+1) + '.png')});
      results.push({query, packet});
      if (packet.status === 'needs-choice' && !query.includes('src/components')) {
        const choice = packet.alternatives.find(a => a.reason.endsWith(': src'));
        assert.ok(choice, 'root src must be offered among same-name folders');
        const chosenResponse = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
        await page.locator('#choices button').filter({hasText: choice.nodeId}).click();
        const chosen = await (await chosenResponse).json();
        assert.equal(chosen.status, 'matched');
        assert.equal(chosen.seedNodeId || chosen.selectedNodeIds[0], choice.nodeId);
        await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent === reason, chosen.reason);
        await page.screenshot({path: path.join(input.out, 'question-' + (i+1) + '-chosen.png')});
        results.push({query, chosenNodeId: choice.nodeId, packet: chosen});
      }
    }
    fs.writeFileSync(path.join(input.out, 'browser.json'), JSON.stringify({importMs, status, errors, results}, null, 2));
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
})().catch(e => {console.error(e); process.exitCode = 1;});
