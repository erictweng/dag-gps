# Folder tree data and answers

Card `t_57ec698f`, branch `folder-tree`, base `15ea217`.
Implementation/gated checkpoint: `fd5104c3cfe99b37ae82b9cb06a05d22a0b8fbee`.
Local only; consultant second opinion requested, final approval/integration belongs
 to the generalist. The lanes drill-down and four-level UI are not implemented.

## Contract

New workspace imports add `map.meta.folderTree: 1`. `onboarding.folder_tree`
annotates the original direct groups and returns missing ancestors. Existing
`folder-<sha256(path)[:16]>` IDs, direct file owners and file/layer edges stay
unchanged. Every mapped-source directory prefix remains addressable. Empty
non-source directories are not invented. Root source files retain `(root)`.

Folders carry `parent`, zero-based `depth`, and `compactLabel`. A chain compacts
only while its current directory has no direct files and exactly one child.
This is a presentation hint, not node removal; the existing flat overview still
shows direct-file groups, not new empty ancestor lanes. There is no drill-down UI
or new folder breadcrumb. Existing snapshots without the marker remain flat;
re-import is required to obtain the tree.

Strict snapshot validation rejects missing/file/cyclic/wrong-level parents,
non-integer or inconsistent depths, fake/duplicate/missing real prefixes,
incorrect immediate ownership and invalid compact chains. A direct owner may
also contain subdirectories: “leaf ownership” means the immediate directory,
not necessarily a childless node. The validated cached index adds `children`,
`descendantFiles` and `ancestors` without a second snapshot validation. The
existing agent-bridge exactly-once validation regression still passes.

Folder traversal is multi-source BFS over descendant **files**, using existing
consumer → dependency edges and excluding realtime. Internal files are seed
members, never returned as dependents/dependencies. Witnesses contain only real
file IDs/edges, ending inside the seed for DOWNSTREAM and starting inside it
for UPSTREAM. The folder seed remains selected; internal witness endpoints need
not be highlighted. Strict potential-impact validation accepts only observed
chains ending in a real descendant and rejects internal selections.

PATH between folders returns the shortest directed path between their files.
Overlapping folders can have a zero-hop witness at their shared file. No folder
hops or duplicated parent edges are stored. Mixed folder/file PATH remains
unsupported. LOCATE pages the folder, subfolders and files. Traversal and locate
pages stay within 200 selected nodes; witnesses remain complete. Oversized
single chains return an explicit unsupported result rather than an endless
continuation. Existing edge and byte limits are unchanged.

Exact paths and bare folder names are indexed. Duplicate bare names require
choice (including same-kind folders), with the original operation retained after
choice. `the src` and `src folder` have the same folder-name semantics. On Honcho,
`src` has eight real folder candidates; it is not silently assumed to mean the
root. An article before a full repeated-segment path no longer selects a shorter
ancestor. Cross-kind collision behavior and legacy flat-map scoring are retained.

## Real-source verification

Pins are unchanged:

- Honcho `3922af856d78ec41133916deec4d821fa9c5a92e`: 663 mapped files,
  86 → 106 folders (20 recovered).
- Salesroom `5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce`: 91 mapped files,
  29 → 35 folders (6 recovered).

Both were re-imported using the production browser import form into a scratch
workspace with a copied Git cache and an ephemeral loopback port. Ports
8765/8766/8767 and live workspaces were not touched. The importer/extractor was
not mocked. `scripts/import_graph.py` was not changed; TS alias work remains a
separate card.

`tests/folder_questions.json` supplies seven audited paths per repo; the five
forms in `tests/folder_tree_measure.cjs` produce a separate 35-question list per
repo. Every mapped path is checked against `git ls-tree` at the pinned commit.
Expected descendant sets use path prefixes; external reachability is computed
by an independent BFS over that snapshot's own file edges, not the production
router. Baseline/re-import file edges compare equal. Expectations therefore grow
with the TS alias extractor rather than freezing today's sparse Salesroom graph.

All 70 questions pass target/choice, traversal set, paging and real-file witness
checks. Honcho has 30 direct matches and 5 correct choices; Salesroom 35 direct
matches. All 71 resulting pages pass Python's strict packet validator (Honcho 36,
Salesroom 35). Supplement and per-page evidence:
`artifacts/folder-tree/{honcho,salesroom}/folder-{questions,packets}.json`.

Browser checks, with zero page errors:

- Honcho `where is src`: eight choices; clicking root src returns 174 selected
  folder/file nodes. `what does src use`: choice, then zero outside dependencies
  for root src. `what uses src/components`: honest no-match (that path is absent).
- Salesroom `where is src`: 84 folder/file nodes. `what uses src/components`:
  zero outside consumers in the currently extracted graph. `what does src use`:
  four outside route files: auth/login, accounts, auth/me and events under app/api.
  This is static extracted evidence, not a claim that no runtime consumers exist.

Screenshots: `artifacts/folder-tree/{honcho,salesroom}/import.png`,
`question-{1,2,3}.png`, plus Honcho `question-{1,3}-chosen.png`.
Inspected root-choice/locate and Salesroom dependency screenshots: flat layout
remains intact. Existing evidence sidebar uses opaque folder IDs; ancestor-only
seeds do not acquire a new canvas lane. UI redesign is deliberately deferred.

## Frozen and variation results

The original question files and grader were not edited. All 107 Honcho and 43
Salesroom questions run unchanged: **zero new wrong or overconfident answers**.
Honcho retains one pre-existing dev wrong answer; Salesroom retains zero. All
18/7 held-out matches remain. Honcho's six dev root-src matches become correct
choices among same-name folders (frozen match count 46 → 40). Four Salesroom src
questions change from choices of subgroups to a root-src match; the old
choice-only success labels do not count these as successes. Those expectations
are not silently relabeled.

The unchanged variation generator contributes 93,096 Honcho / 51,650 Salesroom
rows, including 240 negatives each. A separate `folder` axis adds 35 per repo.
One deterministic correctness sweep per version; this is constructed robustness,
not user accuracy. The old PATH grader requires witness endpoints to be folder
IDs, incompatible with the new real-file witness contract. The supplement
retains **both** its raw result and an explicit folder-PATH audit: witness files
must actually belong to the two expected folder paths. No scorer/gate threshold
or frozen row changes.

| Existing grid (including negatives) | Honcho before → after | Salesroom before → after |
|---|---:|---:|
| Correct | 85,080 → 83,576 | 46,359 → 46,368 |
| Correct choice | 4,146 → 5,305 | 1,928 → 2,004 |
| Wrong, folder-PATH-aware | 288 → 72 | 682 → 661 |
| Newly wrong, folder-PATH-aware | 0 | 0 |
| Raw old-grader wrong after | 2,280 | 3,145 |
| Matched negatives | 0 → 0 | 0 → 0 |

The difference between raw/audited wrong is entirely the file-backed folder PATH
representation (2,208 Honcho / 2,484 Salesroom cases). Correct-or-choice is not
universally improved: Honcho falls from 95.843% to 95.472%; Salesroom rises from
93.489% to 93.653%. Duplicate-folder ambiguity and changed aggregate semantics
are visible tradeoffs, not hidden success claims. Folder-axis success rises from
5/35 to 35/35 and 10/35 to 35/35. Full per-axis/raw rows: `variation.json` and
`{repo}/variation-{before,after}.jsonl` under `artifacts/folder-tree/`.

## Size and latency

Same source pins, same question order, warm direct service calls (2 warm-up passes,
10 measured passes over frozen + folder questions). HTTP uses identical 240-row
inputs, a cold request, 20 warmups and 2 measured passes: 480 requests per
repo/version, 1,920 total. Runs are sequential, not concurrent with other gates.
HTTP exercises the real server, worker and packet validator; query-code bindings
are truthfully rebound by the existing performance harness.

| Measure | Honcho before → after | Salesroom before → after |
|---|---:|---:|
| Direct query p95, ms | 0.793 → 0.917 | 0.111 → 0.149 |
| HTTP p95, ms | 1.939 → 2.022 | 0.784 → 1.346 |
| Compact serialized snapshot bytes | 17,394,986 → 17,407,135 | 74,110 → 77,930 |
| Snapshot growth | 0.070% | 5.155% |
| Observed browser import, seconds | 25.880 → 14.094 | 2.520 → 1.580 |

Both direct and HTTP p95 stay within **+1 ms**, checked in code. Direct samples:
1,420 Honcho / 780 Salesroom per version. Import is one observed browser-form
run per version with an existing Git cache, including polling/render overhead;
these are **not** a statistically established importer speedup. Salesroom's
small snapshot exceeds the plan's estimated <1% size growth, which was an estimate,
not an acceptance threshold. No threshold was changed.

## Gates and reproduction

On `fd5104c`: **499 Python / 274 JS, zero skips**, all eight unchanged project
build/test/smoke/release gates and packaging pass. Release scorer worst p95:
**3.595 ms**, unchanged target <10 ms. Receipt:
`artifacts/folder-tree/gates/verification.json`. No performance-gate retry.

```sh
export PLAYWRIGHT_DIR=/Users/aibert/projects/quest-coder/node_modules/playwright
export NODE_PATH=/Users/aibert/projects/quest-coder/node_modules
export AXE_CORE_PATH=/Users/aibert/projects/quest-coder/node_modules/axe-core/axe.min.js
export TMPDIR=/Users/aibert/.hermes/profiles/dag-worker/cache/scratch
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH
/usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
/usr/bin/python3 scripts/release_check.py --output artifacts/folder-tree/gates-reproduced
# Baseline archive and original frozen snapshots must exist as described above.
/usr/bin/python3 tests/folder_tree_browser.py --baseline
/usr/bin/python3 tests/folder_tree_browser.py
node tests/folder_tree_measure.cjs
/usr/bin/python3 tests/folder_tree_packets.py
node tests/folder_tree_variations.cjs
```

For HTTP use `scripts/bench_server_performance.py` with `--code` pointing to this
checkout or `artifacts/folder-tree/base`, corresponding `--snapshot`, identical
`artifacts/folder-tree/REPO/http-input.json`, and a fresh `--out`. Final reports
are `REPO/http-final-{before,after}/summary.json`.

Initial RED tests failed for missing builder/index, absent folder traversal,
same-name choice routing, repeated-path articles and zero-hop witnesses before
implementation. Initial full-suite runs lacked optional fixtures/browser paths
(2 Python / 8 JS skips); final gates have none. Browser harness setup initially
assumed Honcho src was unique, then incorrectly recopied read-only Git pack files;
those harness assumptions were corrected without changing source permissions.
No remaining blocker; consultant advice and generalist approval are next. No
next mini-milestone, push, merge or PR was started.
