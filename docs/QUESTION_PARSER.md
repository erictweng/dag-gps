# Question parser — rules → synonyms → concept candidates

Card `t_3b508d4b`, local `question-parser` branch. No models, embeddings, provider
calls, push, merge or PR. This is deterministic retrieval, not general language
understanding. Source-only imports never run either repository's code.

## Pipeline

```text
question
  │ shared case/punctuation/contraction normalization
  │ operation parsing + kind hint; remove explicit filler from content terms
  ├─ exact Python name / qualified symbol (case-folded collisions require choice)
  ├─ literal path / basename / stem; architecture names and confirmed aliases
  ├─ no lexical evidence? bounded bidirectional synonym alternatives (lower scores)
  └─ still no match, LOCATE, not an absent literal filename?
       BM25 over bounded names + paths + Python first docstring paragraphs
       ├─ score/coverage/vocabulary floor fails → no-match
       └─ up to 8 candidates → needs-choice, NEVER confident matched
```

The query service remains the common browser/worker/agent implementation.
`queryCode` still binds the exact scorer, router and query-service bytes. The
concept index lives inside the already-bound query service, so there is no
unbound runtime module. Importer producer hashes include the modified extractor.
Legacy snapshots remain readable: `service.conceptStats.available === false`
means BM25 is unavailable; reimport to get text. Their existing packet shape and
legacy parity remain unchanged rather than adding a limitation to every packet.

## Rules

- Case-fold retrieval consistently, retaining real IDs, paths and source refs in
  output. Case-only filename/symbol collisions abstain; no arbitrary winner.
- Normalize curly apostrophes; expand `where's/wheres`, `what's/whats`,
  `who's/whos`, `how's/hows` to the corresponding `… is`. Quotes, question marks,
  exclamation marks, commas, semicolons and parentheses are separators. Existing
  path punctuation such as `/`, `_`, `.`, brackets, `#`, `@` remains available.
  This is not a general filename grammar; parenthesized route paths remain a limit.
- Strip terminal `.`, `!`, `?` runs and trailing whitespace before every tier and
  operation parser. Interior dots in `src/db.py`, `Class.method`, `json.dumps`
  and qualified symbol IDs remain intact. This is sentence punctuation, not path repair.
- Bare literal stems/folder names with comparable evidence across kinds ask for
  a choice **before operation dispatch**, including LOCATE, dependency/dependent,
  caller/callee, trace, upstream/downstream and both PATH/FLOW endpoints. `backfill`
  includes its file and Python class; `events` includes its file and folder.
  Kind hints apply to each endpoint, not the whole question. Alternatives preserve
  the operation and real target IDs. Both `chosenNodeId` and the UI's combined
  alternative query + ID replay run the operation, never silently LOCATE instead.
  Two ambiguous endpoints are resolved in sequence; a fuzzy second endpoint is
  still a choice after resolving the first. Choices paginate at 20 candidates.
  Exact full folder paths are recognized before the absent-file guard.
  File/folder learned-alias scoring retains precedence.
- Kind hints: folder/directory/dir/package → layer; file/module/script → file;
  function/method/class/def → symbol. Prefer a matching hinted kind; fall back to
  the only available kind. Full folder labels outrank suffixes. A folder suffix
  shared by multiple paths stays ambiguous. Hints do not create missing nodes.
- Added filler list: `layer logic code stuff part thing located defined live lives`.
  Kind words also stop counting toward coverage. Existing question/operation stop
  words are retained in `web/scorer.js::STOP`; all lists are explicit, not learned.
- Lexical acceptance remains evidence ≥4, content-term coverage ≥0.6 and margin ≥1.
  Fuzzy names and absent explicit filenames remain nonconfident. Original query
  display text is retained for legacy evidence parity.
- `who invokes X` / `where is X called from` → CALLERS for symbols, DOWNSTREAM for
  file/group relationships. `what does X depend on` remains UPSTREAM;
  `what uses X` remains DOWNSTREAM. These are static links, not runtime proof.
- Choosing a file/folder for caller vocabulary runs DOWNSTREAM over static imports;
  callee/trace vocabulary runs UPSTREAM. Python symbols use call edges: CALLERS and
  CALLEES are one-hop, TRACE and UPSTREAM are forward transitive, DOWNSTREAM is
  reverse transitive. PATH/FLOW retain directed witnesses. Mixed symbol/file or
  folder/file endpoints are unsupported, never silently converted. Certain-only
  filtering and the 1 MiB complete-packet budget apply to the new symbol paths too.
- Clean checkouts run committed collision mechanics and cross-language packet
  tests without external snapshots. Optional real-repository benchmark tests skip
  with the missing artifact named; malformed/present artifacts still fail.
  Collision measurements and reproduction: [PARSER_COLLISIONS.md](PARSER_COLLISIONS.md).

## Synonyms v1

| Bidirectional group | Frozen examples |
|---|---|
| db ↔ database | Honcho qp-001/026; Salesroom sr-014/018 |
| config ↔ configuration ↔ settings | Honcho qp-029/033/034 |
| msg ↔ message | Honcho qp-038/039/040 |
| auth ↔ authentication | Honcho qp-069/071 |
| repo ↔ repository | Salesroom sr-025/027 |
| env ↔ environment | Salesroom sr-028/029 |

Only whitespace-delimited whole content words expand; literal paths are not
rewritten. At most 16 single-word expansions are attempted, without a combinatorial
cross-product. Supported literal results (including ambiguity) win before synonyms.
Synonym-only scorer evidence is multiplied by 0.75 and carries
`matched via synonym A→B`. Fuzzy/missing-name restrictions survive expansion.
Comparable literal synonym targets now receive the same evidence score regardless
of whether they are files or folders; an unrelated per-kind scoring scale can no
longer manufacture a confident winner. Tied candidates are retained, with the
existing packet cap. The frozen synonym table is unchanged. Literal matches still
win, so `db` need not choose a folder called `database` merely because a synthetic
construction intended that synonym; this trade-off remains explicit in the report.
Existing auth/grader morphology remains for legacy architecture-map compatibility.
`llm ↔ model` is intentionally **not** an equivalence: ORM/data models are different.

The workspace worker does **not** load the offline `web/aliases.js` localStorage
UI overlay. The service's existing `learnedAliases` option still composes with the
new rules, tested with an explicit overlay, and literal filenames retain priority.
No alias UI or persistence was added. Wiring workspace aliases is a separate next item.

## Bounded extraction and BM25

`map.search_text` is additive `dag-gps-search-text/v1`:
`{schema, nodes: {nodeId: {name, path, docstring}}, omitted}`.
Name/path tokens split snake/camel case; caps are 80/120 characters. Python module,
class and function docstrings use only the first paragraph, whitespace-normalized
and capped at 300 characters. No comments or target code execution. TS/JS/SQL
use names and paths only; no JSDoc or function extraction is claimed.

The entire extension is capped at 1 MiB encoded JSON, including IDs/keys, and
further restricted to remaining space under the unchanged 16 MiB extractor
sidecar cap. Omission is deterministic, counted and disclosed. Honcho's large
existing call graph leaves about 560 KB for text: 5,465 records are omitted.
Those nodes still get bounded names/paths at index construction, but not missing
docstrings. This is a material recall limit, not a hidden full-text index.
Salesroom has zero omitted records. Python contracts reject unknown IDs/schema,
invalid fields/control characters, oversized strings and invalid omission counts.
The workspace envelope can exceed 16 MiB (Honcho ~18.4 MB); that is not the extractor
sidecar. Neither sidecar nor 1 MiB evidence-packet limits was raised.

Index construction happens once per service/snapshot load. The inverted index
uses BM25 `k1=1.2`, `b=0.75`; binary per-field term frequencies are weighted
name=2, path=0.5, docstring=1.5. Simple plural stripping applies to words longer
than four characters except `ss`. Query-only filler adds `we our i my please`.
A candidate needs score ≥4 and ≥50% BM25 term coverage; every query content term
must exist somewhere in the index. This vocabulary check prevents random unknown
concepts from returning candidates on one generic word. It also causes real misses.
This candidate-only coverage is separate from the unchanged 0.6 lexical acceptance
rule. Ranking is deterministic: score, hinted kind on ties, then real node ID.
Each candidate explains matching terms and fields. Symbol choices display qualified
IDs and carry a normal exact-symbol follow-up query. No selections/edges/witnesses
are emitted before explicit choice. BM25 never handles routes or guesses callers.

## Frozen evaluation

Source-checked worker-drafted regression questions, **not user accuracy**.
Honcho: `3922af856d78ec41133916deec4d821fa9c5a92e`, 107 questions (80 dev / 27 holdout),
20 should-stay-no-match. Frozen before parser edits at `8087431`, baseline code
`7db31cd` (the main commit at branch creation).

Eric added Salesroom mid-run, after Honcho rules. Its separate supplement was
frozen at `bdc8401` before Salesroom-specific changes; its baseline was run against
pristine `7db31cd` modules, not the then-current parser. Pin:
`5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce`, 43 questions (32 dev / 11 holdout),
8 negatives. Rules-only numbers replay `e58c7ae`. Both seeded splits use 3922 and
at least 25% holdout. Expectations/splits were not relabeled after seeing results.
Holdout is checked at each required safety checkpoint, not an untouched blind test.

M=match-correct; C=needs-choice containing an acceptable candidate;
N=no-match-correct; W=confident wrong target/operation; O=confident answer on a
should-be-no-match. Correct matches on expected-choice rows do not count as C.

| Repo / split | Stage | M | C | N | W | O |
|---|---|---:|---:|---:|---:|---:|
| Honcho dev | baseline | 17 | 4 | 16 | 2 | 0 |
| Honcho dev | rules | 45 | 6 | 16 | 2 | 0 |
| Honcho dev | synonyms | 46 | 8 | 16 | 2 | 0 |
| Honcho dev | BM25 | 46 | 12 | 16 | 2 | 0 |
| Honcho holdout | baseline | 6 | 1 | 4 | 0 | 0 |
| Honcho holdout | rules | 18 | 2 | 4 | 0 | 0 |
| Honcho holdout | synonyms | 18 | 3 | 4 | 0 | 0 |
| Honcho holdout | BM25 | 18 | 5 | 4 | 0 | 0 |
| Salesroom dev | baseline | 9 | 3 | 6 | 0 | 0 |
| Salesroom dev | rules | 17 | 4 | 6 | 0 | 0 |
| Salesroom dev | synonyms | 20 | 4 | 6 | 0 | 0 |
| Salesroom dev | BM25 | 20 | 5 | 6 | 0 | 0 |
| Salesroom holdout | baseline | 3 | 0 | 2 | 0 | 0 |
| Salesroom holdout | rules | 7 | 0 | 2 | 0 | 0 |
| Salesroom holdout | synonyms | 7 | 0 | 2 | 0 | 0 |
| Salesroom holdout | BM25 | 7 | 0 | 2 | 0 | 0 |

Zero new wrong or overconfident answers, checked by case ID against baseline in
each split/repository. All 28 negative questions stay no-match. Committed per-case
reports: `eval/question_parser_{baseline,rules,synonyms,bm25}.json` and
`eval/question_parser_salesroom_{baseline,rules,synonyms,bm25}.json`.

### Remaining failures — input to a later decision, not silently solved

- Before the benchmark fixes, Honcho retained two baseline wrong decisions under the frozen expectations:
  `where is the configuration file` selects `src/schemas/configuration.py` rather
  than offering config files; bare `llm` selects `src/telemetry/events/llm.py` rather
  than asking between LLM folders. Literal-name priority is preserved.
  The new bare-name guard changes `llm` to a choice; the kind-worded configuration
  file remains the one known wrong under the frozen intended labels.
- Honcho message-storage and embedding-creation phrasing misses the expected
  targets in the top eight. `where do we store messages` now produces explicit
  choices, but the top symbol is message **search**, not persistence. Word overlap
  is not responsibility understanding; test helpers can outrank production code.
- Salesroom concept-only video playback/persistence questions can miss because
  names/paths contain neither all query terms nor the requested responsibility.
- Salesroom has 118 inventoried files, 91 mapped files and 29 direct-owning folder
  groups. `src` itself is **not a graph node**: its files are in deeper folders.
  `src` questions offer real descendant groups, not an invented root. This grouping
  limitation and unsupported non-source files were not changed by parser work.
- Existing graph expansion can hide a previously expanded group node when a later
  question selects that group. Browser parser cases use Clear between questions
  and independently verify highlights. This UI-state issue was observed, not fixed.
- No TS/JS symbols, semantic embeddings, LLM fallback, new alias UI or side features.

## Verification and reproduction

### Benchmark fixes (`t_b8a8498e`)

Harness review points were accepted first: expanded supported-pattern/file-PATH
coverage, strict ambiguity strata, and successful-operation timing. The corrected
grid was rerun before parser changes, then frozen unchanged for the comparison.
See [QUESTION_PARSER_BENCHMARK_FIXES.md](QUESTION_PARSER_BENCHMARK_FIXES.md) for
the before/after table and [VARIATION_BENCHMARK.md](VARIATION_BENCHMARK.md) for
complete main/fixed-parser axes and timings. No server implementation changed.

Six new service tests start RED across both repository snapshots and cover terminal
punctuation on all grid phrasings, collision choices and kind/path disambiguation,
literal precedence and synonym competition. Artificial competing synonym nodes
are explicitly test fixtures; they are not claimed to exist in the pinned sources.
An added RED assertion caught and fixed choosing the file from a file/class choice.
Frozen questions and splits are unchanged: all expected match counts, including
held-back matches, are retained; Honcho dev wrong decreases 2→1 and expected-choice
success increases 12→13. All other split counts are unchanged, with zero new wrong
or overconfident cases. Per-case results: `eval/question_parser{,_salesroom}_benchmark_fixes.json`.

Real-app spot checks: `env -u PYTHONPATH /usr/bin/python3 scripts/smoke_parser_fixes.py`
with the documented Playwright environment. Six actual Chromium questions pass
through WorkspaceServer and contract validation; screenshots and packet summaries
are under `artifacts/question-parser/benchmark-fixes/browser/`. These checks reuse
the pinned snapshots with honest current query-code hashes; no fresh import or
server optimization is claimed. All eight unchanged gates and packaging passed
on `cc69b4a`: Python 458/458, JS 212/212, zero skips; release worst p95 3.523 ms.
Receipt: `artifacts/question-parser/benchmark-fixes/gates/verification.json`.
The initial background gate lacked browser environment (two skips and smoke
failure); its receipt is retained under `gates-env-failure/`. Explicit Playwright,
axe-core and Node paths fixed setup; no performance-driven retry occurred.
Final receipt documentation is a docs-only commit after the gated commit.

### Review fixes (`t_e1cca752`)

All three consultant findings accepted: dispatch now resolves file/group lexical
evidence (including ambiguous stems) before falling into symbol callers; every
declared file hint selects the file in a file/group collision; traversal and PATH
reasons retain target/endpoint matching provenance. Explicit symbol call requests
remain symbol requests, including missing symbols; file hints break symbol/file
ties without changing static dependency direction.

`eval/question_parser_review_regressions.json` is a separate review-regressions
list, not a change to either frozen dataset or its splits. Its 16 real-repository
cases moved from 8 pass / 8 fail to 16 pass / 0 fail. Seven service tests cover
Python/TypeScript fixtures, all hints, group/file collisions, single-kind controls,
duplicate stems, missing full paths, symbol dispatch and both PATH endpoints.
Initial RED: six failures / one pass; a further symbol/file hint collision was
also demonstrated RED before fixing it. These synthetic collisions are not claimed
to exist in the imported repositories.

Frozen review-fix results (M / C / N / W / O), unchanged from BM25:

| Repo / split | M | C | N | W | O |
|---|---:|---:|---:|---:|---:|
| Honcho dev | 46 | 12 | 16 | 2 | 0 |
| Honcho holdout | 18 | 5 | 4 | 0 | 0 |
| Salesroom dev | 20 | 5 | 6 | 0 | 0 |
| Salesroom holdout | 7 | 0 | 2 | 0 | 0 |

Zero new wrong/overconfident cases versus baseline; all 28 negatives still abstain.
Per-case reports: `eval/question_parser{,_salesroom}_review_fixes.json`.
The remaining failures listed above are unchanged, not relabeled as successes.
Real-app checks passed all 16 review questions with packet/highlight equality and
screenshots in `artifacts/question-parser/review-fixes/{honcho,salesroom}/`.
Honcho dependents are paginated and visibly labeled potentially affected; Salesroom
database traversal visibly retains `matched via synonym database→db`.

Reproduce the supplement with `node scripts/eval_question_parser_review.cjs`;
browser scripts accept `--review-regressions --out <evidence-directory>`.
All eight unchanged release gates and packaging passed on `0059009`; receipt:
`artifacts/question-parser/review-fixes/gates/verification.json`. Python 458/458
and JS 199/199, zero skips. Scorer 47/47, alias 15/15, lookup 39/40 (unchanged).
Release maximum p95 9.399 ms, below the unchanged 10 ms threshold. No performance
retry or sample/threshold changes on this follow-up. Both fresh imported snapshots
and all 16 browser packets also pass Python contracts. Consultant second opinion
is requested before parent approval; no push, merge or PR.
Initial standalone tests: 199 JS passed; Python ran 458 with two browser checks
skipped before configuring NODE_PATH (not counted as full gate evidence).
A post-gate browser rerun initially lacked NODE_PATH; restoring the existing local
Playwright package path resolved it, and both reruns passed without product changes.

Real production WorkspaceServer imports on this card's workspace copy, actual
Chromium input/Enter, packet-vs-highlight assertions and screenshots for seven
questions per repo: `artifacts/question-parser/{honcho,salesroom}/`. The YouTube
question selects `src/lib/youtube.ts`, not its test; DB/case/contraction variants
work. Honcho `src folder` selects the actual src group. Concept questions remain
explicitly uncertain. Qualified choices wrap and scroll; screenshots were inspected.

Measured warm BM25 (20 repeats of every frozen question, 5 warmups): Honcho 2,140
samples, p95 1.218 ms, index construction 59.724 ms; Salesroom 860 samples, p95
0.015 ms, construction 0.379 ms. Full service p95: 1.294 / 0.173 ms respectively.
These measurements exclude browser/network latency. `performance.json` records
raw values; unchanged release scorer scale benchmark separately gates p95 <10 ms.

```sh
# Local QA dependencies as documented in V1_RELEASE.md; use NODE_PATH for browser scripts.
env -u PYTHONPATH /usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
node scripts/eval_question_parser.cjs artifacts/question-parser/honcho/snapshot.json \
  artifacts/question-parser/honcho-eval.json eval/question_parser_baseline.json
node scripts/eval_question_parser.cjs artifacts/question-parser/salesroom/snapshot.json \
  artifacts/question-parser/salesroom-eval.json eval/question_parser_salesroom_baseline.json \
  eval/question_parser_salesroom.json
node scripts/bench_question_parser.cjs
env -u PYTHONPATH /usr/bin/python3 scripts/verify_question_parser.py honcho
env -u PYTHONPATH /usr/bin/python3 scripts/verify_question_parser.py salesroom
env -u PYTHONPATH /usr/bin/python3 scripts/verify_function_honcho.py \
  artifacts/question-parser/function-proof --suite v3
env -u PYTHONPATH /usr/bin/python3 scripts/audit_function_honcho.py \
  artifacts/question-parser/function-proof
env -u PYTHONPATH /usr/bin/python3 scripts/release_check.py \
  --quest-repo /Users/aibert/projects/quest-coder --output artifacts/question-parser/final-gates
```

458 Python / 192 JS tests pass. All eight project/release gates pass on `a54fbca`;
receipt: `artifacts/question-parser/final-gates-complete/verification.json`.
Final release p95 is 8.847 ms. A socket-reset test failure and a prior 11.852 ms
performance failure are retained; unchanged standalone performance repeats passed
at 8.760 and 6.674 ms before the complete passing rerun. No threshold/sample edits.
Scorer 47/47; alias 15/15; lookup retains 39/40. The initial full run identified
legacy parity differences (display casing and an added legacy limitation); these
were fixed rather than weakening the parity tests. Existing test datasets and
performance thresholds/samples are unchanged. Final gate evidence and counts are
recorded in STATUS and the card handoff. Consultant second opinion is required
before parent approval/integration; this report does not claim final approval.
