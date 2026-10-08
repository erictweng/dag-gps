# V1.0 baseline — fresh execution, not v1 release

Worker `v1-baseline`, based on main **489857805e06e250462e545d213b09111417362e**.
Run: **2026-10-07 20:39–20:40 PDT** (2026-10-08 03:39–03:40 UTC).
V1.0 contains planning/foundation artifacts only; no impact, extractor, scorer or UI
implementation. Parent independent review/rerun/integration remains pending.

## Reproduction and actual evidence

All three unchanged non-null `.verify.json` recipes ran from repo root:

| Recipe | Actual return code | Wall time | Evidence under `artifacts/v1-baseline/` |
|---|---:|---:|---|
| build | 0 | 1.097 s | `build.stdout.log`, `build.stderr.log` |
| test | 0 | 11.698 s | `test.stdout.log`, `test.stderr.log` |
| smoke | 0 | 61.201 s | `smoke.stdout.log`, `smoke.stderr.log` |

`verification.json` records full exact command strings, timestamps, source commits,
recipe/input hashes, separate stdout/stderr, return codes and tool/environment probes.
`metrics.json` parses the real evaluator/browser results; `legacy-artifacts/` retains
browser JSON/screenshots; `retained-evidence-inventory.json` distinguishes 59 files
modified during this run from 37 older retained context files (all six browser
reports are fresh). `built/` preserves generated pinned outputs.
`run_baseline.py` is the local evidence recorder, not a substitute verification gate.
Absolute evidence root: `/Users/aibert/projects/dag-gps/artifacts/v1-baseline/`.
All evidence/output is ignored and must be retained locally or rerun by the parent.
Fresh-clone prerequisites: both Git source commits, Python/Node, sibling Playwright
(or `PLAYWRIGHT_DIR`), installed Chromium. No new dependencies were installed.
`.verify.json` needed **no** plumbing changes or placeholder/relaxed gates.

Recorded hardware/tools: Apple M4 Pro, 12 CPUs, 25,769,803,776 bytes RAM; macOS 26.1
(build 25B78), arm64. Python 3.9.6; Node v26.6.0; Git 2.50.1 (Apple Git-155);
Playwright 1.63.0 from `/Users/aibert/projects/quest-coder-assist/node_modules/playwright`;
Chromium 153.0.8010.12. Probe output, not an assumed environment, is in verification.json.

## Immutable sources and graph results

| Source snapshot (exact) | Layers | Inventory files | Layer links | File links | Unresolved imports | Unsupported | Non-source drops |
|---|---:|---:|---:|---:|---:|---:|---:|
| quest-coder `749d8b5de490cc2e6a0c98c713fab3ab856da799` | 18 | 272 | 52 | 413 | 0 | 2 | **14** |
| dag-gps `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93` | 3 | 27 | 3 | 19 | 0 | 4 | 11 |

Quest extractor: 182 nodes, 364 JS + 44 Python raw import pairs; file links contain
389 import / 14 HTTP / 10 RPC, 324 cross-layer (89 same-layer). Ten map checks and
full pinned parity pass, ignoring only documented ref/time metadata. Quest uses
explicit original tops; Python/SQL scans and assignment inventory differ from JS
scope. Do not describe all 272 files as extracted dependency nodes.

Quest's mutable local HEAD is not the audited source: build-time **local HEAD**
was separately probed as `a035ea2161b94323f474cf47908476c13f3285e4`. Its preexisting
untracked AGENTS.md/CLAUDE.md were untouched. Self local HEAD at build was `4898578`,
but self source stays `f92d0cf`. No fetch/latest refresh, source edits or remapping.
Before/after SHA-256 equality verified for both layer specs, quest map/tours and both
eval datasets. Tours still pin the same exact quest SHA. Self demo has no tours.

### Historical discrepancy retained, not papered over

Older STATUS/TASKS and REFRESH_REPORT say **15** non-source quest drops and some M1
notes say 409 raw pairs. The **new unchanged implementation run** prints **14** drops,
364 + 44 raw pairs, with **413 file links and complete frozen map parity unchanged**.
`built/quest-refresh/report.json` explicitly lists all 14 findings (one CSS, 13 JSON).
Historical count cannot be asserted as current; do not change the map/tests to fit
old prose. This looks like an older-extractor/counting-era discrepancy; V1.0 does
not establish its precise historical cause. Prior reports remain historical evidence.

## Historical versus freshly rerun metrics

| Metric | Historical source | Fresh V1.0 run |
|---|---|---|
| Python / JS tests | TOURS_REPORT: 138 / 93 | **138 passed / 93 passed**, zero failures |
| Original generated regression | TOURS_REPORT: op 47/47, top1/top3 44/44 | Same; PATH endpoints 14/14; negatives false accepted 0/10 |
| Lookup challenge | LOOKUP/TOURS_REPORT: op/label 39/40, top1 16/17, top3 17/17 | Same; suggestion recall 15/15, false accepted negatives 0/24, accepted wrong 0/15 |
| Synthetic alias regression | ALIAS/TOURS_REPORT: 15/15 | Same; wrong/negative accepts 0; shipped overlay parity preserved |
| Original warm Node scorer p95 | LOOKUP_REPORT: 1.3480 ms / 940 samples | **1.555708 ms / 940 samples** |
| Lookup warm Node p95 | LOOKUP_REPORT: 0.9129 ms / 800 samples | **1.010167 ms / 800 samples** |
| Original warm Chromium scorer p95 | LOOKUP_REPORT: 1.1000 ms / 940 samples | **1.200000 ms / 940 samples**, 47-case Node/browser parity |
| Alias warm Node p95 | Prior alias performance varies by run | **1.005250 ms / 450 samples** |

These are generated/development benchmarks, **not held-out, user-approved or
real-user accuracy**. Warm scorer timing is not cold initialization, graph layout,
full Ask UI or end-to-end latency. No V1.0 1k/5k-node benchmark is claimed.
`FAIL missing top-level 'layers'` in test stdout is an expected negative renderer
test; unittest stderr reports `Ran 138 tests ... OK`, and recipe return code is 0.

## Browser / smoke evidence

- Canvas four screenshot states and real-click interactions pass.
- M3: 5 canonical + 11 extra checks; lookup: 19; aliases: 19;
  refresh: 7; tours: 29. Counts parsed from actual preserved reports.
- Tour browser verifies all 18 steps and every step/link citation against immutable
  source; 11 tour screenshots retained. Runtime tour links remain separate from imports.
- All six preserved browser reports have zero recorded page/console errors and zero
  automatic external requests; screenshot output plus canvas/interaction results are
  in smoke stdout. Optional pinned GitHub navigation is user-initiated, not runtime fetch.
- Synthetic refresh fixture records actual generated Git before/after SHAs, typed
  connection/assignment diff and alias-orphan behavior; not a real user playtest.

## Known misses and release gaps

- `where is bearer auth?` (lookup l12) still expects runner-service/Likely in the
  worker challenge but yields NOT_SURE / Needs your choice, raw argmax auth and a
  supported runner-service suggestion. Honest unnecessary abstention, not a wrong
  accepted answer. Safety gates pass without requiring cosmetic perfect accuracy.
- `runner.py` does not exist in the frozen map; real alternatives require explicit
  selection. Eric's intended target is not confirmed. No invented Eric query labels.
- Mixed layer/file routes unsupported. Static map has extraction gaps: relative
  Python import in runner/__init__.py, computed Pyodide import, four self Playwright
  requires; configured JS aliases beyond root `@/`, other dynamic loaders and lexical
  syntax limits. Zero unresolved **imports** is not universal completeness.
- CSS/JSON have no nodes (14 quest, 11 self dropped import targets). Quest
  scripts/deployment_smoke.mjs literal `/api/private-pack` has no route handler;
  report contains one unresolved HTTP reference, distinct from unresolved imports.
- Self `f92d0cf` is old/pre-feature, not a current self-map. A newer explicit snapshot
  belongs to V1.3, not a silent V1.0 refresh.
- `file://` persistence is browser/path-dependent; export/import is recovery. No
  cross-tab sync guarantee. Publication is per-file atomic + caught-error rollback,
  not power-loss-safe multi-file transaction; one writer/open after success.
- Tours establish audited source boundaries, not observed quest-coder execution.
  No live auth/submission/tracing performed. Private excerpts require sharing review.
- Impact, trust UI/improvements, reviewed onboarding, feedback capture, release-scale
  audit and **Eric's unaided real session** remain unimplemented/pending.

No automated baseline blocker. V1.0 is **worker verified / parent pending**, not v1
complete. Parent must independently validate docs/spec and rerun relevant gates,
then integrate/push per WORKFLOW. V1.1a is ready for handoff **after that acceptance**,
not started. Contracts: [V1_ACCEPTANCE.md](V1_ACCEPTANCE.md),
[SUPPORTED_SOURCES.md](SUPPORTED_SOURCES.md), [V1_FIXTURES.json](V1_FIXTURES.json).
