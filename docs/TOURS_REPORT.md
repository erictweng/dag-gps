# Architecture-guided tours — local verification

2026-10-07 PDT. Worker branch `architecture-tours`, based on main `3e811d9`.
Worker commits locally only; parent independently verifies and handles main integration/push.

## Delivered

Three source-grounded walkthroughs for **erictweng/quest-coder**, exact audited SHA
**749d8b5de490cc2e6a0c98c713fab3ab856da799**. Source was read from a `git archive`
export of that commit, not the mutable quest-coder checkout. Build compilation verifies
citations again using `git show SHA:path`. No quest-coder files or refs were changed.

| Tour | Ordered steps | Typed links | Step citations | Link citations |
|---|---:|---:|---:|---:|
| Run basic | 5 | 6 | 10 | 9 |
| Submit | 8 | 11 | 24 | 13 |
| Sign in | 5 | 9 | 16 | 10 |

Eighteen steps, 26 directed links, 50 step and 32 link citation instances; 20 distinct
source files. Repeated citations are intentional context, not additional independent evidence.

- **Run basic:** `app/page.tsx:submit` → `browserRunInputs`/`BrowserRunner.run` → module
  worker messages → Pyodide `run_public` → shared `run_challenge` → advisory result.
  Public `tests.run`, `isolate=False`, no rewards/streak. Missing public inputs or
  unavailable Python falls through to the server; a hard timeout stops the attempt.
- **Submit:** the page skips browser grading; `/api/run:POST` verifies session, request
  limits, prerequisites and party locks before `submitToRunner`. Credentialed HTTP
  reaches `/v1/runs`; the gateway, not Next.js, starts the bounded Python CLI. CLI loads
  private tests for Submit and calls the isolated grading engine. Gateway redaction
  can reveal the failed replay case, rather than falsely promising all inputs stay secret.
- **Ordering:** runner result returns to the API **before** activity/clear writes.
  Activity is best-effort even on failed Submit. Only a passing Submit clears and grants.
  The API **awaits writes, rereads progress, then sends the browser response**. The browser
  adopts server-owned progress before result/celebration; animation does not delay writes.
- **Persistence alternatives:** complete Supabase configuration selects service-role
  `quest_coder_apply_clear`; its latest archived definition locks the progress row,
  derives assistance from stored state, updates progress and returns the grant. Local
  mode uses `applyClear` in a SQLite read-modify-write transaction. Partial Supabase
  configuration throws, not fallback. Migrations are source evidence, not proof a live
  deployment has applied them. Party leader/solver/already-rewarded branches are disclosed;
  the solo Submit tour does not pretend those all run consecutively.
- **Sign in:** the shipped `SignInControls` exposes **Google only in Supabase mode**.
  Passwordless OTP remains supported by `/api/session` and the page handler, but is not a
  visible email form in this snapshot. PKCE callback and token-hash confirmation are
  alternative routes. SSR cookie access supports the exchanges; `currentSession` verifies
  `getUser`, not cookie-only `getSession`. User ID becomes the progress/rate-limit identity.
  Protected run rejects null sessions. Local display-name/opaque-cookie sessions are a
  separately disclosed development alternative, not Supabase identity.

## UI and graph semantics

Choose Tours in the small header menu, or Ask `walk me through submitting code`,
`walk me through run basic`, or `walk me through signing in`. Explicit reviewed query
phrases resolve before ordinary scoring and before learned aliases. This is an exact
phrase resolver (case/whitespace/punctuation normalization), not arbitrary free-text Q&A.
Unrecognized questions retain normal locate/dependencies/dependents/directed path behavior.

The optional sidebar section gives brief receives/does/passes boundaries, `Step x of y`,
Previous/Next/Reset/Exit, and citation buttons. Overview can highlight all involved layers
on the **original dependency graph**. Return to step shows current real files plus their
direct cited runtime context, not every file at once; current step nodes have teal outlines.
Arrow keys navigate and Escape exits outside inputs/selects/editable content; modal evidence
owns Escape and blocks tour stepping. No automatic onboarding or new full-height panel.

Citation clicks display actual line-numbered source text offline, path, descriptive symbol,
and audited SHA, with an optional immutable GitHub link (explicit external navigation).
Locate real file means **inspect the actual node in this map**, not opening a local editor
or repository file. Only referenced excerpts are bundled, not the entire private repository.
All map/tour strings are escaped in script literals, DOM text and generated attributes.

**An import path is not an execution trace.** Tours do not use BFS/shortest-path to prove
runtime order. Teal dash-dot edges are a separate tour view with explicit from → to direction,
HTTP / spawn / message / data typing, source evidence, and their own legend. Normal map
edges are never modified. Import-typed tour links must exist in the original import graph.
Inferred/unverified links are schema-supported, labeled in the list, and not drawn; these
three tours include only source-supported links. Source-supported means audited source
supports the stated boundary, not that production execution was observed.

## Reusable build interface and validation

```bash
python3 scripts/render.py --map maps/quest-coder/map.json \
  --out dist/quest-coder.html --tours maps/quest-coder/tours.json \
  --repo /Users/aibert/projects/quest-coder

python3 scripts/build_project.py --repo /Users/aibert/projects/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json \
  --tops app components lib proxy.ts scripts browser-runtime runner \
  --tours maps/quest-coder/tours.json --previous-map maps/quest-coder/map.json \
  --out-dir dist/quest-refresh
```

Omit `--tours` for any other repo, including the pinned self demo at
`dist/dag-gps/index.html`: it honestly says **No curated tours available**. No quest-coder
runtime behavior is hardcoded into the reusable UI/controller/compiler.

Version-1 JSON fields: `repo`, exact 40-character `commit`, `tours[]`; each tour has `id`,
`title`, `overview`, explicit `queries[]`, ordered `steps[]`, and `links[]`.
Steps have `nodeIds[]`, `title`, `does`, `receives`, `passes`, `explanation`, and `evidence[]`.
Evidence has a mapped source `path`, inclusive one-based `start`/`end`, and descriptive
`symbol`; the compiler supplies actual `excerpt` and `nodeId`. Each range is at most 50
lines. A supplied excerpt must match pinned bytes. Links have `from`, `to`, `type`,
`direction: "from-to"`, `status`, `label`, and their own evidence.

Compilation rejects schema/type/unknown ID/missing evidence/invalid path or line bounds,
repo mismatch, ambiguous queries, stale commit, and falsely claimed import links. Legacy
short map SHAs resolve through Git to the exact full commit; ambiguous or nonexistent refs
fail. All tour validation/rendering occurs before refresh promotion; both stale and invalid
tour fixtures preserve every previous artifact byte. Standalone render validates before
opening its destination. Existing per-file atomic publish/rollback and crash limitations
remain unchanged (see REFRESH_REPORT.md).

## Actual verification

All `.verify.json` build/test/smoke commands exit 0. Exact commands and return codes are
recorded in `artifacts/tour-final-verification.json`; full logs are
`artifacts/tour-{build,test,smoke}.log`.

- **138 Python + 93 JS tests**: 15 new Python tour fixtures and 5 pure controller tests.
  Real Git fixtures cover immutable reads, exact identity/commit, missing evidence,
  line/path validation, forged excerpts, bad/duplicate queries and links, nonmutating
  runtime links, safe serialization, stale/invalid refresh and render preservation,
  successful inline evidence compilation, and zero tours on another repo.
- **29 tour browser checks**, every one of the 18 ordered steps and every step/link
  citation compared to actual `git show` source; real menu changes, typing/Enter,
  previous/next/reset, layer overview, file inspection, modal focus restoration and
  keyboard ownership, alias-hijack rejection, ordinary Ask restoration, inert malicious
  strings, honest zero-tours self map. **Zero page/console errors and external requests.**
- Legacy full pinned-map parity / 10 map checks, canvas and real-click interactions,
  shipped scorer parity, M3 **5 canonical + 11 extra**, lookup **19**, alias **19**,
  refresh **7** remain enabled and passing. Original scorer **47/47 operation, 44/44
  target**, lookup challenge **39/40 operation/label, 16/17 top-1**, alias synthetic
  regression **15/15** remain unchanged. The bearer-auth abstention is retained.
- Eleven screenshots: `artifacts/tour-{run-basic,submit,sign-in}.png`, corresponding
  `-layers.png` and `-evidence.png`, plus `tour-submit-1280.png` and
  `tour-submit-phone.png`. Inspected for clipping, readable narration, current-step
  highlighting and source evidence. Phone stacks canvas/sidebar; zoom/pan remains available.

No live quest-coder authentication or submissions were executed. These are audited
source explanations plus DAG GPS browser regressions, not observed application traces,
held-out/user-approved accuracy, or calibrated confidence. Existing map/layers/scorer/router,
model/network/training behavior and alias storage semantics remain unchanged.
