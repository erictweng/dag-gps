# DAG GPS Repository Evidence Workspace Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task. If that skill is unavailable, use a fresh worker for each bounded mini-milestone, followed by parent spec-compliance and code-quality review. This document is planning only; it authorizes no implementation, agent invocation, commit, push, merge, deployment or private-source upload.

**Goal:** Paste a GitHub repository link, see a factual source map without an LLM audit, ask a simple question to highlight relevant evidence, and let an explicitly invoked coding agent explain that same evidence alongside the diagram.

**Architecture:** Keep deterministic source acquisition/extraction, local System 1 retrieval/traversal and optional System 2 interpretation separate. A local workspace service manages versioned source snapshots and calls the existing Python builders and shared JavaScript navigation modules; the browser displays the same evidence packets consumed by agents. Preserve the standalone offline navigator as an export, and keep live worktree revisions distinct from verified commit snapshots.

**Tech Stack:** Proposed v0 defaults: existing Python stdlib/Git build tools; a loopback-only Python workspace service; dependency-free browser JavaScript/SVG; a persistent trusted Node query worker sharing browser query logic; existing unittest/node:test/Playwright/Axe verification. No imported repository dependency installs or execution. No model-provider dependency on the map/lookup path. Runtime dependency additions and a production/hosted server stack require an explicit later decision.

---

## 1. Product contract and proposed defaults

### The product promise

**See where to look before the agent explains, and see the source evidence behind its explanation.** The graph is a shared evidence index, not a decorative image and not an assertion that the system understands every repository.

### Proposed defaults, pending Eric approval

1. Local-first desktop workspace. Human collaboration initially means sharing an explicit snapshot/export or looking at the same workspace; it does NOT mean hosted accounts or multi-user realtime synchronization.
2. Public GitHub repository root URLs plus explicitly selected local Git repositories. Private GitHub access is later; never request credentials through chat or bake them into JSON.
3. Inventory can show other file types, but dependency extraction initially remains the documented JS/TS/Python/static SQL subset. Unsupported relationships remain unknown, not invented.
4. No-LLM inventory, grouping proposals, extraction, ordinary navigation or refresh. Rich explanations require a deliberate Explain action or an explicit agent request.
5. Reuse the existing coding-agent workflow through a bounded read-only tool/CLI bridge first. Do not build a new multi-agent orchestrator or choose a paid hosted provider implicitly.
6. Folder-based grouping is an unreviewed proposal. Only an explicit human action creates a reviewed architecture overlay.
7. Keep contextual uncertainty, existing aliases and off-by-default feedback. A question/feedback label cannot silently teach aliases or trigger an agent.
8. Prioritize the repository-to-evidence workflow. Normalized graph export/import is useful; third-party arbitrary graph field mapping comes after this loop is proven, not instead of it.

### First human-visible slice

`GitHub link → inventory → dependency preview → question → highlighted evidence → source inspection`

This slice must work with System 2 disabled. Add the agent explanation panel only after the human and agent can consume the same validated context packet.

### Explicit out of scope for v0

Hosted SaaS, accounts, cloud sync, shared realtime editing, public repository uploads, executing imported code, installing imported npm/pip dependencies, automatic fixes, automatic tours, full runtime call graphs, universal language coverage, arbitrary prose reasoning in System 1, training a new model, agent-produced facts automatically becoming extracted edges, and automatic LLM calls on every edit.

## 2. Verified current context — October 8, 2026 PDT

Read-only discovery for this plan found:

- Primary checkout `/Users/aibert/projects/dag-gps`, branch `v1-release`, HEAD `757df72`.
- Active isolated workspace `/Users/aibert/projects/dag-gps-release-fixes`, branch `v1-release-fixes`, HEAD `757df72`, with uncommitted IR-01/02/03 fixes. Preserve these changes; do not stage this plan into their fix commit by accident.
- `.hermes/plans/2026-10-07_203500-v1-milestones.md` is the earlier approved roadmap. This plan proposes a new product phase; it does not retroactively change v1 acceptance or declare v1 complete.
- `scripts/draft_layers.py::draft_layers(repo, ref, tops=None)` resolves a full Git commit, inventories supported files, groups them deterministically and returns `reviewed: false`, ownership, observed file edges, diagnostics, trust and validation results. It does NOT publish a failed draft as an approved map.
- `scripts/build_map.py::build` is currently Git/archive-oriented. It returns candidate evidence and checks even on rejection, preserves file cycles, and blocks legacy publication on unresolved imports or layer cycles.
- `scripts/build_project.py::build_project(...)` performs validated snapshot publication; `snapshot_diff(previous, current)` supplies semantic file/edge/group differences. Do not bypass these gates to make arbitrary imports look valid.
- The current map has `meta`, `nodes`, `edges`, `file_edges`, `layers`, `trust`, `diagnostics`. Node kinds are file/layer. Layer links and file links are separate; this is NOT an arbitrary JSON graph loader.
- `web/scorer.js` exports `createScorer`, `validateResult`, and heuristic heads with explicit abstention. It is not a trained model.
- `web/router.js::createRouter(map)` exports `reachable`, `shortestPath`, `route`; edges point consumer → dependency, realtime is excluded, and mixed file/layer routes do not silently convert endpoints.
- `web/impact.js::analyzeImpact(map, tours, fileId)` supplies potential static impact with witness chains and separate boundary relationships. Import-linked tests do not prove runtime coverage.
- Current standalone rendering, highlighting, onboarding, trust, aliases and opt-in feedback can be reused. There is no GitHub-link workspace UI, live watcher, generic agent tool service or automatic agent explanation panel yet.

Grounding files: `README.md`, `AGENTS.md`, `STATUS.md`, `TASKS.md`, `docs/ARCHITECTURE.md`, `docs/WORKFLOW.md`, `docs/V1_ACCEPTANCE.md`, `docs/SUPPORTED_SOURCES.md`, `docs/ONBOARDING_REPORT.md`, `docs/RELEASE_REVIEW_FIXES.md`, `.verify.json`, and the code above.

### Release prerequisite — do not conceal the blocker

The current fix handoff records two earlier green full runs, but later current-source runs stopped at the unchanged performance gate (14.437167 ms then 26.739125 ms worst p95 against 10 ms). No fix commit/exact-postcommit receipt exists. Resolve this existing verification boundary without changing samples/thresholds to hide failures, independently re-review IR-01/02/03, and keep Eric's semantic/unaided acceptance pending. Planning can proceed; product implementation must use a fresh worktree from an independently accepted baseline, not mutate or merge the dirty release-fix workspace.

## 3. Evidence and revision contracts

Create `docs/WORKSPACE_CONTRACT.md` during authorized implementation. The wrapper is new; legacy map contents remain compatible.

### Snapshot envelope (proposed)

```json
{
  "schema": "dag-gps-workspace/v1",
  "projectId": "opaque-local-project-id",
  "snapshotId": "content-derived-revision-id",
  "source": {
    "kind": "git-commit",
    "repo": "owner/repository",
    "commit": "full-resolved-commit-sha",
    "worktreeId": null,
    "manifestSha256": "digest-of-source-manifest"
  },
  "state": "dependency-preview",
  "grouping": {"status": "proposed", "reviewed": false},
  "inventory": [],
  "map": {},
  "limitations": [],
  "extractorVersion": "recorded-version"
}
```

Values above describe fields, not valid fixture hashes. Tests must generate explicit synthetic fixtures or use declared real pins; never use this illustrative envelope as passing evidence.

- Inventory records actual paths/type/size/hash and exclusion reason. All tracked archive files can appear in inventory; only supported/scanned source receives dependency claims. Binary content is metadata-only by default.
- `map` retains the existing code-map structure. Non-code inventory paths do not become fake dependency nodes or silently gain edges.
- Grouping proposals, reviewed overlays, extracted relationships, actual diffs and agent interpretation are separate data. Preserve overlays across stable IDs; renames/deletions surface migration choices.
- Commit snapshots are immutable. Live snapshots use a base commit plus worktree identity and a captured source-manifest digest; never label uncommitted source as the exact committed SHA.
- File cycles are allowed and disclosed. For a cyclic proposed layer view, provide an explicit inventory/file-graph preview and cycle findings, or an SCC overview retaining membership/edges; never delete edges or bypass legacy DAG publication checks.
- A partial preview is not an approved legacy release artifact. Invalid endpoints/duplicate IDs/malformed data block the preview; extraction gaps produce visible limitations on otherwise structurally valid evidence.

### Shared query packet (proposed)

Fields: `schema`, `requestId`, `projectId`, `snapshotId`, `mapSha256`, `scorerSha256`, `operation`, `status`, `selectedNodeIds`, `selectedEdges`, `witnesses`, `alternatives`, `sourceRefs`, `limitations`, `truncated`, `continuation`, and `timings`.

- Status is `matched`, `needs-choice`, `no-match`, `no-path`, `unsupported`, or `stale`; never convert uncertainty into a confident highlighted answer.
- A source reference contains path, inclusive line range when available, exact file hash, snapshot ID and an evidence kind. A file import need not have a known line range yet: record null/unknown rather than inventing it.
- Bounds are explicit and configurable: result/node/edge/excerpt/request sizes, traversal depth, request queue and subprocess deadlines. Initial numerical limits are proposed only after fixture sizing; overflow returns a visible bounded result/continuation, not a falsely complete answer.
- Browser and agent API use the same query implementation and packet. Do not reimplement JavaScript scoring in Python.
- Source evidence is fetched against the packet's revision. Reject stale revisions rather than substituting current bytes into an old explanation.
- Query text is transient by default. Persist history/labels/agent transcripts only with explicit consent; retain the existing feedback consent boundary.

### Highlight semantics

1. Matched/relevant: selected by retrieval; not necessarily modified.
2. Potentially affected: observed dependency witness; not guaranteed breakage.
3. Actually changed: source-manifest/Git diff against a named baseline.
4. Agent-inferred: explicitly labeled interpretation with source references; not promoted into extracted facts.

Do not rely on color alone. Use labels, edge styles and the sidebar explanation. Dimming must preserve readable contrast, keyboard access and the ability to clear the selection.

## 4. Boring v0 architecture

Proposed modules, all new unless explicitly marked existing:

- `app/__init__.py`: package entry.
- `app/contracts.py`: bounded snapshot/context validation and revision guards.
- `app/repositories.py`: public GitHub URL validation, immutable ref resolution and isolated Git object cache.
- `app/snapshots.py`: safe archive preflight, inventory manifests, preview adaptation and immutable publication.
- `app/server.py`: custom loopback-only workspace API and static UI route allowlist.
- `app/query_worker.py`: bounded persistent Node child lifecycle and request IDs; no shell invocation.
- `app/context.py`: safe revision-bound source retrieval/context assembly.
- `app/agent_bridge.py`: transport-neutral read-only agent tools and bounded explanation intake.
- `app/live.py`: opt-in local worktree capture/reconciliation, later incremental caching.
- `scripts/query_worker.cjs`: trusted JSON-lines query worker using shared navigation modules.
- `scripts/workspace_cli.py`: import/query/context/explanation CLI; JSON stdout, diagnostics stderr.
- `web/query-service.js`: shared UMD/CommonJS packet generation around existing scorer/router/impact.
- `web/graph-view.js`: narrowly extract/reuse display/layout behavior from `web/template.html` with parity tests before replacing anything.
- `web/workspace.html`, `web/workspace.js`, `web/workspace.css`: import screen, progressive inventory/map, question box, contextual evidence/explanation panel.

The proposed cache is per project/revision, under an ignored `artifacts/workspace/` development default or a user-selected private cache outside the repo for normal operation. No imported source goes into tracked project files. Store a full immutable revision directory and switch one current-revision pointer after validation; do not present separately overwritten files as a crash-safe transaction. Explicitly document OS/crash guarantees and preserve the prior usable revision on caught failure.

### Security boundary

- Accept canonical HTTPS GitHub repository-root URLs only in v0; reject userinfo, ports, arbitrary hosts, file/SSH schemes, blob/tree URLs and ambiguous inputs with an actionable message. Support local repositories only through explicit local selection, not a remote API accepting arbitrary filesystem paths.
- Resolve default HEAD once; fetch the exact full commit into an isolated bare cache. No checkout, hooks, imported installs, imported commands, recursive submodules or following LFS/other external URLs automatically. Disable interactive credential prompts and untrusted/global Git configuration in this import subprocess. Apply network/process deadlines and cache/disk quotas; private/empty/unavailable repos are honest errors.
- GitHub archive REST is a possible later acquisition adapter, not a reason to invent a Git commit for extracted ZIP files. If used, preserve the resolved source identity and share safe extraction/validation.
- Before legacy builders archive an unfamiliar repo, preflight the same immutable archive for absolute/traversing names, symlinks/hardlinks, devices, duplicates, member counts and expanded byte limits. Use a safe extraction routine for new paths. Do not run imported source or blindly expose host files through source reads.
- Loopback service rejects unexpected Host/Origin, requires a local session capability for state-changing/source-sensitive requests, bounds bodies/queues and serves only explicit UI/API routes. No broad directory-serving handler, wildcard CORS, LAN binding or credential/token logging. Loopback is not itself authentication.
- Stdlib `http.server` is only a tightly scoped local prototype choice; official Python docs warn against production use. A hosted/shared deployment requires a separate reviewed auth/isolation/server design, not changing the bind address.
- Treat README/source/agent text as untrusted data, not instructions. Render text safely; agent content cannot call tools, replace the factual graph or execute imported code merely by being displayed.

## 5. Implementation order and bite-sized tasks

For EVERY code task below, perform the same sequence: (1) add one failing regression; (2) run its focused command and retain actual RED; (3) implement the smallest behavior; (4) run focused GREEN plus the stated milestone smoke; (5) review spec compliance then code quality; (6) commit only the authorized task's files locally after verification. Do not push/merge based on this plan. Each step is a separate work action; milestone estimates are deliberately not invented.

### M0 — Close the existing release boundary and freeze the new contract

**Task 0.1 — Accepted starting point**
- Read existing release-fix diff and `docs/RELEASE_REVIEW_FIXES.md`; preserve it in its own worktree.
- Coordinate a valid complete verification window; retain every failure and use unchanged recipes.
- Independently re-review IR-01/02/03. Once full green permits a local fix commit, rerun `python3 scripts/release_check.py --output artifacts/review-fixes-verification` against that exact commit. Check input/artifact binding, clean provenance and prior-bundle negative probes.
- Do not tick Eric's human acceptance. Branch the product workspace only from the explicitly accepted integration baseline.

**Task 0.2 — Document decisions and limits**
- Create: `docs/WORKSPACE_CONTRACT.md`, `docs/WORKSPACE_ACCEPTANCE.md`.
- Modify later, only after approval: `STATUS.md`, `TASKS.md`, `DECISIONS.md`, `.verify.json`.
- Test target: `tests/test_workspace_contract.py`.
- First regression: structurally valid packet for revision A cannot request source/explanation from revision B. Add separate tests for duplicate IDs, dangling edges, null unknown ranges, malformed imports, unsupported inventory files and consent defaults.
- Focused command: `python3 -m unittest discover -s tests -p test_workspace_contract.py -v`.
- Gate: both docs distinguish proposed/implemented, all four highlight states, commit/live provenance, unsupported scope, and agent invocation consent. No app behavior is claimed merely because contracts exist.

### M1 — Public repository link to a token-free, honest preview

**Task 1.1 — Validate links**
- Create: `app/__init__.py`, `app/repositories.py`.
- Test: `tests/test_repository_import.py`.
- First RED: reject `https://github.com.evil.invalid/a/b`, userinfo, localhost/file paths and `/owner/repo/blob/main/file.py`; accept exactly a repository root.
- Focused command: `python3 -m unittest discover -s tests -p test_repository_import.py -v`.
- Implement a small pure parser before any network call. Representative complete contract example:

```python
import re
from urllib.parse import urlsplit

_SEGMENT = re.compile(r"[A-Za-z0-9_.-]+\Z")

def parse_github_repository(value):
    if not isinstance(value, str) or len(value) > 2048:
        raise ValueError("Expected a bounded GitHub repository URL")
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or parsed.netloc != "github.com"
            or parsed.query or parsed.fragment):
        raise ValueError("Use https://github.com/owner/repository")
    parts = parsed.path.strip("/").split("/")
    if len(parts) != 2 or any(not _SEGMENT.fullmatch(p) or p in {".", ".."} for p in parts):
        raise ValueError("Expected a repository root, not a file or branch URL")
    return {"owner": parts[0], "repo": parts[1]}
```

Do not silently rewrite malformed input. If support for `.git` suffixes or UI query parameters is desired, specify and test that normalization explicitly as a separate task.

**Task 1.2 — Pin/fetch with controlled failures**
- Extend: `app/repositories.py`.
- Reuse: existing Git helper conventions, but import subprocess arguments are fixed and shell-free.
- Add isolated local-Git protocol tests plus mocked transport failures; these are synthetic integration fixtures, NOT real GitHub success evidence.
- Cases: default branch moves between discovery and fetch; exact resolved SHA still used; unavailable/private/empty repo; no prompt; timeout; cache eviction; two imports of the same SHA; poisoned cache; no imported hooks or command execution.
- Real smoke target (create later): `scripts/smoke_workspace_import.py` with explicit `--repo-url` and `--expected-commit`. The reviewer supplies and records a public supported repo/full commit; never pick a moving latest pin invisibly.

**Task 1.3 — Safe inventory before extraction**
- Create: `app/snapshots.py`; test `tests/test_workspace_snapshot.py`.
- First RED: malicious archive path/symlink is rejected and a prior revision remains byte-identical.
- Inventory stage emits files/counts/hash/exclusions independently of dependency success. Show binary/unsupported files without pretending they have extracted links.
- Test expanded-size/member limits, duplicate names, symlink and path traversal, export attributes/missing source, interrupted writes, idempotent hashes and cancellation.
- Focused command: `python3 -m unittest discover -s tests -p test_workspace_snapshot.py -v`.

**Task 1.4 — Preview adapter, not forged approval**
- Reuse: `scripts/draft_layers.py`, `scripts/build_map.py`, `scripts/onboarding.py`, `scripts/trust.py`.
- Create preview adaptation in `app/snapshots.py`; tests `tests/test_workspace_preview.py`.
- First RED: unresolved extraction leaves inventory visible with a truthful partial state; no reviewed marker or approved legacy artifact is emitted. Layer cycles keep file evidence and a blocking diagnostic; no links removed.
- Preserve exact source scope and stable IDs, cache by repository/commit/extractor/options, retain manual overlays separately. Reject corrupt endpoints and invalid ownership rather than hiding them.
- Focused command: `python3 -m unittest discover -s tests -p test_workspace_preview.py -v`.
- Gate M1: one declared real public repository imports without any model call; inventory appears before dependencies; source commit/counts/limits are visible; malformed inputs preserve prior output. Import network goes to explicitly approved GitHub endpoints only; no source execution or upload. Capture the real result, not merely mock receipts.

### M2 — System 1 query packets and focused workspace UI

**Task 2.1 — Shared query adapter**
- Create: `web/query-service.js`, `tests/query-service.test.cjs`.
- Reuse unchanged where possible: `web/scorer.js`, `web/router.js`, `web/impact.js`, `web/aliases.js`.
- First RED: literal known source path produces the same selected ID in browser and worker; duplicate basenames require choice; unknown IDs cannot be highlighted.
- Focused command: `node --test tests/query-service.test.cjs`.
- Add cases for no-path, cycles, import versus boundary impact, full-map paging independence, mixed endpoints, unsupported non-code inventory results, stale revision and bounded truncation.
- Representative complete test for the proposed API:

```javascript
const test = require('node:test');
const assert = require('node:assert/strict');
const map = require('../maps/quest-coder/map.json');
const {querySnapshot} = require('../web/query-service.js');

test('known literal path returns revision-bound evidence', () => {
  const snapshot = {snapshotId: 'declared-unit-fixture', map};
  const packet = querySnapshot(snapshot, {
    requestId: 'unit-request', query: 'locate lib/runner-client.ts'
  });
  assert.equal(packet.snapshotId, snapshot.snapshotId);
  assert.equal(packet.status, 'matched');
  assert.deepEqual(packet.selectedNodeIds, ['lib/runner-client.ts']);
  assert.equal(packet.truncated, false);
});
```

This test uses the existing pinned map for navigation parity, not as evidence of real-user query accuracy.

**Task 2.2 — Local service and Node worker boundary**
- Create: `app/server.py`, `app/query_worker.py`, `scripts/query_worker.cjs`.
- Tests: `tests/test_workspace_server.py`, `tests/query-worker.test.cjs`.
- Proposed endpoints: `POST /api/imports`, `GET /api/imports/{jobId}`, `GET /api/projects/{id}/snapshots/{revision}`, `POST /api/projects/{id}/query`, revision-bound source/context fetch. Paths are opaque IDs, not arbitrary host paths.
- First RED: unexpected Origin/Host and traversal/source paths fail; worker cannot swap project/revision results. Add bounded JSON-lines request IDs, stderr separation, timeout/restart, queue limits and cancellation.
- Query worker runs trusted installed DAG GPS modules only, never JavaScript from an imported project. Python orchestrates rather than reimplementing scoring.
- Commands: `python3 -m unittest discover -s tests -p test_workspace_server.py -v`; `node --test tests/query-worker.test.cjs`.

**Task 2.3 — Progressive UI and graph-view extraction**
- Create: `web/workspace.html`, `web/workspace.js`, `web/workspace.css`, `web/graph-view.js`.
- Modify `web/template.html` ONLY as necessary for extracting reusable presentation; retain standalone behavior and legacy source serialization safety. No whole-template rewrite.
- Test: `tests/workspace.test.cjs`, `tests/graph-view.test.cjs`; smoke: `scripts/smoke_workspace.cjs`.
- First RED: actual typing/Enter highlights a declared source path and its packet; unsupported or ambiguous queries do not dim the screen around a guessed match.
- UI: left project/inventory panel, central graph, question input, contextual right evidence panel. Advanced diagnostics/aliases/feedback remain contextual. Display import stages, extraction counts, freshness and grouping proposal status. Never expose all panels by default.
- Test clear/Escape, keyboard paging/expansion focus, chosen alternatives, source selection, revision switch preserving position, failed import recovery, 1280/1920/390 widths, reduced motion/contrast/names and inert imported labels.
- Commands: `node --test tests/workspace.test.cjs tests/graph-view.test.cjs`; `node scripts/smoke_workspace.cjs`.
- Gate M2: one no-agent user session completes import → question → highlight → witness/source → clear/recovery. Compare browser and worker packets on all declared cases; no automatic model/network call after cached import. Existing legacy smokes continue to pass.

### M3 — Agents consume the same evidence and explain beside it

**Task 3.1 — Bounded source/context tools**
- Create: `app/context.py`, `app/agent_bridge.py`, `scripts/workspace_cli.py`.
- Tests: `tests/test_agent_context.py`, `tests/test_workspace_cli.py`.
- Tool contracts: `find_nodes`, `get_dependencies`, `get_dependents`, `find_path`, `get_source`, `get_changes`. Query outcomes are evidence candidates, never a requirement to stay inside an incomplete graph.
- CLI accepts JSON stdin/returns JSON stdout; validated tool names, project IDs and revisions select trusted actions. Never interpolate query/source text into shell commands.
- First RED: source from revision B cannot be attached to packet A; unknown path and out-of-root symlinks reject. Add excerpts/ranges/hash checks, bounded context with explicit truncation/continuation, unsupported edges, expiry and no graph mutation.
- Commands: `python3 -m unittest discover -s tests -p test_agent_context.py -v`; `python3 -m unittest discover -s tests -p test_workspace_cli.py -v`.

**Task 3.2 — Explicit agent explanation intake**
- Extend: `app/agent_bridge.py`, `web/workspace.js`.
- Test: `tests/test_agent_explanations.py`, `tests/workspace.test.cjs`.
- First RED: stale/foreign-snapshot citation is rejected and cannot replace a current explanation. Add plaintext/safe rendering, unknown citation, malformed response, timeout/cancel, source hashes, explicit inferred-claim tags and file-only evidence with no fabricated line range.
- User selects Explain; context export requires consent before sending source to an external agent/provider. Initial adapter uses Eric's existing approved coding-agent flow; no default paid/raw Anthropic invocation or provider credentials in the app.
- Explanation response: request/revision identity, bounded paragraphs, validated source references, limitations, agent identity when available and measured usage if supplied. Missing provider usage is null/unknown, never invented as zero. Suggested relationships remain an interpretation overlay requiring review.
- Model invocation is an optional adapter. CLI/manual context handoff proves the protocol without prematurely committing to a provider or building an orchestrator. Automated adapter credentials/budgets are a separate approved task.
- Gate M3: the same System 1 packet drives human highlights and one explicitly invoked real-agent explanation. An actual read-only task succeeds with source citations; no modifications to the imported repository. Mocked agent output tests failure handling only; it is not real-agent success or accuracy evidence.

### M4 — Opt-in live map updates during coding

**Task 4.1 — Stable live source capture and actual-diff overlay**
- Create: `app/live.py`; test `tests/test_live_snapshot.py`.
- First RED: edit bursts/interrupted writes retain the last good revision and show updating/stale rather than mixing source versions.
- Explicitly select/register a local worktree. Detect tracked and relevant untracked added/deleted/renamed files; exclude cache/generated/vendor outputs. Capture source into an immutable staging revision and recheck manifest membership/hashes; bounded retries on concurrent edits, then retain old revision with clear pending state.
- Initial implementation may fully rebuild supported evidence after a quiet batch. Do not promise incremental complexity reduction before profiling. Body-only edits may alter source hashes without changing topology.
- Source-manifest diffs determine changed files. Graph reachability determines potential impact. Agent ownership is unknown unless a trusted hook/worktree identity supplies it; a watcher does not prove who edited a file.
- Command: `python3 -m unittest discover -s tests -p test_live_snapshot.py -v`.

**Task 4.2 — Reconciliation and targeted cache**
- Extend: `app/live.py`; create later if justified `scripts/watch_workspace.cjs`.
- First RED: missed/duplicated/rename events still converge to the filesystem truth at reconciliation; cancellation/invalid syntax does not publish corrupt edges.
- Watchers are hints. Use periodic/manual full reconciliation and optional agent completed-batch hooks. Cache extraction by file hash plus resolver/config version; config/deletion/rename changes invalidate all affected references. Compare incremental results against full deterministic rebuild on fixtures before enabling the optimization.
- Add syntax/unsupported diagnostics truthful to the actual parser; do not claim current lexical JS extraction performs full syntax validation. A parser-adapter addition requires its own dependency decision and regressions.
- Browser refresh uses revision events/polling after complete publication, not reparsing/reflowing all nodes per keystroke. Preserve selection/pan/focus; stale explanations visibly expire.
- Smoke: `scripts/smoke_workspace_live.cjs`, real temp Git worktree with controlled actual edits. No watcher writes imported project source or calls models.
- Gate M4: real edit/add/delete/rename/body-only/config changes produce verified revision updates and correct changed-versus-impact styles. Last valid map survives partial code/worker failure. Graph/index parity, bounded refresh cost and zero automatic LLM calls are demonstrated.

### M5 — Prove usefulness, cost and release safety

**Task 5.1 — Real-task comparison protocol**
- Create: `docs/WORKSPACE_EVALUATION.md`, `scripts/eval_workspace_sessions.py`.
- Tests: `tests/test_workspace_evaluation.py`.
- Eric confirms real question/task intent and expected source evidence. Freeze a held-out subset before tuning; retain generated/development/user distinctions. Existing feedback exports can help only when intent and revision are valid.
- Compare the same repo/task/agent configuration with normal agent search versus graph-first evidence. Control context reset/order/caching enough to describe confounders; do not convert a few sessions into generalized accuracy claims.
- Record time to first factual inventory, dependencies-ready time, cold init, warm query, full visible highlight, actual source reads, input/output/model calls, wrong accepted answers, unnecessary abstentions, missed relevant evidence and correct explanations. Record availability/reliability rather than selecting only successful runs.
- Tokens reported by provider/agent instrumentation are measured; missing values stay unknown. No fabricated percentage savings or guaranteed latency.
- Gate: Eric can use one real repository workflow unaided; usefulness and token effects are reported with raw denominators and limitations. Architecture grouping review and final acceptance remain separate.

**Task 5.2 — Package the workspace without regressing exports**
- Create: `scripts/check_workspace.py`, `docs/WORKSPACE_RELEASE.md`, `scripts/smoke_workspace_security.cjs`.
- Modify only after implementation: `.verify.json`, release/input inventories where new shipped sources belong.
- Reuse IR-01/02 contract discipline: freeze input membership/provenance, freeze producer-tested outputs before consumers, stage copies against expected hashes, reject old/unbound receipts, and preserve previous packages on rejection.
- Test source/query/private-export consent, inert data, no external requests after cached import except an explicitly requested agent action, cross-project isolation, Git/archive attacks, provider-disabled navigation, resource limits, keyboard focus and stale explanations.
- Run all legacy `.verify.json` recipes plus new workspace checks. The scorer-only 10 ms gate remains a separate existing requirement; do not call it end-to-end time or tune its samples to hide failures. Document load/hardware and retain failed attempts.
- Gate M5: exact commit/clean-provenance package verification, public/private sharing review, full old/new smokes and recorded human outcome. No automatic release/public upload.

### M6 — Flexible third-party graph JSON import (after the repository loop proves value)

**Task 6.1 — Explicit graph normalization and mapping preview**
- Create: `app/graph_import.py`, `web/graph-import.js`.
- Tests: `tests/test_graph_import.py`, `tests/graph-import.test.cjs`; smoke: `scripts/smoke_graph_import.cjs`.
- First RED: source/target versus from/to is mapped only through a declared adapter or confirmed wizard; ambiguous direction/IDs cannot produce an invented graph.
- Support selected documented shapes first, then expand adapters from actual user files. Unique IDs, endpoint membership, bounded sizes, inert metadata and cycle disclosure are required. Keep originals for reproducibility; no eval or executable labels.
- Generic graph nodes do not masquerade as code file/layer nodes. Add a generic graph adapter/query implementation as an isolated module with graph-specific tests; keep legacy router kind validation intact. No source access/explanation of code without an explicitly attached verified source snapshot.
- Gate M6: supported import shapes map deterministically, user reviews ambiguous mappings, generic traversal works with typed uncertainty, legacy snapshots retain parity. Do not market literal ANY JSON compatibility.

## 6. Validation commands and artifact discipline

Existing real recipes (already present, not rerun merely to write this plan):

```sh
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
node scripts/eval_scorer.cjs
node scripts/eval_lookup.cjs
node scripts/eval_alias.cjs
node scripts/eval_user_queries.cjs
python3 scripts/release_check.py --output artifacts/review-fixes-verification
```

Proposed commands/files above do NOT exist yet. Create them during their named tasks and require actual exit/output, not a stub or a plan checklist. `scripts/check_workspace.py` should aggregate nonrecursive build/unit/import/UI/agent-context/live/security/evaluation checks; do not invoke it from a recipe it recursively invokes.

Per milestone record source pins/tool versions, commands, return codes, request counts, model calls, counts/denominators, revision hashes, timings, screenshots and unknown measurements under ignored `artifacts/workspace-verification/<milestone>/`. Use synthetic fixtures only for regression mechanics; separately label real-repo/real-agent/user sessions. No private source or question history in tracked evidence.

Before implementation resumes, preserve concurrency: read worktrees/status, establish narrow allowed files, run RED/GREEN, keep source pins/extraction parity unless explicitly migrated, obtain independent review and use Eric's configured commit identity. Do not stage the whole dirty release-fix tree. Never treat an earlier receipt from different bytes as current verification.

## 7. Risks and open decisions

- **Local versus hosted collaboration:** hosted users require authentication, tenant/source isolation, authorized acquisition, encryption/storage policy, production server and deployment review. This plan chooses no hosted implementation until explicitly approved.
- **Agent integration:** existing-agent read-only bridge versus an embedded chat provider changes credentials, budgets and privacy. Proposed first default is the bridge plus explicit Explain, not a new orchestrator.
- **Support coverage:** broad inventory is easy to display, architectural semantics are not. Choose a third declared supported public repo for tests; document its full pin and limitations before using it as success evidence.
- **Grouping/cycles:** automatic folders are proposals. Preview mode must not forge legacy human review; SCC overview versus file-only preview is a UI decision to confirm with a real cyclic example.
- **Performance:** Git/network/parse/layout/query/explanation are different costs. Give progressive useful output rather than an unsupported instant-complete promise; profile real workloads before incremental optimizations or parser dependency additions.
- **Completeness:** static graph-first context can miss dynamic relationships. Provide explicit uncertainty and controlled source expansion; never lock agents into an incomplete graph.
- **Repository safety:** imported docs/code are untrusted. No automatic dependency installation, source execution, broad filesystem access or tool instructions from imported content.
- **Freshness/concurrency:** capture exact source revisions and serialize publication per worktree; stale packets/explanations must not silently show current snippets. Multiple agents need worktree/hook attribution, not guesses.
- **Cost proof:** zero model calls on the deterministic path is a design/test invariant; token savings on explanation tasks require measured comparison and may not appear if context selection misses important files.

## 8. Approval and next action

This plan is a proposed product roadmap, NOT another approved v1 milestone. It supersedes none of the current release blockers or human acceptance requirements.

Before execution, Eric confirms:
1. Local-first desktop v0 versus a hosted shared workspace.
2. Existing coding-agent bridge first versus an embedded model/chat provider first.
3. Public GitHub + supported JS/TS/Python first, with arbitrary third-party JSON import after the repository-to-evidence loop.

Once these are settled and the release baseline is independently accepted, authorize **M0/M1 only** as the first implementation handoff. Do not dispatch all milestones concurrently. Prove a real no-agent import/preview before starting agent explanation, live updates or broad generic imports.

## Reference notes (retrieved October 8, 2026)

- GitHub's repository-contents documentation describes ref-bound archive downloads, redirects and public/private access distinctions. Acquisition choice here is isolated Git object caching to preserve compatibility with current builders; archive REST is an alternative adapter, not a mandatory runtime dependency.
- Node's filesystem documentation warns that watcher behavior is not fully consistent across platforms; reconciliation and explicit revision capture are therefore required, not just event handling.
- Python's `http.server` documentation warns against production use; the proposed stdlib service is a local prototype boundary, not a hosted deployment recommendation.

Official reference URLs for the implementer:

```text
https://docs.github.com/en/rest/repos/contents
https://nodejs.org/api/fs.html
https://docs.python.org/3/library/http.server.html
```

Paperclip is a visual/workspace inspiration only. This plan does not copy its runtime, assume its implementation, or add agent orchestration because its dashboard suggests it.
