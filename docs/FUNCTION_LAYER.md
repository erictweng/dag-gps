# Python function layer — current build

Local `function-layer`; fixes `0641dd6`, card `t_0751cc8d`. Main through PR #7 has
lexical function evidence; this branch adds tiers, static re-exports and subsequent
conservative fixes. Consultant second opinion pending; no push/PR/main integration.

## Supported evidence

Python stdlib AST extracts functions, async functions, classes, methods and nested
names with file, qualified name and inclusive definition range. It never imports
or runs target code. Syntax support is limited to the running parser (Python 3.9
in this proof); failed files retain file nodes and explicit diagnostics.

| Tier | Evidence | Drawing |
|---|---|---|
| `resolved` | Unique lexical definition, supported `self.method`, observed repo import, static package re-export or following overload implementation | Solid |
| `instance-local` | Unique direct `x = RepoClass(...)`, or stable `self.attr` initialization, with supported method lookup | Long dash |
| `typed` | Repo-class parameter annotation in its enclosing namespace; direct local annotation in body scope | Dots |
| `through-decorator` | Identified decorated definition, not the behavior of its wrapper | Dash-dot |
| `unresolved` | No supported unique target; no guessed edge | Listed site only |

Tiers are evidence categories, not probabilities. Every witness reports its weakest
tier; multiple call sites retain individual tiers. Own methods can be identified
with external bases; inherited lookup requires a complete in-repo C3 MRO. Private
names abstain (protocol dunders remain supported). A class call identifies its
class definition, not automatic constructor/body traversal. Route/task decorators
supply bounded syntactic entry metadata, never invented framework caller edges.

Named imports follow unique in-repo `__init__.py` direct `from` imports, including
aliases. Every hop requires an observed file-import pair; endpoints must be direct
unconditional definitions. Ordered site `reexports` carry source ranges, local name
and target path/name, validated through packets and clickable source witnesses.
Cycles, shadowing, wildcard exports, conditional/try imports, dynamic `__all__`,
arbitrary module forwarding and runtime `getattr` abstain. Chains are bounded to
64 hops. Literal list/tuple `__all__` is not interpreted and does not block named imports.

Uniquely bound stdlib `typing.overload` imports/aliases mark declarations. Only an
unconditional group with one implementation **after every declaration** coalesces.
Reversed order, conditional definitions, duplicate implementations and declaration-only
names abstain. Known writes/deletes through imported typing module aliases invalidate
markers file-wide; rebinding invalidates unique lookup. Actual decorated implementations
retain the weaker tier. Honcho has 19 recognized declarations; none is a call target.

### Latest consultant dispositions

1. **Accepted:** a method annotation cannot select a future class binding. Lookup
   conservatively abstains when a required binding is not established before the
   annotation, instead of reconstructing the partially executed class namespace.
   Existing earlier class-local and global annotation controls remain supported.
   String/postponed annotations receive the same guard, not emulated evaluation.
2. **Accepted:** overload coalescing now enforces order/unconditional implementation
   and visible marker mutation/rebinding rules above. The consultant's reversed-order
   and mutated-marker false targets reproduce RED and now abstain.
3. **Accepted:** verification uses explicit `--suite v1|v2|v3` (default `v3`), not
   the output basename. Tier audit accepts `--suite v2|v3`, default `v3`.

## Queries, UI and agent bridge

Deterministic LOCATE, direct CALLERS/CALLEES, shortest-path FLOW and forward TRACE
use case-sensitive names; `path:qualname` or `path#qualname@line` disambiguates.
Duplicate names require choice. No path means no supported static path, not no
runtime flow. Real cycles remain; large traces use whole-chain pagination/scrolling.
Group → file → definition drill-down and selected function lanes open hash-verified,
revision-bound source. Clear returns to the group overview.

“Certain links only” (`certainOnly: true` in requests/agent args) removes all three
inferred tiers and restores unresolved ordering. It retains new static re-export
links: it is not a frozen v1 extractor. Thirteen full packets match the unchanged
legacy query engine over the current inference-disabled graph, apart from the mode
marker; unchanged synthetic/file/group parity remains tested.

The additive `dag-gps-symbols/v1` extension retains counts, decorators, site tiers
and compact `certainAdditions` references. Existing file/group arrays and dispatch
remain unchanged. Oversized symbol packets return bounded `unsupported`, with no
highlights, rather than dropping evidence; limits remain 1 MiB per serialized packet
and 16 MiB for the extractor sidecar. No bounds raised.

`scripts/workspace_cli.py --workspace <workspace>` accepts JSON on stdin. Tools:
`find_symbols`, `get_callers`, `get_callees`, with `args.symbol` and optional
`certainOnly`, continuation/choice. Existing `find_nodes`/`get_context` share function
queries; `get_source` keeps literal path/start/end. Context returns the first selected
range per file under its budgets, not all evidence or an automatic provider upload.

## Limits

Direct single-assignment receiver evidence only: branches/loops/try/with assignments,
rebinding/deletion, captures, repeated attribute writes, known method mutations,
optional/union/generic annotations and unsupported factories remain unknown.
Class-body/lambda/generator sites cannot compose into invocation-flow chains.
Wildcard scopes invalidate lookup; defaults/decorators/bases are collected outside
the function body. No full Python execution or closure/dataflow model is claimed.

Receiver escapes are not fully tracked: container storage, passing/returning a value
or mutating through an alias can invalidate runtime behavior without removing an
inferred edge. Annotations may be false; subclass overrides, monkeypatches, DI,
descriptors, wrappers, dynamic callbacks and external SDK dispatch remain boundaries.
Abstract method links identify declarations, not concrete overrides. Proposed grouping
and extraction remain partial; reviewed architecture publication has separate gates.

## Pinned Honcho proof

Source: `https://github.com/plastic-labs/honcho`, commit
`3922af856d78ec41133916deec4d821fa9c5a92e`. All source citations below refer to this pin.
Real Chromium import form, production WorkspaceServer/publication/query worker,
highlighted IDs and source endpoints; no Honcho/provider code executed.

| Measurement | Current |
|---|---:|
| Inventory / mapped files / Python inputs | 1,162 / 663 / 562 |
| Definitions / entry points / parser diagnostics | 7,670 / 116 / 2 |
| Resolved sites / edges | 8,705 / 7,227 |
| Instance-local sites / edges | 465 / 398 |
| Typed sites / edges | 388 / 227 |
| Through-decorator sites / edges | 1,591 / 1,327 |
| Unresolved sites | 33,799 |
| Browser questions / certain-only parity packets | 13 / 13 |

The **entire symbol graph equals the previous v3 graph**: zero link, site, metadata
or count changes from these fixes. Regression counterexamples change, not Honcho.
Fresh audits corroborate all 734 re-export-era added edges / 885 sites against the
pinned v2 baseline, with 562 source hashes and 152 static export bindings. The broader
post-v1 structural audit covers 2,673 edges / 3,313 sites; 80 edges / 91 sites are
displayed across these answers. These remain source corroboration, not runtime accuracy.

### Thirteen source-checked questions

| # | Question | Current result and pinned source |
|---|---|---|
| 1 | Where is `create_messages_for_session`? | **Right**: `src/routers/messages.py:113–184`; entry metadata retained. |
| 2 | What does CRUD `create_messages` call? | **Partial**: six edges; includes `schemas.SessionPeerConfig` at `src/crud/message.py:419` and `SessionCreate` at 422 through the schema initializer; runtime DB/embedding calls remain unknown. |
| 3 | What calls `process_representation_tasks_batch`? | **Right for observed callers**: production caller at `src/deriver/consumer.py:236–247` and eleven test callers; no scheduler caller invented. |
| 4 | How does peer chat reach `DialecticAgent`? | **Right**: route at `src/routers/peers.py:404–417` → construction at `src/dialectic/chat.py:116–128`. |
| 5 | How does peer chat reach `DialecticAgent.answer`? | **Right**: three symbols; `agent.answer` at `src/dialectic/chat.py:130` is `instance-local`. |
| 6 | Trace from `agentic_chat` | **Partial**: 181 symbols / 180 witness edges, including the LLM façade/tool loop; callbacks/provider dispatch remain incomplete. |
| 7 | Where is `chat`? | **Right ambiguity**: peer/workspace routes and SDK/examples remain choices, not an arbitrary selection. |
| 8 | What does deriver `process_item` call? | **Partial**: 15 direct edges; `tracked_db` at `src/deriver/consumer.py:111`; `process_dream` at 152 remains unresolved (non-initializer forwarding). |
| 9 | Trace from peer chat | **Partial**: first page has 200 symbols / 199 witness edges and continuation, not the whole graph; streaming and nonstreaming alternatives coexist. |
| 10 | How does peer chat reach `honcho_llm_call@147`? | **Right for this endpoint**: route → `agentic_chat` → `DialecticAgent.answer` → `src/llm/api.py#honcho_llm_call@147`; final call at `src/dialectic/core.py:589–606`, re-export at `src/llm/__init__.py:10`; path's weakest tier is `instance-local`. |
| 11 | What does `DialecticAgent.answer` call? | **Partial**: nine helper edges, including the LLM implementation, not its three overload declarations; runtime methods remain unknown. |
| 12 | What does `format_reasoning_inputs_as_markdown` call? | **Right for typed evidence**: annotation at `src/telemetry/logging.py:60`, call at 85 → `src/utils/representation.py:540`. |
| 13 | What does `BaseRunner.run_and_summarize` call? | **Partial**: seven edges, three stored MetricsCollector methods and abstract declaration evidence, not concrete override inference. |

Seven narrow right / six partial / zero wrong in this worker-selected set. This is
not an accuracy benchmark or Eric's unaided acceptance; entire-graph equality preserves
the prior source judgments. Wide traces still scroll; long graph labels truncate
while the sidebar keeps full IDs.

## How Honcho is built — chat request through response

1. **HTTP/preflight.** Peer chat registration is at `src/routers/peers.py:243–257`.
   Authorization/scope handling precedes `agentic_chat` at 404–417 (streaming:
   388–398). `src/dialectic/chat.py:79–113` reads peers/session/config in a short DB
   context; 116–128 constructs `DialecticAgent`; 130 calls `answer`. This is static
   instance-local evidence, not automatic constructor/body execution.
2. **Prepare query/tools.** `src/dialectic/core.py:567–575` prepares context and
   tools, then passes messages, executor, budgets, response model and telemetry to
   `honcho_llm_call` at 589–606. The import at 26–30 follows
   `src/llm/__init__.py:10` to `src/llm/api.py:147`; declarations at 52, 84 and 116
   are not targets. The UI proof clicks both initializer and implementation source.
3. **Attempts/tool use.** `src/llm/api.py:461–485` calls decorated `execute_tool_loop`
   (`src/llm/tool_loop.py:292–293`), a `through-decorator` edge. Its per-iteration
   callback calls `honcho_llm_call_inner` at tool_loop.py:401–423 → executor.py:333.
   Retry-wrapping/assignment at tool_loop.py:425–438 and `call_func()` at 440 remain
   **source continuation**, not an invented callback edge. Tool dispatch at 582 and
   the toolless wrapped callable at api.py:425/427 are dynamic boundaries.
4. **Provider attempt.** `src/llm/executor.py:365–372` selects client/backend and
   474–484 calls `execute_completion`; `src/llm/request_builder.py:172` delegates to
   `backend.complete`. Choice remains source-dependent: `src/llm/registry.py:234–237`
   constructs OpenAIBackend for one branch. External SDK calls occur at
   `src/llm/backends/openai.py:188,203,273` (`create`) or 214 (`parse`); they are not
   in-repo targets and no provider was invoked by the proof.
5. **Return/record.** executor.py:485 converts the completion. The loop accumulates
   usage at tool_loop.py:442–445 and checks for another step at 452. The agent
   serializes content, records evidence/metrics and returns at
   `src/dialectic/core.py:613–639`; `src/routers/peers.py:426–429` builds the response.
   These are static alternatives, not a claim every branch executes on one request.

## Verification and how to run

455 Python / 182 JS tests pass; `.verify.json` build/smoke/four evals pass. Lookup
retains 39/40, not perfection. RED-first: eight new methods, 12 failing subcases;
focused GREEN: 51 tests. No existing tests removed/weakened. Browser dependencies
were absent on the first full run; installed documented versions locally, then reran.
Fresh proof at an arbitrary output basename runs all 13 questions, both modes,
three CLI tools and 44 screenshots with zero page errors/external browser requests.
Import-to-ready was 68.021 seconds, not a warm-query latency measurement.
Separate release/performance/packaging and human acceptance were not rerun here.

```sh
env -u PYTHONPATH /usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
OUT=artifacts/function-layer/binding-fixes/honcho-proof
env -u PYTHONPATH /usr/bin/python3 scripts/verify_function_honcho.py "$OUT" --suite v3
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_honcho.py "$OUT"
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_tiers.py "$OUT" --suite v3
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_reexports.py "$OUT"
```

Playwright/Chromium and axe-core setup: [V1_RELEASE.md](V1_RELEASE.md). Configure
`PLAYWRIGHT_DIR`, `AXE_CORE_PATH` and `NODE_PATH` for a non-default QA installation.
The proof server is loopback-only and shuts down afterward; capability tokens are
not stored in reports. Reruns overwrite browser packets/screenshots at the chosen path.
Local/ignored evidence: `artifacts/function-layer/binding-fixes/` contains RED/GREEN,
full tests, `gate-results.json`, `delta.json` and `doc-citations.txt`; `honcho-proof/`
contains browser report, snapshot, packets, source copies and source/parity audits.

## History

- `0989f1f`, `62010f6`: Python function layer and first review fixes (`t_58cccce0`, `t_4977fa02`); PR #7.
- `b97d6d6`: confidence tiers (`t_39e90fae`).
- `06f7ca6`, `915265e`: main prerequisite merge, re-exports and prior review fixes (`t_d663095e`).
- `0641dd6`: binding-order/overload fixes and explicit verification suite (`t_0751cc8d`).

Older narratives remain in git and existing reports, not duplicated here. Next:
unresolved-call classification (`t_21987d99`); in-app Explain awaits Eric's decision.
