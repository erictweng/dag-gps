# Status — DAG GPS

Last updated: 2026-10-07 PDT

## Current focus — V1.3 onboarding worker verified / parent pending

Worker `v1-onboarding` starts from clean main `a5b0255` (integrated V1.2).
No worker push/merge. Full draft → offline review → actual download → validated build
implemented; parent independent acceptance and Eric semantic review remain pending.

- Deterministic pinned folder proposals use the same archive/discovery/exclusion and
  extraction pipeline; explicit flat-root/helper reasoning, exact ownership and stable IDs.
- Dependency-free offline editor: real path search, rename/move/split/merge/delete,
  coverage/empty/cycle evidence, undo/reset, bounded inert imports, visible manual
  alias/tour migration warnings and explicit confirmation before reviewed download.
- Drafts reject publication. Reviewed exact-file specs validate repo/full pin/inventory/
  scope/coverage/dependencies before promotion; legacy glob specs remain compatible.
- Actual browser downloads built BOTH real demos with real-path Ask: new self `a5b0255`
  **48 files / 3 layers / 38 file links**; quest `749d8b5` **272 / 38 / 415**. Existing
  approved quest map/layers/tours and old self `f92d0cf` matrix preserved.
- Both initial folder drafts are acyclic. Real quest runner-client split reveals grouping
  cycle with source pairs; UI merge repairs it without deleting any file links.
- New self full discovery correctly blocks on generated untracked refresh-fixture.json.
  Explicit supported scope scans **47/48**, keeps **all 48 assignments**; blocked draft
  retained. No source mutation/fixture injection or full-coverage claim. Details:
  [ONBOARDING_REPORT](docs/ONBOARDING_REPORT.md).
- `.verify.json` build/test/smoke **exit 0**, **176 Python + 130 JS**; every legacy gate
  retained, full strict pinned parity/10 checks. Onboarding **14 browser checks / 10
  inspected 1280/1920 screenshots**, zero errors/external requests. Invalid downloaded
  candidates preserve all four output bytes; reviewed reimports clear confirmation.
- Evidence: `artifacts/onboarding-verification.json`, `onboarding-{build,test,smoke}.log`,
  `onboarding-browser.json`, `onboarding-*.png`. Editors `dist/onboarding-{dag-gps,quest}.html`;
  built demos `dist/onboarding-{dag-gps,quest}/index.html`. Existing user artifact
  `dist/quest-refresh/index.html` still carries approved map/tours. Outputs local/ignored.
- **Automated worker review samples are not Eric-approved semantics**. Eric still reviews
  proposed responsibilities/reference meaning; no V1.4 query capture or v1 release claim.

## Integrated V1.2 — historical worker evidence (main `a5b0255`)

Worker `v1-trust` starts from clean, verified main `7bc6769` (integrated V1.1).
No worker push/merge. All approved trust, narrow extraction and stale-tour minis built.

- Version-2 map/report provenance: five categories, concrete paths/reasons, exact
  scope/inventory denominator, file cycles and separate lexical/loader/curated/inferred
  evidence. Offline findings navigation plus file/Ask/impact contextual warnings;
  otherwise explicitly repository-level uncertainty, never runtime-completeness percent.
- Fixture-first package-relative Python, namespace/init and concrete submodules;
  narrow explicit file-relative paths/loaders preserve real dependencies without
  suffix guessing. Whitespace CommonJS/TS + indented imports; unsupported constructs
  stay visible. File/self cycles retained; layer cycles still block for grouping review.
- Mutually-exclusive `--without-tours` / `--tours`; exact stale validation stays fail
  closed. No silent omission, including legacy HTML/comparison overrides. Omitted
  evidence cannot resolve a natural tour query; reason/current/unavailable status visible.
- `.verify.json` build/test/smoke **exit 0**, **161 Python + 109 JS**; strict full pinned
  parity/10 checks and every legacy eval/browser gate retained. Trust browser **10
  checks / 13 inspected screenshots** at 1920/1280, zero errors/external requests.
- Same source pins: quest `749d8b5` / self `f92d0cf`. Deliberate extractor migration
  quest **413 → 415**, self **19 → 20** file pairs; no removals, node/membership/source
  edits. Exact pairs/weight changes, fixture rationale and impact audit in
  [TRUST_REPORT](docs/TRUST_REPORT.md). Runner engine: 16 direct / 12 linked tests;
  runner-client unchanged 3 direct / 1 farther / no observed linked tests. Coverage unknown.
- Quest scanned **182 / 272**, 90 unscanned; 14 non-source, **0 unresolved imports**,
  1 literal HTTP miss, 8 unsupported, 280 external findings. Self **27 / 27**, 11
  non-source, 0 unresolved, 4 unsupported, 94 external findings. Not runtime coverage.
- Evidence: `artifacts/trust-verification.json`, `trust-{build,test,smoke}.log`,
  `trust-migration.json`, `trust-browser.json`, `trust-*.png`. Open
  `dist/quest-refresh/index.html`, `dist/quest-coder.html`, `dist/dag-gps/index.html`,
  or explicit opt-out `dist/quest-no-tours/index.html`. Outputs remain local/ignored.

## Integrated V1.1 — historical worker evidence (main `7bc6769`)

V1.0 parent acceptance is integrated on main `6bfc5ee`. Eric authorized full V1.1,
not only the pure engine. `v1-impact` starts from that clean main; no worker push/merge.

- Dependency-free `analyzeImpact(map,tours,fileId)` with deterministic shortest
  import-only reverse BFS witnesses, distinct direct/transitive results, real tests,
  exact raw/compiled tour citations and separate transitive HTTP/RPC boundaries.
- File-detail **Inspect potential impact** and explicit natural Ask; ambiguity/missing
  suggestions require choice, unknowns clear stale state, existing DOWNSTREAM unchanged.
  Recoverable summary, typed witness graph, real-file inspection and offline tour evidence.
- `.verify.json` build/test/smoke **exit 0**: **138 Python + 103 JS** (10 impact tests),
  pinned map 10/10 + full parity; all legacy eval/canvas/scorer/M3/lookup/alias/refresh/tours
  gates retained. New browser: **14 checks / 9 screenshots**, zero page/console errors
  and external requests, both real files plus self no-tour map; 1280/1920 visual inspection.
- Audited `lib/runner-client.ts`: 3 direct imports + 1 farther consumer, **no observed
  linked tests / coverage unknown**; 6 separate boundary witnesses and 4 exact tour
  citations (steps and links). `runner/quest_runner.py`: 14 direct imports, 11 real
  linked tests visible despite hidden canvas test layer; coverage still unknown.
- Quest map/layers/source/tours/evals/scorer/router/extractor unchanged from `6bfc5ee`.
  Pins retained: quest `749d8b5de490cc2e6a0c98c713fab3ab856da799`, old self
  `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93` (not today's source graph).
- Report: [IMPACT_REPORT](docs/IMPACT_REPORT.md). Evidence: `artifacts/impact-verification.json`,
  `impact-{build,test,smoke}.log`, `impact-browser.json`, `impact-*.png`.
  Open `dist/quest-refresh/index.html`, `dist/quest-coder.html`, `dist/dag-gps/index.html`.

## Active worker / next action

V1.3 implementation and local verification complete. Parent independently reviews
onboarding spec/code quality, explicit new self extraction scope, actual downloads,
cycle/migration safety and browser evidence, reruns gates, then integrates/pushes main
per [WORKFLOW](docs/WORKFLOW.md). Eric reviews semantic grouping; automated samples do
not satisfy that gate. V1.4 writes stay serialized against shared UI/scorer.

## Blockers and release boundary

No automated V1.3 blocker within its declared supported scope; unrestricted self
extraction correctly fails on the generated fixture and is visibly retained. Parent
V1.3 acceptance and Eric semantic review remain pending. Entire v1 is **not** complete:
optional evaluation/release and Eric's unaided session remain.
Impact is static potential reachability, not execution/coverage or guaranteed breakage.
Known prior limitations retained: mixed layer/file routes, bearer-auth abstention,
dynamic Python/conditional paths and lexical JS gaps, omitted CSS/JSON nodes, old self snapshot,
best-effort file storage/export fallback, per-file publication not power-loss transaction,
source walkthroughs not observed runtime. See [acceptance](docs/V1_ACCEPTANCE.md),
[supported sources](docs/SUPPORTED_SOURCES.md), [baseline](docs/V1_BASELINE_REPORT.md).

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
