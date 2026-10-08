# M3 — offline Ask and directed route highlights

Verified locally October 7, 2026 (PDT), on `m3-routing`, based on `fad7ad9`.
Eric approved M3; parent independently verified M2 before this task.
No push, merge, Claude launch, dependency installation, quest-coder edits, map
membership changes, or scorer/synonym changes.

## Implemented

- One offline HTML includes the existing local scorer and new pure router. Ask is
  enabled: Enter submits the form; the visible Ask button also submits.
- A second `validateResult(result, MAP)` boundary check runs before any chosen IDs
  are used. Invalid output clears previous answer highlights and produces no action.
- LOCATE highlights only its target, with no implied dependency traversal. Exact
  file queries open their actual layer and fit the full view so the target stays visible.
- UPSTREAM = **Dependencies**, following consumer → dependency edges transitively.
  DOWNSTREAM = **Dependents**, following those edges in reverse. Neither highlights
  the opposite direction. The source remains distinctly selected.
- PATH independently matches both endpoints, then deterministic directed BFS finds
  a shortest route. Lexically sorted adjacency breaks shortest-path ties; typed
  edges are sorted too. Cycles terminate; a self-route contains one node. Realtime
  is excluded from routing and highlighted edges, even if drawn as muted context.
- Successful endpoint matching is shown separately from route success. Unreachable
  queries say **No directed route found**, highlight only the two endpoints (gold
  source, purple destination), and emphasize no edges. No fabricated route.
- Layer and file graphs stay separate. Mixed layer/file endpoints are explicitly
  unsupported: no conversion, no edges, no directed route. This is a deliberate
  limitation, not evidence that the conceptual layers are unrelated.
- File dependency/dependent/path operations use an explicit **global route view**
  containing only selected real file IDs and original typed edges, including files
  from other layers. Full file paths appear on boxes (long ones can be shortened),
  full IDs remain in SVG titles and the answer, and clicks open file details. Back
  returns to layers. No fabricated layer stubs are used in this route view; legacy
  expanded-layer views retain their existing aggregate stubs.
- Result panel shows operation, yes/no acceptance, measured query work latency,
  explanation, heuristic operation/target bars, and top-three candidates for each
  target head with normalized weights, raw scores and component evidence.
  All scores are explicitly **heuristic, not calibrated correctness probabilities**.
- NOT_SURE clears prior focus/highlights and shows alternatives without acting on
  speculative argmax IDs. Alternatives are buttons for explicit overrides. An
  abstained PATH requires explicit selection of **both** endpoints before routing;
  an accepted PATH can override one independently matched endpoint. The original
  scorer yes/no and NOT_SURE stay visible, alongside explicit override status.
- Manual focus/expand/back/tests/Escape clears answer-route state. Legacy pan, zoom,
  fit, details and double-click interactions remain available.

## Renderer safety

`render.py` serializes shipped module source as a JS string and executes that
trusted, fixed source with `new Function`; map/query data are never executable
source. Every `<` is encoded as `\u003c`, including map JSON, to prevent closing
script tags **and** HTML double-escaped script states (`<!--<script>`). U+2028/2029
are escaped. Regression tests execute source containing mixed-case closing tags,
HTML comment/script sequences and line separators, round-trip hostile map text,
and verify both modules are inlined. UI text and attribute values are escaped,
including apostrophes used by legacy single-quoted attributes.

This standalone artifact has no CSP. Hosting under a strict CSP would need a
separate packaging decision because `new Function` requires allowed dynamic code
execution. It executes only shipped local module text, never user questions.

## Actual gates

All `.verify.json` build/test/smoke commands exited **0**. Full commands and raw
outputs are saved in `artifacts/m3-final-verification.json` and `m3-{build,test,smoke}.log`.

```bash
python3 -m unittest discover -s tests -q
node --test tests/scorer.test.cjs tests/eval.test.cjs tests/router.test.cjs
node scripts/eval_scorer.cjs
python3 scripts/build_map.py --repo /Users/aibert/projects/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json --out artifacts/m3-map-smoke.json
python3 scripts/check_snapshot.py maps/quest-coder/map.json artifacts/m3-map-smoke.json
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/
node scripts/check_interactions.cjs
node scripts/smoke_scorer.cjs
node scripts/smoke_m3.cjs
```

- **104 Python tests pass** (99 existing + 2 inline-module regressions + 3 pinned
  parity tests); expected negative renderer test prints `FAIL missing top-level
  'layers'` while the suite exits 0.
- **46 JS tests pass** (40 existing + 6 routing tests), including cycles,
  unreachable/self/shortest ties, determinism under edge shuffling, purity,
  ignored realtime, unknown IDs, directions, real cross-layer files, mixed endpoints.
- Pinned map rebuild: **10/10 checks**; full committed/rebuilt parity ignoring only
  `meta.ref` and `meta.built_at`. All 290 nodes (18 layers, 272 files), 52 layer
  edges, 413 file edges, aliases and layer membership unchanged. `origin/main`
  still pointed to this snapshot at discovery; gates pin it anyway. Committed
  `map.json` is not rewritten. Known notes remain: 15 non-source targets excluded,
  one `/api/private-pack` fetch without a handler.
- Rendered artifact: `dist/quest-coder.html`, **291.6 KB** as reported by renderer.
- Legacy canvas: four screenshot states pass; zero page/console errors and
  external requests. Real-click focus, expansion, details, Escape, tests toggle,
  double-click, Back, wheel zoom and Fit pass.
- Shipped inlined scorer: **47/47 Node/Chromium outputs match** (numeric tolerance
  1e-12), distributions validated, Ask enabled, zero errors/external requests.
  Chromium p95 warm scoring **1.0000 ms**, 940 samples.
- M3 real typing + Enter/button clicks: **5/5 canonical states pass**, with exact
  operations, targets, selected node sets and route edges. Additional checks:
  unknown, ambiguous, stale clearing, explicit single override, reverse unreachable,
  cross-layer file route, inspect/Back, mixed endpoints, both explicit PATH
  overrides, invalid boundary rejection, and usable Ask at 1280×800. **Zero page
  errors, console errors, or non-file requests**. Query work (score + boundary
  validation + route/draw, excludes final answer-panel update/browser paint):
  5.0, 6.6, 3.7, 7.6, 4.9 ms respectively. These five observations are not a p95.

| Canonical query | Operation / chosen target | Route |
|---|---|---|
| where is magic link? | LOCATE / auth | target only |
| dependencies of pyodide | UPSTREAM / browser-run | browser-run → game-domain |
| what depends on runner service | DOWNSTREAM / runner-service | seven dependents, no dependencies |
| path from API routes to runner service | PATH / api, runner-service | api → runner-service |
| locate app/api/health/route.ts | LOCATE / exact file | opens api layer, target only |

## Screenshots and browser evidence

Under `/Users/aibert/projects/dag-gps/artifacts/`:

- `m3-locate.png`, `m3-dependencies.png`, `m3-dependents.png`, `m3-path.png`, `m3-file.png`
- `m3-no-path.png`, `m3-file-path.png`, `m3-1280.png`
- `m3-browser.json` records the actual canonical states, latency, checks and zero errors/requests.

Inspected all five canonical screenshots and the three additional states. No
obvious collisions/clipping; answer panel scrolls for long alternatives/details.
After inspection, global route boxes were changed from basenames to real paths,
exact-file Ask fits its full graph, and obsolete scorer text about deferred M3
traversal was clarified only in presentation. Final path/file screenshots were
re-inspected. Tests and all gates were rerun after code changes.

## Benchmark and limitations (unchanged)

The 47 cases are generated worker-draft regression fixtures, not user-approved or
held-out accuracy. Operation **46/47**, raw target top-1 **42/44**, top-3 **43/44**,
PATH endpoint top-1 **14/14**, abstention **11/47**, negatives abstained **10/10**,
false accepted negatives **0/10**. Node p95 warm scoring **1.7014 ms**, 940 samples.

Grading still incorrectly matches run-gateway rather than runner-service;
authentication still abstains (no stemming/synonym). No query-specific aliases
were added. See M2 report for benchmark provenance and limitations. The import
map is a pinned partial static architecture, not runtime reachability proof.
Large file dependency/dependent views can be dense; pan/zoom and full-ID details
remain available. Mixed endpoints remain unsupported. No unresolved blocker;
parent independent rerun/review is required before milestone acceptance/merge.
