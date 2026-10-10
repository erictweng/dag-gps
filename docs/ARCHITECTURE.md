# Architecture — DAG GPS

## Overview

Pinned Git archive → validated static map/evidence → single offline HTML navigator.
Local operation/target scorer and directed graph APIs; no trained model or network hot path.

## Components

Python stdlib scripts discover/extract/assign/validate/build, compile exact-source tours,
and draft/review layer specs. Dependency-free JS modules handle scoring, routing, impact,
trust, aliases, tours, onboarding and opt-in query feedback; template embeds trusted modules.

## Data Flow

Resolve a Git ref once, archive its immutable commit, preserve static typed file evidence,
roll up reviewed ownership, validate/stage all outputs, then per-file publish with caught-error
rollback. Browser edits download JSON; builders revalidate before publishing. No live source scan.

## Storage

Maps/layers/tours are local files. Browser repo/version-scoped aliases and consented
feedback use best-effort localStorage with explicit export/import recovery; feedback OFF
on reload. No accounts, automatic cross-tab sync or cross-browser file-origin guarantee.

## External APIs

None required by the browser runtime. Extracted HTTP/RPC links describe static potential
boundaries, not calls made by the navigator. Optional pinned source links require user navigation.

## Build / Test Commands

Document the canonical commands here and mirror them in `.verify.json`.

```sh
# Full recipes plus release checks; pinned private quest archive required.
python3 scripts/release_check.py --quest-repo /path/to/quest-coder
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
# Standalone render with verified pinned tour excerpts:
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html \
  --tours maps/quest-coder/tours.json --repo /path/to/quest-coder
```

The runner reads all non-null legacy recipes plus separate release_commands in
`.verify.json`, records actual outputs and fails closed. Browser QA tool setup,
generic-repo draft/edit/download/build CLI and pin/scope handling: `V1_RELEASE.md`.

M2's dependency-free module is `web/scorer.js` (CommonJS or `DagGpsScorer` browser
UMD global). Build-map retains layer alias phrases. The scorer returns operation
and target heads over observed IDs, rejects invalid distributions, and abstains
on insufficient/ambiguous evidence. M3 inlines it with `web/router.js` into the
standalone page. Ask validates outputs again before action. The router is pure,
directed BFS with lexical ties, follows consumer → dependency edges, excludes
realtime, and never invents edges. Layer/file endpoints are routed separately;
mixed endpoints have an explicit unsupported no-route outcome. Real-ID global
file route views preserve cross-layer inspectability. See `docs/M3_REPORT.md`.
The lookup milestone adds file-first evidence tiers, full-path duplicate choices,
suggestion-only missing names/typos, and Exact/Likely/Needs-choice/No-match labels
independent of normalized weights. Additive evidence metadata preserves legacy
validated heads; no-evidence alternatives are not actionable. See
`docs/LOOKUP_REPORT.md` for the separate challenge benchmark and actual gates.
See `docs/M2_REPORT.md` for API, score interpretation, generated-eval provenance,
measured accuracy/latency, error analysis and reproduction details.
`eval/eval.jsonl` is worker-generated, not user-approved ground truth.
Browser smokes borrow installed Playwright; canvas/scorer/M3 accept `PLAYWRIGHT_DIR`.
Pinned rebuilds are compared to the committed map (only ref/time ignored), avoiding
silent layer remaps when origin/main advances. Render uses safely encoded trusted
module strings and map JSON, with no network. Strict hosted CSP is not configured.

## Deployment

Open generated HTML directly from file://. Candidate bundle and exact hashes/pins:
`dist/release/v1.0.0-rc.1/manifest.json`; reproduction/privacy/setup in `docs/V1_RELEASE.md`.
Private excerpts require sharing review; strict hosted CSP may need adaptation for trusted
inline dynamic module execution. No public deployment/upload is part of this release.

## Risks

Static parser/declared-scope gaps, unknown runtime/coverage, stale evidence rejection,
manual semantic/reference review, browser storage portability and per-file (not crash-safe
cross-file) publication. Phone support is inspection, not authoring parity. Human release
acceptance is pending. See V1_ACCEPTANCE.md and SUPPORTED_SOURCES.md.
