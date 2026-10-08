# Tasks — DAG GPS

Work is organized as milestones broken into mini-milestones. Each mini-milestone
should be small enough for one worker run to finish and verify.

Status values: `queued` | `running` | `verified` | `blocked` | `failed`

## Now

### Milestone 1 — Canvas

Eric approved (2026-10-07): add file-level edges, then build the canvas.
- 1.1 file_edges in map.json — handoff `.hsub/handoffs/m1-1-file-edges.md` — verified
- 1.2 canvas (web/template.html + render.py + Playwright smoke) — handoff `.hsub/handoffs/m1-2-canvas.md` — verified

#### 1.2 — `index.html` renders the layer DAG, clicking a layer expands it to its files

Status: verified (M1.2 at d690283)

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

## Milestone 2 — Local scorer + generated evaluation

Status: verified on `m2-scorer`; parent independently verified before M3.

- Dependency-free `web/scorer.js` for Node/browser; observed map IDs only; LOCATE,
  UPSTREAM, DOWNSTREAM, PATH, NOT_SURE; validated heads, heuristic scores,
  component explanations and top-3 alternatives; independent PATH endpoints.
- Persist aliases in map nodes; regression tests preserve existing IDs/edges.
- 47 generated eval questions with inspected graph routes, not user-ground-truth;
  distinct paraphrase regressions plus invalid-contract tests.
- `scripts/eval_scorer.cjs`: op 46/47, raw target top-1 42/44, top-3 43/44,
  negative abstention 10/10, path endpoints 14/14, Node p95 0.7754 ms.
- All verification recipe gates exit 0: 99 Python + 40 JS tests, render/map checks,
  existing canvas/real-click smoke and new Chromium scorer parity (p95 0.7000 ms).
- M1 canvas/Ask unchanged. Known grading/authentication errors remain reported,
  not hidden; see `docs/M2_REPORT.md`. Eric must review draft eval answers.

## Milestone 3 — Offline Ask + route highlighting

Eric approved M3 after parent verified M2.
Status: verified locally on `m3-routing`; parent rerun/review pending.

- Inlined scorer/router, safe script serialization, enabled Enter + visible Ask button.
- Validated IDs; LOCATE/Dependencies/Dependents/directed deterministic BFS; realtime
  excluded, no-route honest, mixed layer/file endpoints explicitly unsupported.
- Heuristic score/latency/yes-no/explanations/top-three explicit overrides; NOT_SURE
  clears old highlights. Cross-layer file routes show real known file IDs.
- 104 Python + 46 JS tests; full pinned map parity + 10/10 map checks.
- Legacy smoke and 47-case shipped scorer parity pass; 5 canonical real UI states
  plus 11 extra checks; zero errors/external requests; screenshots inspected.
- No map/scorer changes, push, merge or quest-coder edits. See `docs/M3_REPORT.md`.

## Filename lookup + evidence-first answers

Eric approved the next milestone after M3.
Status: verified locally on `lookup-evidence`, based on `1844aa2`; parent independent review pending.

- Separate file/architecture retrieval; exact path, basename, stem, partial and conservative
  spelling tiers. All duplicate paths; missing runner.py is honest; no fuzzy auto-action.
- Evidence-first four labels; reasons/paths/aliases, uncalibrated raw Details. No learned aliases/persistence.
- 104 Python + 73 JS tests; full pinned map parity and 10/10 checks; graph/router unchanged.
- Legacy M3 5 canonical + 11 extra checks and new lookup 19 UI checks pass; shipped
  scorer parity for 47 original + 40 lookup cases; zero page/console errors or external requests.
- Original eval rows unchanged: operation 47/47, top-1/top-3 44/44. Separate challenge
  39/40 operation/label, 16/17 top-1, 17/17 top-3; false accepted negatives 0/24,
  wrong accepted requests 0/15; bearer-auth challenge failure retained honestly.
- Nine lookup screenshots inspected; recipe, README, report and progress note updated.
- No push/merge, quest-coder edits, membership changes, or next milestone launch.
  See `docs/LOOKUP_REPORT.md` and `.hsub/build-updates/lookup-evidence.md`.

## Explicit correction-driven alias learning

Eric approved running this next milestone without waiting for real failed queries.
Status: verified locally on `alias-learning` from `ba72d1b`; parent independent
verification/PR pending. All regression examples are synthetic, not user evidence.

- Opt-in only after a real alternative choice; exact alias and real target shown
  before a separate confirmation. Override/review/cancel/asking do not persist.
- Repo/version-scoped best-effort localStorage; immutable scorer overlay; exact
  file/path priority; conflicts abstain; duplicates idempotent; orphans quarantined.
- Inspect/remove/confirmed clear; actual browser JSON download; user-file import
  fully validates before preview/confirmation, merge default vs explicit replace.
- Invalid schema/repo/version/size/strings apply nothing; markup escaped; no alias
  data is executable. Denied/quota storage says Unsaved and navigation still works.
- PATH learning disabled with honest endpoint-query guidance. NOT_SURE without
  a supported explicit override cannot learn. No automatic training or backend.
- 106 Python + 87 JS tests; alias 19 real UI checks / 15 synthetic eval cases /
  5 shipped overlay parity; prior lookup19/M3 canonical5+extras11/canvas/parity and
  pinned map gates pass. No page/console errors or external requests.
- All 272 literal file paths tested against alias hijacking. Both old eval datasets,
  map/layers/router unchanged. Existing bearer-auth miss retained.
- `Python judge` already matched runner-service: no invented baseline failure.
  `Python judge station` demonstrates abstention → correction → accepted repeat.
- Report `docs/ALIAS_LEARNING_REPORT.md`; exact gates/logs and nine screenshots
  under `artifacts/alias*`; no push or merge, no quest-coder changes.

## Backlog

- Eric review/correction of generated eval answers and map aliases.
- M4 hosted backend remains dropped unless revisited.

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
