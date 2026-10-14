# TypeScript path aliases — t_50e6f922

Implemented locally on `ts-paths`, based on `15ea217`. No push, merge or PR.
Only the extractor, new tests/proof harnesses and reporting docs changed; no
snapshot contracts, grouping code or query engine edits. Consultant second
opinion requested; final approval belongs to the generalist.

## Resolution contract

The importer reads root `tsconfig.json` (preferred) or `jsconfig.json`, including
JSONC comments, trailing commas and a UTF-8 BOM. Relative `extends` chains (and
arrays, in declaration order) are followed without executing code or fetching
packages. Inherited baseUrl keeps its declaring directory; paths replaces the
parent table, with its declaring directory retained when no baseUrl exists.
Exact entries precede patterns; otherwise longest literal prefix wins, with
stable declaration-order ties. A single `*` supports both prefix and suffix.
Targets are tried in order using the existing exact/extension/index candidates.
A matching alias with no file is `UNRESOLVED:<specifier>`: no shorter-rule,
baseUrl or legacy fallback after a match. Relative imports keep their resolution.
Bare baseUrl imports become local only when a file exists, otherwise external.

Compatibility: `@/` still means repository root only when no paths entry matches
(and baseUrl has not resolved it), including repositories with no config.
Targets/configs cannot escape the repository via `..` or symlinks. Unsupported
package/absolute extends, cycles, excessive depth and malformed configs are
recorded in `unsupported`; no network/package lookup. Bad config does not disable
otherwise-existing relative imports or the documented legacy fallback.

This is not a full TypeScript compiler resolver: nested project discovery,
package exports/node_modules, project references and JS-extension-to-TS rewriting
remain unsupported. Root configs only. Type-only imports remain static edges as
before, not runtime claims. Optional alias witness metadata was not added, so
edge and snapshot contracts stay unchanged. Keeping the implementation in
`import_graph.py` also keeps it covered by the existing producer fingerprint.

## RED / GREEN and suites

13 initial fixture tests produced 9 failures + 1 error before implementation;
all 13 passed afterward. Four additional cases cover table replacement,
cycle/package/outside/malformed diagnostics, equal-prefix ties and root config
precedence: 17 alias tests total.

Final full suites: 510 Python tests and 266 JS tests pass, zero skips.
Initial clean-artifact run had 2 Python / 8 JS skips. Installing nothing, supplying
existing pinned snapshots and existing Playwright/axe locations enabled them.
The first browser-enabled attempt failed only because axe's default path pointed
to the old checkout; supplying AXE_CORE_PATH fixed it. All attempts are retained.

Commands (from this worktree):

```sh
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 \
 PLAYWRIGHT_DIR=/Users/aibert/projects/quest-coder/node_modules/playwright \
 NODE_PATH=/Users/aibert/projects/quest-coder/node_modules \
 AXE_CORE_PATH=/Users/aibert/projects/quest-coder/node_modules/axe-core/axe.min.js \
 /usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

## Pinned production import proof

Pins:
- Salesroom `erictweng/salesroom-app@5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce`.
- Honcho `plastic-labs/honcho@3922af856d78ec41133916deec4d821fa9c5a92e`.

`tests/ts_paths_proof.py` uses the existing validated bare acquisition cache,
`build_workspace_snapshot` then `load_publication`: the same inventory/extractor/
publication/snapshot path used by WorkspaceServer imports. No mocked graph,
manual edge injection, network acquisition, or changed source checkout. Fresh
output directories before/after, not cached snapshot hits. Baseline was built
before editing the extractor. Both copies use identical current query code.

| Measurement | Before | After |
|---|---:|---:|
| Salesroom source files | 91 | 91 |
| Import file edges | 46 | 187 |
| All file edges (includes 6 HTTP) | 52 | 193 |
| Layer edges | 9 | 52 |
| Unresolved import entries | 141 | 0 |
| All unresolved diagnostics | 143 | 2 |
| External import entries | 80 | 80 |
| Production import wall time, seconds | 1.409989 | 1.292973 |
| Honcho import file edges | 2,005 | 2,005 |
| Honcho layer edges | 263 | 263 |
| Honcho unresolved diagnostics | 113 | 113 |
| Honcho import wall time, seconds | 21.291218 | 22.381085 |

Times are single fresh-publication end-to-end observations, not a statistically
controlled speedup claim. Both include inventory and Git blob subprocess work;
source objects/OS caches may be warm. No performance threshold was changed.
The two remaining Salesroom diagnostics are existing HTTP references from
`src/lib/crm.ts` to `/api/content` and `/api/content/`, not failed aliases.

Honcho's combined `edges` + `file_edges` arrays are byte-identical after canonical
JSON serialization (including witness fields, not just endpoint sets). SHA-256
for both: `51e160b79a9441c572bf00013bc83b4ad12f208ac56e45383c4006fdfc7b97f7`.
No Salesroom edge was removed. All 141 added import edges were checked against
actual import text and destination Git blobs at the pinned commit.

### Ten cited new edges

Each line is the exact import declaration at the Salesroom pin above. Full import
text for all 141 additions is in `graph-report.json` in the evidence bundle.

| Source and line | Resolved target |
|---|---|
| `src/components/content/VideoPlayer.tsx:9` | `src/lib/events.ts` (type import) |
| `src/components/content/VideoPlayer.tsx:8` | `src/lib/format.ts` |
| `src/components/content/VideoPlayer.tsx:7` | `src/lib/progress.ts` |
| `src/components/content/VideoPlayer.tsx:6` | `src/lib/track.ts` |
| `src/components/content/VideoPlayer.tsx:5` | `src/lib/youtube.ts` |
| `app/(seller)/layout.tsx:2` | `src/components/layout/SellerHeader.tsx` |
| `app/(seller)/layout.tsx:1` | `src/server/guards.ts` |
| `app/(seller)/seller/page.tsx:3` | `src/components/seller/AccountGrid.tsx` |
| `app/(seller)/seller/page.tsx:1` | `src/server/guards.ts` |
| `app/(seller)/seller/page.tsx:2` | `src/server/loaders.ts` |

## Frozen answers and variation benchmark

Frozen files, expected answers and templates were not edited. Existing
`eval_question_parser.cjs` was run on both snapshots against the frozen baseline,
then after against before. Salesroom: 43 cases, same scores before/after:
20/20 dev matches, 5/6 dev choices, 6/6 dev no-matches; 7/7 holdout matches,
0/2 holdout choices, 2/2 holdout no-matches. Zero wrong or overconfident results.
Honcho: all 107 per-case evaluation records identical; its one existing dev wrong
answer remains. No frozen expectation needs revision because of missing edges.

All four changed frozen packets are acceptable uncertain choices, not new matches:
- `sr-021`: `src`
- `sr-022`: `where is the src`
- `sr-023`: `where is the src folder`
- `sr-024`: `where is the SRC directory`

For each, candidates change from src/components/buyer, src/components/modules,
src/lib to src/lib, src/server, src/components/ui. More complete graph connectivity
changes the candidate ranking; no fabricated `src` parent group is introduced.
The existing folder-grouping shortcomings belong to the parallel folder-tree card.

`tests/ts_paths_queries.cjs` reuses the frozen variation generator/classifier,
without running its original hard-coded main-vs-parser comparison (that would
compare query versions rather than extractor versions). Same 51,650 rows on both
snapshots, including 240 negatives. Grid SHA-256:
`1cdb8e19f5eca6e55afd4c6a964b6a5e5feb790681dffcf4db7d307190229291`.
This paired replay is a correctness benchmark, one call per row/version, not the
original three-repeat HTTP performance benchmark. Import timing is above.

| Variation outcome | Before | After |
|---|---:|---:|
| Correct matches | 46,359 | 46,359 |
| Choices containing intended target | 1,928 | 2,036 |
| Wrong matches (existing parser failures) | 682 | 682 |
| No-match | 2,431 | 2,431 |
| Unresolved | 250 | 142 |
| Overconfident negatives | 0 | 0 |

15,820 semantic packets changed (only identity hashes/IDs were ignored):
- 108 newly right: uncertain choices now contain the intended target (e.g. `auth`).
- 15,522 changed but both acceptable: 15,450 correct matches get expanded static
  graph evidence; 72 already-correct choices change their candidate list.
- Zero newly wrong.
- 190 pre-existing wrong matches also get expanded graph evidence. These must NOT
  be called acceptable answers; they are explicitly classified separately as
  `changed; pre-existing wrong`. Their wrong target is unchanged. Example:
  `what does the app/(seller)/seller depend on` still picks `app/(seller)`.
  Fixing those pre-existing parser failures is outside this importer card.

Every changed answer (question, ID, classification, full before/after semantic
packet, and pre-existing-wrong marker) is recorded in `frozen-changes.json` and
`variation-changes.json`, not a handpicked sample. Full outcomes include unchanged
cases. Classification uses the established frozen target/operation rubric; the
141 new static edges are independently source-audited, not justified by scores.

## Reproduction and durable evidence

Local evidence root: `artifacts/ts-paths/`. The compressed bundle
`artifacts/ts-paths/ts-paths-evidence.zip` retains reports, full changed packets,
outcomes, snapshots, timings and suite logs, and is attached to the review card.
Large raw evidence is intentionally not checked into Git.

```sh
CACHE=/Users/aibert/projects/dag-gps-question-parser/artifacts/question-parser/workspace/git-cache
# Baseline must run with 15ea217's extractor; it was run before this edit.
# Use separate code checkouts when reproducing, never overwrite a live extractor.
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 tests/ts_paths_proof.py "$CACHE" after
env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 tests/ts_paths_audit.py "$CACHE"
node tests/ts_paths_queries.cjs
node scripts/eval_question_parser.cjs artifacts/ts-paths/after/salesroom/snapshot.json \
 artifacts/ts-paths/frozen-after.json artifacts/ts-paths/frozen-before.json \
 eval/question_parser_salesroom.json
```

Next: consultant second opinion, then generalist decision. No next mini-milestone
started and no decision is currently required from Eric.
