# DAG GPS

A local, offline codebase navigator: ask a short architecture question or name a file,
get an evidence-first answer and a highlighted route on the architecture DAG.
Runs in one standalone HTML page, with no model API or network hot path.

The indexed-table, operation-head and per-target-head pattern is borrowed from
[browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast). Validated
normalized distributions remain available, but are not correctness probabilities.

## v1 foundation and release contract

V1.0 was parent-accepted on main `6bfc5ee`; full V1.1 impact is integrated at `7bc6769`.
Full **V1.2 trust / narrow extraction / stale-tour safety** is integrated on main
`a5b0255`. Full **V1.3 reviewable onboarding** is integrated at `c6543f6`; Eric
semantic review remains pending. Eric authorized full **V1.4 opt-in query feedback /
evaluation**, worker-verified on `v1-feedback`; parent independent review pending. v1 release still requires later gates and Eric's unaided real repository
session, not just automated tests.

- [Approved v1 milestone plan](.hermes/plans/2026-10-07_203500-v1-milestones.md)
- [Locked acceptance contract and evidence owners](docs/V1_ACCEPTANCE.md)
- [Supported-source matrix / extraction limits](docs/SUPPORTED_SOURCES.md)
- [Fresh baseline report](docs/V1_BASELINE_REPORT.md) and [fixture provenance](docs/V1_FIXTURES.json)
- [Current status](STATUS.md), [tasks](TASKS.md), [authorized delivery workflow](docs/WORKFLOW.md)

V1.0 reran unchanged `.verify.json` build/test/smoke: 138 Python + 93 JS tests,
all exit 0. Evidence is local/ignored under `artifacts/v1-baseline/`; earlier
sections below describe integrated pre-v1 functionality, not a complete v1 release.
Desktop-first offline/local, optional query capture off by default, no execution
tracing, and human-reviewed onboarding are locked defaults. Onboarding is implemented
in V1.3 below; optional V1.4 query capture/evaluation is implemented below.

## Opt-in query feedback and evaluation (V1.4)

Open **Query feedback** in the navigator sidebar. It starts **OFF** on every load;
choose real user queries or generated fixture provenance, then explicitly enable local
recording. A persistent header badge says Recording locally. Subsequent ordinary Ask
answers are captured; tours/impact are explicitly excluded with their reason.

Open a record: choose Correct / Wrong / Unclear, review/edit expected operation and real
node IDs (PATH has independent from/to and optional directed route truth), designate
Development or Held-out **before the first label**, then confirm. Wrong can retain
unknown intent; Unclear is never NOT_SURE truth. Held-out labels and designated splits
are frozen. **Labels do not teach aliases**; alias confirmation is separate.

Disable stops recording; remove one or confirm Clear all. Export JSON for backup;
import is a ≤2 MiB inert preview and explicitly consented replacement. Same-repo stale
snapshots remain ineligible, never remapped; foreign repo/version/unknown current IDs
reject. Retention: newest 200 / 90 days (pruned on enable/write), oldest-byte eviction
at 2 MiB. Denied/quota storage shows Unsaved/session-only; export before closing.
`file://` storage is best-effort. Queries/answers/corrections/source metadata/alias overlay
remain local only, without telemetry; review private exports before sharing.

```sh
node scripts/eval_user_queries.cjs maps/quest-coder/map.json \
  /path/to/dag-gps-query-feedback-v1.json artifacts/my-user-eval.json
# No dataset: honest empty collection report, not invented accuracy
node scripts/eval_user_queries.cjs
node scripts/smoke_feedback.cjs
```

Evaluation requires the matching full source pin, canonical map SHA and scorer source
SHA; reports original / alias-off / saved alias-on, user vs generated and development
vs held-out separately. Counts, operation/target top1/top3, accepted wrong targets,
unnecessary abstention, independently checked directed no-path truth (no realtime),
and **warm scorer-only p95**, not UI time. No labeled user cases yet; ≥20 confirmed
Eric cases is a soft collection goal. Existing actual runner.py feedback has unconfirmed
intent. No scorer tuning on synthetic cases; real-user improvement is deferred.

[USER_EVAL_REPORT](docs/USER_EVAL_REPORT.md): 176 Python / 150 JS, all full gates,
20 feedback unit/eval tests; 18 real-browser checks / 6 inspected screenshots. Actual
browser export is explicitly generated, not Eric ground truth. Parent review and V1.5 /
Eric's unaided acceptance remain pending.

## Reviewable project onboarding (V1.3)

```sh
python3 scripts/draft_layers.py --repo /path/to/repo --ref <immutable-commit> \
  --out artifacts/my-layer-draft.json
python3 scripts/render_layer_editor.py --draft artifacts/my-layer-draft.json \
  --out dist/my-layer-editor.html
open dist/my-layer-editor.html
```

Folder proposals cover the pinned tracked inventory, including flat roots and helper
folders, with explicit ownership reasons; **not automatic architectural truth**.
In the offline editor: search real paths, rename labels (stable IDs), select files and
move/split, select layers and merge, delete/undo/reset, save/resume draft. Findings show
unmapped/double ownership, empty layers, unresolved imports and real layer-cycle file
pairs. Split/merge/delete warn about manual alias/tour review; no automatic rebinding.
Review meaning and migration warnings, explicitly confirm, and **download layers.json**.
Then run the builder command shown, with the same full pin and `--tops` scope:

```sh
python3 scripts/build_project.py --repo /path/to/repo --ref <same-commit> \
  --layers /path/to/downloaded/layers.json --tops <scope-shown-by-editor> \
  --without-tours --out-dir dist/my-reviewed-map
```

The browser cannot edit repo files. A draft is not publishable; reviewed exports carry
an explicit confirmation marker, exact per-file ownership, source inventory and scope.
Builder validates them before publication and preserves prior outputs on failure.
Legacy hand-authored glob specs remain compatible. New grouping IDs do not silently
attach existing tours/aliases; use a separate output and reconcile references manually.
Imports ≤8 MiB stay data; wrong repo/commit/scope/evidence rejects unchanged.

**176 Python / 130 JS tests**, all legacy build/test/smoke gates plus **14 onboarding
browser checks / 10 inspected 1280/1920 screenshots**, zero errors/external requests.
Actual browser downloads built both real demos: quest `749d8b5` (**272 files / 38 folder
layers / 415 file links**) and newer self `a5b0255` (**48 files / 3 layers / 38 links**).
A real quest runner-client split exposes a cycle; actual merge fixes grouping without
stripping file links. Existing approved quest map/tours and old self `f92d0cf` stay intact.

Open `dist/onboarding-{dag-gps,quest}.html` (editors), or
`dist/onboarding-{dag-gps,quest}/index.html` (exported builds), generated by
`node scripts/smoke_onboarding.cjs`. **Worker samples are not Eric-approved architecture**;
Eric semantic review remains mandatory. Self full discovery correctly blocks on a
runtime-generated JSON fixture absent from the archive; its supported demo explicitly
scans 47/48 files, retaining all 48 assignments and one disclosed unscanned generator
consumer. The blocked draft remains inspectable at `dist/onboarding-dag-gps-all-source.html`.
Schemas, exact evidence/scope/counts, reproduction and limits:
[ONBOARDING_REPORT.md](docs/ONBOARDING_REPORT.md).


## Potential change impact (V1.1)

Inspect a real file and click **Inspect potential impact**, or Ask
`what could be affected if I change lib/runner-client.ts?` / `impact of runner/quest_runner.py`.
Direct/transitive consumers use reverse **import-only** evidence. Linked tests are
observed import reachability, never coverage proof; **coverage unknown** even with
links. Exact tour citations and transitive HTTP/RPC boundary witnesses are separate
sections. Realtime excluded. “Potentially affected” does not mean “will break”.
Ambiguous/missing files require explicit choice; unknowns clear stale highlights.
Click a result for its shortest typed chain and real-node inspection; Return to impact
graph preserves recovery after inspection/tour evidence. `what depends on …` retains
legacy DOWNSTREAM behavior. No filesystem-opening or runtime/coverage claim.

Open rebuilt `dist/quest-refresh/index.html` or `dist/quest-coder.html`; old pinned
self graph `dist/dag-gps/index.html` honestly has no tours. Historical V1.1 gates: **138 Python +
103 JS**, **14 impact browser checks / 9 screenshots**, zero errors/external requests;
all legacy gates/evals retained. [Impact API, path classification, semantics, source
audit and actual evidence](docs/IMPACT_REPORT.md). V1.2's source-backed extraction migration is documented below.

## Map trust and completeness (V1.2)

**Map trust** shows the pinned source SHA, extraction version and exact scope:
quest **182 / 272 files scanned**, 90 unscanned; self **27 / 27** at its old pin.
These are inventory/file counts, **not runtime completeness**. Filter concrete
findings by category/path and click **Locate source file**. File/Ask/impact warnings
show relevant findings when traceable, otherwise clearly repository-level uncertainty.
Resolved static imports/loaders, curated source-supported tours and inferred/unverified
literal HTTP/RPC/manual links remain distinct. External packages are not local errors.

Static package-relative Python imports and concrete submodules now resolve without
suffix guessing. Narrow whitespace CommonJS/TS and indented side-effect import cases
are supported; dynamic constructs, conditional/unmodeled search paths and parser
limitations remain explicit. Source cycles/self edges are retained; layer cycles still
require review, never deletion of true edges.

Same source pins, deliberate version-2 extraction migration: quest **413 → 415** file
links; self **19 → 20**. No pairs removed or source/layer membership edits. Current
grading-engine impact: 16 direct consumers / 12 import-linked tests, coverage unknown.
Exact source lines, diagnostic counts, fixture/parity rationale and CLI safety:
[TRUST_REPORT.md](docs/TRUST_REPORT.md). **161 Python + 109 JS**, all build/test/smoke
recipes pass; new trust browser **10 checks / 13 inspected screenshots**, zero
page/console errors or external requests, legacy gates retained.

Stale tours still reject with prior outputs preserved. To refresh deliberately
without their evidence, replace `--tours PATH` with **`--without-tours`**:

```bash
python3 scripts/build_project.py --repo /Users/aibert/projects/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json \
  --tops app components lib proxy.ts scripts browser-runtime runner \
  --without-tours --out-dir dist/quest-no-tours
```

Both tour flags together reject; malformed input is never a silent opt-out. An
existing tour build (including legacy HTML) cannot silently lose evidence by omitting
flags or changing the comparison map. The omitted page displays its reason and has
no old tour data/query resolver. Standalone render supports the same explicit flag.

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
into runtime. First builds without reviewed tours show **No curated tours available**,
as in the self demo. Existing attached tours require explicit `--without-tours` to
omit; the exact reason is shown. Supporting excerpts are inline, safely escaped; optional GitHub links
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

Self demo: 3 layers / 27 files / 3 layer connections / 20 file connections at `f92d0cf` (V2 extraction).
Ask `locate scripts/build_map.py` or `dependencies of Regression tests`. Layer draft:
`maps/dag-gps/layers.json`. Quest-coder's frozen scope must be explicit; both commands,
extractor limitations and atomicity guarantees: **docs/REFRESH_REPORT.md**. Neither a
source graph nor a successful build proves every dynamic dependency was extracted.

## Offline Ask — filename lookup + evidence labels

```bash
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html --without-tours
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

- Commands: `.verify.json`; current trust evidence: `docs/TRUST_REPORT.md`; historical baseline: `docs/V1_BASELINE_REPORT.md`;
  integrated feature history: `docs/REFRESH_REPORT.md`, `docs/TOURS_REPORT.md`, `docs/ALIAS_LEARNING_REPORT.md`.
- Filename lookup history: `docs/LOOKUP_REPORT.md`; M3 routing: `docs/M3_REPORT.md`;
  scorer provenance: `docs/M2_REPORT.md`.
- Historical pre-impact/trust: 138 Python + 93 JS tests (15 tour fixtures + 5 controller tests, 17 refresh fixtures, 15 alias tests);
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
preserves frozen source pins, node membership and routing/scoring behavior; V1.2's
deliberate extractor migration adds only audited links/provenance. Reusable refresh adds a separate self-repo layer draft.
