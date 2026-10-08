# Supported sources — v1 contract, current implementation

Support is a bounded **static source map**, not a runtime call graph, package manager,
compiler, coverage tool or universal-language promise. This matrix is grounded in
`scripts/import_graph.py`, `scripts/build_map.py`, `scripts/build_project.py` and the
named tests below at baseline `4898578`. V1.0 changes no extraction behavior.

## Current matrix

| Input / construct | Current behavior | Limits and evidence |
|---|---|---|
| Git source and assignment inventory | Pinned `git archive`; included `.ts/.tsx/.js/.jsx/.mjs/.cjs/.py/.sql` files become candidate source nodes; every included source file must have one layer | `build_map.source_files/included/build`; `RefreshTests.test_mutable_worktree_not_extracted`, `test_vendor_generated_and_node_modules_excluded`, unmapped/duplicate tests. Directory exclusions, not universal generated-file detection |
| TS/JS static import/export-from, side-effect import | Lexical string-spec extraction; relative specs and `@/` resolve existing file, appended JS/TS extension, or directory index | `import_graph.py:14–35,50–67`. `@/` means repo root, **not** reading tsconfig paths. Bare packages/other aliases external; no compiler resolution, Node package exports, complete ESM semantics or symbol graph |
| Literal `import('path')` / `require('path')`, CommonJS/UMD | Literal imports and UMD requires can create static links; comments/quoted fixtures masked for import recognition | `RefreshTests.test_commonjs_umd_and_python_script_imports_are_real`; real self `.cjs` graph. Function shadowing and code execution not modeled |
| Computed JS import/require | Nonliteral patterns are reported unsupported, not evaluated | `RefreshTests.test_unsupported_constructs_reported_not_guessed`; quest Pyodide URL and self Playwright requires reproduced. Regex literals/template interpolation not modeled; findings are not exhaustive |
| JS lexical safety | Lightweight comment/string masking for imports | Not a full parser. Regex-literal syntax can confuse lexical scans; template bodies/interpolation are masked rather than parsed. No promise for all TS syntax; no new parser fixtures claimed in V1.0 |
| Python absolute imports, local scripts, multiline imports | AST scan of included Python files; exact module or same-directory match, then unique suffix heuristic; `as` binding does not change module name | `import_graph.py:82–128`; `RefreshTests.test_commonjs_umd_and_python_script_imports_are_real`. This is not actual sys.path/importlib resolution. `from module import names` selects first resolved candidate group, not complete symbol-to-submodule modeling |
| Ambiguous local Python names | Records unresolved ambiguity; refresh rejects rather than guesses | `RefreshTests.test_ambiguous_python_local_import_rejects_without_guessing` |
| Relative Python imports (`from .…`) | Reported unsupported; omitted edges | `RefreshTests.test_unsupported_constructs_reported_not_guessed`, real `runner/__init__.py`. Planned V1.2 regression-first improvement, **not** implemented |
| Dynamic Python loading | Direct `__import__` calls flagged unsupported; not executed | `import_graph.py:97–98`; importlib/dynamic loader detection is not comprehensive. Unmatched bare imports external/unknown, not proof of installed dependencies. Python syntax parse errors produce unsupported + unresolved findings |
| CSS/JSON/assets/non-code | Not source nodes; resolved targets lacking nodes reported and dropped from file edges | `build_map.file_level_edges` and `diagnostics.non_source_connections`; real baseline quest 14 drops, self 11. Imported `.json` may resolve as an existing file, but receives no graph node |
| Literal HTTP `/api/…` references | Heuristic string pattern matched to route handler; unresolved HTTP references reported | `import_graph.py:36,68–70`, `build_map` HTTP resolution, real `/api/private-pack` miss. This regex scans text, not validated fetch-call execution, and does not share import masking. API-source files are excluded from caller capture; no dynamic URL/general backend tracing |
| RPC and migration SQL | Literal `.rpc('name')` matched to detected migration `create function`; SQL files included in inventory, migration function definitions scanned | `import_graph.py:37,71–80`; builder edge tests and pinned map RPC evidence. Not a SQL parser/general SQL dependency extractor or proof migrations deployed |
| Manual layer / tour boundaries | Reviewed layer links; independently source-cited typed tour links with exact repo/commit/range validation | `tests/test_tours.py`, `tests/tours.test.cjs`, `smoke_tours.cjs`. Source evidence is separate from import graph and observed execution; no automatic tours |
| Other languages / unsupported config aliases | No promised extraction support | A successful build cannot establish runtime completeness. Missing links never imply no consumers, dead code or no tests |

Named tests are members of `tests/test_refresh.py::RefreshTests` unless otherwise
specified. For builder shape/edge/coverage tests see `tests/test_build_map.py`; full
pinned parity is `tests/test_snapshot.py` and `scripts/check_snapshot.py`.
Source inspection supports implementation limits where no dedicated test exists;
we do **not** claim unbuilt trust/parser tests already exist.

## Scope, identity and failure behavior

Generic `build_project.py` discovery uses the included Git source inventory as JS/TS
extraction inputs; explicit `--tops` restricts that scan. Python and migration SQL
still scan repository-wide. Assignment coverage checks all included source inventory,
so **inventory count and extracted-node count can differ**. Quest's baseline has
272 assigned files but 182 extractor nodes. Zero unresolved imports only describes
this chosen extraction scope, not all dependencies or files.

Preserve quest's explicit tops `app components lib proxy.ts scripts browser-runtime runner`
and immutable snapshot `749d8b5de490cc2e6a0c98c713fab3ab856da799`. Prior all-source
trial exposed unresolved generated `.next` references; do not silently broaden scope,
remap layers or refresh latest to make parity pass. Self demo is deliberately pinned
to `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93`, without tours.

Unresolved local references, invalid assignment and layer cycles reject publication.
File cycles are represented by extraction; current layer validation ignores realtime
but rejects dependency layer cycles. Never remove true edges merely to make a DAG.
Publish validates staged artifacts before per-file replacement and rolls back caught
errors (`test_promotion_error_rolls_back_bytes`); hard kill/power loss and concurrent
readers are not a multi-file transaction. Use one writer. No live watcher, external
browser service, automatic cross-tab sync or runtime execution tracing is promised.

Build/UI evidence and count discrepancy with historical reports:
[V1_BASELINE_REPORT.md](V1_BASELINE_REPORT.md). Future trust/onboarding gates:
[V1_ACCEPTANCE.md](V1_ACCEPTANCE.md); fixture provenance: [V1_FIXTURES.json](V1_FIXTURES.json).
