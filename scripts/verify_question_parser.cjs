'use strict';
const fs = require('node:fs'), path = require('node:path'), assert = require('node:assert/strict');
let chromium;
try { ({chromium} = require('playwright')); } catch (_) {
  ({chromium} = require('/Users/aibert/projects/quest-coder-assist/node_modules/playwright'));
}
const [url, out, repo, pin] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.goto(url);
    if (!await page.evaluate(() => document.querySelector('#import-box').open)) await page.click('#import-box summary');
    await page.fill('#repo-url', repo);
    await page.fill('#repo-commit', pin);
    await page.click('#import-form button');
    await page.waitForFunction(() => /^Imported|^Import failed/.test(document.querySelector('#import-status').textContent), null, {timeout: 240000});
    const status = await page.textContent('#import-status');
    fs.writeFileSync(path.join(out, 'import.json'), JSON.stringify({status, errors}));
    assert.ok(status.startsWith('Imported'), status);
    await page.waitForSelector('#graph .node');
    await page.screenshot({path: path.join(out, 'import.png')});
    const questions = repo.includes('salesroom') ? ['youtube', 'where is the youtube', 'where is the src', "where's the db", 'where is the src folder', 'where is the YOUTUBE file', 'where do we play videos'] :
      ['where is the db', 'where is the DB', "where's the db", 'wheres the db', 'where is the src folder', 'where is the database layer', 'where do we store messages'];
    const results = [];
    for (const [i, query] of questions.entries()) {
      await page.fill('#question', query);
      const response = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
      await page.press('#question', 'Enter');
      const packet = await (await response).json();
      assert.ok(packet.selectedNodeIds, JSON.stringify(packet));
      await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent === reason, packet.reason);
      await page.screenshot({path: path.join(out, 'question-' + (i + 1) + '.png')});
      results.push({query, packet});
    }
    fs.writeFileSync(path.join(out, 'browser.json'), JSON.stringify({errors, results}, null, 2));
    assert.deepEqual(errors, []);
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
