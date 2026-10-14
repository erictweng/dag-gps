# Tasks — DAG GPS

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
