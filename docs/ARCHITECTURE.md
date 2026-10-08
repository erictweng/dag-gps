# Architecture — DAG GPS

## Overview

TBD

## Components

TBD

## Data Flow

TBD

## Storage

TBD

## External APIs

TBD

## Build / Test Commands

Document the canonical commands here and mirror them in `.verify.json`.

```bash
python3 scripts/build_map.py --repo /Users/aibert/projects/quest-coder --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 --layers maps/quest-coder/layers.json --out artifacts/m3-map-smoke.json
python3 scripts/check_snapshot.py maps/quest-coder/map.json artifacts/m3-map-smoke.json
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
python3 -m unittest discover -s tests -q
node --test tests/scorer.test.cjs tests/eval.test.cjs tests/router.test.cjs
node scripts/eval_scorer.cjs
node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/
node scripts/check_interactions.cjs
node scripts/smoke_scorer.cjs
node scripts/smoke_m3.cjs
```

M2's dependency-free module is `web/scorer.js` (CommonJS or `DagGpsScorer` browser
UMD global). Build-map retains layer alias phrases. The scorer returns operation
and target heads over observed IDs, rejects invalid distributions, and abstains
on insufficient/ambiguous evidence. M3 inlines it with `web/router.js` into the
standalone page. Ask validates outputs again before action. The router is pure,
directed BFS with lexical ties, follows consumer → dependency edges, excludes
realtime, and never invents edges. Layer/file endpoints are routed separately;
mixed endpoints have an explicit unsupported no-route outcome. Real-ID global
file route views preserve cross-layer inspectability. See `docs/M3_REPORT.md`.
See `docs/M2_REPORT.md` for API, score interpretation, generated-eval provenance,
measured accuracy/latency, error analysis and reproduction details.
`eval/eval.jsonl` is worker-generated, not user-approved ground truth.
Browser smokes borrow installed Playwright; canvas/scorer/M3 accept `PLAYWRIGHT_DIR`.
Pinned rebuilds are compared to the committed map (only ref/time ignored), avoiding
silent layer remaps when origin/main advances. Render uses safely encoded trusted
module strings and map JSON, with no network. Strict hosted CSP is not configured.

## Deployment

TBD

## Risks

TBD
