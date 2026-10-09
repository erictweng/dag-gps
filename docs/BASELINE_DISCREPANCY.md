# Baseline non-source drop discrepancy

## Question

Why did 15 non-source drops become 14, and 409 raw import pairs become
364 JS + 44 Python = 408, without changing the frozen 413-link map?

**Answer:** refresh commit `3e811d953490d4fd6a4037f6642cb705af37c1f0`
added a comment-mask filter after regex matching; a match starting inside a
comment consumes the real first import in `lib/public-packs.ts`, then gets
rejected. This loses exactly the forest public-pack JSON pair from both raw
imports and non-source diagnostics. It is a lexical extraction bug, not removal
of an entirely fictional import. The original M1 counts reproduce correctly.

## Method

Investigation for Kanban `t_dad4aeb2`, branch `kanban/baseline-discrepancy`, based
on `99652d1e1f2c31ca8a9eb3602a3fa1d96c495594`. Only this report is changed.
No extractor fix, regression-test change, map regeneration in the repository,
source checkout/fetch/edit, or push is part of this task.

Evidence uses parent-provisioned, read-only Git archive snapshots under
`/Users/aibert/.hermes/cache/scratch/dag-discrepancy/`:

| Label / directory | Full DAG GPS commit | Role |
|---|---|---|
| `a8e85d4` | `a8e85d4193858dce5cbeaa94a059bef46a44b3ee` | M1.1, first 409/15 prose |
| `3e811d9` | `3e811d953490d4fd6a4037f6642cb705af37c1f0` | Refresh, first lexical guard |
| `811fa0d` | `811fa0d617bb56d658d64bf80039dbf45079a366` | V1.0 baseline reporting discrepancy |
| `99652d1` | `99652d1e1f2c31ca8a9eb3602a3fa1d96c495594` | Task's current implementation |

`quest/` is the archive of quest-coder
`749d8b5de490cc2e6a0c98c713fab3ab856da799`. Historical extractor/build-map
code is captured in each snapshot's `scripts/`. Each extractor runs against
this same archive, and each builder internally reads the same immutable Git
ref. All explicit outputs go to `out/` in scratch.

Counts mean raw `edges` plus `pyedges` entries, before file-edge deduplication.
Drops are raw pairs with an endpoint absent from map file nodes. All dropped
pairs here are unique imports to CSS/JSON, so diagnostic-entry count and unique
pair count agree. We compare pair multisets, not just totals, and compare built
`nodes`, `edges`, `file_edges`, and `layers` against each revision's shipped map.

### Evidence: first appearances and configuration

- `git log -S'409'` first introduces 409 in M1.1 `STATUS.md:52-53`;
  `STATUS.md:32-36` and `TASKS.md:29-30` introduce the 15-drop claim at that same
  `a8e85d4` commit. No earlier occurrence was returned in the searched history.
- M1 `.verify.json:10` requests quest `origin/main`; `STATUS.md:19-20` records
  that it resolved to `749d8b5`. The M1 shipped map and our pinned rerun agree.
  `scripts/build_map.py:26,590` supply default tops
  `app components lib proxy.ts scripts browser-runtime runner`.
- Refresh `docs/REFRESH_REPORT.md:79-84` explicitly pins the full same SHA and
  these same tops. Lines 95-97 say 364 JS + 44 Python but still say 15 targets.
- V1.0 `docs/V1_BASELINE_REPORT.md:40-46,56-64` reports 14 drops and 364+44,
  retaining the historical disagreement rather than explaining it.
- `git diff a8e85d4 99652d1 -- maps/quest-coder/layers.json` is empty.
  Source, layer spec, and explicit tops are held constant in the reruns.

## Exact commands run

Commands below ran from `/Users/aibert/projects/dag-gps-kanban-discrepancy`.
The parent supplied archives; this successful attempt did not extract them.
Read-only `read_file`/`search_files` tool calls also inspected the cited source,
reports, tests, AGENTS, workflow, plan and verification recipes.

```sh
git status --short
git branch --show-current
git log -S'409' --format='%H %s' -p -- STATUS.md TASKS.md docs .hsub
git log -G'15.*(non-source|target|drop)' --format='%H %s' -p -- STATUS.md TASKS.md docs/REFRESH_REPORT.md
git log -S'code_mask' --format='%H %s' -- scripts/import_graph.py
git diff a8e85d4 3e811d9 -- scripts/import_graph.py
git diff a8e85d4 99652d1 -- maps/quest-coder/layers.json
git rev-parse 99652d1 origin/main
git show a8e85d4:.verify.json

for rev in a8e85d4 3e811d9 811fa0d 99652d1; do
  python3 /Users/aibert/.hermes/cache/scratch/dag-discrepancy/$rev/scripts/import_graph.py /Users/aibert/.hermes/cache/scratch/dag-discrepancy/quest /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/$rev-graph.json app components lib proxy.ts scripts browser-runtime runner
  python3 /Users/aibert/.hermes/cache/scratch/dag-discrepancy/$rev/scripts/build_map.py --repo /Users/aibert/projects/quest-coder --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 --layers /Users/aibert/.hermes/cache/scratch/dag-discrepancy/$rev/maps/quest-coder/layers.json --tops app components lib proxy.ts scripts browser-runtime runner --out /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/$rev-map.json
done
python3 /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/compare.py
python3 /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/compare.py > /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/comparison.txt
python3 scripts/check_snapshot.py maps/quest-coder/map.json /Users/aibert/.hermes/cache/scratch/dag-discrepancy/out/99652d1-map.json
```

`compare.py` is a local read-only analysis script, not shipped code. Its count
algorithm is `pairs = list(map(tuple, graph['edges'] + graph['pyedges']))`;
`known = {n['id'] for n in map['nodes'] if n['kind'] == 'file'}`;
`drops = [p for p in pairs if p[0] not in known or p[1] not in known]`.
It prints sorted drop lists, subtracts adjacent `collections.Counter(pairs)`
values in both directions, and uses Python equality on the four graph fields.
For the lexical probe it copies `3e811d9/scripts/import_graph.py:35,38-48`
verbatim (the `imp` regex and `code_mask` function), reads
`quest/lib/public-packs.ts`, and prints each `imp.finditer(text)` match's start
and end line, `mask[m.start()]`, and `repr(m.group(0))`. Thus the probe can be
reconstructed directly from the pinned source without dynamic execution.

### Approval behavior

Earlier attempts stopped on three security approval refusals, preserved with
exact commands and refusal text in this card's comments:

1. `execute_code` arbitrary Python was forbidden in unattended single-query mode.
2. The `git archive | tar -x -C ...` provisioning command was rejected for
   extraction into a sensitive path. The parent subsequently provisioned archives.
3. A chained inline `python3 -c` comparison/AST/`exec` probe was rejected for
   suspicious inline execution and unresolved nested executable analysis.

The parent explicitly authorized plain file-based analysis instead; no approval
mode was changed. This attempt had no security approval refusals. One initial
`write_file` call encountered the ordinary stale-write guard because a prior
attempt had already created `compare.py`; it changed nothing. Reading and using
that existing script resolved it without overwriting it.

## Old vs new counts and drop lists

### Evidence: fresh execution

| Extractor/builder | JS raw | Python raw | Total raw | Drops | Duplicate retained pairs | Unique import links | All file links |
|---|---:|---:|---:|---:|---:|---:|---:|
| M1 `a8e85d4` | 365 | 44 | 409 | 15 | 5 | 389 | 413 |
| Refresh `3e811d9` | 364 | 44 | 408 | 14 | 5 | 389 | 413 |
| Baseline `811fa0d` | 364 | 44 | 408 | 14 | 5 | 389 | 413 |
| Current `99652d1` | 364 | 46 | 410 | 14 | 5 | 391 | 415 |

All four builders print `10/10 checks passed`; all extractors print
`182 nodes`, `0 cycles`, `0 unresolved`. All builds contain 18 layers, 272 files
and 52 layer edges. Each built map's four graph fields equals its own shipped
map. Refresh and V1.0 `edges`, `file_edges`, and `layers` equal M1's as well.

Important correction to the question's temporal wording: 364+44 is the V1.0
baseline, not current `99652d1`. Current Python extraction adds exactly
`runner/__init__.py -> runner/quest_runner.py` and
`runner/tests/test_trusted_boundary.py -> runner/quest_runner.py` after baseline,
with no additional removed pair. This is separate from the 409-to-408 issue.

Full non-source list (all are `import`; yes means present in the drop list):

| Importer | Target | M1 | Refresh / V1.0 / current |
|---|---|---|---|
| `app/layout.tsx` | `app/globals.css` | yes | yes |
| `lib/public-packs.ts` | `content/public/forest-of-patience-climbing-stairs.json` | yes | **no** |
| `lib/public-packs.ts` | `content/public/spun-vault-binary-search.json` | yes | yes |
| `lib/public-packs.ts` | `content/public/tutorial-island-masquerade.json` | yes | yes |
| `lib/public-packs.ts` | `content/public/tutorial-island-numerology-goblin.json` | yes | yes |
| `lib/public-packs.ts` | `content/public/tutorial-island-picky-dragon.json` | yes | yes |
| `lib/public-packs.ts` | `content/public/tutorial-island-royal-joust.json` | yes | yes |
| `lib/public-packs.ts` | `content/public/tutorial-island-wobblesworth.json` | yes | yes |
| `lib/quests.ts` | `content/server/forest-of-patience-climbing-stairs.json` | yes | yes |
| `lib/quests.ts` | `content/server/spun-vault-binary-search.json` | yes | yes |
| `lib/quests.ts` | `content/server/tutorial-island-masquerade.json` | yes | yes |
| `lib/quests.ts` | `content/server/tutorial-island-numerology-goblin.json` | yes | yes |
| `lib/quests.ts` | `content/server/tutorial-island-picky-dragon.json` | yes | yes |
| `lib/quests.ts` | `content/server/tutorial-island-royal-joust.json` | yes | yes |
| `lib/quests.ts` | `content/server/tutorial-island-wobblesworth.json` | yes | yes |

The complete raw multiset delta M1 → refresh is:

```text
RAW REMOVED [('lib/public-packs.ts', 'content/public/forest-of-patience-climbing-stairs.json')] RAW ADDED []
```

Refresh → V1.0 prints `RAW REMOVED [] RAW ADDED []`.
The builder's console samples only part of the drop list; the table above uses
the complete raw graph, not the truncated console sample.

## Cause

### Evidence

At quest SHA `749d8b5de490cc2e6a0c98c713fab3ab856da799`,
`lib/public-packs.ts:1-5` is a block comment; line 3 contains `one import here`.
Line 6 is a real `import forestOfPatience from
"../content/public/forest-of-patience-climbing-stairs.json";`.

M1 `scripts/import_graph.py:34,41-43` runs its multiline-capable import regex
without a lexical mask. Refresh keeps that regex at line 35 but introduces
`code_mask` at lines 38-48 and filters matches by `mask[m.start()]` at line 58.
`git log -S'code_mask'` identifies exactly `3e811d9` as its introduction.

The probe prints this first match:

```text
lines 3 6 mask False match 'import here, one in lib/quests.ts,\n * one entry in lib/run-contract.ts and runner/private_pack.py (tests/unit/pack-registry.test.ts checks them).\n */\nimport forestOfPatience from "../content/public/forest-of-patience-climbing-stairs.json"'
```

Subsequent JSON import matches begin on lines 7, 9, 10, 11, 12, 13 and have
`mask True`. Current `99652d1/scripts/import_graph.py:36,39-49,59` still applies
this post-match start-mask check; its newer regex does not prevent this case.

### Inference grounded in that evidence

The original regex reaches across the comment terminator and captures the
real line-6 target. Refresh rejects the entire match because its start is in
the comment. Non-overlapping `finditer` has already consumed line 6 and does
not retry there. The lost pair is real static import evidence, even though its
old regex match began at the wrong token. Therefore:

- **Extractor change is the cause** of both numerical deltas.
- **409 is not an arithmetic typo:** the old extractor really emits 365+44.
- **Different source/layers/tops are not needed to explain the change:** the
  controlled same-input runs reproduce it, and the recorded configurations agree.
- **No drop-definition change is needed:** exactly one raw pair disappears and
  the same endpoint-based classification produces both lists. M1
  `build_map.py:167-205` drops unknown endpoints before deduping retained triples.
- **Refresh prose is stale/inconsistent:** its 364+44 claim reproduces, but its
  15-drop claim does not reproduce at that revision with its documented inputs.
  The historical evidence does not establish why the author retained that number.

## Impact on shipped maps/tests

### Evidence

The removed target has no map file node, so both old and new pipelines exclude
it from drawn file links. Both have five duplicate retained raw pairs, leaving
389 unique import links plus 14 HTTP and 10 RPC = 413 through V1.0. The current
map has 391 import links plus those same HTTP/RPC totals = 415, due to the two
separately audited Python additions, not the JSON discrepancy.

The relevant current `.verify.json` smoke components were exercised as pinned
builds redirected to authorized scratch plus strict snapshot validation:

```text
PASS pinned map parity: 749d8b5, 290 nodes, 52 layer edges, 415 file edges; only ref/time ignored
```

`tests/test_snapshot.py:15-33` checks strict parity semantics, not raw-import
counts. `tests/test_extraction_trust.py:125-133` explicitly requires the two
new Python edges and 415 links. Searching current tests for 409, 408, 413, 389,
415 and non-source wording found the 415 assertion, not a historical 15/409
hard-coded test requirement. Parity and the ten builder checks can pass while
missing non-source import evidence; neither proves extractor completeness.

### Inference / remaining risk

The 15→14 change does not alter the shipped navigable map, layer graph or
routes at the refresh/baseline boundary, but underreports the non-source
findings by one real JSON import. Current diagnostics retain this blind spot.
The same regex/filter interaction could hide source imports in other files;
this investigation establishes this pinned case, not the prevalence of that
class of bug. Fixing and regression-testing it needs a separate authorized
implementation task. No code/test fix is included here.

Full UI/build/test recipes were not run for this docs-only investigation;
they write outside the card's scratch-only output scope and would not prove
the historical cause. No new feature, calibrated accuracy, runtime execution,
or release-readiness claim is made.

### Build update / handoff

[BUILD] DAG GPS — dag-engine

- Milestone: baseline discrepancy investigation; one documentation mini-task.
- Status: verified investigation, parent review required.
- Output: precise pair, lexical mechanism, historical/current counts and map impact.
- Verification: four pinned extractor/build reruns, each 10/10; multiset/drop-list
  comparison and graph-field parity; strict current snapshot check passed.
- Next: parent independently reviews this report; no next milestone launched.

This update is embedded here rather than adding a second file or modifying
STATUS/TASKS, in accordance with this card's one-new-file constraint.
