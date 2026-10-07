# Goal Checker — DAG GPS

A selective, read-only reviewer pass for finished worker runs. It reduces
hallucinated success and scope drift without spending tokens on tiny tasks.

## What it does

`hsub review` compares the original goal and acceptance criteria against the
worker report, the changed files / diff summary, and the verification output,
then returns:

- Verdict: `pass | fail | partial | needs-human`
- Evidence
- Missing criteria
- Scope drift
- Risks
- Recommended next action

The reviewer is read-only: it is launched with Read/Grep/Glob only, with
Write/Edit/Bash denied, and its prompt forbids changing files.

## Commands

```sh
hsub review check  RUN_ID [--high-risk] [--pre-merge] [--semantic]   # trigger policy only, no LLM; exit 0 = recommended
hsub review prompt RUN_ID [--criteria FILE] [--out FILE]              # reviewer prompt only, no LLM
hsub review run    RUN_ID [--force] [--out .hsub/reports/review-RUN_ID.md]   # opt-in read-only Claude reviewer
```

## When to use it

- high-risk or user-facing milestone
- worker timeout / max-turns
- more than 3 files changed
- architecture or rules logic changed
- tests pass but acceptance criteria are semantic
- before merging to main or declaring a milestone complete

## When to skip it

- small docs edits
- a single config change
- format-only work
- changes fully proven by one deterministic command (e.g. `.verify.json` passed)

## Flow

1. Worker finishes (`hsub --report --verify ...`).
2. `hsub review check RUN_ID` (add `--pre-merge` for the last mini of a milestone).
3. Exit 0 -> `hsub review run RUN_ID --out .hsub/reports/review-RUN_ID.md`. Exit 1 -> normal verification only.
4. `pass` -> mark verified. `partial`/`fail` -> relaunch the worker with the missing criteria as the assignment.
   `needs-human` -> ask Eric using the recommended next action.

Never run the reviewer automatically on every task.
