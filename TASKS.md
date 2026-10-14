# Tasks — DAG GPS

## TypeScript aliases card — verified, consultant second opinion requested

`t_50e6f922`: importer config resolution and RED-first fixtures complete on
`ts-paths`; 510 Python / 266 JS pass. Pinned Salesroom 46→187 imports, Honcho
edges identical; frozen/variation zero-new-wrong gate passes. Full evidence and
limits: `docs/TS_PATH_ALIASES.md`. Next: consultant advice, generalist approval.
No next feature launched; no push, merge or PR.

## Current question-log card — verified, consultant second opinion requested

`t_44e9d449`: port playground journal/labels/history and persistent session safely
onto cached server; export review drafts without modifying frozen sets. 492 Python /
266 JS pass; Honcho browser five-question and restart proof passes. Eight unchanged
gates/packaging pass on `365197b`, HTTP p95 6.070 ms vs server-speed 6.246 ms.
Dag-consultant second opinion requested. Local `question-log` only;
no push/main merge/PR. Parent pagination finding accepted via merged `1adb892`.

## Current parser-collision card — verified, consultant second opinion requested

`t_29b602b9`: resolve literal cross-kind targets before every operation, preserve
explicit-choice traversal, and make pinned-snapshot tests clean-checkout safe.
Implementation and RED-first regressions are in isolated `parser-collisions`.
474 Python / 265 JS pass with pinned data, zero skips; clean detached checkout
passes 474 Python and 225 JS with 8 explicit optional-data skips. All eight gates
and packaging pass on `01dfb1b`. Same-grid wrong decreases on both repos with no
newly wrong cases; frozen sets unchanged. Dag-consultant second opinion requested,
approval remains with generalist. Parenthesized paths remain a separate limitation.

## Current server-speed card — verified, consultant second opinion requested

`t_20ef91ae`, `server-speed` at `8277e35`: cached strict snapshot indexes across
all workspace routes; generation-bound workers and concurrency/tamper tests.
Warm Honcho HTTP p95 6.993 ms (<20 ms target), down from 487.774 ms; all 960
before/after paired response hashes match. 473 Python / 212 JS, zero skips;
all eight unchanged gates and packaging pass on `8bfc232` (release p95 3.547 ms).
Frozen-validator replay: 180 packet checks, 71 rejections, 54 real packets, no
differences. Dag-consultant second opinion requested; approval stays with the
generalist. Details: `docs/SERVER_PERFORMANCE.md`.
No parser changes, push, merge or PR. No next feature launched.

## Prior parser follow-up — implemented and verified, consultant feedback received

`t_b8a8498e`: terminal punctuation, bare-name choices and comparable synonym
targets implemented, with RED-first service regressions on both pinned repos.
Harness review points accepted and corrected separately before measuring fixes.
Frozen sets have zero new wrong and no held-back match loss. Corrected-grid wrong
falls 800→380 (Honcho) and 777→712 (Salesroom); six real-app checks pass.
Python 458/458 and JS 212/212 (zero skips), all eight unchanged gates and packaging
pass on `cc69b4a`; release p95 3.523 ms. Consultant second opinion requested.
No next feature launched; no push/merge/PR. Final approval remains with the generalist.

## Prior measurement follow-up — reviewed; corrections above

`t_984c3139`: deterministic question-variation benchmark implemented and run on
main `7db31cd` and unchanged parser code `4ad61d9`, same source-checked targets.
114,726 generated cases; per-axis/operation and HTTP/direct speed tables in
`docs/VARIATION_BENCHMARK.md`. Python 458 / JS 204 pass with zero final skips.
Newly exposed ambiguity, punctuation and typo failures are findings only.
Next: dag-consultant second opinion, then generalist approval. Still parser-only;
no next feature, PR, push or merge authorized by this card.

## Current card

`t_3b508d4b` — the only active feature: natural-language question parser.
Rules, synonyms and bounded BM25 choices implemented on `question-parser`, with
frozen Honcho (107) and late-added Salesroom (43) cases, seeded holdouts and
per-stage reports. Zero new wrong answers; baseline mistakes and concept misses
remain documented. See [QUESTION_PARSER.md](docs/QUESTION_PARSER.md).
Real-app evidence and project gates: `artifacts/question-parser/`.
Consultant second opinion required before parent approval. No push/merge/PR.
Follow-up `t_e1cca752`: all three findings implemented with RED-first service
regressions, a separate 16-question real-repo supplement and browser screenshots.
Frozen sets/splits unchanged; eight unchanged gates and packaging pass on `0059009`
(458 Python / 199 JS, zero skips; p95 9.399 ms). Second opinion pending.
The prior function-layer card is on main through PR #8.

## Parked items — do not start while parser work is active

1. **Queued — `t_21987d99`: unresolved-call split.** Separate `unresolved-split`
   worktree after this card's acceptance: classify builtins/external libraries,
   unknown receivers and in-repo gaps; expose counts and source-audited examples.
2. **Needs Eric's decision — in-app Explain.** Existing validated explanation/
   agent bridge is implemented; decide the in-app action and invocation UX.
3. **Queued — workspace M4.** Live refresh and revision/diff handling; not the old
   optional hosted-Jev backend. Do not begin without its own authorized scope.
4. **Queued — TypeScript/JavaScript function symbols.** Python is the current
   function extractor; file-level JS/TS evidence does not imply function support.

The separate playground is local, unshipped and skipped. No work on it in this sequence.

## Done

- Offline map/canvas, local scorer, routing, filename lookup and explicit alias
  learning; pinned refresh, curated tours and import-based impact.
- Trust diagnostics/extraction refinement, grouping draft/review editor and opt-in
  query feedback. Real-user scorer tuning remains deferred pending confirmed labels.
- Workspace foundations, public repository import, query service/server/UI,
  revision-bound source and validated agent context/explanation bridge: on main
  through PR #6. See the [workspace UI](docs/WORKSPACE_UI.md) and linked reports.
- Python function layer and first consultant fixes (`t_58cccce0`, `t_4977fa02`):
  main through PR #7 (`2bd93b1`); scope/ownership guards, packet bounds and legacy parity.
- Call-confidence tiers (`t_39e90fae`, `b97d6d6`): implemented on `function-layer`.
- Static package re-exports and prior consultant fixes (`t_d663095e`, `915265e`):
  implemented on `function-layer`; the remaining review findings are fixed by this card.

## Separate acceptance/backlog

- Eric's unaided real-repo session and semantic grouping review remain pending;
  automated proof does not substitute for either.
- Final release acceptance/packaging and any parent integration are separate gates.
- Scorer tuning needs user labels and a pre-tuning holdout (20 cases is a soft goal).
- The old hosted-Jev M4 remains dropped unless explicitly revisited.

Historical milestone detail and measurements remain in git and existing reports;
[STATUS.md](STATUS.md) is the short live view. No subsequent mini-milestone was started.
