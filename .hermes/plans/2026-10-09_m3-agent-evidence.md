# M3 — Agents consume the same evidence and explain beside it

Branch `workspace-repo-import`, worktree `/Users/aibert/projects/dag-gps-repo-import`, base `4b20b5c`
(M2 complete, full release gate passed). Roadmap: `.hermes/plans/2026-10-08_130312-repository-evidence-workspace.md` §M3.

Goal: an explicitly invoked coding agent reads the same System 1 evidence packet + revision-bound source the
human sees, and its explanation is validated (citations bound to the exact revision) and shown beside the graph.
No automatic model calls, no provider credentials in the app, no imported-code execution, no graph mutation.

## Waves (parallel within a wave; disjoint files per task; parent integrates + commits)

### Wave 1 (parallel, pure Python, no server/UI)
- **T1 Revision-bound source + context** — `app/context.py`, `tests/test_agent_context.py`, `docs/WORKSPACE_CONTEXT.md`.
  `read_source(git_dir, snapshot, path, start=None, end=None)` reads the blob at the snapshot commit through the
  accepted `_run_git`, verifies SHA-256 against the inventory (mismatch = stale/tampered), returns bounded lines.
  `build_context(git_dir, snapshot, packet, budget...)` validates the packet against the snapshot first, then
  attaches bounded excerpts for selected files with explicit truncation/omissions.
- **T2 Explanation contract** — `app/explanations.py`, `tests/test_agent_explanations.py`, `docs/WORKSPACE_EXPLANATIONS.md`.
  `dag-gps-explanation/v1` validator: bound to packet requestId/snapshotId/packetSha256; plaintext bounded paragraphs;
  citations must match inventoried path + hash + in-range lines (or null file-level); claims without citations must be
  tagged inferred; suggested relationships are an agent-inferred overlay only; usage tokens null when unknown.

### Wave 2 (parallel, after Wave 1 accepted)
- **T3 Agent bridge + CLI** — `app/agent_bridge.py`, `scripts/workspace_cli.py`, `tests/test_workspace_cli.py`.
  Tools `find_nodes, get_dependencies, get_dependents, find_path, get_source, get_context, submit_explanation`;
  JSON stdin/stdout; validated tool names/IDs; never shell-interpolates text; read-only except storing a validated
  explanation beside the revision (never the graph).
- **T4 Server + UI** — source endpoint, context export (explicit consent), explanation intake/display;
  `app/server.py`, `web/workspace.*`, `tests/test_workspace_server.py`, `tests/test_workspace_ui.py` extensions.

### Wave 3 (parent)
Integration, `.verify.json` inventory, independent review of Wave 1–2 bytes, one real explicitly invoked
read-only agent explanation on a real repo (needs Eric's consent + agent choice), full release gate, commit.

## Rules for every task
TDD with retained RED; Python 3.9 stdlib; no network/model calls in code or tests; reuse `app.repositories._run_git`,
`app.contracts`, `app.workspace_snapshot` unchanged; don't touch files outside the task's list; no commit/push;
write a report with RED/GREEN commands, counts and file SHA-256s.
