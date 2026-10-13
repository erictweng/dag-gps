# Tasks — DAG GPS

## Current card

`t_0751cc8d` — implementation and local verification done; consultant second opinion
pending before parent acceptance. Fix commit `0641dd6`: future class annotation
bindings abstain; only supported following overload implementations coalesce;
mutated/rebound markers invalidate; Honcho coverage uses an explicit suite option.
STATUS and FUNCTION_LAYER now describe only the current build.

455 Python / 182 JS tests, `.verify.json` build/smoke and four evals pass. Fresh
13-question Honcho proof and source/parity audits pass; zero symbol-graph or count
changes from v3. See [FUNCTION_LAYER.md](docs/FUNCTION_LAYER.md) and local evidence
`artifacts/function-layer/binding-fixes/`. No push/merge/PR in this card.

## Next items, in order

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
