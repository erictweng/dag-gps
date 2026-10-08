# Decisions

Record durable decisions here. One entry per decision, newest at the bottom.

Format:

```text
## YYYY-MM-DD — <title>

Context: <why this came up>
Decision: <what was decided>
Why: <reasoning>
Tradeoffs: <what we gave up>
```

## 2026-10-07 — Project workspace initialized

Context: Need a durable file structure for Hermes orchestration and Claude Code workers.
Decision: Use the standard `hproj` layout (PROJECT/TASKS/STATUS/DECISIONS/NOTES/AGENTS, `docs/`, `.hsub/`, `.claude/agents/`, `.verify.json`).
Why: Keeps durable context in files instead of the chat context window.
Tradeoffs: Slight upfront structure overhead; much better continuity across workers.

## 2026-10-08 — Phase 0 repository-evidence foundation only

Context: Eric approved “ok do phase 0” after the repository-evidence workspace plan.
Decision: Independently re-review/verify existing IR-01/02/03 fixes, commit locally,
verify exact committed bytes, and freeze transport-independent snapshot/evidence,
uncertainty/highlight, bounds and explicit-consent contracts with regression tests.
No Phase 1 importer/UI/live watcher, agent/provider invocation, push/merge, public
upload or final human acceptance is authorized by this step.
Why: Reuse a dependable factual navigation foundation rather than let agent prose
or stale artifacts become the source of truth. Relevant/affected/actually changed
are distinct; trusted source identity must match packets and citations.
Tradeoffs: Conservative byte/provenance freezing invalidates receipts on doc edits;
full gates must be rerun against final local HEAD. Contract guards do not themselves
prove filesystem bytes, architectural meaning, a human consent UI or useful answers.
Pending decisions: local-first versus hosted collaboration; existing-agent bridge
versus embedded provider; later private GitHub/generic JSON scope and measured budgets.
Those are still proposed defaults, not silently approved by Phase 0.
Evidence: release fix 9a5a327583936efd2844e80a6834b8d0a170be03 passed exact-postcommit
eight-gate/packaging verification with clean provenance and 17/17 real-receipt
negative/rollback probes. Final Phase 0 contract commit still requires its own receipt.
