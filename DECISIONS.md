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

## 2026-10-08 — Phase 1 defaults approved

Context: Eric requested Phase 1, then explicitly answered “use defaults” to the
pending deployment and agent-integration choices.
Decision: Local-first desktop workspace with snapshot sharing initially; connect
existing coding agents through the evidence bridge later, rather than embed chat
or create a hosted multi-user service now. Phase 1 is token-free public GitHub
root URL acquisition, immutable pin/cache, safe file inventory and provisional
dependency JSON/offline preview. No agents, provider APIs, workspace server,
live watcher or arbitrary graph import in this phase. No push/merge/public upload.
Why: Prove deterministic factual indexing before context explanation and live UI.
Starting point: independently verified local Phase 0 e94cfbae24f3f22bde4c35cbdfa74b6b95f94f5d,
new isolated branch workspace-repo-import at /Users/aibert/projects/dag-gps-repo-import.
Declared real public smoke: pallets/itsdangerous at
672971d66a2ef9f85151e53283113f33d642dabd, resolved through noninteractive GitHub
ls-remote before implementation. This is a validation fixture, not user ground truth.
Tradeoffs: No hosted collaboration/account design or private-GitHub authentication;
unsupported extraction and provisional folder grouping stay visible. Runtime
scripts use no model calls; development workers still use the configured coding tools.

## 2026-10-08 — Phase 1 coding-worker fallback explicitly approved

Eric requested deployment of an OpenAI coding worker, specifically GPT-5.6 Sol,
after the Claude Code weekly-limit failure. Launched hsub Hermes backend using
per-invocation --model gpt-5.6-sol --provider openai-codex, without changing the
main gateway/provider configuration or using raw Anthropic. Coding delegation
is disabled in this worker's toolset so the requested coding model stays pinned.
Run: 20261008-151949-a33182; workspace-repo-import; first acquisition mini only.
Parent verified metadata running and exact model/provider command flags. Initial
RED test creation is progress, not implementation or acceptance. Original failed
Claude logs/report are retained. Source/test/public import gates still required.
