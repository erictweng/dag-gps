# Filename lookup and evidence-first answers

Locally verified on `lookup-evidence`, based on M3 `1844aa2`. Eric identity is
configured. No push/merge, dependency installation, Claude use, quest-coder edits,
map changes or layer membership changes. Parent independently verifies before acceptance.

## Implemented behavior

- Separate file retrieval from architecture responsibilities. Explicit filenames,
  full paths, `file NAME`, recognized extensionless stems and conservatively near
  filename spellings use real file nodes. Bare architecture identities/aliases stay
  architectural unless file syntax makes the request explicit. Each PATH endpoint
  is classified and matched independently.
- File tiers: **exact full path (60) > exact basename (50) > stem (40) > filename
  token/partial (30) > conservative fuzzy spelling (20 minus edit distance)**.
  Structural prior is zero for files, so fan-in cannot break basename ambiguity.
  Directory-qualified exact paths disambiguate basenames. A bare name remains
  ambiguous even if one duplicate happens to be at repo root. Literal tokens
  are preserved whole: suffixes or `./` are not silently repaired into exact files.
- Stem means only the final extension is omitted; extensionless full paths work too.
  Partial names need at least four characters and a filename token/substring match.
  Unique, separated stems/partials can be Likely matches. A fully specified absent
  filename/path **never auto-accepts a nonexact substitute**, even if unique.
- Fuzzy lookup permits one edit for lengths 5–7, up to two for lengths ≥8, and an
  edit ratio ≤0.2. It is always suggestion-only; low-length/irrelevant strings do
  not acquire evidence from graph structure. Fuzzy weights may be high, but cannot
  authorize action.
- Duplicate basenames retain **every tied full path**, not merely three candidates.
  `route.ts` has 13 real matches in the snapshot; choosing one outside top three is
  browser-tested. No automatic choice on a tie.
- The actual map has no `runner.py`. Its answer says **No exact file named runner.py**,
  suggests `runner/quest_runner.py` and `runner/quest_runner_cli.py`, and requires
  an explicit **Override** click. It never silently selects a runner layer or an
  invented filename. Real clicks highlight the selected actual file.
- No-match heads keep their observed-ID normalized distribution and deterministic
  argmax for contract compatibility, but have **no supported suggestions/buttons**.
  NOT_SURE clears stale highlights. An unknown PATH endpoint cannot be overridden
  using an arbitrary uniform argmax; supported abstained endpoints still require
  both explicit choices. No aliases are learned and no browser persistence is used.

## Evidence labels and architecture metadata

Labels use evidence, query coverage and runner-up margin, not softmax confidence:

| Label | Evidence rule |
|---|---|
| Exact match | Accepted literal full path/basename, or literal architecture label/alias/identity |
| Likely match | Accepted stem/unique partial or nonliteral responsibility evidence |
| Needs your choice | Supported suggestions exist, but ambiguity, missing exact name, spelling or insufficient separation blocks acceptance |
| No match | No supported evidence/candidates, or incomplete intent |

Acceptance retains ≥4 lexical evidence, ≥0.6 query coverage and ≥1 raw score
margin. Missing exact names and all fuzzy candidates additionally force abstention.
A table-size regression proves the same evidence retains its label/acceptance when
normalized weight changes. Reasons, full paths and aliases are visible. **Details**
contains raw scores/components, normalized weights and runner-up margin, explicitly
uncalibrated. It includes all offered suggestions, including duplicate paths beyond
three; no percentage bars are used as answer confidence.

Architecture scoring keeps M2 weights (label/alias/description/path/identity/prior),
but excludes file fragments from architectural ranking. Metadata was inspected:
runner-service is a Python **grader**, with alias `grader`; auth is the map's
abbreviation for the session/sign-in responsibility. A small declared concept
morphology table normalizes grading/grader/graded → grade and
authentication/authenticated/authenticating → auth for **all metadata and queries**.
This is not an exact-question dispatch or a new map alias. Morphology-only matches
are labeled **Likely**, not literal Exact. The exact `grading request` alias still
finds run-gateway. No layer descriptions, aliases or memberships were rewritten.

## Backwards-compatible contract

Existing operation/target `{choice, probabilities, confidence}` fields, observed-ID
coverage, finite normalized distributions, argmax consistency and fixed `top3`
remain. Additive `evidenceVersion: 1` supplies `match` and `suggestions` metadata;
legacy M2/M3 heads without those additions still validate. New validation rejects
unknown evidence versions, invalid labels/tiers/margins/coverage, inconsistent
acceptance, invented/duplicate suggestion IDs, false paths/aliases and nonfinite
raw scores. The UI revalidates before routing and before overrides. Query/map text
is still escaped; inline serialization and pure directed router are unchanged.

## Actual gates

All non-null `.verify.json` commands exited **0**, after final code changes.
Exact commands, exit codes and logs: `artifacts/lookup-final-verification.json`,
`lookup-build.log`, `lookup-test.log`, `lookup-smoke.log`.

- **104 Python tests pass**; existing negative renderer test prints `FAIL missing
  top-level 'layers'` while the suite correctly exits 0.
- **73 JS tests pass**: 46 existing plus 27 lookup/evidence regressions. Coverage
  includes paths, basenames, every duplicate path, stems, partials, runner.py,
  minor typos, irrelevant unknowns, responsibility cases, filename/intent collisions,
  independent PATH endpoints, no wrong confident acceptance, table-size independence,
  literal-token preservation and legacy/new schema validation.
- Pinned rebuild at `749d8b5de490cc2e6a0c98c713fab3ab856da799`: **10/10 checks**, full
  snapshot parity ignoring only documented ref/build-time fields. Committed map
  untouched: 290 nodes, 18 layers, 272 files, 52 layer edges and 413 file edges.
  Upstream still pointed to the pinned ref at discovery; the recipe pins it anyway.
- `artifacts/lookup-scope.json` verifies map, layers, `web/router.js` and the original
  `eval/eval.jsonl` are byte-identical to M3, recording SHA-256 values.
- Build: standalone `dist/quest-coder.html`, renderer-reported **303.2 KB**.
- Legacy canvas four states and real-click interactions pass: focus, expansion,
  details, Escape, tests toggle, double-click, Back, zoom/Fit. No runtime canvas,
  animation, pan/zoom or router changes.
- M3 **5/5 canonical + 11 additional checks** pass, with original operations,
  actual targets, route edges, no-path honesty and cross-layer file behavior.
  Presentation assertions now check evidence labels/Details and supported candidate
  counts, not three arbitrary buttons. The both-endpoint override check uses an
  evidence-backed ambiguous endpoint (`top bar`), not unknown uniform alternatives.
  Lookup smoke separately confirms unknown PATH endpoints have no override button.
- Shipped-source parity: **47/47** original cases and **40/40** lookup cases,
  exact decisions/IDs/keys with numeric tolerance 1e-12. No replacement scorer injection.
- Lookup real typing, Enter/Ask, explicit override clicks, raw Details, all duplicate
  paths, clearing, no-evidence PATH and 1280×800: **19 checks pass**. Browser reports
  have zero page/console errors and zero non-file requests. Local/session storage
  both remain empty. Evidence: `artifacts/lookup-browser.json`, `m3-browser.json`,
  `m2-browser.json`.

## Measured evaluation — not held-out accuracy

The original **47 generated worker-draft regression rows are unchanged**. Their
operation accuracy improves 46/47 → **47/47**, raw target top-1 42/44 → **44/44**,
top-3 43/44 → **44/44**, PATH endpoints remain **14/14**, negative false acceptance
remains **0/10**. The grading/authentication cases now match their drafted targets.
Abstention is **10/47**. Warm scoring p95: Node **1.3480 ms**, Chromium **1.1000 ms**
(940 samples each, including scorer's contract validation).

A separate `eval/lookup.jsonl` contains **40 worker-draft challenge/regression cases**,
including 24 abstention requests (missing, ambiguous, typo, irrelevant and PATH
endpoints), and 16 positive requests. It is not user-approved or held-out truth,
and has informed development. Expectations were inspected against real map IDs;
its retained failure is not dropped or relabeled to hide an error.

| Lookup metric | Actual result |
|---|---|
| Operation / answer-label accuracy | 39/40 / 39/40 |
| Raw positive target top-1 / top-3 | 16/17 / 17/17 (PATH counts two endpoints) |
| Requested suggestion recall | 15/15 |
| Negative false acceptance | 0/24 |
| Wrong accepted requests | 0/15 accepted requests |
| Warm Node p95 | 0.9129 ms, 800 samples |

`where is bearer auth?` is retained as a failure: expected runner-service/Likely,
but the raw target argmax is auth with inadequate coverage, so it abstains and
shows runner-service as a supported explicit suggestion. **No wrong confident
acceptance** occurs on that case. This small benchmark does not prove universal
safety/generalization. `scripts/eval_lookup.cjs` reports every result/failure and
fails its safety gates on false accepted negatives or accepted wrong requests;
it does not require a cosmetically perfect challenge score.

## Screenshot inspection and development notes

Nine actual lookup screenshots under `artifacts/`:
`lookup-{exact,missing,override,unknown,ambiguous,typo,stem,details,1280}.png`.
Inspected labels, full-path wrapping, real file selection, empty unknown actions,
long duplicate choices and uncalibrated Details. Final Details and smaller viewport
were reinspected. No obvious answer clipping/collisions; panel scroll remains
available. The first smaller-viewport capture preceded the existing 120 ms resize
fit; the smoke now waits for that handler before capturing, without altering runtime.

An early test assumed page.tsx was unique; inspecting the real paths corrected it
into an ambiguity regression. A description-weight experiment regressed top-bar
ambiguity and was discarded; M2 architecture weights remain. Initial red tests and
these development failures were resolved before the final gates. Two quoted
scope-probe command attempts failed with syntax errors; the corrected real probe
produced `lookup-scope.json`. No fabricated outputs or unresolved tool blocker.

Remaining limits: sparse responsibility metadata still causes honest abstentions
(the bearer-auth challenge); spelling/stemming rules are conservative heuristics,
not semantic understanding. Mixed graphs remain unsupported; imports are a pinned
partial static map, not runtime reachability proof. Eric review of expectations and
map, and parent independent review/rerun, remain required. No next milestone,
remote PR, push or merge was performed.
