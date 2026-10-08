# V1.2 — Map trust and completeness (worker verified)

Implemented all three approved minis on `v1-trust` from clean main `7bc6769`.
Worker verification: **2026-10-07 PDT** (2026-10-08 UTC). Parent independent
review/rerun/integration/push remains pending. This is **not v1 release acceptance**.

## Trust contract / UI

New builds emit `meta.extraction_version: 2`, full `snapshot_commit` and
`trust.version: 2` / `extractor: dag-gps-static-v2`. `map.json` and `report.json`
carry identical `trust` objects. The low-level builder now serializes diagnostics
before validating/promoting the map (previously they existed only in the return
value). Schema validation checks version, source pin, categories, findings counts
and the extracted/unscanned inventory partition. Pinned parity still compares every
field except the existing documented `meta.ref` / `meta.built_at` exceptions.

Distinct observed findings, deduplicated by all finding fields:

| Category | Meaning / evidence |
|---|---|
| `resolved_source` | Mapped source link: `resolved_lexical_import`, explicit `resolved_static_loader`, or `inferred_unverified` HTTP/RPC literal pattern |
| `non_source_target` | Existing resolved target lacks a source node; e.g. CSS/JSON. Not an unresolved import |
| `unresolved_local_reference` | Unresolved local import or literal HTTP/RPC target; concrete reason retained. Import failures block publication; HTTP/RPC misses remain disclosed notes |
| `unsupported_dynamic_construct` | Nonliteral JS import/require, Python dynamic loader/search-path constructs not safely modeled; not evaluated/guessed |
| `external_dependency` | Bare/external package or unrecognized alias; installed/package resolution unverified. **Not an unresolved local error** |

Each finding has `category`, `path`, `target`, `reason`, `evidence`. Counts are
source/target findings, **not import occurrences**. `scope` records exact JS inputs,
repository-wide Python and migration SQL scans, included-source inventory denominator,
scanned and unscanned paths. Scanned files mean the documented source extractor ran,
not complete parsing or runtime coverage. No runtime-completeness percentage exists.

**Map trust** disclosure offers category/path filtering and real-file navigation.
Concrete findings precede verbose limitations, which have their own disclosure.
File inspection and Ask show contextual warnings for findings incident to selected
files/layer ownership or actual route IDs. Impact uses selected file plus real
shortest-witness chain files, including separate HTTP/RPC witnesses. Otherwise the
badge explicitly says **repository-level uncertainty**, not “this file is complete”.
External findings remain inspectable but are not presented as local resolution errors.
An unknown path has no invented evidence or arbitrary navigation target.

Evidence tiers remain separate: resolved static imports/loaders; independently
validated **curated source-supported** tour links; inferred/unverified literal
HTTP/RPC or uncited manual layer links. Tours are source walkthroughs, not observed
execution. `meta.tours` records current/omitted/unavailable, snapshot and reason;
current evidence is `curated_source_supported`, `observed_execution: false`.

## Narrow extraction improvements

Fixture-first Python AST resolution supports exact modules, same-directory scripts,
one/multiple-level relative imports, real package `__init__` and namespace-directory
submodules. `from module import symbol` never fabricates a symbol file; a real
submodule links separately alongside an existing package node. Module/package
collisions and missing relative/namespace modules reject deterministically. Unique
suffix resolution is removed: suffix candidates can explain an unsupported/ambiguous
reference but **never select its target**.

To preserve real self-demo dependencies without suffix guessing, recognize the
archived explicit file-relative path syntax in `scripts/python_static.py`: unconditional
top-level `sys.path.insert(0, path)` and concrete `spec_from_file_location` file paths;
`Path(__file__)`, lexical `.resolve()`, `.parent` / bounded `.parents[i]`, `/` literals,
`str`, `os.path.abspath/dirname/join`, and prior simple assignments. No `eval`, imports
of repository code, loader execution or filesystem/symlink-resolution claim. Conditional
path changes and arbitrary expressions remain explicit unsupported findings. This is
a bounded syntax helper, not a Python interpreter/full importlib or JS parser.

JS changes cover whitespace between literal `require`/`import` and `(`, indented
side-effect imports, and the literal require part of TS `import X = require (...)`.
Comments/quoted fixtures remain masked. These synthetic cases reproduce narrow lexical
blind spots; they add **no JS pairs to the frozen quest graph**. Computed imports,
template interpolation, configured aliases/package exports and complete scope/shadowing
semantics remain limitations.

Source cycles, including explicit self-imports, are retained and reported at file
level. Same-layer file cycles publish; true layer cycles still reject with an actionable
cycle path for grouping review. No SCC redesign or edge removal to make a DAG green.
The old synthetic `test_self_edges_are_skipped` expectation is deliberately migrated
to exact retained-edge assertions under V2. Neither real pinned repo has a file cycle.

## Deliberate graph/provenance migration — unchanged source pins

### Quest `749d8b5de490cc2e6a0c98c713fab3ab856da799`

Rebuilt with `git archive` and unchanged tops
`app components lib proxy.ts scripts browser-runtime runner`.

- **18 layers / 272 files / 52 layer pairs**, unchanged nodes, membership and layer
  closure/top-fan-in metadata. **413 → 415 file pairs**, imports **389 → 391**;
  HTTP 14 and RPC 10 unchanged. Cross-layer file pairs **324 → 325**.
- Exact additions (no removals):
  - `runner/__init__.py → runner/quest_runner.py` (`import`), source line **3**:
    `from .quest_runner import run_submission`.
  - `runner/tests/test_trusted_boundary.py → runner/quest_runner.py` (`import`),
    source line **14**: `from runner import quest_runner`. Its existing package
    `runner/__init__.py` link is retained, not replaced.
- `tests → runner-service` import rollup weight **26 → 27**; no layer pairs removed/added.
- Both tours and map still audit the same full source SHA. Added extractor/trust
  metadata is **not a new source revision**. `diff.json` baseline/snapshot provenance
  now includes `extraction_version` so same-source migrations are visible.
- **182 / 272 scanned**, 90 unscanned inventory paths (including TS tests/config and
  non-migration SQL), 415 resolved links, 14 non-source targets, **0 unresolved imports**,
  **1 unresolved literal HTTP reference**, **8 unsupported findings**, 280 external
  source/package findings. Unsupported: Pyodide template import; two `import_module`
  calls in `test_engine_portable.py`; five conditional/unmodeled search-path insertions
  in quest_runner_cli, service/app, test_engine_portable, test_pack_dir, scripts/private_pack.
- `/api/private-pack` in `scripts/deployment_smoke.mjs` is the literal HTTP miss, not
  a local-import failure or proof the endpoint cannot exist at runtime.

### Self `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93`

No silent update to current source. Rebuilt old/current extractors on the same archived
source for the comparison (`artifacts/trust-self-before-map.json`, migration JSON).

- **3 layers / 27 files / 3 layer pairs**, nodes and ownership unchanged.
  **19 → 20 file pairs**, no removals.
- Exact addition: `tests/test_aliases.py → scripts/build_map.py` (`import`), source
  line **6**, explicit `spec_from_file_location` with
  `pathlib.Path(__file__).parents[1] / 'scripts/build_map.py'`.
  Evidence is **resolved_static_loader**, not an ordinary import statement or
  proof of execution. Existing explicit search-path imports are preserved via
  their source paths, never suffix guessing.
- `tests → pipeline` import rollup weight **5 → 6**. `pipeline.top_fan_in` legitimately
  changes; no layer closure or membership change.
- **27 / 27 scanned**, 20 resolved links, 11 non-source targets, 0 unresolved,
  4 unsupported computed Playwright requires, 94 external source/package findings.
  Even all inventory files scanned does **not** mean runtime completeness.

### Impact expectation audit / fixture migration

`lib/runner-client.ts` remains 3 direct consumers, 1 farther consumer, 0 observed
linked tests, 6 separate boundary witnesses and 4 exact tour citations. Its **Locate**
answer uses repository-level uncertainty; its **impact** warning correctly includes
`deployment_smoke.mjs`'s HTTP miss because that file is in an actual boundary witness.
It does not attribute that miss to runner-client itself.

`runner/quest_runner.py` changes **14 → 16 direct consumers**, **11 → 12 linked tests**,
0 farther consumers: the two exact additions above justify the change. Browser source
assertions verify the new test's exact `from runner import quest_runner` line instead
of pretending every test uses `from runner.quest_runner import ...`. Existing import
expectations are retained. Coverage remains unknown.

Self `scripts/build_map.py` changes **1 → 2 direct/linked tests**: test_build_map plus
the newly explicit test_aliases loader. No runtime/coverage claim. Query/scorer/alias
datasets and both layer specs/tours/router/scorer remain byte-identical to main
`7bc6769`; hashes are recorded in verification JSON. New extraction/trust fixtures
are worker-generated synthetic development cases, not Eric-authored query labels.

The original root `gone.py: from .helper import thing` fixture was not a valid package
import: V2 migrates it from “unsupported” to exact **local failure with byte preservation**.
The unsupported regression is retained with actual `__import__(name)` plus nonliteral
JS require. No test was dropped or threshold relaxed to hide a miss.

## Stale-tour / explicit opt-out safety

Exact repo/full-SHA/ID/source-range validation remains unchanged and fail closed.
Stale/malformed tours preserve **all prior map/HTML/diff/report bytes**. To omit tours:

```sh
python3 scripts/build_project.py \
  --repo /Users/aibert/projects/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json \
  --tops app components lib proxy.ts scripts browser-runtime runner \
  --without-tours --out-dir dist/quest-no-tours
```

`--tours` and `--without-tours` are mutually exclusive in both build and standalone
render CLIs (also checked in the build API). No malformed tour file becomes a silent
opt-out. An existing current-tour build or **legacy HTML with attached evidence**
requires reviewed `--tours` or explicit `--without-tours`; an explicit comparison map
cannot bypass this check. Standalone render also refuses silent loss. First/no-tour
repositories retain honest unavailable defaults. Omission publishes `TOUR_DATA = null`,
disables Tours and displays the reason; natural tour queries cannot invoke old tours.

Publication guarantees are unchanged: staged validation, per-file atomic replacements
and caught-error rollback, **not a power-loss-safe cross-file transaction**.

## Actual worker verification

All non-null `.verify.json` **build / test / smoke exit 0**. New gates supplement all
legacy gates; exact commands, stdout/stderr, exits, durations and immutable-input
hashes: `artifacts/trust-verification.json`, `trust-{build,test,smoke}.log` and separate
`.stdout.log` / `.stderr.log`. These outputs are local/ignored, not shipped in a clone.

- **161 Python tests, OK**, including raw package/module/scope/missing/ambiguous/self
  and multi-file-cycle fixtures, bounded static paths/loaders, schema/provenance migration,
  failure preservation and explicit stale-tour omission. Initial red evidence:
  `trust-red.log`, `trust-path-red.log`, `trust-pathlib-red.log`, `trust-selfcycle-red.log`.
- **109 JS tests, 109 pass, 0 fail**; six new pure contextual trust tests. Existing
  impact, aliases, tours, routing and scorer suites retained.
- Original 47-case generated eval, 40-case lookup challenge and 15-case synthetic
  alias eval retained; bearer-auth responsibility abstention remains. No real-user
  or held-out accuracy claim.
- Frozen quest map **10/10 checks + strict full pinned parity**; both refreshed demos,
  canvas/real interactions, shipped scorer parity, M3, lookup19, alias19, refresh7,
  tours29/all 18 steps/every citation and impact14 gates pass.
- `scripts/smoke_trust.cjs`: **10 checks / 13 screenshots**, real clicks, typing/Ask,
  category/path/source navigation, contextual worker/impact and clean general warning,
  external vs local miss vs non-source distinction, unknown path, explicit omitted
  tours/natural-query safety and old self pin. **Zero page/console errors or external
  requests**. All final screenshots inspected at 1920 and 1280; sidebar controls/reasons
  wrap without horizontal clipping. Detailed limitations are disclosed without pushing
  the filtered concrete finding offscreen. Graph overview labels remain fit/zoom scale.

Open `dist/quest-refresh/index.html`, `dist/quest-coder.html`, `dist/dag-gps/index.html`,
or the explicit opt-out `dist/quest-no-tours/index.html`. Screenshots:
`artifacts/trust-{evidence-tiers,findings-1920,context-answer,context-impact,boundary-context,general-answer,external,unresolved-http,non-source,unknown,1280,omitted-tours,self-scope}.png`.

No hosted dependency, quest-coder source edits, push/merge, onboarding/history/release
redesign or source-pin advance. Quest checkout has untracked `AGENTS.md`/`CLAUDE.md`
owned outside this task; left untouched. Parent review/integration and later milestones/
Eric's unaided session remain pending. Remaining limitations are the bounded static
extractor, partial scan, unmodeled dynamic behavior, inferred HTTP/RPC/manual links,
unknown runtime/coverage and old self snapshot—not implementation blockers hidden by
false confidence.
