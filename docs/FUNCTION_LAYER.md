# Python function layer — confidence tiers, consultant review pending

## Current build: `t_39e90fae` (Honcho v2)

Local-only on `function-layer`, on top of `62010f6`. No push, merge, source execution,
model call or change to scorer/import evidence. The historical report below records
the earlier lexical-only build; this section supersedes its support limits and numbers.

### Evidence tiers and certain-only mode

| Tier | Supported evidence | Drawing |
|---|---|---|
| `resolved` | Unchanged legacy lexical resolver | Solid |
| `instance-local` | Direct single-assignment `x = RepoClass(...)`, then `x.method()`; or a uniquely assigned `self.attr = RepoClass(...)` in `__init__`, used in that class | Long dash |
| `typed` | A parameter or direct variable annotation naming a repo class; method lookup against that class | Dots |
| `through-decorator` | A lexically identified decorated definition, including decorated classes; original decorator text retained, not wrapper behavior | Dash-dot |
| `unresolved` | No supported unique target | Listed call sites, never drawn |

These are evidence categories, not calibrated probabilities or runtime dispatch.
Method lookup uses C3 MRO for fully known in-repo bases. Own methods can be identified
without resolving external bases; inherited lookup never skips an unknown base.
An edge and each witness report their weakest tier, ordered as in the table.
Multiple sites on one edge retain individual tiers. No new site becomes `resolved`.

Assignments inside branches/loops/with/try blocks, receiver rebinding/deletion,
captured locals, multiple attribute writes, known method mutation, missing methods
and `getattr` stay unknown. Candidates are deliberately conservative: direct function
body assignments only, use on a later line, no factory-return inference, no receiver
aliases, no optional/union/generic annotation inference, and no inferred instance type
through a decorated class constructor. Annotations can be false and subclasses can
override methods. Monkeypatching/DI/descriptor dispatch are not fully modeled.
The original wildcard, definition-time scope, lambda/generator and class-body guards remain.

Recognized route/task/scheduler decorators mark definitions as `entryPoint` metadata
with their bounded decorator text; registration creates no handler caller edge.
Recognition is syntactic (common registration method names and `app`/`router`/`scheduler`
prefixes), not exhaustive framework analysis. Abstract decorated methods identify a
declaration, not a concrete override. Decorator text is capped at 512 characters each.

CALLERS/CALLEES/FLOW/TRACE traverse all tiers by default. The UI checkbox “Certain
links only” and boolean request/agent argument `certainOnly: true` restore legacy
lexical selections, call sites, unresolved ordering, witnesses, reasons and limitations.
Thirteen complete Honcho packets and six synthetic packets match `62010f6` exactly
after removing only the explicit `certainOnly` mode marker. This also handles an edge
containing both old and new sites. File/group questions keep their legacy dispatch.

The additive `dag-gps-symbols/v1` extension has per-tier counts, node decorator/entry
metadata, site confidence, and compact `certainAdditions` triples `[before, edgeIndex,
siteIndex]`. Triples reference existing evidence to reconstruct legacy unknown sites
without duplication. Contracts validate counts, references, weakest edge confidence,
decorator provenance and packet entry points. Producer fingerprints include the new
`python_call_tiers.py` module; older producer receipts remain readable.

### Pinned real-app proof and counts

Honcho pin: `3922af856d78ec41133916deec4d821fa9c5a92e`. Real Chromium import form,
production WorkspaceServer, extraction/publication/query worker, rendered questions,
source endpoints and three agent CLI tools, not a mocked import. Snapshot:
`f55d5acd4c489f0c102b2330702c1eb0fa941e98438af0cc057e09cc0432bcbd`.

| Measurement | Observed |
|---|---:|
| Inventory / mapped files / Python definitions | 1,162 / 663 / 7,670 |
| Resolved sites / edges (unchanged) | 7,836 / 6,506 |
| Instance-local sites / edges | 461 / 396 |
| Typed sites / edges | 388 / 227 |
| Through-decorator sites / edges | 1,579 / 1,316 |
| Unresolved sites | 34,684 |
| Entry points / syntax diagnostics | 116 / 2 |
| Newly supported sites / edges | 2,428 / 1,939 |
| Browser questions / certain-only comparisons | 13 / 13 |
| New links in those answers / call sites checked | 37 / 44 |

The 37 newly displayed links were spot-checked against pinned source, including all
12 callers of the decorated deriver (one production caller and eleven test callers),
the two agent instance methods, typed representation formatting and stored metrics
collector methods. The review sheet includes every displayed added link and all its
sites: `artifacts/function-layer/honcho-v2/displayed-new-links.txt`.
Wrong new links found in these audited answers: **none (`[]`)**. No tier was disabled.
The abstract-method links in question 13 are declaration evidence, not implementations.

Additionally, all 1,939 new repository edges / 2,428 sites were mechanically corroborated
against real AST call expressions, target definition ranges and decorator text, using
272 hash-verified source files (`all-new-links.json`, `tier-audit.json`). That is a
structural check, not a manual semantic audit of every repository edge, nor proof of
runtime dispatch. Tests/examples/SDK code remain included; no repository-wide accuracy claim.

### Thirteen source-checked questions

Questions 1–8 are unchanged from `eval/function-honcho.json`. Questions 9–13 are added
by the v2 real-app proof. “Right” is limited to the cited endpoint/evidence, not a claim
that every possible runtime callee was discovered. All source citations use the pin above.

| # | Question | Result and source evidence |
|---|---|---|
| 1 | Where is `create_messages_for_session` defined? | **Right**: `src/routers/messages.py:113–184`; route decorators at 100–112 now appear as entry metadata. |
| 2 | What does `src/crud/message.py:create_messages` call? | **Partial**: adds decorated `models.Message` construction at 452 and `MessageEmbedding` at 484 (`src/models.py:212–213,293–294`). DB/embedding runtime calls still missing. |
| 3 | What calls `process_representation_tasks_batch`? | **Right for observed callers**: production `src/deriver/consumer.py:236–247` now reaches `src/deriver/deriver.py:43–44` through its Sentry decorator; eleven explicit test callers also source-checked. No scheduler caller invented. |
| 4 | How does `src/routers/peers.py:chat` reach `DialecticAgent`? | **Right**: route call at `src/routers/peers.py:404–417`, construction at `src/dialectic/chat.py:116–128`; still construction, not automatic constructor/body traversal. |
| 5 | How does that route reach `DialecticAgent.answer`? | **Right**: route → `agentic_chat` → `DialecticAgent.answer`; new `instance-local` site at `src/dialectic/chat.py:130`, target `src/dialectic/core.py:548`. |
| 6 | Trace from `src/dialectic/chat.py:agentic_chat` | **Partial, improved**: reaches `answer` and preparation helpers (51 symbols); LLM façade/reexport boundary at `src/dialectic/core.py:26–30,589–606` remains unknown. |
| 7 | Where is `chat` defined? | **Right ambiguity**: routes at `src/routers/peers.py:257` and `src/routers/workspaces.py:311` plus SDK/example definitions; no arbitrary highlight. |
| 8 | What does `src/deriver/consumer.py:process_item` call? | **Partial**: adds `tracked_db` at `src/deriver/consumer.py:111` → decorated `src/dependencies.py:56–57`; reexports/runtime dispatch still missing, including `process_dream` at consumer line 152. |
| 9 | Trace from `src/routers/peers.py:chat` | **Partial, improved**: 82 symbols / 81 witness edges, including both `agent.answer` at chat.py:130 and `agent.answer_stream` at 214. LLM client still requires source continuation. |
| 10 | How does that route reach `src/llm/api.py#honcho_llm_call@147`? | **Partial**: explicit no-path, not “no flow.” Source continues through the `src.llm` reexport (`src/llm/__init__.py:10`), whose target also has overload declarations at api.py:52,84,116. |
| 11 | What does `DialecticAgent.answer` call? | **Partial**: eight direct helper edges, including `_prepare_query` at core.py:568 and `_select_tools` at 575; unresolved `honcho_llm_call` at 589 retained with its source line. |
| 12 | What does `src/telemetry/logging.py:format_reasoning_inputs_as_markdown` call? | **Right for typed evidence**: parameter annotation at logging.py:60 supports `representation.format_as_markdown` at 85 → `src/utils/representation.py:540`, visibly dotted and labeled `typed`; builtins remain unknown. |
| 13 | What does `tests/bench/runner_common.py:BaseRunner.run_and_summarize` call? | **Partial**: unique `self.metrics_collector` construction at runner_common.py:436 supports calls at 770,777,778 → MetricsCollector methods at `src/telemetry/metrics_collector.py:226,191,281`. Abstract decorated methods at runner_common.py:447,519,524 are declarations, not runtime overrides. |

Disposition: **6 narrow right / 7 partial / 0 wrong**. Among the original eight:
**5 right / 3 partial**, versus the prior 3 right / 5 partial. This is a worker-chosen
source-check set, not an accuracy benchmark or an unaided Eric session.

### How Honcho is built — the chat request, with an explicit evidence boundary

1. HTTP entry: peer chat registration and handler are at `src/routers/peers.py:243–257`;
   its nonstreaming branch calls `agentic_chat` at 404–417. The entry marker does not
   fabricate a framework caller. The streaming branch calls `agentic_chat_stream`
   at 388–398; both branches are static alternatives, not a single execution trace.
2. Preflight and construction: `src/dialectic/chat.py:79–113` validates peers/session
   and reads configuration in `tracked_db`; 116–128 constructs the agent, and 130
   invokes `agent.answer`. That last hop is now drawn as `instance-local`, reaching
   the definition at `src/dialectic/core.py:548`.
3. Query preparation and tools: `answer` obtains telemetry and calls `_prepare_query`
   at `src/dialectic/core.py:567–570`, selects tools at 575, and invokes `honcho_llm_call`
   with tools, messages, budgets and response model at 589–606. The helper edges are
   drawn; the LLM façade call remains an unresolved source site.
4. **Continue by source, not a claimed graph hop:** core.py imports from `src.llm`
   at 26–30; `src/llm/__init__.py:10` reexports api.py's implementation at 147.
   Overload declarations at api.py:52,84,116 and reexports are deliberately not
   resolved by this build. `honcho_llm_call` orchestrates retry/fallback and, when
   tools are used, invokes `execute_tool_loop` at `src/llm/api.py:461–485`.
5. The tool loop calls `honcho_llm_call_inner` in its per-iteration callable at
   `src/llm/tool_loop.py:401`, invokes that callable at 440, and dispatches tool
   results through the supplied `tool_executor` at 582. This is callback-driven
   source behavior, not an invented static connection to an arbitrary tool.
6. One provider attempt: `src/llm/executor.py:365–372` chooses client/backend;
   nonstreaming execution invokes `execute_completion` at 474–484. The request
   builder delegates to `backend.complete` at `src/llm/request_builder.py:172`.
   Provider choice is conditional: e.g. `src/llm/registry.py:234–237` constructs
   `OpenAIBackend`, whose `complete` method can reach the external SDK's
   `self._client.chat.completions.create` at `src/llm/backends/openai.py:188,203,273`
   or `parse` at 214. This is one supported provider branch, not a claim that
   Honcho always uses OpenAI or that any provider was called during this proof.

Message ingestion/persistence and deriver flow remain the separate source route in
the historical walkthrough below, except the decorated deriver call is now visible.

### Verification, bounds and artifacts

- RED-first tier suite: `tiers-red.log` (all four positive categories failed before
  implementation). Extra method-mutation counterexamples reproduced RED before fixing.
- Final full suites: **430 Python / 182 JS tests pass**. Commands remain
  `env -u PYTHONPATH /usr/bin/python3 -m unittest discover -s tests -q` and
  `node --test tests/*.test.cjs`. One prior decorated-target test was updated to the
  explicitly requested behavior, not removed; consultant regression tests are unchanged.
- `.verify.json` build, smoke and four eval recipes pass; lookup remains **39/40**.
  The unchanged 1 MiB whole-packet fallback and legacy file/group parity tests pass.
- Initial v2 import exceeded the unchanged **16 MiB extractor sidecar** limit because
  legacy unresolved records were copied. Fixed by compact references to existing
  sites, not dropping evidence or raising bounds. Initial failure is in `browser.log`.
  The workspace snapshot is a different envelope and can exceed 16 MiB; no limit changed.
- Browser: 13 questions, certain-only toggle for each, exact highlight checks,
  tier dash-style checks, source opening, manual drilldown, zero page errors or
  external browser requests. 41 screenshots. Small paths are readable; 82-node
  traces still require horizontal/vertical scrolling and are not fit-to-screen.
- Final import-form rerun used the existing local cache (~24.761 seconds); the prior
  full extraction/publication run took ~59.951 seconds. These are not comparable to
  warm query-only timing; no new latency/accuracy benchmark claim.
- All four prior consultant recommendations remain **accepted**: scope invalidation,
  execution ownership guards, bounded packet fallback, legacy dispatch/parity.
  New consultant second opinion and generalist/parent integration remain pending.

Artifact root (local, ignored): `artifacts/function-layer/honcho-v2/`.
Key files: `browser-report.json`, `snapshot.json`, `packet-1.json`…`packet-13.json`,
`certain-*.json`, `drawing-*.json`, `question-*.png`, `source-*.png`, `audit.json`,
`tier-audit.json`, `all-new-links.json`, `displayed-new-links.txt`, `certain-parity.log`,
`python-final.log`, `js-final.log`, `gate-results.json` and `source/`.

Reproduce:
```sh
env -u PYTHONPATH /usr/bin/python3 scripts/verify_function_honcho.py artifacts/function-layer/honcho-v2
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_honcho.py artifacts/function-layer/honcho-v2
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_tiers.py artifacts/function-layer/honcho-v2
```

---

## Historical lexical-only build (`62010f6`)

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
