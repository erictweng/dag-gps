# Cross-kind operation choices

Card `t_29b602b9`, branch `parser-collisions`, base `08f1b4d` (server-speed).
No push, merge or PR. Generalist approval remains separate from consultant advice.

## Change and semantics

The service resolves literal cross-kind names before selecting the import or call
graph, including both directed-route endpoints. Alternatives retain the operation;
kind/path/qualified-ID selection and the UI's alternative query + chosen ID replay
are covered. Two ambiguous endpoints require sequential choices. Fuzzy endpoints
remain suggestions, and mixed graph kinds are unsupported, not silently converted.

File/folder caller vocabulary executes import DOWNSTREAM; callee/trace vocabulary
executes UPSTREAM. Symbol callers/callees are one-hop; TRACE/UPSTREAM and DOWNSTREAM
are forward/reverse transitive calls. PATH/FLOW retain complete directed witnesses.
Certain-only filtering and packet bounds remain in force. This is static evidence,
not a statement about runtime invocation.

RED-first regressions exercised the actual service on both unchanged pinned
snapshots plus a small committed mechanics fixture. Initial failures are retained
in `artifacts/parser-collisions/red.log`. Tests cover each operation, invalid
choices, endpoint-local hints, multi-step routes, UI replay, pagination, fuzzy
non-promotion, directed call witnesses and certain-only filtering. Cross-language
worker packets are checked against the unchanged Python contract.

Two legacy tests intentionally changed: call-tier tests qualify their colliding
`a` symbol rather than silently preferring it over `a.py`; legacy file/group
LOCATE parity remains exact, while caller vocabulary now checks traversal instead
of preserving the old LOCATE fallthrough. No assertions on edge confidence or
witness correctness were removed.

## Final measurement

The frozen corrected variation grid is unchanged: seed
`dag-variation-v1-20261013`, templates SHA-256
`72e693930dcea20a22532532d50038f4bec51c74bc97e0f00d2173068655a388`.
Honcho: 92,856 positives + 240 negatives; Salesroom: 51,410 + 240.
Three timed sweeps per version, 200 seeded warmups. Raw case results, timing,
per-operation collision-target counts and frozen reruns are under
`artifacts/parser-collisions/`; runner: `node scripts/bench_parser_collisions.cjs`.
It archives the base web modules without changing any other worktree, verifies
snapshot hashes, and invokes the existing frozen-question grader unchanged.

Implementation measured: `01dfb1b3c6d09dd99f6753257e9ab0101ef48273`; query-service
SHA-256 `b0caa490ab05643d31b76948cc48c047737df50371bc62c9d2d148959296677b`.
868,476 timed calls across both versions and repos. Compact committed receipt:
`eval/parser_collision_results.json`; complete axes and raw JSONL remain local.

| Repo | Correct | Correct-or-choice | Confident wrong | Matched→choice | Correct→choice | New wrong |
|---|---:|---:|---:|---:|---:|---:|
| Honcho | 85,135→85,080 | 89,243→89,226 | 380→288 | 152 | 60 | 0 |
| Salesroom | 46,358→46,359 | 48,257→48,287 | 712→682 | 30 | 0 | 0 |

All 60 formerly correct Honcho matches become choices containing the intended
target. Correct-or-choice still drops slightly on Honcho: first-page grading and
the operation of unresolved cross-graph choices remain strict, not relabeled.
Both repos' 240 generated negatives remain no-match. No individual case becomes
newly confident-wrong, hence none of the fixed operation/axis buckets increases.
Construction-label robustness is not user accuracy.

### Frozen-grid collision targets, per operation

This subset includes any row targeting an ID whose literal name occurs across
multiple kinds, including explicit path/kind forms. It is not limited to the
ambiguous spelling, and is not the separate `backfill`/`events` supplement below.

| Repo / operation | N | Correct | Correct choices | Wrong | Matched→choice |
|---|---:|---:|---:|---:|---:|
| Honcho LOCATE | 10,178 | 9,085→9,085 | 915→915 | 0→0 | 0 |
| Honcho UPSTREAM | 6,960 | 6,230→6,200 | 630→660 | 40→0 | 70 |
| Honcho DOWNSTREAM | 8,352 | 7,294→7,264 | 676→686 | 52→0 | 82 |
| Honcho CALLERS | 155 | 145→145 | 0→0 | 0→0 | 0 |
| Honcho CALLEES | 62 | 58→58 | 0→0 | 0→0 | 0 |
| Honcho TRACE | 62 | 29→29 | 0→0 | 0→0 | 0 |
| Honcho PATH | 3,480 | 3,282→3,285 | 45→45 | 0→0 | 0 |
| Honcho FLOW | 29 | 28→28 | 0→0 | 0→0 | 0 |
| Salesroom LOCATE | 868 | 798→798 | 56→56 | 0→0 | 0 |
| Salesroom UPSTREAM | 620 | 570→570 | 40→40 | 0→0 | 0 |
| Salesroom DOWNSTREAM | 744 | 668→668 | 46→40 | 0→0 | 0 |
| Salesroom PATH | 290 | 276→276 | 0→0 | 0→0 | 0 |

Salesroom has no extracted symbols and no generated CALLERS/CALLEES/TRACE/FLOW
target rows. Its overall 30 wrong→choice improvements are outside this literal
collision-ID subset. Six formerly credited Salesroom DOWNSTREAM choices now have
the unresolved CALLERS operation; they remain choices, not confident wrongs.

### Concrete counterexample supplement (not added to the frozen grid)

`x` is Honcho `backfill` or Salesroom `events`; `y` is that repository's exact
colliding file path. C=needs-choice, M=matched, N=no-match. Every after packet is
a choice with the requested syntactic operation, before the graph kind is known.

| Query family | Honcho before→after | Salesroom before→after |
|---|---|---|
| where is x | C→C | C→C |
| what uses x / dependents of x / downstream of x | M→C (each) | C→C (each) |
| what does x use / dependencies of x / upstream of x | M→C (each) | C→C (each) |
| who invokes x | M→C | C→C |
| callers of x | M→C | N→C |
| what does x call / callees of x | M→C (each) | N→C (each) |
| trace from x | M→C | M/LOCATE→C/TRACE |
| path from x to y / path from y to x | M→C (each) | C→C (each) |
| how does x reach y / how does y reach x | M/PATH→C/FLOW (each) | C→C (each) |

Honcho 15/16 matched→choice; Salesroom 1/16. These are separate from the grid's
152/30 transitions, not added to them. Every file/symbol/folder candidate is tested
through original-query choice and UI-style query+ID replay. All 160 real-repo
packets (80 per repo, including choices and follow-through) pass the Python contract:
`artifacts/parser-collisions/real-contracts.json`.

### Frozen hand-written sets (identical before and after)

| Repo / split | Cases | Correct matches | Correct choices | Negative no-match | Wrong |
|---|---:|---:|---:|---:|---:|
| Honcho dev | 80 | 46 | 13 | 16 | 1 |
| Honcho holdout | 27 | 18 | 5 | 4 | 0 |
| Salesroom dev | 32 | 20 | 5 | 6 | 0 |
| Salesroom holdout | 11 | 7 | 0 | 2 | 0 |

Direct warm p95: Honcho 0.823→0.791 ms; Salesroom 0.124→0.127 ms. No CPU isolation
or randomized version order; these are whole-service measurements, not a claim of
server speed. No new HTTP performance measurement was required or substituted.

## Clean-checkout behavior

Committed mechanics/contract tests need no ignored data. The old pinned benchmark
regressions and variation coverage tests now explicitly skip if their snapshots
are absent, naming the missing optional artifact. A malformed present artifact is
not swallowed. A fresh `git worktree add --detach` checkout of `01dfb1b` passed
474 Python tests; JS 225 passed, 8 skipped, zero failed (233 registered). It had
no copied snapshots. The committed collision mechanics/packet tests ran. The
temporary checkout was clean and removed with `git worktree remove` afterward.
Logs: `artifacts/parser-collisions/clean-{js,python}.log`.

## Gates and retained attempts

On `01dfb1b`, all eight unchanged gates passed on the first full attempt:
build, test, smoke, release_session, accessibility, performance, ui_performance,
milestone_acceptance. Packaging passed. Test gate: 474 Python / 265 JS, zero skips.
Release scorer worst p95 4.307 ms (<10 ms). No performance retry or threshold change.
Receipt: `artifacts/parser-collisions/gates/verification.json`; package receipt
beside it. Later edits are measurement-harness/reporting only, not query behavior.

The RED run, intermediate JS failures, one legacy-parity Python failure and the
one-sweep diagnostic benchmark are retained. The initial RED harness also had an
incorrect LOCATE seed assertion; it was corrected to check traversal seeds only.
The legacy failure was the now-intentional caller→traversal change described above,
not hidden by weakening confidence/edge assertions. Final unchanged release gates
ran with the installed Playwright/axe dependencies and all tests enabled.

Reproduce with the frozen snapshots present:

```sh
node scripts/bench_parser_collisions.cjs
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

Release/browser environment is documented in `docs/SERVER_PERFORMANCE.md`.
Run `/usr/bin/python3 scripts/release_check.py --output artifacts/parser-collisions/gates-reproduced`
from this checkout with that environment. No other worktree is modified by these commands.

## Retained limits

Parenthesized route paths (`app/(seller)/...`) remain unchanged and out of scope.
The frozen-grid choice grader requires all intended endpoints on the first choice
page; sequential endpoint choice is tested separately and is not relabeled as a
benchmark success. Caller syntax can yield a CALLERS choice before the user chooses
a file and therefore switches to the import graph's DOWNSTREAM operation.

The parent consultant's AgentBridge duplicate-validation finding is not fixed by
this parser card. Its server-speed approval remains an upstream responsibility.
No following feature was started.
