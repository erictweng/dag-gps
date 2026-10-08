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
python3 scripts/build_map.py --repo /Users/aibert/projects/quest-coder --ref origin/main --layers maps/quest-coder/layers.json --out maps/quest-coder/map.json
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
python3 -m unittest discover -s tests -q
node --test tests/scorer.test.cjs tests/eval.test.cjs
node scripts/eval_scorer.cjs
node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/
node scripts/check_interactions.cjs
node scripts/smoke_scorer.cjs
```

M2's dependency-free module is `web/scorer.js` (CommonJS or `DagGpsScorer` browser
UMD global). Build-map retains layer alias phrases. The scorer returns operation
and target heads over observed IDs, rejects invalid distributions, and abstains
on insufficient/ambiguous evidence. It does not traverse routes or wire Ask (M3).
See `docs/M2_REPORT.md` for API, score interpretation, generated-eval provenance,
measured accuracy/latency, error analysis and reproduction details.
`eval/eval.jsonl` is worker-generated, not user-approved ground truth.
Browser smokes borrow installed Playwright; canvas/scorer accept `PLAYWRIGHT_DIR`.

## Deployment

TBD

## Risks

TBD
