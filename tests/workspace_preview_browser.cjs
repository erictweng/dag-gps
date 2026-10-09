#!/usr/bin/env node
'use strict';
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const {chromium} = require('/Users/aibert/projects/quest-coder-assist/node_modules/playwright');

function args() {
  const values = process.argv.slice(2);
  const result = {};
  for (let index = 0; index < values.length; index += 2) result[values[index]] = values[index + 1];
  if (!result['--real'] || !result['--hostile'] || !result['--report'] || !result['--screenshots']) {
    throw new Error('usage: workspace_preview_browser.cjs --real DIR --hostile DIR --report FILE --screenshots DIR');
  }
  return result;
}

function expected(directory) {
  return {
    inventory: JSON.parse(fs.readFileSync(path.join(directory, 'inventory.json'), 'utf8')),
    preview: JSON.parse(fs.readFileSync(path.join(directory, 'preview.json'), 'utf8')),
  };
}

(async () => {
  const options = args();
  fs.mkdirSync(options['--screenshots'], {recursive: true});
  const cases = [
    {name: 'real', directory: path.resolve(options['--real'])},
    {name: 'hostile-cycle', directory: path.resolve(options['--hostile'])},
  ];
  const browser = await chromium.launch({headless: true});
  const report = {browser: await browser.version(), cases: []};
  for (const item of cases) {
    const data = expected(item.directory);
    const context = await browser.newContext({viewport: {width: 1280, height: 900}});
    const page = await context.newPage();
    const httpRequests = [], consoleErrors = [], pageErrors = [];
    await page.route(/^https?:\/\//, route => {
      httpRequests.push(route.request().url());
      return route.abort('blockedbyclient');
    });
    page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()); });
    page.on('pageerror', error => pageErrors.push(String(error)));
    await page.goto(pathToFileURL(path.join(item.directory, 'index.html')).href, {waitUntil: 'load'});

    const supported = data.inventory.files.find(file => file.extraction.status === 'included');
    const unsupported = data.inventory.files.find(file => file.extraction.status === 'unsupported');
    if (!supported || !unsupported) throw new Error(`${item.name} requires supported and unsupported rows`);

    async function assertDetail(file, method) {
      const button = page.getByRole('button', {name: file.path, exact: true});
      if (method === 'click') await button.click();
      else {
        await button.focus();
        await page.keyboard.press('Enter');
      }
      const node = data.preview.map.nodes.find(value => value.kind === 'file' && value.path === file.path);
      const incidents = data.preview.map.file_edges.filter(edge => edge.from === file.path || edge.to === file.path);
      const actual = {
        path: await page.locator('#detail-path').innerText(),
        sha256: await page.locator('#detail-sha256').innerText(),
        kind: await page.locator('#detail-kind').innerText(),
        lines: await page.locator('#detail-lines').innerText(),
        reason: await page.locator('#detail-reason').innerText(),
        group: await page.locator('#detail-group').innerText(),
        links: await page.locator('#detail-links li').allInnerTexts(),
        focusId: await page.evaluate(() => document.activeElement && document.activeElement.id),
        ariaCurrent: await button.getAttribute('aria-current'),
      };
      const expectedReason = file.extraction.reason || 'Included in documented static extraction scope.';
      const layerNode = node && data.preview.map.nodes.find(value => value.kind === 'layer' && value.id === node.layer);
      const expectedGroup = node ? ((layerNode && layerNode.label) || node.layer)
        : 'Not in provisional graph (unsupported for extraction).';
      if (actual.path !== file.path || actual.sha256 !== file.sha256 || actual.kind !== file.contentKind ||
          actual.lines !== (file.lineCount === null ? 'Unknown' : String(file.lineCount)) ||
          actual.reason !== expectedReason || actual.group !== expectedGroup || actual.focusId !== 'file-detail' ||
          actual.ariaCurrent !== 'true') throw new Error(`${item.name} ${method} detail mismatch: ${JSON.stringify(actual)}`);
      if (actual.links.length !== Math.max(1, incidents.length)) throw new Error(`${item.name} incident link count mismatch`);
      for (const edge of incidents) {
        const witness = edge.witness && edge.witness.path ? edge.witness.path : 'unknown';
        if (!actual.links.some(text => text.includes(`${edge.from} → ${edge.to}`) && text.includes(`source witness path: ${witness}`))) {
          throw new Error(`${item.name} missing exact incident witness`);
        }
      }
      return {method, file: file.path, expectedIncidentLinks: incidents.length, ...actual};
    }

    // Groups and group links must be shown by human folder label, never by opaque hash id.
    const layerLabels = new Map(data.preview.map.nodes.filter(n => n.kind === 'layer').map(n => [n.id, n.label || n.id]));
    const groupTexts = await page.locator('#groups li').allInnerTexts();
    const name = id => layerLabels.get(id) || id;
    const byLabel = (a, b) => (a < b ? -1 : a > b ? 1 : 0);
    const expectedGroups = Object.entries(data.preview.map.layers)
      .sort((a, b) => byLabel(name(a[0]), name(b[0])) || byLabel(a[0], b[0]))
      .map(([id, g]) => `${name(id)}: ${g.files.length} files`);
    if (JSON.stringify(groupTexts) !== JSON.stringify(expectedGroups)) {
      throw new Error(`${item.name} group labels mismatch: ${JSON.stringify(groupTexts)}`);
    }
    const groupLinkTexts = await page.locator('#group-links li').allInnerTexts();
    const expectedGroupLinks = data.preview.map.edges.length ? [...data.preview.map.edges]
      .sort((a, b) => byLabel(name(a.from), name(b.from)) || byLabel(name(a.to), name(b.to)) || byLabel(a.type, b.type))
      .map(e => `${name(e.from)} → ${name(e.to)}: ${e.weight} ${e.type} links`)
      : ['No links between groups.'];
    if (JSON.stringify(groupLinkTexts) !== JSON.stringify(expectedGroupLinks)) {
      throw new Error(`${item.name} group links mismatch: ${JSON.stringify(groupLinkTexts)}`);
    }

    const click = await assertDetail(supported, 'click');
    const keyboard = await assertDetail(unsupported, 'keyboard-enter');
    const screenshot = path.join(path.resolve(options['--screenshots']), `${item.name}.png`);
    await page.screenshot({path: screenshot, fullPage: true});
    const value = {
      name: item.name,
      source: data.inventory.source,
      inventoryRows: await page.locator('#files tr').count(),
      state: data.preview.state,
      publicationBlocked: data.preview.publicationBlocked,
      fileCycles: data.preview.diagnostics.counts.fileCycles,
      click,
      keyboard,
      httpRequests,
      consoleErrors,
      pageErrors,
      imageElements: await page.locator('img').count(),
      injectedValue: await page.evaluate(() => globalThis.__injected ?? null),
      screenshot,
    };
    if (value.inventoryRows !== data.inventory.files.length || httpRequests.length || consoleErrors.length ||
        pageErrors.length || value.imageElements || value.injectedValue !== null) {
      throw new Error(`${item.name} browser safety/detail check failed: ${JSON.stringify(value)}`);
    }
    report.cases.push(value);
    await context.close();
  }
  await browser.close();
  fs.writeFileSync(options['--report'], JSON.stringify(report, null, 2) + '\n');
  console.log(JSON.stringify(report));
})().catch(error => { console.error(error); process.exit(1); });
