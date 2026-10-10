# V1.5 independent-review follow-up (local worker)

Scope: IR-01 (P1 artifact integrity), IR-02 (P2 input inventory/provenance),
IR-03 (P2 keyboard focus). Base `757df72b25fb8b60e8f9dee4ba50c5318e79f2ad`;
isolated `v1-release-fixes` worktree. No V1.6, source-pin migration or model tuning.
Parent independent re-review and Eric semantic/unaided acceptance remain pending.

## Contract and closure rationale

- Verification receipts deliberately migrate to **dag-gps-verification/v2** and
  bundle manifests to **dag-gps-release/v2**. Old unbound green receipts fail with
  a rerun instruction. HEAD must equal the receipt, and complete input membership,
  bytes, start/end HEAD, status and diff provenance must match.
- All tracked inputs plus the recursive non-output project trees
  are frozen, including relevant untracked/ignored additions, newly introduced
  package directories and nested fixtures. Git administrative paths are excluded.
  Only declared build-output roots (`artifacts`, `dist`), Git administrative paths
  and interpreter/dependency caches are excluded. Missing tracked inputs fail closed. This is conservative:
  even an unrelated tracked-doc edit invalidates the receipt. Dirty precommit
  verification is allowed but its exact provenance is explicit, not called clean.
- Producer/test boundaries freeze generated inventories, actual download bytes,
  screenshots, evidence JSON and each completed gate's stdout/stderr. The build
  freezes editors/draft; smoke legitimately rebuilds timestamp-bearing navigators
  and freezes their final generation after the refresh/tour/impact/trust/onboarding/
  feedback consumers. Release-session builds then opens/tests its actual downloaded
  grouping outputs before freezing them. Accessibility/performance/UI evidence is
  frozen at its producing gate, before subsequent consumers. Later gates cannot
  rewrite any already-frozen bytes or change membership.
- Packaging stages all 25 payloads and four supporting evidence JSONs, comparing
  each copied byte set to its **expected verified** SHA-256 before scanning/parsing.
  It never certifies a new digest as the expected value. Receipt, source, inventory
  and provenance are rechecked before promotion. Rejection leaves every previous
  bundle byte unchanged; caught promotion failure restores the previous directory.
  Successful promotion is a directory replacement with a brief rename gap, **not**
  power-loss-safe publication or a concurrent-writer transaction.
- Receipts are local evidence, not cryptographic signatures against an adversary
  rewriting both receipt and source. Use one release writer. Synthetic isolated
  unit receipts remain explicitly synthetic; their manifests say synthetic-unit-only
  and never stand in for the runner's actual command evidence.
- Row rerender restores the same enabled action where possible, otherwise the
  opposite enabled action at first/final boundaries. SVG Shift+Enter expansion
  moves to the visible stable Back action. Input/dialog Escape ownership, full-map
  APIs, 150-row/80-node disclosure and graph/tour/impact evidence are unchanged.
  UI gates use trusted real Enter/Shift+Enter events and activeElement assertions,
  including next/previous interior and first/final boundaries on both synthetic sizes.

## Evidence (ignored, local)

- RED baseline: `artifacts/review-fixes-red/` retains packaging mutations/copy-race
  failures, omitted-input regression failures, and actual keyboard BODY focus.
  `baseline/` is an isolated archive, not the source checkout or a distributable.
- Focused GREEN and retained initial fixture failure:
  `artifacts/review-fixes-focused/` (initial fixture incorrectly placed its receipt
  among root inputs; moved it under ignored artifacts, without relaxing inventory).
- Full precommit and exact postcommit runner receipts: recorded below after real
  execution. Existing eight recipes and all legacy pins/parity gates remain intact.

No private artifacts are committed or uploaded. No push, merge, PR, release,
visibility change or paid/raw Anthropic API use. Repository is currently public;
that does not authorize sharing local private-source-bearing payloads.

## Remaining acceptance

Parent independently re-reviews these fixes and reruns relevant negative tests.
Eric's semantic grouping review and unaided real repository session remain pending.
V1.4 real-user tuning remains deferred (zero confirmed labels). No final release or
human acceptance is claimed by this worker.

## Executed follow-up outcomes

- Baseline RED packaging suite: 7 tests / 5 failing cases (changed HTML/evidence/doc,
  modified JSON overwriting the previous bundle before failing, and staged copy-race).
  Keyboard baseline probe: 3/3 actual Enter/Shift+Enter actions dropped focus to BODY.
  Real baseline receipt omitted 4/4 asserted tests/packaged-doc inputs. New contract
  API regression tests also failed on the baseline's missing contract implementation.
- First full precommit execution: all eight gates + packaging exit 0, 189 Python /
  152 JS. Initial fixture placement error and temporary-stage ResourceWarning are
  retained; the fixture moved under artifacts and stages now use explicit cleanup.
- Second full precommit execution: all eight gates + packaging exit 0, **192 Python /
  152 JS**, **2 sessions / 22 step groups / 70 events**, **23 Axe states / zero
  violations**, **32 screenshots / 194 computed SVG text instances**, **50,000
  scorer samples**. Additional consumer-gate regressions exercise actual subprocess
  source edits, byte-identical-source HEAD drift and changed previously frozen HTML.
- Real second-run receipt, disposable mirror: **1/1 clean package accepted; 15/15
  negative probes rejected**, all preserving every previous bundle byte. Tests cover
  HTML/JSON, supporting evidence/screenshot/gate-log, missing/added generated inputs,
  all three formerly omitted tests, new untracked test/deleted source, both payload
  and evidence copy races, and HEAD drift. `artifacts/review-fixes-probe-757df72b-review-fixes-verification-2/results.json`.
- A conservative inventory refinement also includes new untracked package directories,
  not just existing source directories; focused tests cover it. The complete runner is
  rerun before commit. Final postcommit evidence is authoritative at
  `artifacts/review-fixes-verification/verification.json` and the local bundle manifest.
  It must name the exact final commit and a clean worktree. Parent review is still pending.

### Retained current-source performance failure

`artifacts/review-fixes-verification-3/verification.json`: build, test, smoke,
release_session and accessibility passed; unchanged performance gate returned 1.
Worst synthetic-5k alias-on PATH p95 **14.437167 ms**, plus alias-off nickname
**11.265875 ms**, both over the unchanged 10 ms limit. Report recorded load average
11.299; subsequent live uptime reported 26.68 (12 logical CPUs). This is a real
failed attempt, not dismissed as passing because two earlier runs were green.
No scorer, target, samples, queries or warmups were changed. One complete unchanged
retry is run; no failed-gate-only receipt or cherry-picked recipe substitution.
Original measured report is archived with the failed attempt before retry.

### Historical worker block — before renewed Phase 0 authorization

The single complete unchanged retry, `artifacts/review-fixes-verification-4/`, also
returned 1 at performance: synthetic-5k PATH p95 **26.739125 ms alias-off** /
**23.225583 ms alias-on**; recorded load averages **27.7148 / 20.1665 / 14.1797**
on 12 logical CPUs. Build/test/smoke/release_session/accessibility passed (192 Python /
152 JS); UI performance and milestone acceptance were not reached. No packaging ran.
The failed benchmark JSON is archived alongside this receipt. Earlier green full runs
and real mirror-negative results are retained; they are not substituted for this failed
current-source receipt. Current focused tests still pass 16/16.

**Stopped after the authorized single unchanged full retry. No commit was made**:
this handoff requires full green before a local commit, then a complete exact-postcommit
rerun. HEAD remains `757df72b25fb8b60e8f9dee4ba50c5318e79f2ad`; source fixes are dirty
only in the isolated `v1-release-fixes` worktree. Do not treat the earlier local bundle
as a final candidate for these current source bytes. Parent may coordinate a quiet
verification window and rerun the whole unchanged recipe, then commit with Eric identity
and rerun postcommit. Do not weaken performance, tune scorer, or stop unrelated user
processes merely to obtain a green receipt. Independent and human acceptance stay pending.

## Renewed Phase 0 authorization — October 8, 2026

Eric authorized Phase 0 only. The repository-evidence roadmap is preserved separately
from the release-fix changes; no Phase 1 importer, live UI or agent integration is
implemented by this release-fix commit.

- Actual renewed complete runner `artifacts/phase0-precommit/verification.json`
  returned **0**: all eight unchanged recipes plus packaging. **192 Python / 152 JS**,
  **12/12 actual keyboard-focus cases**, **23 Axe states / zero violations**,
  **32 primary screenshots**, **22 session step groups / 70 recorded events**;
  worst scorer p95 **4.557041 ms** on the recorded environment. This is scorer-only,
  not end-to-end latency. Prior failures remain archived; no target/sampling/scorer
  change or failed-gate-only substitution was made.
- Independent read-only reviewer reported source-review **PASS** for IR-01/02/03,
  overall verification **PARTIAL pending parent gates**. Parent inspected the exact
  report and performed fresh gates/probes; source fingerprints correspond to the
  reviewed implementation. Report: `artifacts/phase0-independent-review/review.md`.
- Fresh real receipt in an ignored disposable mirror: **1/1 clean packaging accepted;
  17/17 negatives rejected**, preserving every previous bundle byte. In addition to
  HTML/JSON/evidence/screenshot/log, membership/source edits, copy races and HEAD
  drift, this includes actual injected promotion failure and promoted-target
  corruption/readback rollback. Results:
  `artifacts/review-fixes-probe-757df72b-phase0-precommit/results.json`.
- Reviewer scope caveat is retained: frozen generated evidence covers the primary
  release reports, their references, selected producer outputs and recipe logs.
  It does **not** certify every standalone legacy browser/eval report or screenshot.
  Future certification consumers must add their inputs explicitly before claiming
  byte binding. Input source/test/fixture/doc membership remains recursive.

### Findings transition and exact-commit boundary

IR-01, IR-02 and IR-03 are fixed in source and independently source-reviewed with
fresh regression/gate evidence. Parent's final automated closure is recorded only
in the exact-commit receipt and `artifacts/phase0-completion.json` after local commits,
a complete unchanged postcommit rerun, independent negative reruns and clean
provenance readback. If any of those fail, closure remains blocked; this document
cannot substitute for a passing receipt. No push/merge or final human acceptance.

Eric's unaided workflow and semantic grouping review remain pending. The local
single-writer contract is not signed evidence or a power-loss/concurrent-adversary
transaction. No unrelated processes were stopped to obtain a passing benchmark.
