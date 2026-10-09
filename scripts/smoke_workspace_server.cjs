// M2.2 real end-to-end smoke: drive the workspace page through import -> ask -> choose -> page.
// Usage: node scripts/smoke_workspace_server.cjs URL_WITH_SESSION REPO_URL COMMIT SCREENSHOT_DIR REPORT
'use strict';
const fs = require('fs');
const path = require('path');
let chromium;
try { ({chromium} = require('playwright')); } catch (_) {
  ({chromium} = require('/Users/aibert/projects/quest-coder-assist/node_modules/playwright'));
}
const [url, repoUrl, commit, shots, reportPath] = process.argv.slice(2);
(async () => {
  fs.mkdirSync(shots, {recursive: true});
  const origin = new URL(url).origin;
  const browser = await chromium.launch();
  const page = await browser.newPage({viewport: {width: 1280, height: 900}});
  const external = [], errors = [];
  page.on('request', r => { if (!r.url().startsWith(origin)) external.push(r.url()); });
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(url);
  if (new URL(page.url()).hash) throw new Error('session key left in the address bar');
  await page.fill('#repo-url', repoUrl);
  await page.fill('#repo-commit', commit);
  await page.click('#import-form button');
  await page.waitForFunction(() => /^Imported|^Import failed/.test(document.getElementById('import-status').textContent), null, {timeout: 120000});
  const importStatus = await page.textContent('#import-status');
  if (!importStatus.startsWith('Imported')) throw new Error(importStatus);
  const projectInfo = await page.textContent('#project-info');
  const cases = [];
  async function ask(q) {
    await page.fill('#question', q);
    await page.keyboard.press('Enter');
    await page.waitForFunction(prev => document.getElementById('answer-status').textContent && document.body.dataset.prev !== document.getElementById('answer-reason').textContent + document.getElementById('answer-status').textContent, null);
    await page.waitForTimeout(150);
    const value = {query: q, status: await page.textContent('#answer-status'), reason: await page.textContent('#answer-reason'),
      files: await page.locator('#files li').allInnerTexts(), choices: await page.locator('#choices li').allInnerTexts()};
    await page.evaluate(() => { document.body.dataset.prev = document.getElementById('answer-reason').textContent + document.getElementById('answer-status').textContent; });
    cases.push(value);
    return value;
  }
  await ask('what depends on screener/fast.py');
  await page.screenshot({path: path.join(shots, 'dependents.png'), fullPage: true});
  const choice = await ask('__init__.py');
  if (!choice.choices.length) throw new Error('expected a choice');
  await page.locator('#choices button').first().click();
  await page.waitForFunction(() => document.querySelectorAll('#files li').length === 1);
  cases.push({query: '(clicked first choice)', status: await page.textContent('#answer-status'), files: await page.locator('#files li').allInnerTexts()});
  await ask('path from run_margin.py to screener/geom.py');
  await page.screenshot({path: path.join(shots, 'path.png'), fullPage: true});
  const report = {importStatus, projectInfo, cases, external, errors};
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report, null, 1));
  await browser.close();
  if (external.length || errors.length) process.exit(1);
})().catch(e => { console.error(e); process.exit(1); });
