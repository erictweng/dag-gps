# Reusable maps and safe refresh — local verification

2026-10-07 PDT. Worker branch `reusable-refresh`, based on `f92d0cf`.
Parent independently verifies and integrates; worker does not merge or push.

## Deliverables

`python3 scripts/build_project.py --repo REPO --ref REF --layers LAYERS --out-dir OUTPUT`
produces `map.json`, standalone offline `index.html`, deterministic `diff.json`, and
`report.json` in one command. `--previous-map` chooses a baseline; otherwise an
existing output `map.json` is the baseline. Without one, the diff explicitly says
`initial_build` (additions are not represented as a discovered upstream change).

The requested ref is resolved to a full commit before **git archive** extraction.
No mutable source worktree is read. Metadata records requested ref, exact audited
`snapshot_commit`, UTC `built_at`, and verified local source `HEAD` at build time.
The latter is not a network fetch, current remote tip, or offline freshness claim.
Quest-coder's local HEAD is `a035ea2161b94323f474cf47908476c13f3285e4`, while its audited
snapshot is the deliberately pinned `749d8b5de490cc2e6a0c98c713fab3ab856da799`.
No quest-coder files, refs, layers, or committed map were changed.

Diffs compare node IDs/metadata excluding volatile indices and build timestamps;
include added/deleted files and layers, added/removed **typed** connections with
layer/file scope, node metadata changes, and explicit before/after layer assignments.
Connection identity is scope/from/to/type; edge weight/sample changes alone are not
added/removed connections. Full details are machine-readable, with a visible HTML
summary and provenance disclosure. Expanding provenance refits the existing canvas.

Identity comes from actual origin, normalizing common GitHub SSH/HTTPS spellings;
without a usable network-style origin it is `local:` plus canonical repository path.
A layer spec cannot override identity. Alias storage retains the same repository
namespace across commits, not snapshot SHA or output filename. Exact surviving IDs
are retained; deleted IDs are visible ORPHANs excluded from scoring, never rebound.
Loaded-alias status now states the actual count rather than saying no names saved.
`file://` localStorage remains browser/path-dependent best effort; visible export/import
is the portable backup/transfer fallback, not an automatic storage guarantee.

## Safety boundaries

All four artifacts are staged together on the output filesystem, checks run before
promotion, JSON is reloaded, and HTML is rendered from the staged map. Validation,
extraction, unmapped, duplicate-assignment, cycle, or render failures leave previous
published artifacts byte-identical. `build_map.py` itself now also validates a private
candidate before replacing its destination, retaining its legacy successful JSON shape.
Unmapped files and duplicate assignments are rejected, never guessed. Local unresolved
imports reject the refresh; diagnostic arrays and checks are printed in full. Unsupported
constructs and non-source/HTTP/RPC targets are explicit findings, not silently invented edges.

Promotion uses atomic **per-file** replace and restores previous bytes on caught errors.
Tests inject an error during promotion and verify all previous bytes. This is not a
cross-file filesystem transaction: concurrent readers can see an intermediate generation,
and hard kill/power loss is not covered. Use one writer and open artifacts after success.
If storage also prevents rollback, the error explicitly says rollback incomplete; no false
preservation claim. No watch, deploy, network browser dependency, or source auto-remapping.

## Extraction scope and honest limitations

- Generic default discovers tracked TS/TSX/JS/JSX/MJS/CJS/Python/SQL source files.
  `--tops` provides explicit JS/TS scope; Python and migration SQL retain the extractor's
  repository-wide scan. Assignment coverage still checks **all included source files**.
  Actual scope is recorded in metadata. Source/import scans exclude `.git`, node_modules,
  vendor, virtualenv/cache, dist/artifacts/build/.next directories. This is path-based,
  not detection of every individually generated file inside otherwise valid folders.
- Static CommonJS literal `require()` and UMD-wrapped requires are now detected, including
  `.cjs`; comments and quoted fixture strings cannot invent JS imports. Python AST scanning
  handles multiline and local-script imports without interpreting fixture strings as code.
  Ambiguous local Python matches fail, rather than choosing the first suffix.
- This is a narrow lexical JS extractor, **not a full JS parser**. Regex literals and template
  interpolation are not modeled. Nonliteral require/import, relative Python imports and
  dynamic Python imports are unsupported and not guessed. Bare Python names without a unique
  local match remain external/unknown, not proof of an installed dependency. Literal HTTP/RPC
  patterns remain heuristic. `report.json` includes these limitations and concrete findings.
- Preserve quest-coder's original extraction scope explicitly (command below). Automatic
  all-source discovery also examines its tests and `next-env.d.ts`, whose generated `.next`
  imports do not exist in a clean archive; that attempt correctly rejected the refresh with
  two unresolved imports. We did not remap or erase them to make a gate pass.
- A trial expansion of relative Python resolution added a previously absent same-layer
  connection in quest-coder; it was not retained. Relative imports remain explicitly
  unsupported in this narrow milestone, keeping frozen graph/evaluation/routing unchanged.

## Real repository demos

```bash
python3 scripts/build_project.py --repo /Users/aibert/projects/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json \
  --tops app components lib proxy.ts scripts browser-runtime runner \
  --previous-map maps/quest-coder/map.json --out-dir dist/quest-refresh

python3 scripts/build_project.py --repo . \
  --ref f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93 \
  --layers maps/dag-gps/layers.json --out-dir dist/dag-gps
```

| Committed snapshot | Layers | Files | Layer connections | File connections | Unresolved imports | Unsupported findings |
|---|---:|---:|---:|---:|---:|---:|
| quest-coder `749d8b5` | 18 | 272 | 52 | 413 | 0 | 2 |
| dag-gps `f92d0cf` | 3 | 27 | 3 | 19 | 0 | 4 |

Quest: 364 JS + 44 Python raw imports; 15 non-source targets and one unresolved literal
HTTP route are retained diagnostic findings. Unsupported: nonliteral pyodide module URL,
relative import in runner/__init__.py. Full pinned legacy JSON parity passes unchanged.
Self: **27 JS + 3 Python raw imports**, not an empty graph. Eleven non-source JSON imports
are reported; four unsupported nonliteral Playwright requires are listed. Its independent
hand-authored `maps/dag-gps/layers.json` is grounded in real scripts/web/tests, still a worker
draft requiring Eric review. The self demo intentionally audits the pre-implementation
commit, not the mutable worker branch. Stable snapshot rebuild diffs are zero.

## Verified gates and browser evidence

All non-null `.verify.json` build/test/smoke commands exit 0. Exact commands and actual
exit codes: `artifacts/refresh-final-verification.json`; logs `refresh-{build,test,smoke}.log`.

- **123 Python + 88 JS tests**. Seventeen new Python real-Git fixtures cover additions/deletions,
  typed edges, reassignment, cycle/unmapped/duplicate/unresolved rejection, mutable-worktree
  isolation, renderer failure, standalone build-map preservation, promotion rollback,
  identity, deterministic diff, foreign baseline, UMD/local Python imports, ambiguous-Python rejection, exclusions,
  and honest unsupported findings. One new alias test verifies cross-map ID/orphan migration.
- Prior canvas, real-click interactions, scorer parity, M3 5 canonical + 11 extra,
  lookup 19 and alias 19 browser gates remain enabled and pass unchanged.
- New refresh browser **7 checks**, with zero page/console errors and zero external requests.
  Real self-repo Ask `locate scripts/build_map.py` resolves that file in pipeline. Real
  `dependencies of Regression tests` follows actual consumer → pipeline/browser edges.
  Fit, tests toggle, real inspect/expand/back and 1280×800 viewport exercised.
- Real quest Ask `where is magic link?` still resolves auth, with zero snapshot changes.
- Synthetic Git fixture (clearly labeled, not user evidence) compares two actual commits:
  `new.cjs` added, `gone.py` deleted, a.cjs→b.js removed, new.cjs→b.js added, and a.cjs
  reassigned consumer→dependency. `diff.json` retains exact fixture commit SHAs. Browser
  rebuilds the same HTML URL and reloads: valid alias retains a.cjs in its new layer;
  retired alias remains gone.py ORPHAN and abstains. Real JSON export includes both bindings.
- Original generated scorer remains op 47/47, target top-1/top-3 44/44. Separate lookup
  challenge retains op/label 39/40 and top-1 16/17, negatives false-accept 0/24; existing
  bearer-auth abstention is not disguised. Synthetic alias regression remains 15/15.
  These are worker-draft cases, not held-out/user-approved accuracy.

Five full-page screenshots inspected for clipping: `artifacts/refresh-self-file.png`,
`refresh-self-dependencies.png`, `refresh-self-1280.png`, `refresh-quest.png`, and
`refresh-alias-migration.png`. Tall source expansion is fitted after provenance disclosure;
1280 layout wraps the header and preserves Ask/sidebar/canvas without horizontal clipping.
No unrelated layout redesign. Low-opacity nonfocused nodes retain existing styling.

Outputs: `dist/{dag-gps,quest-refresh,refresh-fixture}/index.html`, `map.json`, `diff.json`,
`report.json`; fixture before-map under `artifacts/refresh-fixture/`, exact browser assertions
and fixture diff in `artifacts/refresh-browser.json`. Generated outputs remain ignored.
