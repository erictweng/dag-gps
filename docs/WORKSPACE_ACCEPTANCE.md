# Repository evidence workspace acceptance — Phase 0

Roadmap: `.hermes/plans/2026-10-08_130312-repository-evidence-workspace.md`.
Contract: `docs/WORKSPACE_CONTRACT.md`. User authorization: 2026-10-08 (PDT),
“ok do phase 0”. This authorizes the foundation/review/contracts only, not Phase 1,
push/merge, deployment, agent calls or final human acceptance.

## 1. Verified starting point

- Separate local roadmap commit: `aa6a1e83fe1f5006e0471cf9737fe1aa0ebabfd1`.
- Local release-fix commit: `9a5a327583936efd2844e80a6834b8d0a170be03`.
- Exact fix-commit complete runner + packaging passed all eight unchanged gates,
  192 Python / 152 JS, with matching start/end clean provenance. Parent read back
  the exact manifest and all 25 payload hashes/sizes against their expected bindings.
- Fresh exact-fix-commit mirror: clean package accepted 1/1, 17/17 mutations/faults
  rejected with previous bundle bytes preserved, including promotion/readback faults.
- Independent read-only source review passed IR-01/IR-02/IR-03. Parent compared all
  four reported implementation fingerprints against actual source bytes and supplied
  the fresh gates/probes that the reviewer explicitly left pending.
- These constitute local automated/source closure for the targeted findings, NOT
  main integration, Eric's semantic grouping review, unaided workflow or final v1
  release. Prior failed benchmarks remain retained. No gate/sampling/scorer change.

Evidence: `artifacts/phase0-release-postcommit/verification.json`,
`artifacts/review-fixes-probe-9a5a3275-phase0-release-postcommit/results.json`,
`artifacts/phase0-independent-review/review.md`. Later contract changes require
fresh exact-final-commit verification; the prior receipt cannot certify new bytes.

## 2. Phase 0 implementation boundary

Implemented in this mini-milestone:
- Versioned pinned-snapshot/evidence structure and provenance guards in
  `app/contracts.py`, with `app/__init__.py` package marker only.
- Explicit false-by-default query-recording/agent controls and literal boolean
  consent guard. These are internal contracts, not a consent UI/authentication layer.
- Synthetic regression suite `tests/test_workspace_contract.py`.
- This acceptance contract, the normative contract document and Phase 0 decision
  record. No invented provider or runtime deployment decision.

NOT implemented: GitHub-link importer, source store, workspace server/UI, agent
provider/tool launcher, parser improvements, live watcher, generic graph importer,
new scoring rules or a trained model. Existing offline artifacts remain the product
implementation. Phase 0 tests are not evidence of those future features working.

## 3. Phase 0 acceptance checks

| Check | Evidence / responsibility |
|---|---|
| Existing IR findings independently reviewed and regression-backed | Source review report plus fresh complete receipts/17 negative probes above |
| No old/historical receipt substituted for exact current bytes | Final receipt must name final local HEAD, clean provenance and source/output bindings |
| Phase 0 contract tests reproduce RED then GREEN | `phase0-contract-red.*` records missing module; current GREEN and focused negative cases retained |
| Version, project/revision, map/scorer/source-manifest hashes agree | Drift and same-ID manifest-reuse regressions |
| Structural facts are honest | Duplicate/dangling/mixed/wrong-scope node/edge, source inventory/ownership and directed witness tests; real cycles retained |
| Unknown ranges are not invented | Explicit null pairs; actual known inclusive line bounds; wrong revision/hash/path rejects |
| Relevant/affected are not falsely “changed” | Distinct highlight states; actual-changed requires explicit trusted baseline/change record; potential impact requires witnesses |
| Uncertainty does not choose guessed routes | Needs-choice/no-match/stale and no-path regressions |
| Bounds reject overflow rather than silently hiding results | Finite JSON, arrays/string/byte caps and explicit truncation/continuation regressions |
| Consent/labels do not silently enable agents/history | Fresh false controls, explicit True only, no model/logger/IO implementation |
| Code and docs accurately disclose limitations | Trusted snapshot producer required; validation alone does not hash actual files, prove human consent, infer architecture or establish query accuracy |
| Final complete unchanged gate and package readback | `artifacts/phase0-final/verification.json`, package result and exact manifest/source hashes |
| New contracts independently reviewed | Initial FAIL retained at `artifacts/phase0-contract-review/review.md`; corrected bytes require `review-followup.md`; any blocker fixed and reverified before handoff |
| Scope/ownership preserved | Separate local commits; primary checkout unchanged; no Phase 1 execution or external write |

The complete Phase 0 outcome is recorded after actual execution in
`artifacts/phase0-completion.json`, including local SHAs, actual counts, exact
receipt/probe paths, reviewed fingerprints and explicit pending human acceptance.
An absent/failed final receipt means Phase 0 remains incomplete, regardless of prose.

## 4. Verification recipes

Focused new contract test:

```sh
python3 -m unittest discover -s tests -p test_workspace_contract.py -v
```

All unit/regression coverage:

```sh
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

Final complete release check, preserving all existing recipe semantics:

```sh
python3 scripts/release_check.py --output artifacts/phase0-final
```

Use a distinct ignored output directory for a retained failed attempt; do not
cherry-pick its passing subrecipes into another receipt. Source/doc edits and
commits invalidate existing input/provenance bindings. Run final recipes against
the actual final commit with no source writer running; read exact targets back.

The existing 10 ms warm scorer-only target is NOT full Ask/highlight latency.
Keep all failures/environment load data. No related processes may be stopped
without user authorization just to obtain green performance.

## 5. Decisions and approval boundaries

Decided by Phase 0 scope:
- Keep deterministic factual indexing/navigation separate from agent interpretation.
- Keep old offline navigator and strict publication/source-evidence checks.
- Default query recording and agents off; no private/context upload or paid API.
- Guard pinned source identity, explicit uncertainty, typed relationship witnesses,
  actual diffs versus relevance, and controlled bounds.
- Local-only commits; no main integration/push or final human release sign-off.

Still proposed, NOT silently locked by Phase 0:
- Local-first desktop service versus hosted/shared accounts/workspace.
- Existing-agent bridge versus embedded chat/provider.
- Public GitHub + documented language subsets first; timing of private access and
  broad third-party graph JSON adapters.
- Production server/framework, transport auth, resource/latency budgets based on
  real import/query fixtures, and incremental parser/watcher dependencies.

Confirm architecture-changing decisions before Phase 1/agent implementation.
Transport-independent Phase 0 guards do not select a paid provider or authorize
hosted access. Broader live/generic source identities need an explicit later
version/contract extension, not a fake commit or disguised file node.

## 6. Human acceptance remains pending

Eric must still complete an unaided real-repository workflow and review semantic
layer grouping. Real-user accuracy/tuning requires confirmed intent and a frozen
held-out subset; synthetic cases/worker sample review markers are not substitutes.
No hosted collaboration, universal-language understanding, guaranteed token saving,
instant complete analysis or end-to-end latency claim is established by Phase 0.

When Phase 0 passes, the next action is an explicit Phase 1 authorization plus
needed architecture decisions, using a fresh isolated worktree from the locally
accepted final SHA. This plan does not start that work automatically.

## 7. Contract review regression record

Initial independent review found three medium-severity blockers even though the
initial focused and complete recipes passed. No contract commit was made on those
bytes. Regressions reproduce absent nullable fields, disconnected/mixed impact
selections, and nonfinite/circular/non-native snapshot metadata; RED 47 tests with
16 failing cases is retained. Corrected source now passes 47/47 focused tests.
The original review/full receipt remains historical, not current acceptance.

Dispositions: nullable presence is strict; potential-impact selections are each
witnessed to an explicit selected seed (seed itself is not a consumer); snapshots
and packets use bounded JSON-native finite data. Unsupported requests may show
observed context only with a disclosed limitation, never as a complete answer.
Authorization is rendered as 2026-10-08 (PDT). The initial report's apparent date
placeholder was a tool-output redaction artifact: patch context confirmed the file
already contained October 8, 2026. This formatting clarification changes no scope.

Final completion still requires independent follow-up on corrected fingerprints,
complete current-source/precommit and exact-postcommit gates, fresh package negative
probes and clean final provenance. No Phase 1 or human-acceptance scope is added.

