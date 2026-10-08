# DAG GPS

A local, offline codebase navigator: ask a short architecture question or name a file,
get an evidence-first answer and a highlighted route on the architecture DAG.
Runs in one standalone HTML page, with no model API or network hot path.

The indexed-table, operation-head and per-target-head pattern is borrowed from
[browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast). Validated
normalized distributions remain available, but are not correctness probabilities.

## Offline Ask — filename lookup + evidence labels

```bash
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html
open dist/quest-coder.html
```

Type a question and press Enter or click **Ask**:

- Architecture: `where is magic link?`, `where does grading live?`,
  `where is authentication?`, `dependencies of pyodide`.
- File: `locate app/api/health/route.ts`, `quest_runner.py`, `quest_runner`,
  `file bounded_sub`.
- Route: `path from API routes to runner service`,
  `path from app/api/friends/route.ts to friends-store`.

File lookup prefers **exact path → exact basename → extensionless stem → filename
token/partial → conservative spelling suggestions**. Architecture lookup uses
layer labels, aliases and responsibility descriptions, while explicit filenames
and paths resolve real file nodes. If a bare name is also an architecture alias,
use `file NAME` to make file intent explicit.

The pinned map has **no `runner.py`**. Asking for it says **No exact file named
runner.py**, offers real full paths (`runner/quest_runner.py` and
`runner/quest_runner_cli.py`), and does not act until you click an **Override**.
Typos are suggestion-only. Duplicate basenames such as `route.ts` show every
matching full path and require your choice. Unknown queries without evidence
show **No match**, with no arbitrary override buttons. Nothing is learned or saved.

Answers say **Exact match / Likely match / Needs your choice / No match** based
on evidence, coverage and runner-up separation, never a softmax percentage.
Reasons, full paths and aliases are visible; **Details** exposes uncalibrated
raw scores and normalized weights. Morphology-normalized architecture matches
(e.g. grading/grader and authentication/auth) are labeled Likely, not literal Exact.

Edges point **consumer → dependency**. Dependencies follow edges; Dependents
reverse them. PATH is shortest directed BFS ignoring realtime. Matched endpoints
do not guarantee a route. Mixed layer/file endpoints are explicitly unsupported.
File routes use real IDs across layers; click to inspect and Back to layers.
NOT_SURE clears prior highlights and never acts on speculative IDs; an abstained
PATH requires supported explicit overrides for both endpoints.

## Verification and limits

- Commands: `.verify.json`; current report: `docs/LOOKUP_REPORT.md`.
- M3 routing history: `docs/M3_REPORT.md`; scorer provenance: `docs/M2_REPORT.md`.
- 104 Python + 73 JS tests; legacy M3 5 canonical + 11 extra browser checks,
  lookup 19 UI checks, and shipped scorer parity for both datasets.
- The unchanged 47-case generated regression now has operation 47/47, target
  top-1 44/44. The separate 40-case lookup challenge has operation/label 39/40,
  target top-1 16/17, and no false accepted negatives (0/24). The bearer-auth
  responsibility case remains an honest abstention, not a confident wrong answer.
- Both datasets are **worker-draft regression/challenge cases, not held-out or
  user-approved accuracy**. Eric still needs to review map and expectations.
- Browser checks borrow sibling Playwright (`PLAYWRIGHT_DIR` override). Runtime
  needs no server, CDN or companion files; build uses Python stdlib and tests use Node.

Plan: `docs/PLAN.md`; idea capture: `docs/IDEA.md`. The layer map remains
`maps/quest-coder/layers.json` (draft, awaiting Eric's corrections). This milestone
does not change map membership, graph routing, pan/zoom or legacy interactions.
