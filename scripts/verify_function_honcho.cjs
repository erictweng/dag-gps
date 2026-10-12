'use strict';
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
let chromium;
try { ({chromium} = require('playwright')); } catch (_) {
  ({chromium} = require('/Users/aibert/projects/quest-coder-assist/node_modules/playwright'));
}
const [url, out] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({viewport: {width: 1920, height: 1080}, reducedMotion: 'reduce'});
    const errors = [], external = [];
    page.on('pageerror', e => errors.push(String(e)));
    page.on('request', r => { if (!r.url().startsWith(new URL(url).origin)) external.push(r.url()); });
    await page.goto(url);
    if (!(await page.evaluate(() => document.querySelector('#import-box').open))) await page.click('#import-box summary');
    await page.fill('#repo-url', 'https://github.com/plastic-labs/honcho');
    await page.fill('#repo-commit', '3922af856d78ec41133916deec4d821fa9c5a92e');
    const started = performance.now();
    await page.click('#import-form button');
    await page.waitForFunction(() => /^Imported|^Import failed/.test(document.querySelector('#import-status').textContent), null, {timeout: 180000});
    const importStatus = await page.textContent('#import-status'), importMs = performance.now() - started;
    fs.writeFileSync(path.join(out, 'import-result.json'), JSON.stringify({importStatus, importMs}, null, 2));
    assert.ok(importStatus.startsWith('Imported'), importStatus);
    await page.waitForFunction(() => !document.querySelector('#import-form button').disabled);
    await page.waitForSelector('#graph .node');
    await page.locator('#graph').getByRole('button', {name: 'src/dialectic', exact: true}).click();
    await page.locator('#graph').getByRole('button', {name: 'src/dialectic/chat.py', exact: true}).click();
    await page.locator('#graph').getByRole('button', {name: 'src/dialectic/chat.py:agentic_chat:50', exact: true}).click();
    await page.waitForFunction(() => document.querySelector('#source-lines').start === 50 && document.querySelector('#source-lines').children.length);
    await page.screenshot({path: path.join(out, 'manual-drilldown-source.png')});
    await page.click('#clear');
    assert.equal(await page.locator('#graph').getByRole('button', {name: 'src/dialectic', exact: true}).count(), 1);
    const questions = JSON.parse(fs.readFileSync(path.join(__dirname, '../eval/function-honcho.json')));
    if (/honcho-v[23]$/.test(out)) questions.push('trace from src/routers/peers.py:chat',
      'how does src/routers/peers.py:chat reach src/llm/api.py#honcho_llm_call@147',
      'what does DialecticAgent.answer call',
      'what does src/telemetry/logging.py:format_reasoning_inputs_as_markdown call',
      'what does tests/bench/runner_common.py:BaseRunner.run_and_summarize call');
    fs.writeFileSync(path.join(out, 'questions.json'), JSON.stringify(questions, null, 2));
    const results = [];
    for (let i = 0; i < questions.length; i++) {
      const query = questions[i];
      await page.fill('#question', query);
      const response = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
      const start = performance.now();
      await page.press('#question', 'Enter');
      const packet = await (await response).json();
      assert.ok(packet.selectedNodeIds, JSON.stringify(packet));
      await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent === reason, packet.reason);
      const elapsedMs = performance.now() - start;
      fs.writeFileSync(path.join(out, 'packet-' + (i + 1) + '.json'), JSON.stringify(packet, null, 2));
      if (out.endsWith('honcho-v3') && i === 9) {
        assert.equal(packet.status, 'matched');
        assert.deepEqual(packet.selectedNodeIds, ['src/routers/peers.py#chat@257',
          'src/dialectic/chat.py#agentic_chat@50', 'src/dialectic/core.py#DialecticAgent.answer@548',
          'src/llm/api.py#honcho_llm_call@147']);
        const llm = packet.selectedEdges.find(e => e.to === 'src/llm/api.py#honcho_llm_call@147');
        assert.equal(llm.confidence, 'resolved');
        assert.equal(llm.sites[0].reexports[0].start, 10);
      }
      const highlights = await page.locator('#graph .node[data-state=on], #graph .node[data-state=seed]').evaluateAll(ns => ns.map(n => n.dataset.id));
      assert.deepEqual(new Set(highlights), new Set(packet.selectedNodeIds));
      await page.screenshot({path: path.join(out, 'question-' + (i + 1) + '.png')});
      if (packet.selectedNodeIds.length) await page.locator('#graph svg').screenshot({path: path.join(out, 'graph-' + (i + 1) + '.png')});
      if (packet.selectedNodeIds.length > 10) {
        await page.locator('#graph .node').last().scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(out, 'question-bottom-' + (i + 1) + '.png')});
      }
      results.push({query, status: packet.status, operation: packet.operation, elapsedMs, highlights});
      if (/honcho-v[23]$/.test(out)) {
        const drawn = await page.locator('#graph .edge').evaluateAll(es => es.map(e => ({tier: e.dataset.confidence, dash: getComputedStyle(e).strokeDasharray})));
        fs.writeFileSync(path.join(out, 'drawing-' + (i + 1) + '.json'), JSON.stringify(drawn));
        for (const e of drawn) if (e.tier && e.tier !== 'resolved') assert.notEqual(e.dash, 'none');
        await page.check('#certain-only');
        const legacyResponse = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
        await page.press('#question', 'Enter');
        const certain = await (await legacyResponse).json();
        assert.ok(certain.selectedNodeIds, JSON.stringify(certain));
        assert.ok(certain.selectedEdges.every(e => e.confidence === 'resolved'));
        fs.writeFileSync(path.join(out, 'certain-' + (i + 1) + '.json'), JSON.stringify(certain, null, 2));
        await page.uncheck('#certain-only');
        const again = page.waitForResponse(r => r.url().endsWith('/query') && r.request().method() === 'POST');
        await page.press('#question', 'Enter'); await again;
        await page.waitForFunction(reason => document.querySelector('#answer-reason').textContent === reason, packet.reason);
      }
      if (packet.selectedNodeIds.length && packet.status === 'matched') {
        await page.locator('#results button').first().click();
        await page.waitForFunction(() => document.querySelector('#source-lines').children.length > 0);
        const ref = packet.sourceRefs[0];
        assert.equal(await page.locator('#source-lines').getAttribute('start'), String(ref.start));
        await page.screenshot({path: path.join(out, 'source-' + (i + 1) + '.png')});
      }
      if (out.endsWith('honcho-v3') && i === 9) {
        await page.getByRole('button', {name: /^Re-export: src\/llm\/__init__.py:10/}).click();
        await page.waitForFunction(() => document.querySelector('#source-lines').start === 10);
        await page.locator('#source-lines').scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(out, 'q10-reexport-source.png')});
        await page.locator('#graph').getByRole('button', {name: 'src/llm/api.py:honcho_llm_call:147', exact: true}).click();
        await page.waitForFunction(() => document.querySelector('#source-lines').start === 147);
        await page.locator('#source-lines').scrollIntoViewIfNeeded();
        await page.screenshot({path: path.join(out, 'q10-implementation-source.png')});
      }
    }
    assert.deepEqual(errors, []); assert.deepEqual(external, []);
    fs.writeFileSync(path.join(out, 'browser-report.json'), JSON.stringify({importStatus, importMs, manualDrilldown: true, results, errors, external}, null, 2));
    console.log(JSON.stringify({ok: true, importMs, questions: results.length}));
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
