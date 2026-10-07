# .hsub

Project-local handoff area for ephemeral workers.

## Directories

- `reports/` — concise worker reports
- `handoffs/` — task prompts and intermediate planning/handoff files
- `build-updates/` — one Markdown note per mini-milestone; `hsub` posts new or
  changed notes to the Discord build channel (see `docs/BUILD_UPDATES.md`)
- `worktrees/` — optional git worktrees for isolated implementation tasks

## Examples

```bash
hsub --cwd . "Small Hermes task"
hsub --cwd . --large "Large Claude Code task"
hsub --cwd . --worktree feature-x --large "Implement TASKS.md item 1.1 and verify"
hsub review check RUN_ID        # should this run get a read-only goal check? (no LLM)
hsub review run RUN_ID          # opt-in read-only reviewer; see docs/GOAL_CHECKER.md
```
