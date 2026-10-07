# Tasks — DAG GPS

Work is organized as milestones broken into mini-milestones. Each mini-milestone
should be small enough for one worker run to finish and verify.

Status values: `queued` | `running` | `verified` | `blocked` | `failed`

## Now

### Milestone 0 — Map

#### 0.2 — Cover the files quest-coder added since `71bc83a`

Status: blocked (needs Eric — he owns layer membership)

`layers.json` has no glob for `lib/party-lock.ts`, `lib/party-lock-server.ts`,
`lib/story-beats.ts`, `lib/story-scenes.ts`. Until then the `.verify.json` smoke
(which resolves `origin/main`) FAILs the unmapped check and exits 1.

Done when:

- Either `layers.json` covers them, or `.verify.json` pins the smoke to a fixed ref.
- `python3 scripts/build_map.py … --ref origin/main …` exits 0.

## Next

### Milestone 1 — Canvas

#### 1.1 — `index.html` renders the layer DAG, clicking a layer expands it to its files

Status: queued

Notes from M0 for whoever builds this:

- `map.json` `edges` are layer→layer only, as the M0 brief specified. Expanding a layer
  to show file→file edges needs either a new field in `map.json` or a re-derivation.
  Worth deciding before M1 starts.
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

- 0.2 above (layer map coverage; Eric's call).

## Done

### Milestone 0 — Map

#### 0.1 — `build_map.py` merges `layers.json` + the import graph into `map.json`

Status: verified (2026-10-07, branch `m0-build-map`)

- `scripts/import_graph.py` vendored unchanged from the `codebase-architecture-audit` skill.
- `scripts/build_map.py` — snapshot → extract → assign → roll up → typed edges → index →
  precompute → write, with a printed check report and a non-zero exit on any FAIL.
- `tests/test_build_map.py` — 63 unittest cases on in-memory fixtures that mirror the
  real `import_graph.json` shapes.
- `maps/quest-coder/map.json` — built at `71bc83a`, 8/8 checks passed.
