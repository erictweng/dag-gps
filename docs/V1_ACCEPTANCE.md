# DAG GPS v1 acceptance contract

Approved scope: Eric's “Start with v1.0” / “Execute DAG GPS V1.0 only” authorization,
2026-10-07 PDT. The [user-authored milestone plan](../.hermes/plans/2026-10-07_203500-v1-milestones.md)
is authoritative; this contract records its defaults, not an extension of scope.
V1.0 is foundation only and was parent-accepted on main `6bfc5ee`.
Eric subsequently authorized full **V1.1a+b** (engine AND UI/Ask), worker-verified
on `v1-impact`. V1.1 parent independent review/rerun/integration remains pending;
neither milestone declares v1 released.

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
approved plan. V1.0 is parent-accepted; V1.1a+b worker checks are complete but
remain parent-pending. Later unchecked gates are still future work.

| State | Check / milestone | Required evidence | Owner |
|---|---|---|---|
| Parent accepted | [V1.0](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v10--freeze-the-release-contract-and-baseline): reproducible baseline, coherent status, matrix, contract | Non-null `.verify.json` build/test/smoke exit 0; exact pinned parity, retained miss, report and fixture manifest | Worker; parent independent rerun/review |
| Worker verified; parent pending | [V1.1a](../.hermes/plans/2026-10-07_203500-v1-milestones.md#mini-11a--pure-analysis): explainable FILE impact | 10 pure impact tests: cycles/shortest/order/immutability, distinct direct/transitive, unknown/isolated, HTTP/RPC separation, path-classified tests, raw/compiled exact citations/orphans; coverage always unknown. [Actual report](IMPACT_REPORT.md) | V1.1 worker; parent independent review |
| Worker verified; parent pending | V1.1b: UI and impact Ask | 14 real browser checks / 9 inspected screenshots: runner-client and quest_runner, source-audited witnesses/tests, unknown/ambiguity fail closed, typed chain/real-file inspection/tour recovery, 1280/1920 and no-tours second map; all legacy gates retained, zero errors/network. [Evidence](IMPACT_REPORT.md) | V1.1 worker; parent independent browser/code review |
| Not started | [V1.2](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v12--map-trust-and-completeness): evidence quality / extraction | Future trust fixtures/browser checks; concrete findings with path/reason, source vs runtime evidence, relevant limitation badges; static relative Python fixes fixture-first, no invented runtime completeness | V1.2 worker; parent |
| Not started | V1.2 stale tours / refresh integrity | Exact-commit mismatch preserves prior bytes; explicit no-tour opt-out, legacy extractor parity retained or deliberately migrated with evidence; source cycles not deleted for a DAG gate | V1.2 worker; parent; Eric for architectural decisions |
| Not started | [V1.3](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v13--reviewable-repo-onboarding): draft → review → export → publish | Future draft/editor/export tests and second real repo onboarding without hand-editing JSON; zero missing/double assignments, invalid exports preserve output, stable IDs/warnings; newer self snapshot explicitly chosen, not silently substituted | V1.3 worker; parent; Eric reviews meaning |
| Not started | [V1.4](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v14--opt-in-real-query-evaluation-parallel-track): consent and evaluation | Future feedback browser/import/privacy tests, local opt-in/export/remove/clear, snapshot/overlay provenance, generated/dev/held-out/user distinctions; ideally ≥20 confirmed Eric queries, held-out subset before tuning | V1.4 worker; parent; Eric labels intent |
| Not started | V1.4 accuracy claims | Report accepted wrong answers, unnecessary abstentions, top1/top3, no-path truth, separate scorer p95; missing user labels block real-user accuracy claims, not feature implementation | Worker measures; parent audits; Eric confirms |
| Not started | [V1.5a](../.hermes/plans/2026-10-07_203500-v1-milestones.md#v15--release-usability-and-performance): full workflow on both demos | Future recorded find → inspect → tour (or explicit unavailable) → impact → alias correction/export → grouping edit → refresh → import; no stale highlights, overlapping controls or impossible recovery | Release worker; parent |
| Not started | V1.5b: scale / accessibility | 1280/1920 desktop and graceful 390px; keyboard/focus/Escape, contrast/names/reduced motion; declared real graphs + labeled synthetic 1k/5k nodes, recorded hardware; warm scorer p95 <10ms, cold init/layout/full Ask separately | Release worker; parent |
| Not started | V1.5c: reproducible release / safety | All legacy and implemented milestone gates; versioned manifest, pinned regeneration/CLI/setup/storage recovery docs; zero automatic external requests, malformed imports inert, immutable excerpts verified, failed build preserves output, no silent learning, no P0/P1 defects | Release worker; parent |
| Human pending | v1 final acceptance | **Eric completes one real repository session without operational assistant help**, with session outcome recorded; semantic layer/expectation review, unresolved severe defects closed | Eric; parent records verdict |

Automated gates alone permit a release candidate, **never “v1 complete”** while the
human session is pending. Optional explicit pinned GitHub evidence-link navigation
is not an automatic browser request. Review bundled private source excerpts before
sharing; no automatic public upload.

## Known constraints that must not disappear in release prose

Mixed layer/file routes are unsupported; bearer-auth responsibility lookup abstains.
Relative/dynamic Python and nonliteral JS imports leave gaps; configured JS aliases
other than root `@/` are not resolved. CSS/JSON targets have no nodes. Self demo
currently audits old `f92d0cf`, not current feature coverage. `file://` storage is
best-effort with export/import recovery; no cross-tab synchronization guarantee.
Publication is per-file atomic with caught-error rollback, not a power-loss-safe
multi-file transaction. Tours are audited source explanations, not observed execution.
These are documented limitations, not new scope decisions. Parent must return any
contradictory scope or acceptance-blocking uncertainty to Eric rather than weaken tests.

## V1.1 delivery boundary

Eric authorized both V1.1a+b after V1.0 parent acceptance. Actual pinned graph/source
was audited before fixtures; `lib/runner-client.ts` has zero observed linked tests,
while `runner/quest_runner.py` has eleven real import-linked tests. Neither establishes
coverage. Engine plus Inspect/Ask UI are worker-verified, not parent-accepted.
Extractor/trust redesign, onboarding and query logging remain outside V1.1.
V1.4 shared scorer/UI writes remain serialized; no later milestone launched here.
