# Python function layer — local implementation, review pending

Tasks `t_58cccce0` / review fixes `t_4977fa02`, branch `function-layer`. This extends the local workspace, not
legacy offline maps. No model/provider calls, source execution, push, PR or main
integration. Consultant review and parent acceptance remain pending.

## What is supported

- Python stdlib AST definitions: functions, async functions, classes, methods and
  nested definitions, with qualified name, file and inclusive definition range.
- Resolved lexical calls to unique same-module definitions, `self.method()` in an
  undecorated method, and functions reached through already-observed repo imports
  (`from x import f`, `import x`, aliases and concrete relative submodules).
- Separate unresolved call-site records, never guessed edges. Decorated targets,
  variable-held instances, inherited methods, reexports, framework scheduling,
  external functions, module-scope calls and unsupported bindings remain unknown.
  A class call targets its definition, not an inferred constructor/body execution.
  Class-body, lambda and generator-expression calls remain non-traversable unresolved
  evidence; they cannot compose into an invocation-flow chain.
- AST parameters, lexical rebinding and duplicate definitions prevent confident
  name selection. Wildcard-import scopes invalidate lookup conservatively; defaults,
  decorators, bases and annotations are collected in their defining scope, not the
  new function body. Literal attribute stores invalidate matching attribute calls
  conservatively across their file. Comprehension/lambda parameters are conservative. This is not a
  full Python interpreter: monkeypatching, conditional execution, runtime attribute
  mutation, import hooks and complete closure/dataflow semantics are not modeled.
- Deterministic operation head plus exact symbol target head: LOCATE, direct
  CALLERS, direct CALLEES, shortest-path FLOW, forward TRACE. Names are
  case-sensitive; qualified `path:qualname` or `path#qualname@line` disambiguates.
  Duplicate names require choice; FLOW endpoints can be chosen sequentially.
- Call witnesses retain all observed call-site lines. No-path means no *resolved
  static* path, not that runtime flow cannot occur. Genuine call cycles remain.
  Symbol packets exceeding the unchanged 1 MiB serialized contract budget return
  bounded `unsupported` with no highlights, rather than clipping call-site evidence.
  Whole-chain cardinality pagination remains; oversized byte results are not paged.
- Proposed group → file → definition expansion; questions show only selected
  symbols in their source-file lanes. Symbol and call-site buttons open hash-
  verified, revision-bound source. Clear returns to the group overview.
- Versioned `map.symbol_graph` is additive. Legacy map arrays/scorer/router remain
  unchanged; existing file/group packets keep their behavior. Bounds remain
  unchanged. See [WORKSPACE_CONTRACT.md](WORKSPACE_CONTRACT.md).

Syntax is limited by the running Python parser (3.9 in this verification). A parse
error produces a file diagnostic, leaves its file node intact, and does not claim
symbols/calls for that file. Honcho has two such symbol diagnostics at this pin.

## Agent bridge

`scripts/workspace_cli.py --workspace <workspace>` accepts one JSON request on
stdin, using the existing project/snapshot binding. New tools are `find_symbols`,
`get_callers`, `get_callees`; each takes `args: {"symbol": "name-or-qualified-ID"}`
and optional continuation/choice. Existing `find_nodes` and `get_context` also
accept function questions through the shared query service. `get_source` retains
its literal path/start/end API.

`app/context.py` starts symbol excerpts at their definitions, not line 1. It still
returns only the first selected range per file and reports its budgets/limits;
packets retain the full selected evidence. It never executes imported code or
sends context to a provider. The real Honcho audit ran all three new CLI tools,
validated their packets, and matched their selections to browser results. A
source/context probe starts at the message-ingestion definition, line 113.

## Real Honcho proof

Source: `https://github.com/plastic-labs/honcho`, exact commit
`3922af856d78ec41133916deec4d821fa9c5a92e`.

The real app's import form was driven in Chromium against `WorkspaceServer`,
using production acquisition, inventory, extraction, publication, query worker
and source endpoints. Honcho itself was not run or installed. Snapshot:
`6f12d85256dcea4a07ef2ea841f77a574bc6468682531bd9b3d4cbfd80d09346`.

| Measurement | Observed value |
|---|---:|
| Inventory members | 1,162 |
| Mapped source files (all supported file languages) | 663 |
| Python source files supplied to symbol extraction | 562 |
| Python definitions, including tests/examples/SDK overloads | 7,670 |
| Resolved call sites | 7,836 |
| Unique resolved call edges | 6,506 |
| Unresolved call sites | 37,112 |
| Symbol syntax diagnostics | 2 |
| Real app import-to-ready | 50.480 seconds |
| Warm JS query p95 | 1.678 ms, 800 measured samples |
| JS query index creation | 68.051 ms |

The review-fix rerun used the real import form and a new snapshot identity. Its
import-to-ready timing includes the acquisition/publication/UI path, unlike the
original 20.604-second cache-only build measurement (historical `build-timing.json`).
The conservative fixes move 63 previously resolved sites to unresolved evidence;
definition count is unchanged. No source pin or contract limit changed.
The query benchmark used all eight questions, 10 warm-up and 100 measured rounds
per question. It excludes Python validation, worker IPC, HTTP and drawing. Actual
browser request-to-render timings are separately retained in `browser-report.json`
and range from roughly 528 to 1,497 milliseconds, not the JS-only result.

The first symbol-enabled import failed with exactly:
`Static extractor graph output exceeded its limit` (16,777,216 bytes).
A diagnostic measured that initial symbol extension at 18,329,034 bytes indented,
15,634,405 bytes compact, before later binding refinements. The minimum fix applied
was compact serialization of the machine-read extractor sidecar: removing JSON
whitespace, not evidence. The unchanged 16 MiB limit then accepted the real import.
No quota, timeout, packet bound, source scope or test threshold was raised.
`app-proof.log` and `limit-measurement.json` retain the initial failure/evidence.

Grouping remains proposed, extraction remains partial, and existing unresolved
imports/cycles still block *reviewed architecture publication*. That does not
prevent inspection of the dependency preview. There is no runtime-completeness
or repository-wide accuracy claim.

## Eight source spot-checks

Questions are checked in at `eval/function-honcho.json`. `packet-N.json`,
`question-N.png` and corresponding source screenshots use the numbering below.
“Right” means the checked narrow result agrees with source, not general accuracy.
“Partial” means useful evidence remains missing even when displayed links are true.
All Honcho file/line citations below refer to the exact commit above. The review-fix
rerun preserves all eight statuses, selected IDs and call edges, and hash comparison
confirms all seven audited source files are unchanged. The table's source findings
and three-right/five-partial disposition therefore remain unchanged. Evidence:
`../artifacts/function-layer/review-fixes/honcho-comparison.json` (local/ignored).

| # | Question | Source check and result |
|---|---|---|
| 1 | Where is `create_messages_for_session` defined? | **Right**: `src/routers/messages.py:113–184`; route decorators at 100–112, CRUD call at 122–127, background enqueue at 166. LOCATE opens the exact definition. |
| 2 | What does `src/crud/message.py:create_messages` call? | **Partial**: resolved `reject_scope_peers` at `src/crud/message.py:411–416` and `get_or_create_session` at 420–424 are real. DB methods at 426–432, 465 and 497 and instance-based embedding preparation at 477 are not resolved edges. |
| 3 | What calls `process_representation_tasks_batch`? | **Partial**: no resolved caller is returned, explicitly not “no callers exist.” A real caller is `src/deriver/consumer.py:236–247`; its target is decorated at `src/deriver/deriver.py:43–44`, so the conservative extractor leaves that call unresolved. |
| 4 | How does `src/routers/peers.py:chat` reach `DialecticAgent`? | **Right for this endpoint**: `src/routers/peers.py:404–417` → `agentic_chat`; `src/dialectic/chat.py:116–128` → class definition `src/dialectic/core.py:62`. This is construction evidence, not an inferred full LLM path. |
| 5 | How does that route reach `DialecticAgent.answer`? | **Partial**: graph says no resolved path. Source has `agent.answer(...)` at `src/dialectic/chat.py:130`; the instance-held call is deliberately unresolved. The answer method exists at `src/dialectic/core.py:548`. |
| 6 | Trace from `src/dialectic/chat.py:agentic_chat` | **Partial**: checked outgoing configuration and constructor calls at `src/dialectic/chat.py:102,116–128` match the drawing. The important `agent.answer` step at 130 is absent; the trace is not the full chat request. |
| 7 | Where is `chat` defined? | **Right ambiguity**: both server routes `src/routers/peers.py:257` and `src/routers/workspaces.py:311` appear among alternatives; SDK/example definitions also remain visible. No arbitrary target is highlighted. |
| 8 | What does `src/deriver/consumer.py:process_item` call? | **Partial**: checked reconciler at `src/deriver/consumer.py:72`, webhook at 89, summarizer at 130–138, deletion at 165 and scope handlers at 180/195 agree with selected branches. Runtime dispatch and decorated `process_dream` at 152 remain outside the resolved graph. |

Disposition: three narrow results right, five partial, none of these spot-checks
classified wrong. This is a worker-selected sample, not an accuracy benchmark.
Only cited portions of complex answers were manually audited; packet validation
checks provenance/structure, not semantic completeness of every edge.

## How Honcho is built — a source-grounded reading route

1. Start at message ingestion: the session POST handler calls CRUD, constructs
   message payloads and schedules enqueue through background tasks
   (`src/routers/messages.py:100–127,147–166`). The map locates the handler but
   does not turn framework scheduling into a call edge.
2. Follow persistence separately: CRUD checks scope peers, establishes the session,
   obtains a PostgreSQL advisory lock, creates message objects, optionally prepares
   embedding rows, and commits (`src/crud/message.py:411–432,448–497`). The two
   direct helper links are drawn; DB/instance methods remain unknown.
3. Follow asynchronous processing by source, not a fabricated graph hop: the
   consumer branches on `queue_item.task_type` (`src/deriver/consumer.py:47–58`),
   with summarization at 130–138 and deletion at 165. Representation batches call
   the decorated deriver at 236–247; the decorator boundary is visible in
   `src/deriver/deriver.py:43–44` and is unresolved in this map.
4. Read the question path: the peer route invokes `agentic_chat`
   (`src/routers/peers.py:404–417`), which reads configuration, constructs
   `DialecticAgent`, and calls the instance's `answer`
   (`src/dialectic/chat.py:102,116–130`). The first two hops are drawn; the
   instance call is established by this source check, not by the graph.
5. Inside `answer`, tools/query context are prepared and `honcho_llm_call` is
   invoked with tools, messages and budgets
   (`src/dialectic/core.py:567–605`). This explains the missing destination in
   the static trace; it is not a claim that DAG GPS executed or traced an LLM.

## Verification and artifacts

- Prerequisite `origin/main` merged as `eb72a73`; baseline 401 Python / 173 JS passed.
- RED evidence: `extraction-red.log`, `contract-query-red.log`, `drilldown-red.log`,
  `shadowing-red.log`, `attribute-rebinding-red.log` under `artifacts/function-layer/`.
- Review-fix acceptance: 418 Python tests and 178 JS tests passed. Commands:
  `env -u PYTHONPATH /usr/bin/python3 -m unittest discover -s tests -q` and
  `node --test tests/*.test.cjs`. Existing suites were not edited.
- All four consultant points accepted and fixed. Six new Python test methods
  exercise binding scope, wildcard invalidation, deferred ownership, 150-function
  chains with 1 and 20 sites per edge through JS/Python validation, and exact legacy
  packet parity against `eb72a73` both with and without the symbol extension.
  The RED run records failures for every reported category; the GREEN run passes.
- `.verify.json` build/smoke and all four eval commands exit 0. Lookup retains
  39/40 operation/label correctness, not perfection; no scorer tuning. Separate
  release packaging/performance recipes were not part of this follow-up acceptance.
  Logs: `artifacts/function-layer/review-fixes/`.
- One development failure found an SVG nested-interactive accessibility issue;
  the containing SVG now has role `group`, and the existing real-browser/Axe suite
  passes. A later unchanged-suite run hit an oversized-body connection reset in
  `test_m3_route_specific_body_limits`; the full unchanged rerun passed. Both logs
  are retained; no weakening or test removal.
- Honcho browser proof: eight questions, exact highlighted-ID assertions, manual
  group/file/function clicks, source line starts, zero page errors and zero external
  browser requests. This does not assert a new Honcho-specific Axe audit.
- Large diagrams still scroll. `question-bottom-8.png` shows the lower part of the
  long callee view; SVG crops are not a fit-to-screen guarantee.

Artifact root: `artifacts/function-layer/honcho/` (local/ignored). Key files:
`browser-report.json`, `audit.json`, `build-timing.json`, `query-benchmark.json`,
`snapshot.json`, `packet-1.json` through `packet-8.json`, `question-*.png`,
`source-*.png`, `manual-drilldown-source.png`, and hash-verified `source/` copies.

Reproduce the real app proof and audit from this checkout:

```sh
env -u PYTHONPATH /usr/bin/python3 scripts/verify_function_honcho.py
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_honcho.py
node scripts/bench_function_honcho.cjs
```

Playwright is required; the script uses the repo's established installed fallback.
The server is loopback-only, its session capability is not written to reports, and
it shuts down when the proof finishes. Browser/packet artifacts are overwritten on
rerun; the failed import and test logs are separate retained files.
