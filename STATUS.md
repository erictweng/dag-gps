# Status — DAG GPS

Last updated: 2026-10-07

## Current Focus

M1.1 (`file_edges` in `map.json`) is done. Next: M1.2, the canvas
(`web/template.html` + `render.py` + a Playwright smoke) — handoff
`.hsub/handoffs/m1-2-canvas.md`.

## Active Worker

None.

## Last Verified

2026-10-07, branch `m1-file-edges`:

- `python3 -m unittest discover -s tests -q` — 78 tests, OK.
- `.verify.json` smoke (`build_map.py … --ref origin/main`) — 10/10 checks passed, exit 0,
  at quest-coder `749d8b5`. 18 layers + 272 files = 290 nodes, 52 layer edges
  (import 43, http 6, build 1, data 1, realtime 1), **413 file edges** (import 389,
  http 14, rpc 10; 324 cross-layer, 89 same-layer), 305 KB.
- `maps/quest-coder/map.json` is committed at this ref. `nodes`, `edges` and `layers` are
  byte-identical to the M0 map; the only additions are the top-level `file_edges` array
  and `meta.counts.file_edges`.

## Blockers

None.

Noted, not blocking: the smoke prints two notes. 15 import edges are dropped because the
target is not a map file node (`app/globals.css`, the `content/{public,server}/*.json`
quest packs) — `SOURCE_EXTS` is ts/tsx/js/mjs/py/sql, so those files have no node to point
at. And `scripts/deployment_smoke.mjs` fetches `/api/private-pack`, which has no route
handler. Both are reported rather than silently swallowed.

## Rule

Complete and verify one mini-milestone before launching the next worker.
Update this file whenever a worker starts, finishes, or gets blocked.

## M0 — Hermes-verified 2026-10-07
- 63 unit tests OK; build_map vs quest-coder origin/main 749d8b5: 8/8 checks, exit 0 (18 layers, 272 files, 52 layer edges).
- layers.json: mapped 4 files added upstream mid-run (party-lock -> social-domain, party-lock-server -> social-services, story-beats -> game-domain, story-scenes -> solve-ui).
- Open for M1: map.json has layer->layer edges only; file-level edges needed for expand-to-files.

## M1.1 — verified 2026-10-07
- `map.json` now carries `file_edges`: `{from, to, type, cross_layer}` with file-path
  endpoints, typed `import | http | rpc`. Same-layer edges are kept (`cross_layer: false`),
  unlike the layer rollup, which drops them — that is what expand-to-files needs.
- Deduped on `(from, to, type)`, sorted by the same triple. 409 raw import pairs →
  389 edges after dedupe and dropping 15 non-source targets.
- New check: every `file_edges` endpoint must be a **file** node id (a layer id FAILs too).
- `edges` is unchanged in shape and content, so nothing that reads the M0 map breaks.

## M1.2 — verified 2026-10-07
Recovered Claude partial implementation after session quota exhaustion. Offline HTML canvas, renderer, unit tests, browser smoke, real-click interaction check complete. 97 unit tests pass; map checks 10/10; four screenshot states with zero page errors and zero external requests. Real clicks, expand, file details, Escape, test toggle, double-click, back, zoom and fit pass. Artifact: dist/quest-coder.html. Scorer remains M2 (Ask disabled deliberately).
