# Status — DAG GPS

Last updated: 2026-10-07 PDT

## Current focus — V1.0 worker verified / parent pending

`v1-baseline` starts at current main `489857805e06e250462e545d213b09111417362e`.
The prior tours/refresh/alias/lookup/routing implementations are already integrated
on main; older worker-pending prose below has been reconciled against Git.

- V1.0 only: baseline, locked release contract, truthful supported-source matrix,
  fixture provenance and coherent status. No new runtime user feature.
- Unchanged `.verify.json` build/test/smoke each exit 0 on 2026-10-07 PDT:
  **138 Python + 93 JS tests**, 10 map checks and full pinned parity.
- Generated original eval op 47/47, target top1/top3 44/44; lookup op/label 39/40,
  top1 16/17, top3 17/17, negative false accepts 0/24; alias synthetic 15/15.
  Bearer-auth abstention remains. These are not Eric-authored/held-out accuracy.
- Exact pins: quest `749d8b5de490cc2e6a0c98c713fab3ab856da799`; old self demo
  `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93`. Map/layers/tours/evals unchanged.
- Current non-source quest drops are **14**, not older reports' 15; extractor prints
  364 JS + 44 Python pairs. Frozen map still has 413 links. Historical discrepancy
  explicitly retained in [baseline report](docs/V1_BASELINE_REPORT.md).
- Contracts: [acceptance](docs/V1_ACCEPTANCE.md), [sources](docs/SUPPORTED_SOURCES.md),
  [fixtures](docs/V1_FIXTURES.json), [approved plan](.hermes/plans/2026-10-07_203500-v1-milestones.md).
- Evidence: `/Users/aibert/projects/dag-gps/artifacts/v1-baseline/verification.json`,
  separate gate stdout/stderr, metrics, copied browser reports/screenshots and builds.

## Active worker / next action

V1.0 implementation worker finished local verification; parent independently
reviews contracts/spec/code quality and reruns gates before integrating/pushing
main per [WORKFLOW](docs/WORKFLOW.md). Worker does not merge/push.
**V1.1a not started**: pure impact analysis is the next handoff after parent acceptance.
V1.4 optional query evaluation can start after V1.0; shared scorer/UI writes serialized.

## Blockers and release boundary

No automated baseline blocker. Parent V1.0 acceptance remains pending. Entire v1
is not complete: impact/trust/onboarding/feedback/release gates and **Eric's unaided
real repository session** are future work. Defaults locked: desktop-first offline/local,
static import impact/no execution tracing, optional local query capture off by default,
human-reviewed onboarding. See acceptance checklist for evidence and owners.

Known limitations: mixed endpoint routes; bearer-auth abstention; dynamic/relative
Python and lexical JS gaps; omitted CSS/JSON nodes; old self snapshot; best-effort
file:// storage/export fallback; no cross-tab sync; per-file atomic publication, not
power-loss transaction; source tours, not observed execution. Do not hide these by
loosening tests or inventing user labels.

## Integrated milestone history (not current pending work)

The following preserves earlier counts and observations as historical results;
new V1.0 logs above govern current metrics. Prior reports retain original worker context.

### Architecture tours — historical worker evidence

Architecture-guided tours locally verified on `architecture-tours` from main `3e811d9`.
Integrated on main at 4898578; the following are historical worker results, not current pending integration.

- quest-coder audited archive SHA `749d8b5de490cc2e6a0c98c713fab3ab856da799`: Run basic
  5 steps, Submit 8, Sign in 5; 20 source files, source excerpts and exact line evidence.
- Offline menu/natural Ask resolver, typed directed runtime links kept separate from
  imports, layer overview, step controls and scoped keyboard navigation, evidence modal
  with real node inspection and optional pinned permalink. Normal Ask/aliases unchanged.
- Reusable optional `--tours`; exact repo/commit/source bounds validation before publish;
  stale/invalid artifacts preserved. Self demo honestly has no tours.
- 138 Python + 93 JS; all prior gates plus 29 tour browser checks, 18 ordered steps and
  every citation exercised, zero page/console errors or external requests; 11 screenshots.
- Source walkthroughs, not observed production execution; Google-only shipped auth UI
  vs email API alternative, Supabase/SQLite, Run/Submit and party reward branches disclosed.
- Open `dist/quest-refresh/index.html` or `dist/quest-coder.html`. Report:
  `docs/TOURS_REPORT.md`; logs `artifacts/tour-{build,test,smoke}.log`.

### Reusable refresh — historical worker evidence

Reusable maps and safe refresh locally verified on `reusable-refresh` from `f92d0cf`.
Integrated on main before 4898578; historical local-worker evidence follows. Open `dist/dag-gps/index.html` or
`dist/quest-refresh/index.html`; report `docs/REFRESH_REPORT.md`.

- One-command pinned Git archive → validated map/offline HTML/deterministic diff/report;
  generic discovery or explicit scope, origin identity/canonical local fallback.
- Staging before publish; rejected assignments/imports/cycles/render leave prior bytes;
  caught promotion error rollback tested (not a cross-file crash transaction).
- HTML source commit/ref vs build-time local HEAD, no offline live-freshness claim;
  same-repo exact aliases retained, deleted IDs ORPHAN, export/import fallback visible.
- 123 Python + 88 JS tests; unchanged existing eval/browser/parity gates plus 7 new
  refresh browser checks, zero errors/external requests. Five refresh screenshots inspected.
- Self snapshot f92d0cf: 3 layers/27 files/3 layer/19 file connections, 0 unresolved,
  4 unsupported dynamic requires. Quest frozen map/layers remain unchanged, 0 unresolved.
- CommonJS/UMD literal requires, .cjs/.jsx source discovery, multiline local Python imports;
  unsupported/ambiguous constructs explicit. No large extractor redesign or source guessing.
- Real synthetic committed snapshots prove added/deleted/typed edge/reassignment diff and
  browser alias migration; clearly labeled as synthetic, not user accuracy evidence.
- Exact gates/logs: artifacts/refresh-final-verification.json and refresh-{build,test,smoke}.log.

### Earlier integrated milestones — historical evidence

Alias learning, branch `alias-learning` (historical worker run; now integrated on main):

- `.verify.json` build/test/smoke exit 0: **106 Python + 87 JS tests**, including
  14 pure alias tests and safe trusted-source inlining; all 272 exact file paths
  protected against learned alias hijacking, including dynamic-route brackets.
- Explicit override → typed exact alias → review real target → confirm. No implicit
  learning. PATH learning disabled with single-endpoint-query guidance.
- Repo/version-scoped best-effort localStorage, immutable overlays, visible conflicts
  and orphan quarantine, inspect/remove/confirmed clear, browser JSON download,
  atomic validated previewed merge (default)/replace import. Denial/quota says Unsaved.
- Alias **19 UI checks**, 15/15 synthetic eval cases, 5 overlay parity cases;
  existing lookup **19**, M3 **5 canonical + 11 extra**, 47 original + 40 lookup
  source parity, canvas/interaction gates and pinned map checks remain passing.
  Browser reports contain zero page/console errors and zero external requests.
- `Python judge` baseline was already runner-service, reported honestly. Synthetic
  `Python judge station` demonstrates a real abstention → correction → repeat match.
  Existing bearer-auth challenge miss retained; no user queries fabricated.
- Map, layer membership, router, and both existing eval datasets byte-identical to
  `ba72d1b`. No quest-coder changes, remote writes, backend or automatic training.
- Report `docs/ALIAS_LEARNING_REPORT.md`; exact gates/logs in
  `artifacts/alias-final-verification.json`, `alias-{build,test,smoke}.log`;
  nine inspected screenshots `artifacts/alias-*.png`; best-effort storage limits documented.

### Filename lookup evidence

Filename lookup, branch `lookup-evidence` (historical worker run; now integrated on main):

- `.verify.json` build/test/smoke exit 0: **104 Python + 73 JS tests**, pinned map
  10/10 + full snapshot parity. Map, layers, router and original eval unchanged.
- File-first path/basename/stem/partial/spelling tiers; missing runner.py and typos
  require explicit override. Every duplicate basename path is offered; no-evidence
  unknowns have no arbitrary buttons and clear prior highlights. No persistence.
- Exact / Likely / Needs your choice / No match labels from evidence and margin,
  not percentages. Paths/reasons/aliases visible; raw uncalibrated Details accessible.
- Existing canvas interactions; M3 **5 canonical + 11 extra checks**; lookup **19 UI
  checks**, 47 original + 40 lookup shipped-source parity; zero errors/requests.
- Original generated regression: op 47/47, raw top-1/top-3 44/44, PATH 14/14, false
  accepted negatives 0/10. Separate worker-draft lookup challenge: op/labels 39/40,
  top-1 16/17, top-3 17/17, suggestion recall 15/15, false accepted negatives 0/24,
  wrong accepted requests 0/15. Bearer-auth responsibility abstention retained.
- Final p95: Node original 1.3480 ms (940), lookup 0.9129 ms (800); original
  Chromium 1.1000 ms (940). Draft fixtures, not held-out/user accuracy.
- Report: `docs/LOOKUP_REPORT.md`; logs: `artifacts/lookup-final-verification.json`;
  screenshots: `artifacts/lookup-{exact,missing,override,unknown,ambiguous,typo,stem,details,1280}.png`
  (nine inspected states; final Details/smaller viewport reinspected).

### M3 evidence

2026-10-07, branch `m3-routing` (historical worker run; now integrated on main):

- `.verify.json` build/test/smoke exit 0: **104 Python + 46 JS tests**, map 10/10
  at pinned `749d8b5de490cc2e6a0c98c713fab3ab856da799`; committed map untouched.
- Ask enabled, validated scorer boundary, Dependencies/Dependents/directed PATH,
  heuristic bars/top-three clickable overrides, honest abstention/no-path.
- 5/5 canonical real-typing/Enter/button browser states plus 11 additional UI checks;
  zero errors/external requests. Real-ID cross-layer file view; mixed endpoints
  explicitly unsupported. Existing canvas and real-click interactions pass.
- Scorer parity 47/47, Node p95 1.7014 ms / Chromium 1.0000 ms (940 samples each).
  Generated benchmark unchanged: op 46/47, target 42/44 top-1, 43/44 top-3;
  grading/authentication shortcomings retained honestly.
- Report: `docs/M3_REPORT.md`; logs: `artifacts/m3-final-verification.json`;
  screenshots: `artifacts/m3-{locate,dependencies,dependents,path,file}.png`
  plus no-path, file-path, 1280 states (inspected for clipping/collisions).

### M2 evidence

2026-10-07, branch `m2-scorer` (historical parent verification before M3):

- `.verify.json` build/test/smoke all exit 0: 99 Python tests, 40 JS tests,
  map 10/10 checks; existing canvas screenshots and real-click smoke pass.
- 47 generated eval cases, not user-ground-truth: operation 46/47 (97.87%),
  raw target top-1 42/44 (95.45%), top-3 43/44 (97.73%), PATH endpoints 14/14.
- Abstention 11/47; negatives 10/10 abstained, false accepts 0/10.
- p95 warm: Node 0.7754 ms, Chromium 0.7000 ms, 940 samples each (<10 ms).
- Chromium parity across 47 outputs (numeric tolerance 1e-12), zero errors/external
  requests; Ask still disabled. M1 template, renderer, node IDs and edges unchanged.
- Remaining scorer errors: grading → run-gateway (expected runner-service),
  authentication → NOT_SURE. Generated expectations need Eric review.
- Full report: `docs/M2_REPORT.md`; actual logs: `artifacts/m2-final-verification.json`.

### Previous milestone evidence

2026-10-07, branch `m1-file-edges`:

- `python3 -m unittest discover -s tests -q` — 78 tests, OK.
- `.verify.json` smoke (`build_map.py … --ref origin/main`) — 10/10 checks passed, exit 0,
  at quest-coder `749d8b5`. 18 layers + 272 files = 290 nodes, 52 layer edges
  (import 43, http 6, build 1, data 1, realtime 1), **413 file edges** (import 389,
  http 14, rpc 10; 324 cross-layer, 89 same-layer), 305 KB.
- `maps/quest-coder/map.json` is committed at this ref. `nodes`, `edges` and `layers` are
  byte-identical to the M0 map; the only additions are the top-level `file_edges` array
  and `meta.counts.file_edges`.


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
