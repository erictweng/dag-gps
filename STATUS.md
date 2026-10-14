# Status — DAG GPS

## Question-variation measurement — ready for consultant review

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

Only parser work is active. Parent approval follows consultant review. Unresolved
classification, in-app Explain, live refresh and TS/JS symbols remain parked.
Workspace alias-overlay wiring and the observed expanded-group highlight issue
are reported limitations, not implemented in this card. Eric's unaided acceptance
and semantic grouping review remain separate from automated verification.
