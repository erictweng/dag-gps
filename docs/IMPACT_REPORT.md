# V1.1 — Explainable potential impact (historical integrated evidence)

V1.1 is integrated on main `7bc6769`. The original worker evidence below is retained
as history. V1.2's deliberate same-source extractor migration is documented in
[TRUST_REPORT.md](TRUST_REPORT.md): quest 413 → 415 file pairs, no removals;
`runner/quest_runner.py` 14 → 16 direct consumers and 11 → 12 linked tests;
self `scripts/build_map.py` 1 → 2 linked tests through an explicit static loader.
The runner-client expectations remain unchanged. Browser/unit source assertions
were updated to the exact newly resolved statements, not weakened. Coverage stays
unknown, and current impact warnings disclose incident extraction findings or
explicit repository-level uncertainty. Current all-gate totals: 161 Python + 109 JS;
parent V1.2 acceptance remains pending.

Implemented both V1.1a **and** V1.1b on `v1-impact` from main `6bfc5ee`.
Original worker verification: 2026-10-07 PDT. The pending-review statements below
are historical; V1.1 subsequently integrated. This is not acceptance of later v1 gates.

## Contract and decisions

`web/impact.js` is dependency-free CommonJS / browser `DagGpsImpact`:

```js
const {analyzeImpact} = require('./web/impact.js');
const result = analyzeImpact(map, validatedToursOrNull, realFileId);
```

- Only real **file** IDs are accepted. Unknown/layer IDs, duplicate node IDs and
  dangling/non-file file-edge endpoints reject; no layer-to-file membership inference.
- `directConsumers` are one reverse **import** edge away; `transitiveConsumers` are
  farther import-only consumers and exclude direct consumers. Each result appears
  once per section with `{id,path,distance,chain,edges,reason}`. `chain` and original
  typed edges read **consumer → dependency → selected file**, not execution order.
- Sorted adjacency, FIFO BFS and visited state give deterministic shortest witnesses,
  including ties. Duplicate typed edges collapse; origin never reappears or becomes
  a self-result, and cycles terminate. Inputs are not mutated.
- `boundaryImpacts` is intentionally **transitive**, not just direct callers. It uses
  reverse import/HTTP/RPC reachability with **at least one HTTP/RPC** edge. A two-state
  BFS tracks whether a boundary was crossed, so a shorter import-only path cannot
  incorrectly erase a boundary witness. It retains the shortest qualifying witness;
  equal-length ties follow sorted edge tuples. Nodes can appear both here and in
  import consumers, explicitly disclosed; the outputs are never merged. Cyclic
  boundary walks may repeat non-origin IDs across the two states; these are static
  reachability evidence, not a runtime trace. Realtime and all other types excluded.
- `linkedTests` is the test subset of import-only consumers, independent of the
  canvas tests toggle. Recognized by explicit `is_test:true` / `classification:'test'`,
  or documented **source path** rules: directory components `test`, `tests`,
  `__tests__`, `e2e`; Python `test_*.py`; JS/TS `*.test.*` / `*.spec.*` extensions
  ts/tsx/js/jsx/cjs/cts/mjs. No guessing from prose or loose substring such as
  `contest.ts`. This is observed dependency reachability, not coverage/execution.
  `coverage` is always **unknown**, even when linked tests exist.
- `tourReferences` includes exact selected-file citations in both ordered steps and
  typed tour links, not node membership or downstream narrative inference. It returns
  tour ID/title, step number/title (or link number/label), source path, start/end,
  symbol, evidence and inclusion reason. Duplicate identical citations per context
  collapse; orphan paths/node references are excluded and reported. No tours is an
  explicit unavailable state.
- Tours accept the **existing validated version-1 raw or compiled schema**, not a
  newly invented schema. Compiled evidence adds `nodeId`/`excerpt`; raw evidence is
  path/start/end/symbol. Envelope repo/snapshot/ranges are checked defensively here;
  immutable-source validation remains the existing `compile_tours` build boundary.
  Legacy seven-character map SHA can match the validated full tour SHA; refreshed
  maps carry full `snapshot_commit`. This pure module does not fetch source or
  independently prove raw excerpts. Wrong snapshot/repository/schema reject.

## UI / Ask

Open `dist/quest-refresh/index.html` (also `dist/quest-coder.html`). Inspect a real
file then choose **Inspect potential impact**, or type:

```text
what could be affected if I change lib/runner-client.ts?
impact of runner/quest_runner.py
```

Also accepts explicit `impact on/for` and `inspect potential impact` forms. A narrow
UI intent resolver reuses unchanged scorer file-first target retrieval and validation;
legacy **what depends on …** remains DOWNSTREAM, with its existing typed-edge behavior.
Neither scorer nor router is redesigned. No analysis on `yes:false` or a layer target;
all duplicate basenames and missing-name suggestions require an explicit real-file
choice. Unknowns clear summary/focus/highlights and offer no speculative argmax action.

The sidebar contains Direct consumers / Transitive consumers / Linked tests / Tour
references / Potential boundary impacts / Limits, with snapshot SHA, potential-only
language, explicit edge direction and coverage unknown. The overview shows real IDs
across layers and only witness edges, with the selected file distinguished. Clicking
a consumer/test/boundary result focuses its real-file shortest witness chain for
readability, shows every typed edge, and offers **Inspect real file in map**. Summary
survives inspection, Back and tour/evidence navigation; **Return to impact graph**
restores the full overview. Tour citations open their source-backed tour/step and
bundled offline evidence. No filesystem/editor-opening claim. New Ask or tour-menu
selection clears the prior impact. Existing pan/zoom/Fit, routes, aliases and tours
retain their legacy tests. Controls use real buttons, visible focus and keyboard Enter.

## Frozen-source audit before fixtures

Quest snapshot **749d8b5de490cc2e6a0c98c713fab3ab856da799**, same 272 files / 413
file edges / layer memberships; source and map were not edited.

`lib/runner-client.ts`:
- Direct import consumers: `app/api/health/route.ts` (line 3),
  `app/api/run/route.ts` (line 10), `lib/party-boss-server.ts` (line 8),
  verified by `git show` at the pin.
- One transitive consumer: `app/api/party/boss/route.ts` →
  `lib/party-boss-server.ts` → `lib/runner-client.ts`.
- **Zero observed linked tests; coverage unknown**, never “untested”.
- Six separate potential boundary results; e.g. `app/page.tsx` → HTTP
  `app/api/run/route.ts` → import `lib/runner-client.ts`.
- Four exact tour citations: Submit step 3 lines 31–46 and 49–83;
  Submit link 3 lines 56–62 and link 6 lines 63–79. Counting step citations alone
  would omit real compiled link evidence. Raw and compiled shapes are supported.

Second audited graph-backed target `runner/quest_runner.py`:
- Fourteen direct import consumers, zero farther consumers, **eleven real tests**
  in `runner/tests/`. Their pinned `from runner.quest_runner import …` statements
  are checked by the browser script, not invented fixture edges.
- Tests remain in the impact graph with the Show tests layer toggle off.
- Three exact step citations: Run basic step 4 lines 974–999; Submit step 5 lines
  779–803 and 974–999. Coverage still unknown.

The second demo remains explicitly pinned to old self snapshot
**f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93**. It audits the old source graph but runs
current UI: `scripts/build_map.py` has one observed importing test and no curated
tours. No silently advanced source snapshot or invented self tours.

## Actual verification

All non-null `.verify.json` recipes **build / test / smoke exit 0**. Gates add impact
checks, not replacements or weakened legacy gates.

- `python3 -m unittest discover -s tests -q`: **138 tests, OK**.
- `node --test tests/*.test.cjs`: **103 tests, 103 pass, 0 fail**; ten new pure
  impact cases cover cycles, shortest ties, order/immutability, edge types,
  direct/transitive duplicates, invalid/isolated IDs, test evidence, raw/compiled
  citations, orphans and real pinned expectations.
- Original generated evaluation remains op 47/47, target top1/top3 44/44;
  separate lookup challenge remains op/label 39/40, top1 16/17, top3 17/17,
  suggestion recall 15/15, negative false accepts 0/24. Bearer-auth abstention
  retained. Synthetic alias eval 15/15. Not user/held-out accuracy.
- Full legacy map build **10/10** checks plus pinned snapshot parity; canvas,
  interaction, scorer parity, M3, lookup19, alias19, refresh7 and tours29 browser
  gates pass. Tour gate exercises all 18 steps and every source citation.
- `node scripts/smoke_impact.cjs`: **14 browser checks / 9 screenshots**, real
  sequential typing/Enter and actual clicks on both files, chain inspection,
  separated HTTP boundary witness, tour evidence/recovery, all 13 `route.ts`
  alternatives, missing `runner.py`, unknown clearing, layer/non-single target
  rejection, unchanged DOWNSTREAM, 1280/1920 layout, keyboard close, second map
  no-tour state. **Zero page/console errors or external requests**.
- Visually inspected every impact state. 1280 sidebar/control text does not clip;
  wide overview graph uses fit/zoom (small labels at fit), result-click witness view
  deliberately enlarges the chain without changing graph IDs or source evidence.
- Immutable map/layers/tours/evals/scorer/router/extractor equal main `6bfc5ee`
  bytes; SHA-256 values recorded in local verification JSON. No quest-coder changes.

Local/ignored evidence (not shipped in fresh clones):
- `artifacts/impact-{build,test,smoke}.log` — complete real command output.
- `artifacts/impact-verification.json` — exact recipe commands, exits, timings,
  test totals and immutable-input hashes.
- `artifacts/impact-browser.json` — enumerated checks, screenshots, empty error/
  external-request arrays. `artifacts/impact-*.png`: runner-client, chain, boundary,
  tour-evidence, linked-tests, ambiguous, unknown, 1280, self-no-tours.
- Rebuilt HTML: `dist/quest-refresh/index.html`, `dist/quest-coder.html`,
  `dist/dag-gps/index.html` (offline artifacts remain ignored as before).

One initial tour-click smoke exposed strict-eval scope isolation: calling the tour
module's private helper from another eval module failed. Fixed by exporting a narrow
`tourUI.openReference` API, then reran the entire recipes; final errors are zero.
No unresolved implementation blocker. Parent acceptance/push and human release
session remain pending. Extraction blind spots, snapshot staleness, boundary
heuristics and lack of coverage proof are unchanged; no trust/onboarding/query-log
features were added.
