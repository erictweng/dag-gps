#!/usr/bin/env node
// Playwright smoke for the offline DAG canvas.
//
//   node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/
//
// Playwright is not a dependency of this repo; it is borrowed from a sibling
// checkout (override with PLAYWRIGHT_DIR). Loads the page over file://, drives
// window.dagGps, asserts against map.json, and writes 1920x1080 screenshots.
// Exits 1 on any page error, console error, or failed assertion.
import { createRequire } from "node:module";
import { readFileSync, mkdirSync } from "node:fs";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const PW_DIR = process.env.PLAYWRIGHT_DIR
  || "/Users/aibert/projects/quest-coder-assist/node_modules/playwright";

const [pageArg, outArg] = process.argv.slice(2);
if (!pageArg || !outArg) {
  console.error("usage: node scripts/smoke_canvas.mjs <page.html> <artifacts-dir>");
  process.exit(2);
}
const PAGE = resolve(pageArg);
const OUT = resolve(outArg);
const MAP_PATH = process.env.MAP_PATH
  ? resolve(process.env.MAP_PATH)
  : resolve("maps/quest-coder/map.json");

let chromium;
try {
  const req = createRequire(join(PW_DIR, "/"));
  ({ chromium } = req(PW_DIR));
} catch (err) {
  console.error(`FAIL  cannot load playwright from ${PW_DIR}: ${err.message}`);
  console.error("      set PLAYWRIGHT_DIR to a checkout that has playwright installed");
  process.exit(1);
}

const MAP = JSON.parse(readFileSync(MAP_PATH, "utf8"));
const LAYER_IDS = MAP.nodes.filter((n) => n.kind === "layer").map((n) => n.id);
const NON_TESTS = LAYER_IDS.filter((id) => id !== "tests").length;
const filesOf = (id) => (MAP.layers[id] || {}).files || [];

const problems = [];
function check(ok, msg) {
  if (!ok) problems.push(msg);
  return ok;
}
function step(name, ok, detail) {
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}  ${detail}`);
}

mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });

page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("console", (m) => {
  if (m.type() === "error") problems.push(`console.error: ${m.text()}`);
});
// The page must be self-contained: any network attempt beyond the favicon is a bug.
page.on("request", (r) => {
  if (/^https?:/.test(r.url())) problems.push(`external request: ${r.url()}`);
});
page.on("requestfailed", (r) => {
  if (!r.url().endsWith("/favicon.ico")) problems.push(`requestfailed: ${r.url()}`);
});

const url = pathToFileURL(PAGE).href;
await page.goto(url, { waitUntil: "load" });
await page.waitForFunction(() => window.dagGps && window.dagGps.state().visibleNodes > 0);

async function shot(file) {
  const p = join(OUT, file);
  await page.screenshot({ path: p });
  return p;
}
const settle = () => page.waitForTimeout(250);

// ----------------------------------------------------------- 1. layer view
{
  const s = await page.evaluate(() => window.dagGps.state());
  const nodes = await page.locator("#nodes g.node").count();
  const ok =
    check(s.view === "layers", `overview view is ${s.view}, want "layers"`) &&
    check(s.focused === null, `overview focused is ${s.focused}, want null`) &&
    check(
      s.visibleNodes === NON_TESTS,
      `overview visibleNodes ${s.visibleNodes} != ${NON_TESTS} non-tests layers`
    ) &&
    check(nodes === NON_TESTS, `overview drew ${nodes} node groups, want ${NON_TESTS}`) &&
    check(s.visibleEdges > 0, "overview drew no edges");
  await settle();
  const p = await shot("01-layers.png");
  step("layers", ok, `${s.visibleNodes} nodes, ${s.visibleEdges} edges, zoom ${s.zoom.toFixed(2)} -> ${p}`);
}

// ------------------------------------------------------- 2. focus a layer
{
  const target = "run-gateway";
  const s = await page.evaluate((id) => window.dagGps.focus(id), target);
  const sel = await page.locator("#nodes g.node.sel").count();
  const faded = await page.locator("#nodes g.node.faded").count();
  const info = MAP.layers[target];
  const lit = new Set([target]);
  for (const id of info.upstream.concat(info.downstream)) {
    if (id !== "tests") lit.add(id);
  }
  const expectLit = lit.size;
  const ok =
    check(s.focused === target, `focused is ${s.focused}, want ${target}`) &&
    check(s.view === "layers", `focus changed view to ${s.view}`) &&
    check(sel === 1, `expected exactly 1 .sel node, got ${sel}`) &&
    check(
      faded === NON_TESTS - expectLit,
      `faded ${faded}, want ${NON_TESTS - expectLit} (${expectLit} lit of ${NON_TESTS})`
    );
  await settle();
  const p = await shot("02-focus.png");
  step("focus", ok, `${target}: ${expectLit} lit / ${faded} dimmed -> ${p}`);
}

// ------------------------------------------------------ 3. expand solve-ui
{
  const target = "solve-ui";
  const want = filesOf(target).length;
  const s = await page.evaluate((id) => window.dagGps.expand(id), target);
  const stubs = await page.locator("#nodes g.node.stub").count();
  const ok =
    check(s.view === "files", `expand view is ${s.view}, want "files"`) &&
    check(s.expanded === target, `expanded is ${s.expanded}, want ${target}`) &&
    check(s.visibleNodes >= want, `expand visibleNodes ${s.visibleNodes} < ${want} files`) &&
    check(stubs > 0, "expand drew no layer stubs");
  await settle();
  const p = await shot("03-expand-solve.png");
  step("expand", ok, `${target}: ${s.visibleNodes} nodes (${want} files + ${stubs} stubs), ${s.visibleEdges} edges -> ${p}`);
}

// ------------------------------- 4. back, then expand persistence
{
  const b = await page.evaluate(() => window.dagGps.back());
  const okBack =
    check(b.view === "layers", `back view is ${b.view}, want "layers"`) &&
    check(b.expanded === null, `back expanded is ${b.expanded}, want null`) &&
    check(b.visibleNodes === NON_TESTS, `back visibleNodes ${b.visibleNodes} != ${NON_TESTS}`);
  step("back", okBack, `back to layer view with ${b.visibleNodes} nodes`);

  const target = "persistence";
  const want = filesOf(target).length;
  const s = await page.evaluate((id) => window.dagGps.expand(id), target);
  const stubs = await page.locator("#nodes g.node.stub").count();
  const ok =
    check(s.view === "files", `expand view is ${s.view}, want "files"`) &&
    check(s.expanded === target, `expanded is ${s.expanded}, want ${target}`) &&
    check(s.visibleNodes >= want, `expand visibleNodes ${s.visibleNodes} < ${want} files`);
  await settle();
  const p = await shot("04-expand-persistence.png");
  step("expand", ok, `${target}: ${s.visibleNodes} nodes (${want} files + ${stubs} stubs), ${s.visibleEdges} edges -> ${p}`);
}

await browser.close();

if (problems.length) {
  console.log(`\n${problems.length} problem(s):`);
  problems.forEach((p) => console.log(`  - ${p}`));
  process.exit(1);
}
console.log(`\nsmoke OK — 0 page errors, 4 screenshots in ${OUT}`);
