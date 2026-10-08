# DAG GPS

A local, offline codebase navigator: ask a short architecture question or name a file,
get an evidence-first answer and a highlighted route on the architecture DAG.
Runs in one standalone HTML page, with no model API or network hot path.

The indexed-table, operation-head and per-target-head pattern is borrowed from
[browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast). Validated
normalized distributions remain available, but are not correctness probabilities.

## v1 foundation and release contract

Eric approved V1.0 only. Baseline worker verification passes; parent independent
acceptance/integration is pending. V1.1a impact analysis is **not started**, and
v1 release requires Eric's unaided real repository session, not just automated gates.

- [Approved v1 milestone plan](.hermes/plans/2026-10-07_203500-v1-milestones.md)
- [Locked acceptance contract and evidence owners](docs/V1_ACCEPTANCE.md)
- [Supported-source matrix / extraction limits](docs/SUPPORTED_SOURCES.md)
- [Fresh baseline report](docs/V1_BASELINE_REPORT.md) and [fixture provenance](docs/V1_FIXTURES.json)
- [Current status](STATUS.md), [tasks](TASKS.md), [authorized delivery workflow](docs/WORKFLOW.md)

V1.0 reran unchanged `.verify.json` build/test/smoke: 138 Python + 93 JS tests,
all exit 0. Evidence is local/ignored under `artifacts/v1-baseline/`; earlier
sections below describe integrated pre-v1 functionality, not a complete v1 release.
Desktop-first offline/local, optional query capture off by default, no execution
tracing, and human-reviewed onboarding are locked defaults, not newly shipped features.

## Architecture-guided tours

```bash
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html \
  --tours maps/quest-coder/tours.json --repo /Users/aibert/projects/quest-coder
open dist/quest-coder.html
```

Choose **Run basic**, **Submit**, or **Sign in** in Tours, or Ask
`walk me through submitting code`. Previous/Next/Reset/Exit step through brief
input/output boundaries and actual offline line-numbered source evidence. Overview
can highlight involved layers; Locate real file inspects a node, not a local editor.
Arrow keys step and Escape exits outside typing/modal contexts.

Tours audit quest-coder **749d8b5de490cc2e6a0c98c713fab3ab856da799** from immutable
source, not the mutable checkout. **Import paths are not execution traces**: separately
styled directed tour links carry HTTP, spawn/message or data-flow evidence; normal
imports and Ask stay unchanged. Run basic is advisory; Submit returns its runner result
to the API before progress writes, but responds to the browser after writes/reread.
Google is the shipped Supabase sign-in UI; email OTP routes remain an API alternative.
Supabase vs local SQLite and party reward branches are disclosed, not stitched into
one false execution sequence. No live application execution or calibrated confidence claim.

Optional `--tours PATH` also works with `scripts/build_project.py`. Repository, exact
commit, node IDs, paths, evidence bounds and typed links validate before publishing;
stale/invalid tours preserve previous artifacts. Tour data is per repo, not hardcoded
into runtime. Omitting it gives an honest **No curated tours available**, as in the
self demo. Supporting excerpts are inline, safely escaped; optional GitHub links
point to the exact audited SHA. Full schema, commands and limits: **docs/TOURS_REPORT.md**.

Verification: **138 Python + 93 JS tests**, all legacy gates plus **29 tour UI checks**,
18 steps and every citation exercised with real clicks/typing, zero errors/requests.
Eleven tour screenshots under `artifacts/tour-*.png`; gates in `.verify.json`.

## Reusable pinned maps + safe refresh

```bash
python3 scripts/build_project.py --repo . \
  --ref f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93 \
  --layers maps/dag-gps/layers.json --out-dir dist/dag-gps
open dist/dag-gps/index.html
```

One command produces **map.json + standalone offline index.html + diff.json + report.json**.
Use any local Git repository and reviewed layer spec. It resolves the ref to a commit
and extracts **git archive**, not the mutable worktree. Source discovery is generic;
`--tops` chooses explicit extraction scope without reducing assignment coverage.
Origin determines repository identity (canonical local fallback); no fixed project URLs.

`--previous-map PATH` compares with an explicit baseline; otherwise an existing output
map is used. Diffs list added/deleted files/layers, added/removed typed connections,
node changes and before/after layer assignments, with a visible HTML summary. Initial
builds are labeled, not presented as upstream changes. All outputs are staged/checked
before promotion; failed mapping/extraction/render checks preserve previous outputs.
Caught promotion errors roll back; per-file replace is not a crash-safe cross-file
transaction. Use one writer and open after success.

HTML distinguishes **audited source commit/ref**, build time and **verified local HEAD
at build time**. It cannot detect live remote freshness offline. Rebuilds keep the same
alias namespace: surviving exact IDs persist, deleted IDs stay ORPHAN, never rebound.
file:// storage portability remains best-effort; visible Export/Import JSON is the fallback.

Self demo: 3 layers / 27 files / 3 layer connections / 19 file connections at `f92d0cf`.
Ask `locate scripts/build_map.py` or `dependencies of Regression tests`. Layer draft:
`maps/dag-gps/layers.json`. Quest-coder's frozen scope must be explicit; both commands,
extractor limitations and atomicity guarantees: **docs/REFRESH_REPORT.md**. Neither a
source graph nor a successful build proves every dynamic dependency was extracted.

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

- Commands: `.verify.json`; current baseline: `docs/V1_BASELINE_REPORT.md`;
  integrated feature history: `docs/REFRESH_REPORT.md`, `docs/TOURS_REPORT.md`, `docs/ALIAS_LEARNING_REPORT.md`.
- Filename lookup history: `docs/LOOKUP_REPORT.md`; M3 routing: `docs/M3_REPORT.md`;
  scorer provenance: `docs/M2_REPORT.md`.
- 138 Python + 93 JS tests (15 tour fixtures + 5 controller tests, 17 refresh fixtures, 15 alias tests);
  tours 29 UI checks, refresh 7 UI checks, legacy M3 5 canonical + 11 extra
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
preserves the frozen quest-coder map and routing/scoring behavior; reusable refresh adds a separate self-repo layer draft.
