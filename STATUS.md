# Status — DAG GPS

## Folder tree data — verified, consultant second opinion requested

`t_57ec698f`, isolated `folder-tree`, implementation/gated checkpoint `fd5104c`.
New imports retain all real mapped-source folder ancestors, stable direct owners,
compact-chain hints and file-backed folder answers with 200-node paging. No
drill-down UI; existing flat overview retained. Honcho 86→106 folders, Salesroom
29→35. 70 source-checked folder questions pass; unchanged frozen sets have zero
new wrong answers. 499 Python / 274 JS, zero skips; eight unchanged gates and
packaging pass. Direct/HTTP p95 within +1 ms; full measurements and caveats in
`docs/FOLDER_TREE.md`. Same-name src requires choice on Honcho; Salesroom's small
snapshot grows 5.155%. Consultant advice/generalist approval pending. No push,
merge, PR, TS alias changes or next feature launched.

## Question log + persistent session — verified, consultant second opinion requested

`t_44e9d449`, isolated `question-log`, includes server-speed and parser-collisions
(including parent's `1adb892` pagination fix). Workspace query journal, saved
verdicts/history, safe persistent key, explicit HTTPS proxy hosts and draft export
implemented. 492 Python / 266 JS pass, zero skips; first Python attempt retained
an existing oversized-body connection-reset failure, unchanged rerun passed.
Real Chromium Honcho: five questions, verdicts, same-link restart/history pass.
All eight unchanged gates and packaging pass on `365197b`; scorer p95 3.873 ms.
Warm Honcho HTTP p95 6.070 ms vs fresh server-speed 6.246 ms (480 requests each),
within +1 ms. Consultant second opinion requested. No push/main merge/PR.
See `docs/QUESTION_LOG.md`; only this feature is active in this worktree.

## Parser collision resolution — verified, consultant second opinion requested

`t_29b602b9`, isolated `parser-collisions` branch from `08f1b4d`.
Cross-kind target choices now precede every operation and resolve PATH endpoints
independently. Candidate/kind/path choices retain traversal; optional pinned-data
tests skip clearly in clean checkouts, with committed mechanics regressions.
Implementation `01dfb1b`: 474 Python / 265 JS pass, zero skips; eight unchanged
gates and packaging pass, scorer worst p95 4.307 ms. Fresh detached checkout:
474 Python pass; JS 225 pass / 8 optional-artifact skips / zero failures, removed
afterward. Corrected-grid wrong: Honcho 380→288, Salesroom 712→682, zero newly wrong
cases; frozen sets unchanged. 152/30 confident answers become choices, including
60 formerly correct Honcho answers. Full report: `docs/PARSER_COLLISIONS.md`.
Consultant advice requested; final approval remains with the generalist. No push,
merge or PR. Later changes are measurement/reporting only.
Parenthesized paths and the parent card's AgentBridge duplicate validation are
not part of this card. No next feature launched.

## Server speed — verified, consultant second opinion requested

`t_20ef91ae`, isolated `server-speed` branch, implementation `8277e35`.
Full snapshot validation is cached with a four-entry, file-generation-aware LRU;
query/source/context/explanation routes reuse the validated index. Warm HTTP
p95: Honcho 487.774→6.993 ms; Salesroom 3.078→1.075 ms, 480 requests/repo/version.
All 960 paired response hashes match. Cold starts remain expensive and measured
combined Honcho RSS rises; see `docs/SERVER_PERFORMANCE.md` for limits and evidence.
473 Python / 212 JS pass, zero skips. Independent frozen-validator replay:
180 packet checks (71 rejections), 176 indexed checks, 54 real packets; no differences.
All eight unchanged gates and packaging pass on `8bfc232`; scorer worst p95
3.547 ms (<10 ms). Receipt: `artifacts/server-performance/gates/verification.json`.
Later changes are docs only. No push/merge/PR. Consultant second opinion requested;
final approval remains with the generalist. No next feature launched.

## Prior benchmark fixes — verified, consultant feedback received

`t_b8a8498e`, query code `2b80e8d` on `question-parser`. All three prior benchmark
review points accepted; harness corrected first at `103b6e5`. Same expanded grid
before/after: 144,746 cases per version, 868,476 timed calls, 1,920 HTTP requests.
Correct-or-choice: Honcho 72,179→89,243 / 92,856; Salesroom 37,555→48,257 / 51,410.
Wrong: 800→380 / 777→712. Period matches question-mark performance exactly.
Each repo trades 36 formerly correct answers for choices containing the intended
target. New wrong vs main: 149→61 / 542→535. Seven newly wrong Salesroom period
cases expose the existing parenthesized-path bug; their `?` counterparts were
already wrong. No new frozen wrong, all holdout matches retained (18 / 7).
Direct p95: Honcho 1.080 ms, Salesroom 0.232 ms; zero matched negatives.
Python 458/458, JS 212/212, zero skips; real-app 6/6 pass. All eight unchanged
gates and packaging pass on `cc69b4a`; release worst p95 3.523 ms (<10 ms).
Receipt: `artifacts/question-parser/benchmark-fixes/gates/verification.json`.
First gate attempt lacked browser environment in its background process (two
Python skips, smoke failure); explicit dependency paths fixed setup and the full
unchanged rerun passed. No performance retries or threshold changes.
Reports: `docs/QUESTION_PARSER_BENCHMARK_FIXES.md`, `docs/VARIATION_BENCHMARK.md`.
Screenshots and retained attempts: `artifacts/question-parser/benchmark-fixes/`.
No server changes, push, merge or PR. Consultant second opinion requested;
approval remains with the generalist. Changes after the gated commit are docs only.

## Prior question-variation measurement — reviewed; corrections above

Card `t_984c3139`, same `question-parser` branch; no parser behavior changed.
114,726 constructed cases across pinned Honcho/Salesroom, identical main/parser
grids, 688,356 timed service calls and 1,920 real HTTP requests. Correct-or-choice:
Honcho 53.99% → 78.81%; Salesroom 71.16% → 71.79%. Parser warm p95: 0.812 / 0.095 ms;
HTTP p95: 487.779 / 2.920 ms. Synthetic known-target robustness, not user accuracy.
Wrong totals improve, but 149 Honcho / 444 Salesroom newly confident-wrong cases
remain (including ambiguous forms and mismatching kinds); findings only, no fixes.
Zero matched negatives among 240 per repo/version. Report, axes, failures and
reproduction: [VARIATION_BENCHMARK.md](docs/VARIATION_BENCHMARK.md).
Python 458/458 and JS 204/204, zero final skips; raw totals/statuses/source audit
verified. Consultant second opinion requested; no push, merge or PR.

## Current work — question parser, local only

Card `t_3b508d4b`, branch `question-parser`, based on main `7db31cd` (PR #8).
Rules, kind hints, versioned synonyms and bounded deterministic BM25 candidates
are implemented. No model fallback, side features, push, merge or PR.
See [QUESTION_PARSER.md](docs/QUESTION_PARSER.md) for the pipeline, frozen eval
matrix, measured limits and remaining failures. Follow-up `t_e1cca752` accepts and
fixes all three consultant findings: lexical dispatch, file hints and traversal
synonym reasons. Seven service tests and 16 real-app review cases pass; frozen
split results are unchanged. All eight unchanged gates and packaging pass on
`0059009`: Python 458/458, JS 199/199, zero skips; release p95 9.399 ms, no retry.
Receipt: `artifacts/question-parser/review-fixes/gates/verification.json`.
Both fresh snapshots and 16 real-app packets pass contracts. Second opinion pending.

- Frozen Honcho: 107 questions / 27 holdout; late-added Salesroom: 43 / 11 holdout.
- Every stage has a committed per-case report. Zero new wrong/overconfident answers
  versus baseline in either repo/split; all 28 negative cases remain no-match.
- Honcho keeps two baseline literal-name mistakes; BM25 still misses some concept
  targets. These are reported, not relabeled or called semantic understanding.
- Salesroom `where is the youtube` selects `src/lib/youtube.ts`. Its missing `src`
  parent group remains an extraction limitation; choices reference real subgroups.
- Python docstrings are bounded first paragraphs; TS/JS use names/paths only.
  BM25 never auto-selects. Honcho's sidecar budget omits 5,465 text records, with
  name/path-only fallback and explicit disclosure.

## Prior parser verification (before review fixes)

458 Python / 192 JS tests pass. All eight project/release gates passed against
implementation commit `a54fbca`; final scorer scale p95 was 8.847 ms (<10 ms).
Scorer 47/47, alias 15/15, lookup 39/40. Full receipt:
`artifacts/question-parser/final-gates-complete/verification.json`.
Real Chromium imports/questions/screenshots on both pinned repos; 13-question
Honcho function proof and source audit pass. Existing legacy parity tests retained.
BM25 Honcho p95 1.218 ms / index build 59.724 ms; Salesroom 0.015 / 0.379 ms.
Evidence: `artifacts/question-parser/`. An oversized-request test socket reset and
one 11.852 ms performance failure are retained; unchanged complete rerun passed.

## Existing shipped foundation

Main through PR #8 includes local pinned public-repo import, dependency preview,
file/group queries, revision-bound source, agent bridge/explanations and Python
function/call extraction with confidence tiers, re-exports and overload safeguards.
See [FUNCTION_LAYER.md](docs/FUNCTION_LAYER.md) and [WORKSPACE_QUERY.md](docs/WORKSPACE_QUERY.md).

## Next

Only the server-speed card is active in this worktree. Parser traversal-ambiguity
and parenthesized-path review findings remain separate follow-ups. Unresolved
classification, in-app Explain, live refresh and TS/JS symbols remain parked.
Workspace alias-overlay wiring and the observed expanded-group highlight issue
are reported limitations, not implemented in this card. Eric's unaided acceptance
and semantic grouping review remain separate from automated verification.
