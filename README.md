# DAG GPS

A System-1 navigator for codebases. Ask a short question, get an operation, a target, a heuristic score (not calibrated correctness), and a highlighted route on the architecture DAG in milliseconds. It runs fully offline in one HTML page.

The pattern is borrowed from [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast): an indexed table, an operation head plus per-operation target heads, and probabilities plus confidence. Here it is implemented locally.

## Offline Ask (M3)

```bash
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
open dist/quest-coder.html
```

Type a question and press Enter or click **Ask**. Examples: `where is magic link?`,
`dependencies of pyodide`, `what depends on runner service`,
`path from API routes to runner service`, `locate app/api/health/route.ts`.
No server, CDN, model API or network requests. The generated HTML needs no companion files.

Edges point **consumer → dependency**. Dependencies follow edges, Dependents reverse
them, PATH is shortest directed BFS ignoring realtime. Matching endpoints does not
guarantee a route. Mixed layer/file endpoints are explicitly unsupported. File routes
use a global real-ID view; click to inspect, Back to layers. NOT_SURE does not act;
click an alternative to override explicitly (both endpoints for an abstained PATH).
Heuristic bars/weights are not measured accuracy. Grading/authentication still have
the documented M2 errors; generated eval cases are regression fixtures, not ground truth.

Verification: `.verify.json`; report/commands/screenshots: `docs/M3_REPORT.md`.
Browser checks borrow sibling Playwright, overridable with `PLAYWRIGHT_DIR`
(canvas, scorer, M3 smoke). No runtime dependencies beyond Python stdlib / Node.

- Plan: `docs/PLAN.md`
- Idea capture: `docs/IDEA.md`
- First map: `maps/quest-coder/layers.json` (draft, awaiting Eric's corrections)
- Map check:
  `python3 scripts/check_layers.py maps/quest-coder/layers.json <quest-coder-repo> origin/main <import_graph.json> maps/quest-coder/layers.mmd`
