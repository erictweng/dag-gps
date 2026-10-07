# Handoff — DAG GPS M0: build_map.py

## Final goal (project)
DAG GPS: ask a short question about a codebase and get a Jev-style answer (operation + target + probabilities + confidence) highlighted on an architecture DAG, in one offline HTML page. Read `docs/PLAN.md` first.

## This mini-milestone ONLY
Build `scripts/build_map.py`, which merges the hand-drawn layer map and the auto-extracted import graph into `map.json`. Do not build the scorer, the HTML page, or anything from M1–M3.

## Source of truth
- `docs/PLAN.md` (architecture, M0 smoke)
- `maps/quest-coder/layers.json` (layers with globs, aliases, manual_edges). Do NOT change layer membership; Eric owns the map. If a check fails because of the map, report it; do not "fix" the map.
- `scripts/check_layers.py` (existing glob semantics: `dir/**` = prefix match; other globs = fnmatch with the same number of `/`). Reuse these exact semantics.
- Import extractor: copy `/Users/aibert/.hermes/skills/software-development/codebase-architecture-audit/scripts/import_graph.py` into `scripts/import_graph.py` unchanged (vendored). Usage: `import_graph.py <src_dir> <out.json> [tops...]`. Its output `edges` is a list of `[from, to]` pairs; it also emits `api_calls`, `rpcs`, `sqlfns`, `unresolved`, `cycles`, `fan_in`, `fan_out`. Inspect its real output before relying on any key's shape.
- Target repo: `/Users/aibert/projects/quest-coder` at `origin/main` (currently 71bc83a). Its local `main` checkout is behind; NEVER read the working tree. Export with `git -C <repo> archive <ref> | tar -x -C <tmpdir>`. Do not write into the quest-coder repo.

## CLI
`python3 scripts/build_map.py --repo <path> --ref <git ref> --layers <layers.json> --out <map.json>`
Stdlib only. Exit 0 only if every check passes; non-zero otherwise, after printing the report.

## Steps
1. Snapshot: resolve ref to a short SHA, export to a temp dir (cleaned up afterwards).
2. Extract: run the vendored import_graph.py with tops `app components lib proxy.ts scripts browser-runtime runner` (make tops a `--tops` option with this default).
3. Assign: every source file (`git ls-tree` at ref, extensions ts tsx js mjs py sql) to exactly one layer via globs.
4. Roll up file import edges (+ py edges if present) into layer edges: `{from, to, type: "import", weight, sample: [fromFile, toFile]}`.
5. Typed edges:
   - http: for each file with `fetch('/api/...')` calls, an edge file-layer → api layer (layer containing the matching `app/api/.../route.ts`), with the path as sample.
   - rpc: `.rpc('fn')` caller → layer of the migration that last defines `fn` (if found).
   - manual: copy `manual_edges` from layers.json with their type and `why`.
6. Index: assign `idx` (1-based string, like Jev's `[n]` table) to every layer node, then every file node.
7. Precompute per layer: `upstream` (transitive layers it depends on), `downstream` (transitive dependents), `files`, `top_fan_in` (top 5 files by importers). Ignore `realtime` edges for transitive closure and cycle checks.
8. Tokens per node: lowercase words from label, aliases, desc, and path segments, split on non-alphanumerics, camelCase, and `-`/`_`; dedupe; drop 1-char tokens.
9. File desc: top-of-file block comment or `//` comment only (strip `"use client"`/imports first); fall back to `exports: A, B`; else "".
10. Write `map.json`:
```
meta:   {repo, ref, commit, built_at, counts:{layers, files, edges}}
nodes:  [{idx, id, kind: "layer"|"file", layer, label, desc, path, lines, tokens}]
edges:  [{from, to, type, weight, sample, why?}]
layers: {id: {files[], upstream[], downstream[], top_fan_in[]}}
```
Line counts use `count("\n")`.

## Checks (printed report; any FAIL → non-zero exit)
- unresolved imports == 0
- unmapped files == 0, double-mapped == 0, empty layers == 0
- no layer cycles (ignoring realtime); print the cycle if any
- every manual edge references existing layer ids
- map.json round-trips through json.load and every edge endpoint is a known layer/file id

## Tests
`tests/test_build_map.py` (unittest, stdlib): glob semantics, tokenizer, rollup/weights, cycle detection (incl. realtime ignored), unmapped/double detection, desc extraction — on small in-memory fixtures. Fixtures must mirror the REAL import_graph.json shapes you observed.

## Verification (run before reporting)
- `python3 -m unittest discover -s tests -q`
- the smoke command in `.verify.json`; paste the full printed report into your final message.
- Report: map.json size, node/edge counts per type.

## Allowed files
`scripts/build_map.py`, `scripts/import_graph.py`, `tests/**`, `maps/quest-coder/map.json`, `STATUS.md`, `TASKS.md`. Nothing else.

## Git
Repo-local author is already configured. Commit on branch `m0-build-map` (create it), message "M0: build_map.py + tests + quest-coder map.json". Do not push, do not merge.

## Stop conditions
Stop and report (don't improvise) if: import_graph output shape differs from this brief in a way that changes the design, a check fails because of layers.json, or anything would require editing files outside the allowed list.
