# Agent Instructions — DAG GPS

## Project Context

Read `PROJECT.md`, `STATUS.md`, `TASKS.md`, `DECISIONS.md`, and `docs/ARCHITECTURE.md`
before major work. Read `docs/BUILD_UPDATES.md` before posting any update.

## Model Routing

- Use Hermes for orchestration and small tasks.
- Use `hsub --large` or `hsub --backend claude` for large-context repo work.
- Do not use Hermes `--provider anthropic` unless Eric explicitly approves potential extra usage.

## Mini-Milestone Workers

Each worker run handles exactly one mini-milestone from `TASKS.md`.

- Do only the assigned mini-milestone. Do not start the next one.
- Verify with real command output before reporting completion. Use `.verify.json`
  when it defines commands.
- Write a build update to `.hsub/build-updates/<milestone>-<mini>.md` using the
  format in `docs/BUILD_UPDATES.md` before finishing.
- Update `STATUS.md` (and the task's status in `TASKS.md`) when done or blocked.
- If blocked or tests fail, stop and report. Do not pivot to adjacent work.

## Goal Checker (selective, read-only)

After a worker finishes, the lead may run a read-only reviewer that compares the
original goal and acceptance criteria against the worker report, changed files,
and verification output, and returns `pass | fail | partial | needs-human`.

- Run `hsub review check RUN_ID` first; it applies the trigger policy without a model.
- Use it when: high-risk or user-facing milestone; worker timeout/max-turns;
  more than 3 files changed; architecture or rules logic changed; tests pass but
  the criteria are semantic; before merging to main or declaring a milestone complete.
- Skip it for: small docs edits, a single config change, format-only work, or
  changes fully proven by one deterministic command.
- The reviewer never edits files. Workers do not launch reviewers on themselves.
- Details: `docs/GOAL_CHECKER.md`.

## Worker Handoff Format

When a worker finishes, report:

1. Task attempted
2. Result
3. Files changed
4. Commands run
5. Verification output
6. Blockers / follow-ups
7. Whether the next mini-milestone is ready to launch

## Coding Standards

- Prefer small, verifiable changes.
- Do not claim success without real command output or file verification.
- Keep generated docs concise and durable.

## Do Not Do

- Do not paste huge logs into chat when a file path/report is better.
- Do not overwrite existing user files unless explicitly asked.
- Do not perform paid/raw Anthropic API calls unless explicitly approved.
