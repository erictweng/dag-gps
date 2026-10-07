# Project: DAG GPS

## Goal

System-1 codebase navigator: Jev-style local scorer over an architecture DAG, standalone HTML

## User / Customer

TBD

## Problem

TBD

## Success Criteria

- [ ] Clear user-visible outcome defined
- [ ] Build/test command documented in `.verify.json` and `docs/ARCHITECTURE.md`
- [ ] First milestone shipped or demoable

## Milestones

Each milestone is split into small mini-milestones (see `TASKS.md`). One worker
handles one mini-milestone at a time and must verify before the next starts.

- [ ] Milestone 1: TBD

## Current Status

Initialized on 2026-10-07. See `STATUS.md` for the live view.

## Build Channel

All build updates go to Discord build channel `1549653555433054308`.
Workers write notes to `.hsub/build-updates/` (see `docs/BUILD_UPDATES.md`).

## Constraints

- Keep Hermes as orchestrator.
- Use `hsub --large` / `hsub --backend claude` for large-context work.
- Avoid routine Hermes `--provider anthropic` unless explicitly approved.
- Do not start the next worker until the previous worker's output is verified.

## Goal Checker Policy

A read-only reviewer (`hsub review check|prompt|run RUN_ID`) is available but is
never automatic. Use it selectively for medium/high-risk work where tests alone
do not prove success; skip it for tiny tasks. See `docs/GOAL_CHECKER.md`.

## Links

- Status: `STATUS.md`
- Tasks: `TASKS.md`
- Architecture: `docs/ARCHITECTURE.md`
- Build updates: `docs/BUILD_UPDATES.md`
- Goal checker policy: `docs/GOAL_CHECKER.md`
- Agent rules: `AGENTS.md`
- Project lead agent: `.claude/agents/project-lead.md`
- Decisions: `DECISIONS.md`
- Verification config: `.verify.json`
