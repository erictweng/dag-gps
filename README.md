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
show **No match**, with no arbitrary override buttons. Override alone never learns;
remembering a name requires separate review and confirmation.

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

## Explicit learned names

After selecting an **Override**, the page offers **Remember this name for this node?**.
Enter a specific alias, click **Review name…**, inspect the exact text and real target
path/layer, then **Confirm remember**. Cancel, typing, asking, and override alone
never save anything. NOT_SURE without a supported explicit choice cannot learn.
PATH learning is deliberately disabled: ask about a single endpoint separately
rather than remembering the entire route question.

**Manage learned aliases** lets you inspect and remove names, clear all with an
explicit confirmation, download JSON, and import a user-selected JSON file.
Import fully validates first and previews the resulting names, conflicts and
orphan count; **Merge** is the default, **Replace all** must be selected explicitly.
Confirm applies the preview; invalid imports apply nothing. Duplicate bindings
are idempotent. Conflicting normalized names require a target choice, never silent
overwrite. Deleted/unknown IDs remain visible as quarantined orphans; no guessing.

The version-1 schema is `{version: 1, repo: "erictweng/quest-coder", aliases:
[{alias: "Python judge", nodeId: "runner-service"}]}`. Limits: 256 KiB UTF-8,
1,000 entries, 1–160 alias characters with no controls. Do not store secrets.
Learned overlays do not change the generated map or its built-in aliases.
Exact literal filenames/paths take precedence, including ambiguous basenames.
Matching uses exact endpoint names (case/whitespace-insensitive), not fuzzy learning.

Storage is namespaced by repository and schema version, **not commit**, so a rebuild
of the same repository can retain names. `file://` localStorage is **browser-dependent
and best-effort**: this does not promise portability across file paths or browsers.
Use export/import for backup and transfer. Denied/quota storage reports **Unsaved**;
names remain usable for this session and exportable, but persistence is not claimed.
There is no server, model training, automatic alias generation or network learning.

## Verification and limits

- Commands: `.verify.json`; current report: `docs/ALIAS_LEARNING_REPORT.md`.
- Filename lookup history: `docs/LOOKUP_REPORT.md`; M3 routing: `docs/M3_REPORT.md`;
  scorer provenance: `docs/M2_REPORT.md`.
- 106 Python + 87 JS tests (14 new alias tests); legacy M3 5 canonical + 11 extra
  browser checks, lookup 19 UI checks, alias 19 UI checks, and shipped scorer parity.
- Synthetic alias regression: 15/15, zero wrong accepts or false accepts on negative requests.
  `Python judge` already matched runner-service before this milestone; the harder
  synthetic `Python judge station` demonstrates abstention → opt-in correction → match.
  These are worker regression examples, not user evidence.
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
