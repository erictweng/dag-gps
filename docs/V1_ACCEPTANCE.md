# DAG GPS v1 acceptance contract

Approved scope: Eric's “Start with v1.0” / “Execute DAG GPS V1.0 only” authorization,
2026-10-07 PDT. The [user-authored milestone plan](../.hermes/plans/2026-10-07_203500-v1-milestones.md)
is authoritative; this contract records its defaults, not an extension of scope.
V1.0 is foundation only and was parent-accepted on main `6bfc5ee`.
Eric subsequently authorized full **V1.1a+b** (engine AND UI/Ask), worker-verified
on `v1-impact` and integrated on verified main `7bc6769`. Eric authorized full
**V1.2a+b+c**, integrated on main `a5b0255`. Eric authorized full **V1.3a+b+c**;
integrated on main `c6543f6`; Eric semantic review pending. Eric authorized full
**V1.4a+b+c**; opt-in capture/evaluation and held-out infrastructure worker verified
on `v1-feedback` and integrated on main `99652d1`. Eric authorized full **V1.5a+b+c**;
release worker audit is documented in [V1_RELEASE.md](V1_RELEASE.md). Parent release
review and human acceptance remain pending. Real-user tuning is deferred
until confirmed labels; no milestone here declares v1 released.

## Goal and locked defaults

Eric can orient himself in a supported repository, understand a feature, inspect
potential change impact, correct lookup vocabulary, and refresh the map without
assistant intervention or misleading claims.

- Desktop-first standalone offline/local HTML; mobile supports graceful inspection,
  not equivalent authoring. No browser network hot path, accounts or hosted inference.
- Pinned Git archive → validated map/evidence → offline HTML. Source snapshot and
  build-time local HEAD are separate; no offline claim of live remote freshness.
- Impact defaults to reverse **static import** evidence. HTTP/RPC potential boundary
  impact is separate; realtime excluded from default traversal. No execution/coverage
  tracing, guaranteed breakage, or inference that missing test edges mean “untested”.
- Query capture is optional, **off by default**, local only, explicit consent plus
  remove/clear/export. Existing alias correction requires separate review/confirmation;
  no silent learning. Query capture itself is not implemented by V1.0.
- Onboarding proposes deterministic groupings; a human reviews meaning before
  publication. Browser download/export followed by rebuild; no browser filesystem edits.
- Support means the [documented TS/JS/Python subsets](SUPPORTED_SOURCES.md), not
  universal language understanding. Limitations stay visible; expanding coverage is
  post-v1 unless a supported real repo blocks an approved acceptance check.
- User session is required for release; no fixed release date or schedule promise.

Out of scope: local trained model, free-form LLM explanations, automatic tours,
execution/coverage tracing, applying changes, live watcher, IDE plugin, cloud sync,
accounts, collaboration, backend hosting. Additions go to post-v1 unless Eric approves
an acceptance-blocking change. Worker implements; parent verifies/integrates and
[directly pushes main](WORKFLOW.md); workers never merge/push.

## Evidence and fixture rules

[V1_FIXTURES.json](V1_FIXTURES.json) names the two immutable real source repos and
existing/generated vs planned synthetic cases. No Eric-authored target labels are
available in this baseline. Real `runner.py` feedback establishes a failed lookup,
**not** Eric's intended replacement node; obtain his confirmation before labeling it.
Generated development regressions are not held-out/user accuracy. Preserve misses,
negative acceptance metrics and alias-off/alias-on results separately.

Current baseline evidence: [V1_BASELINE_REPORT.md](V1_BASELINE_REPORT.md).
`artifacts/v1-baseline/verification.json` records actual commands, stdout/stderr paths,
return codes, environment, versions, commits and input hashes. Evidence is ignored
and local, not magically present in a fresh clone. Parent reruns recipes from repo
root and retains its own evidence. No placeholders count as passing release gates.

## Release checklist and owners

Unchecked entries are **future acceptance**, not tests claimed to exist. Worker
owns implementation/test evidence; parent owns independent acceptance/integration;
Eric owns semantic review and unaided session. Milestone anchors below link the
approved plan. V1.0 is parent-accepted; V1.1a+b is integrated at `7bc6769`;
V1.2a+b+c is integrated at `a5b0255`; V1.3 is integrated at `c6543f6` with Eric
semantic review pending. V1.4 feature gates are integrated at `99652d1`; real-user labeling/tuning remains
deferred. V1.5 automated worker gates are separate from Eric semantic review and
unaided session; both remain unchecked until a real human outcome is recorded.

| State | Check / milestone | Required evidence | Owner |
|---|---|---|---|
| Parent accepted | [V1.0](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v10--freeze-the-release-contract-and-baseline): reproducible baseline, coherent status, matrix, contract | Non-null `.verify.json` build/test/smoke exit 0; exact pinned parity, retained miss, report and fixture manifest | Worker; parent independent rerun/review |
| Integrated main `7bc6769` | [V1.1a](../.hermes/plans/2026-10-07_203500-v1-milestones.md#mini-11a--pure-analysis): explainable FILE impact | 10 pure impact tests: cycles/shortest/order/immutability, distinct direct/transitive, unknown/isolated, HTTP/RPC separation, path-classified tests, raw/compiled exact citations/orphans; coverage always unknown. [Actual report](IMPACT_REPORT.md) | V1.1 worker; parent independent review |
| Integrated main `7bc6769` | V1.1b: UI and impact Ask | 14 real browser checks / 9 inspected screenshots: runner-client and quest_runner, source-audited witnesses/tests, unknown/ambiguity fail closed, typed chain/real-file inspection/tour recovery, 1280/1920 and no-tours second map; all legacy gates retained, zero errors/network. [Evidence](IMPACT_REPORT.md) | V1.1 worker; parent independent browser/code review |
| Integrated main `a5b0255` | [V1.2](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v12--map-trust-and-completeness): evidence quality / extraction | Versioned map/report categories/scope/counts; concrete path/reason navigation and contextual vs repo-level warnings; fixture-first relative Python/namespace/init/submodule and narrow static paths/CommonJS/TS, no suffix guessing/runtime completeness fiction; 161 Python + 109 JS; trust10 checks / 13 inspected 1280/1920 screenshots, all legacy gates pass. [Report/migration](TRUST_REPORT.md) | V1.2 worker; parent independent review/rerun |
| Integrated main `a5b0255` | V1.2 stale tours / refresh integrity | Exact-commit/malformed rejection preserves every prior artifact byte; mutually-exclusive explicit `--without-tours`, no stale natural-query evidence, legacy HTML/comparison bypass rejected; same pins, +2 quest / +1 self audited pairs, none removed; full strict parity; file/self cycles retained, layer cycles actionable and blocking | V1.2 worker; parent; Eric for future architectural decisions |
| Integrated main `c6543f6`; Eric pending | [V1.3](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v13--reviewable-repo-onboarding): draft → review → export → publish | Deterministic pinned folder proposals, offline editor/exact-file reviewed export, actual downloads build quest 749d8b5 and newer self a5b0255; 176 Python + 130 JS, onboarding14 / 10 inspected screenshots, all legacy gates; no missing/double/empty/cyclic final assignments, invalid all-byte preservation, stable IDs/manual migration warnings; explicit self 47/48 scan and blocked unrestricted draft retained. [Actual report](ONBOARDING_REPORT.md) | V1.3 worker; parent independent acceptance; Eric semantic review (automated samples do not satisfy human gate) |
| Integrated main `99652d1` | [V1.4](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v14--opt-in-real-query-evaluation-parallel-track): consent and evaluation | 20 feedback tests; 18 browser checks / 6 inspected screenshots; opt-in/export/remove/confirmed clear, bounded inert imports/storage fallback, full snapshot/scorer/overlay provenance, generated/user/dev/frozen heldout distinctions; [report](USER_EVAL_REPORT.md); ≥20 Eric cases soft goal | V1.4 worker; parent; Eric labels intent |
| Infrastructure verified; real-user claims deferred | V1.4 accuracy claims | Actual downloaded generated set 8 records / 4 evaluable / 0 user labels; original/off/on accepted wrong, abstentions, top1/top3, independent BFS no-path and warm scorer p95; missing labels block user accuracy/tuning, not feature | Worker measures; parent audits; Eric confirms |
| Worker audit; parent/human pending | [V1.5a](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v15--release-usability-and-performance): full workflow on both demos | Actual recorded two-repo find → inspect → tour (or explicit unavailable) → impact → alias correction/export → grouping edit → refresh → import; no stale highlights, overlapping controls or impossible recovery | Release worker; parent |
| Worker checks; parent pending | V1.5b: scale / accessibility | 1280/1920 desktop and graceful 390px; keyboard/focus/Escape, contrast/names/reduced motion; declared real graphs + labeled synthetic 1k/5k nodes, recorded hardware; warm scorer p95 <10ms, cold init/layout/full Ask separately | Release worker; parent |
| Candidate only; parent/human pending | V1.5c: reproducible release / safety | All legacy and implemented milestone gates; versioned manifest, pinned regeneration/CLI/setup/storage recovery docs; zero automatic external requests, malformed imports inert, immutable excerpts verified, failed build preserves output, no silent learning, no P0/P1 defects | Release worker; parent |
| Human pending | v1 final acceptance | **Eric completes one real repository session without operational assistant help**, with session outcome recorded; semantic layer/expectation review, unresolved severe defects closed | Eric; parent records verdict |

Automated gates alone permit a release candidate, **never “v1 complete”** while the
human session is pending. Optional explicit pinned GitHub evidence-link navigation
is not an automatic browser request. Review bundled private source excerpts before
sharing; no automatic public upload.

## Known constraints that must not disappear in release prose

Mixed layer/file routes are unsupported; bearer-auth responsibility lookup abstains.
Dynamic Python/conditional search paths and nonliteral JS imports leave gaps; configured JS aliases
other than root `@/` are not resolved. CSS/JSON targets have no nodes. Self demo
currently audits old `f92d0cf`, not current feature coverage; V1.3's separate newer
`a5b0255` onboarding demo explicitly scans 47/48 inventory files because an archived
smoke consumer references generated untracked JSON. Its unrestricted draft is visibly
blocked; no extraction-completeness claim. `file://` storage is
best-effort with export/import recovery; no cross-tab synchronization guarantee.
Publication is per-file atomic with caught-error rollback, not a power-loss-safe
multi-file transaction. Tours are audited source explanations, not observed execution.
These are documented limitations, not new scope decisions. Parent must return any
contradictory scope or acceptance-blocking uncertainty to Eric rather than weaken tests.

## V1.1 delivery boundary

Eric authorized both V1.1a+b after V1.0 parent acceptance. Actual pinned graph/source
was audited before fixtures; `lib/runner-client.ts` has zero observed linked tests,
while `runner/quest_runner.py` has eleven real import-linked tests. Neither establishes
coverage. Engine plus Inspect/Ask UI are integrated at `7bc6769`. These are historical
V1.1 expectations; V1.2 adds the source-audited twelfth runner test and records the
same-pin migration in [TRUST_REPORT.md](TRUST_REPORT.md).
Extractor/trust redesign, onboarding and query logging remain outside V1.1.
V1.4 shared scorer/UI writes remain serialized; no later milestone launched by V1.1.

## V1.4 delivery boundary

Off-by-default local consented history/labels/export/import and versioned reproducible
user-evaluation infrastructure are worker-verified; [USER_EVAL_REPORT](USER_EVAL_REPORT.md)
records actual full gates, 20 feedback tests, 18 browser checks and generated exported
results. Labels do not teach aliases; Unclear/unknown Wrong intent are not ground truth.
Source/scorer/overlay provenance, frozen user-controlled holdout before first labeling,
original/alias-off/on reports and independent realtime-free PATH truth are implemented.
Tours/impact are visibly excluded, not relabeled as scorer operations. Mini c real-user
scorer changes are **deferred**: zero confirmed Eric labels, no synthetic tuning; actual
runner.py feedback remains unconfirmed. ≥20 cases is a soft goal, not a feature blocker.
V1.4 is integrated at `99652d1`; parent release verification, Eric label collection
and human acceptance remain pending. This is not a real-user accuracy or final-release
claim. V1.5 candidate evidence is in V1_RELEASE.md.

## V1.3 delivery boundary

Eric authorized full reviewed onboarding. Worker verified deterministic pinned drafts,
offline editor, actual downloaded export/build and real-path Ask on both declared real
repo scopes. Draft schema and reviewed exact-file schema are separate; confirmation
never defaults on, and reviewed imports require fresh review. Legacy glob compatibility
is explicit, not automatic browser approval. Invalid candidates retain prior artifacts.
Splits/merges/deletes warn about layer reference migration; no rebinding or tour rewrite.
Real cycle file pairs stay intact and visible. New self a5b0255 is a separate supported
snapshot/draft/sample, not relabeling the frozen f92d0cf matrix.

[ONBOARDING_REPORT.md](ONBOARDING_REPORT.md) records actual tests/browser downloads,
source scopes/counts, inert bounded imports, retained full-discovery failure and legacy
gates. **Eric semantic review still required**: automation exercises explicit confirmation
but is not human architectural approval. V1.3 is now integrated at `c6543f6`.
V1.4 query capture/evaluation is a separate delivery below; V1.5 release remains pending.
