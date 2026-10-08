# Status — DAG GPS

Last updated: 2026-10-07

## Current Focus

Filename lookup + evidence-first answers is locally verified on `lookup-evidence`,
based on approved M3 `1844aa2`. Parent independent rerun/review pending; no push
or merge. Open `dist/quest-coder.html` for the offline demo.

## Active Worker

None.

## Last Verified

Filename lookup, branch `lookup-evidence` (local worker; parent review pending):

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

2026-10-07, branch `m3-routing` (local worker; parent review pending):

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

2026-10-07, branch `m2-scorer` (parent independently verified before M3):

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
