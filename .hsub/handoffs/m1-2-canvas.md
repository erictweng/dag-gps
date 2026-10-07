## Project
DAG GPS: ask a short question about a codebase and get a Jev-style answer (operation + target + probabilities + confidence) highlighted on an architecture DAG, in one offline HTML page. Read `docs/PLAN.md`, `STATUS.md`, `TASKS.md` first. M0 (`scripts/build_map.py` → `maps/quest-coder/map.json`) is verified on main.

Target repo for real data: `/Users/aibert/projects/quest-coder`, ref `origin/main`. Never read or write its working tree; build_map already exports a snapshot.
Do NOT edit `maps/quest-coder/layers.json` (Eric owns layer membership). If origin/main gained unmapped files, stop and report.
Git: repo-local author is configured. Work on the branch named below (create it from main). Commit when verified. Do not push, do not merge.

## This mini-milestone ONLY — M1.2: the canvas (standalone HTML)
Build the offline page that renders the architecture DAG from `map.json`. No scorer, no question answering (that's M2/M3). No CDN, no network, no build step, no npm deps.

### Files
- `web/template.html`: single file, inline CSS + JS, with a `/*__MAP__*/null` placeholder replaced by map.json.
- `scripts/render.py`: `python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html`. Stdlib only. Escape `</` in the inlined JSON.
- `scripts/smoke_canvas.mjs`: Playwright smoke (see below).
- `.gitignore`: add `dist/` and `artifacts/`.

### Behavior
1. **Layer view (default).** One box per layer: label, file count, line count. Layout: longest-path layering, consumers on the left → dependencies on the right; ~14 alternating barycenter sweeps to order each column. Ignore `realtime` edges for layering (still draw them). Draw edges before boxes. Edge colour/dash by `type` (import solid; http, rpc, data, build, realtime dashed with distinct colours) with per-type arrow markers; stroke width scales with `weight` (clamped). Legend for edge types.
2. **Tests layer hidden by default** (toggle checkbox). It has ~95 files and would dominate.
3. **Click a layer** → highlight it + transitive `upstream` and `downstream` (use the precomputed `layers[id]` fields), dim everything else. Side panel: label, desc, aliases, files (sorted by lines), upstream list, downstream list, top_fan_in. Click background → clear.
4. **Expand a layer** (double-click or panel button "Expand") → file view of that layer: its files as nodes laid out with the same algorithm over `file_edges` inside the layer; edges leaving/entering the layer drawn to stub boxes for the other layers (one stub per layer, labelled, with counts). File node shows the file name; panel shows path, lines, desc, imports, importers. "Back to layers" button + Esc.
5. **Pan/zoom:** wheel zoom around the cursor, drag on background to pan (not when the drag starts on a node). Layer view opens fit-to-screen; file views with >40 nodes open at zoom ≥0.6 anchored top-left.
6. **Header:** repo, commit, built_at, counts from `meta`. A disabled input labelled "Ask (M2)" as a placeholder for the scorer.
7. **Test hook:** `window.dagGps = {state(), focus(id), expand(id), back()}` where `state()` returns `{view, focused, expanded, visibleNodes, visibleEdges}`. The smoke uses this; the UI must not depend on it.
8. No text overlap or clipping in boxes: truncate long labels with an ellipsis and a `<title>` tooltip.

### Smoke (`node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/`)
Load Playwright from `process.env.PLAYWRIGHT_DIR || "/Users/aibert/projects/quest-coder-assist/node_modules/playwright"` (via createRequire). Open the file:// URL at 1920×1080 and collect `pageerror` + console errors. Then:
- overview: assert visibleNodes == number of non-tests layers; screenshot `artifacts/01-layers.png`
- `focus("run-gateway")`: assert focused set; screenshot `02-focus.png`
- `expand("solve-ui")`: assert visibleNodes ≥ the layer's file count; screenshot `03-expand-solve.png`
- `back()` then `expand("persistence")`: screenshot `04-expand-persistence.png`
- exit 1 if any error was collected or any assertion failed; print a one-line summary per step.

Look at every screenshot yourself and fix overlaps, clipped labels and edges cutting through boxes before reporting.

### .verify.json
Set `commands.build` to `python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html`, and set `commands.smoke` to the existing build_map smoke `&& python3 scripts/render.py ... && node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/`. Keep `test` as is.

Branch: `m1-canvas`. Commit message: "M1.2: offline DAG canvas + render + smoke". Do not commit `dist/` or `artifacts/`.
Allowed files: `web/**`, `scripts/render.py`, `scripts/smoke_canvas.mjs`, `.gitignore`, `.verify.json`, `tests/**` (render.py tests ok), `STATUS.md`, `TASKS.md`.

## Verification (paste real output)
- `python3 -m unittest discover -s tests -q`
- full `.verify.json` smoke chain, exit 0, with the per-step lines
- list the screenshot paths

## Stop conditions
Stop and report if Playwright can't be loaded, if map.json lacks a field you need (do not edit build_map.py), or anything needs files outside the allowed list.
