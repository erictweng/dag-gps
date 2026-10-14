/* Real browser smoke; the private URL stays in the environment, never artifacts. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.PLAYWRIGHT_DIR || 'playwright');
(async () => {
  const [phase, out] = process.argv.slice(2);
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.DAG_TEST_URL);
    await page.waitForFunction(() => document.querySelector('#project-info').textContent.includes('files,'));
    await page.locator('#history-box').evaluate(node => { node.open = true; });
    if (phase === 'before') {
      const rows = [
        ['where is src/db.py', 'matched', 'match'],
        ['where is the quantum flux capacitor', 'no-match', 'no match'],
        ['what uses backfill', 'needs-choice', 'unsure'],
        ['where is src/config.py', 'matched', 'match'],
        ['where is src/db.py', 'matched', 'unsure']
      ];
      const results = [];
      for (let i = 0; i < rows.length; i++) {
        const [question, expected, verdict] = rows[i];
        await page.locator('#question').fill(question);
        const response = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
        await page.locator('#ask-form button[type=submit]').click();
        const packet = await (await response).json();
        assert.equal(packet.status, expected, question);
        await page.locator('#label-box').waitFor({state: 'visible'});
        await page.locator('#label-box [data-label="' + verdict + '"]').click();
        await page.waitForFunction(label => document.querySelector('#label-verdict').textContent.includes('you said: ' + label), verdict);
        await page.waitForFunction(n => document.querySelector('#history-count').textContent === String(n), i + 1);
        results.push({question, status: packet.status, verdict});
        await page.screenshot({path: path.join(out, 'question-' + (i + 1) + '.png')});
      }
      fs.writeFileSync(path.join(out, 'browser-questions.json'), JSON.stringify(results, null, 2));
    } else {
      await page.waitForFunction(() => document.querySelector('#history-count').textContent === '5');
      assert.equal(await page.locator('#history > li').count(), 5);
      assert.equal(await page.locator('#history [aria-pressed="true"]').count(), 5);
      // Correct an older question in its original record, without asking again.
      const item = page.locator('#history > li').last();
      await item.getByRole('button', {name: 'no match', exact: true}).click();
      await page.waitForFunction(() => document.querySelector('#history > li:last-child').textContent.includes('you: no match'));
      assert.equal(await page.locator('#history-count').textContent(), '5');
      await page.screenshot({path: path.join(out, 'after-restart.png')});
    }
    assert.deepEqual(errors, []);
    console.log('question log browser ' + phase + ': pass');
  } finally { await browser.close(); }
})().catch(error => { console.error(error.message); process.exitCode = 1; });
