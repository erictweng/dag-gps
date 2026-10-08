# Tasks — DAG GPS

Work is organized as milestones broken into mini-milestones. Each mini-milestone
should be small enough for one worker run to finish and verify.

Status values: `queued` | `running` | `verified` | `blocked` | `failed`

## Now

### Milestone 1 — Canvas

Eric approved (2026-10-07): add file-level edges, then build the canvas.
- 1.1 file_edges in map.json — handoff `.hsub/handoffs/m1-1-file-edges.md` — verified
- 1.2 canvas (web/template.html + render.py + Playwright smoke) — handoff `.hsub/handoffs/m1-2-canvas.md` — queued

#### 1.2 — `index.html` renders the layer DAG, clicking a layer expands it to its files

Status: queued

Notes for whoever builds this:

- Use the top-level `file_edges` array for the expanded view:
  `{from, to, type: import|http|rpc, cross_layer}`, endpoints are file paths. 413 of them
  at `749d8b5`. `cross_layer: false` edges live inside one layer, so they are the ones that
  draw when a layer expands; `cross_layer: true` edges are the file-level detail behind a
  layer→layer edge in `edges`.
- `edges` stays layer→layer with `{weight, sample}`; `file_edges` has no weight, since it is
  deduped on `(from, to, type)`.
- 15 import targets have no node (CSS, the `content/*.json` quest packs) and 1 fetch path has
  no route handler. They are reported as notes by the smoke, not drawn.
- Layer nodes carry `path: ""` (a layer owns globs, not one path); their `tokens`
  include the glob path segments.
- `layers[id].top_fan_in` is empty for `api`: nothing imports a route handler. Use
  `weight` on the incoming edges for that layer's prominence instead.

Done when:

- A Playwright run on `file://` with 0 console errors, plus 1920×1080 screenshots.

## Backlog

- M2 — scorer + `eval.jsonl` (~30 questions).
- M3 — route highlight, confidence bar, top-3 alternatives.

## Blocked

- Nothing.

## Done

### Milestone 1 — Canvas

#### 1.1 — file-level edges in `map.json`

Status: verified (2026-10-07, branch `m1-file-edges`)

- `file_level_edges()` in `scripts/build_map.py` emits `{from, to, type, cross_layer}` for
  every import pair, every resolved `fetch('/api/…')` and every `.rpc()` with an SQL
  definition. `meta.counts.file_edges` and per-type + cross-layer counts are printed.
- New check (FAIL → exit 1): every `file_edges` endpoint is a known **file** node id.
- 78 unit tests OK; smoke 10/10 PASS at quest-coder `749d8b5`.

### Milestone 0 — Map

#### 0.2 — Cover the files quest-coder added since `71bc83a`

Status: verified (34d7ef9: 4 files mapped; build_map vs 749d8b5 8/8 PASS)

#### 0.1 — `build_map.py` merges `layers.json` + the import graph into `map.json`

Status: verified (2026-10-07, branch `m0-build-map`)

- `scripts/import_graph.py` vendored unchanged from the `codebase-architecture-audit` skill.
- `scripts/build_map.py` — snapshot → extract → assign → roll up → typed edges → index →
  precompute → write, with a printed check report and a non-zero exit on any FAIL.
- `tests/test_build_map.py` — 63 unittest cases on in-memory fixtures that mirror the
  real `import_graph.json` shapes.
- `maps/quest-coder/map.json` — built at `71bc83a`, 8/8 checks passed.

## M1.2 — verified 2026-10-07
Recovered Claude partial implementation after session quota exhaustion. Offline HTML canvas, renderer, unit tests, browser smoke, real-click interaction check complete. 97 unit tests pass; map checks 10/10; four screenshot states with zero page errors and zero external requests. Real clicks, expand, file details, Escape, test toggle, double-click, back, zoom and fit pass. Artifact: dist/quest-coder.html. Scorer remains M2 (Ask disabled deliberately).
