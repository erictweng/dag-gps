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

## Measurement checkpoint

The frozen corrected variation grid is unchanged: seed
`dag-variation-v1-20261013`, templates SHA-256
`72e693930dcea20a22532532d50038f4bec51c74bc97e0f00d2173068655a388`.
Honcho: 92,856 positives + 240 negatives; Salesroom: 51,410 + 240.
Three timed sweeps per version, 200 seeded warmups. Raw case results, timing,
per-operation collision-target counts and frozen reruns are under
`artifacts/parser-collisions/`; runner: `node scripts/bench_parser_collisions.cjs`.
It archives the base web modules without changing any other worktree, verifies
snapshot hashes, and invokes the existing frozen-question grader unchanged.

Checkpoint: confident wrong Honcho 380→288, Salesroom 712→682, zero newly wrong
cases. Matched→choice: 152 Honcho / 30 Salesroom, including 60 formerly correct
Honcho matches. Frozen hand-written results are unchanged on every split; no
negative becomes confidently matched. Construction-label robustness is not user
accuracy. The runner's final rerun and eight-gate receipt are pending.

## Clean-checkout behavior

Committed mechanics/contract tests need no ignored data. The old pinned benchmark
regressions and variation coverage tests now explicitly skip if their snapshots
are absent, naming the missing optional artifact. A malformed present artifact is
not swallowed. Full-suite detached-checkout counts will be recorded after running
against committed HEAD, then removing the temporary checkout.

## Retained limits

Parenthesized route paths (`app/(seller)/...`) remain unchanged and out of scope.
The frozen-grid choice grader requires all intended endpoints on the first choice
page; sequential endpoint choice is tested separately and is not relabeled as a
benchmark success. Caller syntax can yield a CALLERS choice before the user chooses
a file and therefore switches to the import graph's DOWNSTREAM operation.

The parent consultant's AgentBridge duplicate-validation finding is not fixed by
this parser card. Its server-speed approval remains an upstream responsibility.
No following feature was started.
