# Tasks — DAG GPS

Work is organized as milestones broken into mini-milestones. Each mini-milestone
should be small enough for one worker run to finish and verify.

Status values: `queued` | `running` | `verified` | `blocked` | `failed`

## Now — approved v1 sequence

Authoritative [v1 plan](.hermes/plans/2026-10-07_203500-v1-milestones.md),
[acceptance/evidence owners](docs/V1_ACCEPTANCE.md), [supported sources](docs/SUPPORTED_SOURCES.md),
[fixture manifest](docs/V1_FIXTURES.json). V1.0 is parent-accepted on main `6bfc5ee`,
V1.1 integrated at `7bc6769`, V1.2 integrated at `a5b0255`; Eric authorized full
**V1.3a+b+c**, now integrated at `c6543f6`, and full **V1.4a+b+c**. V1.4
integrated at `99652d1`; real-user tuning deferred. Worker samples
do not replace Eric's semantic review.

| Milestone | Status | Evidence / next action |
|---|---|---|
| V1.0 baseline and contract | **parent accepted** | Main `6bfc5ee`; [baseline](docs/V1_BASELINE_REPORT.md), 138 Python + 93 JS at that milestone |
| V1.1a pure impact analysis | **integrated main `7bc6769`** | 10 pure impact tests; audited real witnesses, import-only BFS, separate HTTP/RPC, coverage unknown; [historical report](docs/IMPACT_REPORT.md) |
| V1.1b impact UI/Ask | **integrated main `7bc6769`** | Historical 14 browser checks / 9 screenshots; legacy gates retained in V1.2 |
| V1.2a trust contract / diagnostics UI | **integrated main `a5b0255`** | Map/report V2 scope/category/count provenance; concrete findings/filter/navigation, relevant Ask/impact warning or explicit repo-level uncertainty; [report](docs/TRUST_REPORT.md) |
| V1.2b narrow extraction | **integrated main `a5b0255`** | Fixture-first relative Python/namespace/init/symbol vs submodule, explicit static paths/loaders with no suffix guessing, narrow CommonJS/TS; cycles retained; same source pins, audited +2 quest / +1 self pairs, none removed |
| V1.2c stale-tour handling | **integrated main `a5b0255`** | Exact validation preserved; explicit mutually-exclusive `--without-tours`, malformed/stale all-byte preservation, legacy/comparison omission bypass blocked, no stale natural query |
| V1.2 full automated gate | **integrated main `a5b0255`** | `.verify.json` build/test/smoke exit 0; 161 Python + 109 JS, strict pinned parity/10 checks; all legacy browser/eval gates plus trust10 / 13 inspected 1280/1920 screenshots, zero errors/network |
| V1.3a deterministic draft | **integrated main `c6543f6`** | Same pinned archive/discovery/exclusions/extractor; complete ownership, stable folder IDs, root/helper reasons, no auto architecture claim; [report](docs/ONBOARDING_REPORT.md) |
| V1.3b offline review editor | **integrated main `c6543f6`** | Rename/move/split/merge/delete/search/undo/reset, migration warnings/no rebinding, inert ≤8 MiB imports, real cycle evidence and explicit review/export |
| V1.3c real export/build roundtrip | **integrated main `c6543f6`; Eric semantic review pending** | Actual downloads build new self a5b0255 (48 files, 3 layers, 38 links) and quest 749d8b5 (272, 38, 415); real Ask, invalid all-byte preservation; declared self 47/48 scan, blocked unrestricted draft retained |
| V1.3 full automated gate | **integrated main `c6543f6`** | All `.verify.json` recipes exit 0; 176 Python + 130 JS, strict parity/all legacy gates; onboarding14 / 10 inspected 1280/1920 screenshots, zero errors/network; worker samples not Eric-approved |
| V1.4a opt-in history/labels | **integrated main `99652d1`** | Explicit consent/OFF each load, indicator, completed scorer Ask, visible tour/impact exclusions, Correct/Wrong/Unclear independent expectations, local deletion/clear/download/atomic inert imports, bounds/unsaved fallback |
| V1.4b provenance/evaluation | **integrated main `99652d1`** | Full pin/map/scorer SHA/overlay, original/off/on, user/generated/dev/heldout separation, first-label heldout freeze; independent route BFS; counts/top1/top3/warm scorer p95; [report](docs/USER_EVAL_REPORT.md) |
| V1.4c real-user improvement | **deferred — user labels pending** | No scorer tuning on generated fixtures; actual runner.py intent unconfirmed; collect ideally ≥20 confirmed Eric cases and designate genuine holdout before tuning |
| V1.4 full automated gate | **integrated main `99652d1`** | 176 Python + 150 JS; 20 feedback tests, full build/test/smoke/legacy parity exit 0; feedback18 / 6 inspected screenshots, zero errors/network; actual generated export 8 records / 4 evaluable / 0 user-labeled |
| V1.5a full-session audit | worker audited; parent/human pending | Both actual find/inspect/tour-or-unavailable/impact/alias/export/grouping-download/refresh/import/feedback flows; `artifacts/release-browser.json` |
| V1.5b scale/accessibility | worker checks; parent pending | Real maps + exact synthetic 1000/5000 nodes; separate scorer/layout/full Ask, Axe and computed SVG contrast, 1920/1280/390 and actual keyboard recovery; [release evidence](docs/V1_RELEASE.md) |
| V1.5c packaging/docs | candidate only; parent/human pending | Repeatable fail-closed release runner, versioned local-only manifest/hashes/sizes, private-source review, install/build/test/storage guide; **Eric unaided session and semantic review still pending** |

No automated V1.3 blocker within declared scope; unrestricted new self scan correctly
rejects its generated fixture and remains visible. Parent owns independent acceptance/
integration/direct main push per WORKFLOW; worker commits locally only. Eric semantic
review remains pending. V1.4 logging is now opt-in only; no quest-coder source edits or
v1 release claim. V1.4 evidence above; historical V1.3 evidence: `artifacts/onboarding-verification.json`, `onboarding-browser.json`,
`onboarding-*.png`, `.hsub/build-updates/v1-onboarding*.md`; legacy pins/maps retained.
The old worker-local/pending statuses below are historical and now integrated as
of baseline main 4898578; old metrics are not a fresh execution. Fresh quest
non-source drops are 14 versus historical prose's 15 (see baseline discrepancy).

## Integrated pre-v1 history

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
Status: integrated on main; historical `m3-routing` worker results below.

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
Status: integrated on main; historical `lookup-evidence` run based on `1844aa2` below.

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
Status: integrated on main; historical `alias-learning` run from `ba72d1b` below.
All regression examples are synthetic, not user evidence.

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

## Reusable maps and safe refresh

Status: integrated on main; historical `reusable-refresh` run from `f92d0cf` below.

- One-command repo/ref/layers → staged validated map.json/index.html/diff.json/report.json.
- Immutable Git archives; generic source discovery or explicit scope; actual origin identity.
- Deterministic added/deleted files/layers, typed connections, node/assignment changes;
  visible source provenance and diff summary, no offline live-freshness promise.
- Reject unmapped/duplicate/unresolved/cycle candidates, preserve valid published bytes;
  caught promotion failure rollback tested and cross-file/crash limits documented.
- CommonJS/UMD/CJS and multiline Python local-script coverage with honest unsupported findings.
- Independent real self-repo snapshot/layer draft (f92d0cf), actual source Ask and graph clicks.
- Same repo aliases survive rebuild; deleted IDs remain orphan, never guessed/rebound;
  best-effort file storage and visible export/import fallback.
- 123 Python + 88 JS; prior gates retained; new refresh browser 7 checks, no errors/network;
  five screenshots inspected; synthetic fixture compares actual before/after Git commits.
- Report docs/REFRESH_REPORT.md; .verify.json exercises both repos. Quest map/layers untouched.

## Architecture-guided tours

Status: integrated on main at `4898578`; historical tours run from `3e811d9` below.

- Three tours at exact quest-coder archive SHA `749d8b5de490cc2e6a0c98c713fab3ab856da799`:
  Run basic (5), Submit (8), Sign in (5), grounded in code/function/constant evidence.
- Brief receives/does/passes narration, actual inline excerpts/path/lines, immutable links;
  overview highlights involved layers, current-step files/context and distinct typed tour edges.
- Explicit natural Ask resolver before scorer/learned aliases; previous/next/reset/exit,
  appropriate keyboard controls, modal focus and real node inspection. No import trace fiction.
- Generic optional tours compiler/render/build, exact repo/SHA/IDs/line/source checks;
  failed stale/invalid builds preserve prior artifacts; second self repo has zero tours.
- 138 Python + 93 JS tests; 29 real browser checks for all 18 steps/every citation;
  11 inspected screenshots, zero errors/external requests; all legacy gates/evals retained.
- Report `docs/TOURS_REPORT.md`; verification logs `artifacts/tour*`; no quest-coder edits,
  model/network/training changes or graph/scorer/alias mutation.

## Backlog

- Eric review/correction of generated eval answers and map aliases.
- M4 hosted backend remains dropped unless revisited.

## Current release acceptance pending

- Eric unaided real-repo session and semantic grouping review.
- Parent independent release review/rerun and direct-main integration/push.
- V1.4 real-user tuning deferred until confirmed labels / pre-tuning holdout; ≥20 is a soft goal.

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

## V1.5 independent-review fixes — local worker, parent/human pending

Independent review of `757df72` blocked integration on IR-01 (P1 unbound generated
payloads), IR-02 (P2 incomplete gate inputs/provenance) and IR-03 (P2 keyboard focus).
The isolated `v1-release-fixes` follow-up adds regression-backed v2 byte/inventory
binding, producer-boundary freezing, staged rejection preserving the previous bundle,
complete recursive test/data/doc inventory and HEAD/worktree provenance, plus real
keyboard paging/expansion focus assertions. Old receipts require a full rerun.
Exact outcomes/evidence and residual risks: [RELEASE_REVIEW_FIXES.md](docs/RELEASE_REVIEW_FIXES.md).
Two actual precommit complete runs and packaging passed; the later run had
192 Python / 152 JS, all eight gates, 32 screenshots, 23 Axe states and 50,000
scorer samples. Real receipt mirror accepted clean packaging and rejected 15/15
negative probes with previous bundle bytes preserved. **Renewed Phase 0 precommit verification passed** all eight unchanged recipes and
packaging (192 Python / 152 JS; worst scorer p95 4.557041 ms). Independent source
review passed IR-01/IR-02/IR-03; fresh real-receipt probes accepted 1/1 clean package
and rejected 17/17 negatives, preserving all previous bundle bytes, including
injected promotion/readback faults. Earlier performance failures remain retained.
Local fix commit and exact-postcommit rerun follow; only the final clean-provenance
receipt certifies the exact committed bytes. No main integration or human acceptance
is implied. Evidence: `artifacts/phase0-precommit/`, `artifacts/phase0-independent-review/`;
final handoff: `artifacts/phase0-completion.json`.
Do not treat worker verification as final acceptance.
Parent independent re-review, Eric semantic grouping and unaided real session remain
pending. No push/merge/public artifact upload or later milestone in this follow-up.

## Phase 0 — repository-evidence workspace foundation (local only)

Eric authorized Phase 0 on 2026-10-08. The separate roadmap commit is aa6a1e8;
release-fix commit 9a5a327 passed exact-postcommit all eight unchanged gates and
packaging with clean provenance. Independent IR source review passed; parent fresh
17/17 negatives (including promotion/readback rollback) preserve all prior bundle bytes.
Earlier load-sensitive performance failures remain retained; no gate or scorer tuning.

The new foundation defines pure pinned snapshot/evidence guards and false-by-default
query/agent controls, documented in docs/WORKSPACE_CONTRACT.md and
WORKSPACE_ACCEPTANCE.md. Focused contract tests initially passed 38/38, but independent review found three
medium-severity gaps. Stricter fixes now pass 47/47 focused and all Python 239 /
JS 152; initial review and 47-test/16-failure RED remain retained.
New-contract independent review and exact final-commit full verification are required
before handoff; artifacts/phase0-completion.json and artifacts/phase0-final/ are the
final authority, not a claim that future features are implemented.

No GitHub-link importer, workspace service/UI, agent invocation, live updates or
third-party graph mapping was started. Local-versus-hosted and agent-provider choices
remain pending before Phase 1. Human unaided workflow and semantic review are pending;
no push/merge, deployment, private-source upload or final v1 acceptance.

## Phase 1 acquisition — worker availability blocked (2026-10-08)

Eric approved local-first/existing-agent defaults. Isolated workspace-repo-import
starts from verified e94cfba; current work is URL validation and immutable public
GitHub acquisition, not a server/UI or agent runtime. Declared public fixture:
pallets/itsdangerous at 672971d66a2ef9f85151e53283113f33d642dabd.

Claude Code hsub run 20261008-150944-05823f exited 1 at its weekly usage limit
before implementing source. Its reported reset is 6pm America/Los_Angeles.
app/repositories.py and tests/test_repository_import.py are absent; no Phase 1
success or commit is claimed. Handoff/build note and exact logs/report are retained.
Await Eric's permission to switch to the configured OpenAI coding worker, or wait
for reset. No raw Anthropic fallback, source execution, push/merge or future phase.

### Worker fallback authorized and running

Eric explicitly selected OpenAI GPT-5.6 Sol. Run 20261008-151949-a33182 is active
on the acquisition mini, pinned to gpt-5.6-sol / openai-codex by per-invocation
flags, with no global model/config change or silent alternate-model delegation.
Prior Claude quota block is historical; fallback availability is resolved, not
feature acceptance. Runtime metadata and initial RED-test creation were verified;
implementation/full tests and actual public import remain pending parent checks.

### Phase 1 receipt-bound fix + first full gate attempt (2026-10-08)

IRP-01 residual fixed directly by the parent (Eric's instruction, no worker):
`receipt.json` capped at MAX_RECEIPT_BYTES (64 KiB), rejected from lstat size
before open; in-limit receipts read once via a no-follow fd whose dev/inode must
match. RED retained (65,537-byte receipt fully decoded before rejection); GREEN
snapshot 17/17, preview 9/9, acquisition 25/25. Reviewer's own follow-up probe
now shows readAttempted=false on its 5.2 MB receipt; all 28 other independent
properties still hold. Fresh pinned itsdangerous import and file:// browser
click/Enter regression pass on the new bytes. Evidence: artifacts/phase1-receipt-bound-fix/.

Full precommit `artifacts/phase1-precommit/`: build, test (290 Python / 152 JS),
smoke, release_session, accessibility passed; performance FAILED, worst scorer p95
12.4565 ms vs unchanged 10 ms target at load ~10-11 on 12 CPUs, host saturated by
desktop Google Chrome. web/, bench scripts and maps are byte-identical to e94cfba
(passed at 4.557 ms). UI performance, milestone acceptance and packaging not
reached. No gate/sampling change, no commit; retry unchanged on a quieter host.

Retry after Eric closed desktop Chrome: `artifacts/phase1-precommit-2/` passed all
eight unchanged gates plus packaging; worst scorer p95 3.7377 ms (target 10 ms),
290 Python / 152 JS. Confirms the earlier 12.46 ms failure was host contention;
the failed receipt is retained. Exact-commit verification follows the local commit.
Human unaided-workflow and semantic grouping acceptance remain pending; no push/merge.
