# M2 — local scorer and evaluation

Verified locally on 2026-10-07 (PDT), based on M1 commit `d690283`, branch `m2-scorer`.
Quest-coder snapshot: `749d8b5` (290 existing candidates: 18 layers + 272 files).
No push, merge, hosted model, network hot path, or Ask wiring. M3 remains separate.

## API and contract

```js
const {createScorer, validateResult} = require('./web/scorer.js');
const scorer = createScorer(require('./maps/quest-coder/map.json'));
const result = scorer.score('what depends on runner service?');
validateResult(result, require('./maps/quest-coder/map.json'));
```

In a browser, load `web/scorer.js` and use `globalThis.DagGpsScorer.createScorer(map)`.
The UMD module has no dependencies, DOM access, external calls, or Node-only imports.
It is not yet included in the rendered page: M2 browser smoke injects it independently
and verifies that `#ask` remains disabled. `web/template.html` is unchanged.

- `operation`: `{choice, probabilities, confidence}` over LOCATE, UPSTREAM,
  DOWNSTREAM, PATH, NOT_SURE.
- `targets.locate_target`: same head over every existing map ID for single-target ops.
- PATH instead returns `targets.from_target` and `targets.to_target`, matched independently.
- Heads return `yes`, a reason, and `top3` candidates with IDs, probabilities, scores,
  and named scoring components. The result also returns `yes`, `reason`,
  `requestedOperation`, and `scoreKind`.
- `confidence` is precisely the probability assigned to the head's argmax.
  Every output is explicitly labelled **heuristic model score (not measured accuracy)**.
  These are normalized local weights, NOT trained or calibrated probabilities.
- NOT_SURE keeps speculative alternatives for review, including a deterministic
  map-order choice for uniform/no-evidence heads. **Do not act on targets when `yes` is false.**
- Validators reject unknown/missing/extra IDs, nonfinite/out-of-range probabilities,
  sums differing from 1 by more than 1e-9, non-argmax choices, inconsistent confidence,
  incompatible heads, and invalid alternative/acceptance metadata. `score()` validates
  its own output; malformed map tables or dangling edge endpoints fail construction.

## Scoring and intent

Build-map now preserves layer `aliases[]` phrases directly in map nodes (not only
flattened tokens). Regression tests verify persistence, copying, and unchanged IDs.
Each candidate is indexed by label, aliases, description, path and identity.
Tokens split camel case and punctuation; instruction stopwords are excluded from coverage.

Components (additive):

| Component | Exact / partial |
|---|---|
| Label | 8 for exact normalized phrase; otherwise 4 × query-token overlap |
| Alias | 9 for exact alias phrase; otherwise 4.5 × overlap |
| Description | 1.5 × overlap |
| Path | 14 for full literal path in query; otherwise 3 × overlap |
| Identity | 11 for exact normalized ID (literal file IDs also supported) |
| Structural | min(0.08, 0.015 × log(1 + incoming edges)); only with lexical evidence |

Overlap is the fraction of distinct query terms present in that field. Realtime
edges are ignored for structural prominence. The structural prior cannot produce
a lexical match, and is too weak to resolve an ambiguous tie into acceptance.
Target probabilities are softmax(score / 1.5) over all 290 IDs, including unmatched
candidates. Acceptance requires ≥4 raw lexical score, ≥0.6 query coverage, and ≥1
score margin over second place. These thresholds are heuristics, not accuracy estimates.
Operation weights are rule-based: 6 for the selected operation, 0 for other operations,
then the same softmax. A failed target head or malformed PATH selects NOT_SURE.

Intent separates **what depends on X / who uses X / dependents of X** (DOWNSTREAM,
reverse dependency edges) from **what does X depend on / dependencies of X / what
is X built on** (UPSTREAM, forward dependency edges). PATH parses `from A to B`,
`route between A and B`, or `how does A reach B`; it never uses one endpoint's
lexical evidence to fill the other. No route traversal/highlighting is performed
by the scorer; M3 must resolve selected IDs against the graph and handle no-path.

## Benchmark provenance and definitions

`eval/eval.jsonl` contains **47 generated worker-draft cases**, not Eric-approved
answers or user-ground-truth: 37 positive cases (including 7 PATH queries), and
10 negatives. Intent/target expectations were drafted before evaluation; routes
were inspected/computed against the actual committed graph. The reverse database→editor
case has `expected_route: null`: matching endpoints does NOT imply a route exists.
The evaluator checks every expected route against deterministic directed BFS,
ignoring realtime edges, and rejects invented targets/routes.

Distinct regression paraphrases are in `tests/scorer.test.cjs`, not benchmark rows.
The benchmark is small, generated from known aliases, and partly used during development:
**it is a regression benchmark, not a held-out generalization or user-accuracy claim.**
Two real shortcomings are retained rather than adding query-specific aliases to make
this fixture perfect. General fixes addressed filename/intent collision (`route.ts`)
and a short layer ID falsely dominating a longer alias (`hidden tests`).

Metrics include all rows for operation accuracy; raw top-1/top-3 include every
expected positive target head (30 single targets + 14 path endpoints = 44), even
abstained heads. Accepted-target top-1 is reported separately; it must not be confused
with unconditional accuracy. Negative cases have their own abstention/false-accept
metrics and per-kind breakdown. Warm latency excludes map construction, warms all
queries five times, then runs all 47 queries twenty times (940 samples); nearest-rank
p95 includes scoring and built-in contract validation, without trimming samples.

## Measured results

See `artifacts/m2-eval.json`, `artifacts/m2-browser.json`, and
`artifacts/m2-final-verification.json` for actual outputs (ignored generated artifacts).
Node `v26.7.0`, macOS; Chromium smoke uses installed sibling Playwright.

| Metric | Result |
|---|---|
| Operation accuracy | 46/47 = 97.87% |
| Positive-only operation accuracy | 36/37 = 97.30% |
| Target top-1, unconditional | 42/44 = 95.45% |
| Target top-3, unconditional | 43/44 = 97.73% |
| Target top-1, accepted heads only | 42/43 = 97.67% |
| Overall abstention | 11/47 = 23.40% |
| Positive abstention | 1/37 = 2.70% |
| Negative abstention | 10/10 = 100% |
| Negative false acceptance | 0/10 = 0% |
| PATH endpoint top-1 | 14/14 = 100% |
| PATH both endpoints + operation | 7/7 = 100% |
| Node p95 warm latency | 0.7754 ms (<10 ms target) |
| Chromium p95 warm latency | 0.7000 ms (<10 ms target) |

Negatives: empty/instruction-only 2/2 abstained, unknown 4/4, ambiguous 2/2,
missing endpoint 2/2. This is not evidence of safety on all unknown/ambiguous queries.

Retained errors:
1. **Where does grading live?** returns LOCATE/run-gateway instead of runner-service.
   The `grading request` alias outweighs the runner's description: an accepted wrong target.
2. **Where is authentication?** abstains: there is no stemming/synonym dictionary
   mapping `authentication` to `auth`. Its uniform target head picks app-shell, but
   `yes:false` ensures it is not an actionable fabricated match.

## Verification and reproduction

```bash
python3 scripts/build_map.py --repo /Users/aibert/projects/quest-coder --ref origin/main \
  --layers maps/quest-coder/layers.json --out maps/quest-coder/map.json
python3 -m unittest discover -s tests -q
node --test tests/scorer.test.cjs tests/eval.test.cjs
node scripts/eval_scorer.cjs
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/
node scripts/check_interactions.cjs
node scripts/smoke_scorer.cjs
```

For pinned reproduction, replace `origin/main` with `749d8b5`; rebuilding changes
`built_at`. Scorer/eval need only Node and the committed map, not quest-coder or
Playwright. Browser checks borrow Playwright from the same sibling checkout used by M1;
`PLAYWRIGHT_DIR` overrides it for canvas/scorer smoke (M1 real-click check retains its
existing hardcoded path). `.verify.json` mirrors all gates.

- Python: **99 pass** = existing 97 + 2 alias regressions. The printed `FAIL missing
  top-level layers` is expected output from an existing negative renderer test; suite exits 0.
- JS: **40 pass**, including deterministic heads, independent endpoints, unknown and
  ambiguous abstention, invalid-contract rejection, Node/VM compatibility, generated
  dataset checks and graph-route validation.
- Map: **10/10 checks**, same 290 candidate IDs, 52 layer edges and 413 file edges as M1.
- Existing canvas smoke: all four 1920×1080 screenshot states, zero page/console errors
  and external requests. Existing real-click interactions pass.
- Chromium scorer smoke: all 47 outputs match Node decisions/IDs/keys exactly;
  floating-point fields within 1e-12 (different V8/libm versions differ by a few ULPs),
  with all distributions independently validated; zero errors/requests; Ask disabled.

An initial exact-float browser parity assertion failed on sub-ULP math differences;
only numeric comparison tolerance was changed, not semantic assertions or scorer outputs.
Transient terminal/write-tool interruptions were recovered using direct subprocess execution;
no fabricated results or unresolved execution blocker remains.

## Scope / follow-up

M1 is preserved; `web/template.html`, renderer, canvas smoke, real-click script and
layer/file graph IDs/edges are unchanged. Only alias phrases and build timestamp were
added/updated in the map. No dependency installation, main merge or push occurred.
Parent independently reviews before declaring the milestone accepted. Eric still needs
to correct generated eval expectations and aliases. M3 may integrate this module, route
accepted IDs, explicitly handle unreachable endpoints, and display heuristic scores and
NOT_SURE alternatives without presenting them as calibrated confidence.
