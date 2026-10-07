# Build Updates — DAG GPS

All worker updates go to Discord build channel `1549653555433054308`.

## How Updates Are Sent

Workers do not post to Discord directly. Write a Markdown note to
`.hsub/build-updates/<milestone>-<mini>.md`; `hsub` watches that directory and
posts new or changed notes to the build channel.

## Format

```text
[BUILD] DAG GPS — <worker or Hermes>
Milestone: <milestone name or number>
Mini: <n>/<total> — <mini-milestone name>
Status: started | implementation-complete | verifying | verified | failed | blocked | goal-check
Output: <what changed or what was learned>
Verification: <actual commands/results, or pending>
Next: <next mini-milestone or blocker>
```

## Standard Update Sequence

For normal build work, use these staged updates:

1. `started` — what this mini-milestone is attempting, expected files/area, verification plan.
2. `implementation-complete` — what changed; this is still a worker claim until verified.
3. `verifying` — exact command/check now being run.
4. `verified` / `failed` / `blocked` — actual result, evidence, and next action.

For high-risk/user-facing/pre-merge work, also post `goal-check` with the `hsub review check` recommendation or reviewer verdict.

## Rules

- One note per mini-milestone. Update the same file rather than creating duplicates.
- `Verification` must contain real commands and results, not intentions.
- Post operational telemetry only: what changed, what command is running, what passed/failed, what is blocked, and what is next. Do not stream chain-of-thought.
- If blocked or tests fail, stop and report. Do not pivot to random adjacent tooling work.
