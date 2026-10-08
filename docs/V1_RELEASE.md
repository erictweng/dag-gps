# DAG GPS — v1.0.0-rc.1 local release candidate

V1.5a/b/c authorized together. Audit started **2026-10-07 PDT** and continued
**2026-10-08 PDT**, from main `99652d1` on worker branch `v1-release`.
This is a **candidate**, not v1 complete: parent independent review, Eric's
semantic grouping review and an unaided real-repository session remain pending.
V1.4 real-user tuning is deferred; zero confirmed Eric labels. No push/public upload.

## Install, build, open

Runtime artifacts are standalone HTML: a current desktop Chromium browser is the
verified target. Python stdlib builds them; Node is for unit/evaluation/browser gates,
not a runtime service. Recorded local environment: Python 3.9.6; initial Node v26.6.0, candidate-2 Node v26.8.2;
Git 2.50.1, macOS arm64 / Apple M4 Pro / 24 GiB; exact execution versions and
hardware are captured by `release_check.py`. Playwright 1.63.0 / Chromium and
axe-core 4.13.0 are installed in the sibling test-tool directory locally.

From this repository root, generic supported-repo onboarding:

```sh
python3 scripts/draft_layers.py --repo /path/to/local-git-repo --ref FULL_COMMIT \
  --out artifacts/my-draft.json
python3 scripts/render_layer_editor.py --draft artifacts/my-draft.json \
  --out dist/my-editor.html
open dist/my-editor.html  # macOS; otherwise open the HTML in your browser
```

Search paths, inspect responsibilities and findings, rename/reassign/merge/split,
resolve grouping cycles using their real file witnesses, then explicitly review and
**download reviewed layers.json**. The browser does not write the repository.
Run the exact builder command displayed in the editor, replacing the path placeholders.
Retain its full pin and `--tops` list. Example for an all-source draft:

```sh
python3 scripts/build_project.py --repo /path/to/local-git-repo --ref FULL_COMMIT \
  --layers /path/to/actual-downloaded-layers.json --without-tours \
  --out-dir dist/my-project
open dist/my-project/index.html
```

An all-source draft's source list is its explicit extraction scope; omitting `--tops`
uses generic discovery. A scoped draft must pass its declared scope unchanged.
Unresolved local imports, missing/double ownership, empty/cyclic layer grouping or
stale/malformed evidence fail with diagnostics; never delete true links to pass.
Use a separate output directory when reviewing new architecture IDs.

The repeatable approved quest demo (requires private Git source locally):

```sh
python3 scripts/build_project.py --repo /path/to/quest-coder \
  --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 \
  --layers maps/quest-coder/layers.json \
  --tops app components lib proxy.ts scripts browser-runtime runner \
  --tours maps/quest-coder/tours.json --out-dir dist/quest-refresh \
  --previous-map maps/quest-coder/map.json
open dist/quest-refresh/index.html
```

These are real tested CLIs, not a hardcoded-only self-demo interface. Full verification
below also requires the frozen quest archive and the repository's old self commits.

## Navigator workflow

1. Ask a literal source path, e.g. `locate lib/runner-client.ts`. Inspect the full
   path/details. Fit is an **overview**, not a promise that all graph labels are readable.
   **Readable zoom** provides 100% labels; pan/zoom or use the keyboard-accessible lists.
2. Select a tour, step, inspect source, Escape to return; or observe explicit
   **No curated tours available**. Source explanations are not execution traces.
3. Ask `impact of lib/runner-client.ts` or Inspect potential impact. Read direct /
   transitive import consumers, a witness chain, linked tests and separate HTTP/RPC
   boundary evidence. Coverage remains unknown. Inspect/Return/Close recover views.
4. A missing `runner.py` does not become a guessed file. Choose an explicit real
   override, type a nickname, Review and Confirm remember. Repeat the nickname.
   Override alone and feedback labels never teach aliases. PATH nicknames are unsupported.
5. Manage learned aliases → Export JSON. Onboarding edit → actual download → validated
   rebuild in a new directory. Import the alias export, preview and Confirm merge.
   Literal file IDs survive grouping; removed layer IDs are orphans, not remapped.
6. Optional feedback: explicitly choose provenance/consent, Ask, confirm a label and
   expected real IDs, then Export. Freeze a user-controlled holdout before its first label.
   Wrong alone does not establish intended target; Unclear is not NOT_SURE gold truth.

Graph nodes and sidebar navigation are focusable. Enter/Space inspects a graph node;
Shift+Enter expands a layer. Escape goes back outside typing and modal contexts.
Source dialogs own Escape and restore citation focus. Primary actions have visible focus;
reduced-motion preference disables transitions/animation. Phone support is inspection
with ordinary vertical document scrolling, not desktop-equivalent authoring.
Toolbar and legend occupy separate layout rows outside the clipped SVG: readable zoom
does not draw labels over controls. File canvas pages contain **80 files**, sidebar file lists **150 rows/page**, with visible
counts/next/previous and explicit off-page canvas-edge omission. Ask still searches the
whole pinned corpus and opens the target's page. The actual map, scorer, routing, impact
and raw layout retain all IDs/edges, including cycles. No hidden source deletion.

## Test setup and repeatable release check

Only browser QA needs extra packages. Existing tools are borrowed locally; a fresh
machine can install them into its own tool directory (network installation is opt-in):

```sh
npm install --prefix "$HOME/.local/share/dag-gps-browser" playwright@1.63.0 axe-core@4.13.0
export PLAYWRIGHT_DIR="$HOME/.local/share/dag-gps-browser/node_modules/playwright"
export AXE_CORE_PATH="$HOME/.local/share/dag-gps-browser/node_modules/axe-core/axe.min.js"
"$HOME/.local/share/dag-gps-browser/node_modules/.bin/playwright" install chromium
python3 scripts/release_check.py --quest-repo /path/to/quest-coder
```

Installation commands are setup guidance, not a claim that this worker fetched packages.
This worker reused installed tools. `PLAYWRIGHT_DIR` is the package directory, not `.bin`;
`AXE_CORE_PATH` is the actual JavaScript file. `DAG_GPS_QUEST_REPO` is also supported.
The runner executes every unchanged non-null legacy `.verify.json` recipe, substituting
only the configured private quest checkout, then the actual release session, Axe,
scorer benchmark and browser layout/Ask checks. All packages' tests are included:

```sh
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
node scripts/eval_scorer.cjs
node scripts/eval_lookup.cjs
node scripts/eval_alias.cjs
node scripts/eval_user_queries.cjs
```

`--legacy-only` is explicitly incomplete and cannot package a candidate. Missing inputs,
Git pin, browser tool/browser, assertion, Axe engine, performance target or failed gate
returns nonzero. Logs/stdout/stderr/commands/return codes/timestamps/environment/input
hashes live under `artifacts/release-check/`. Timeout is 600 seconds **per recipe**.
Full-session step/download evidence: `artifacts/release-browser.json`; accessibility:
`release-accessibility.json`; performance: `release-performance.json` and
`release-ui-performance.json`. Historic failed attempts are retained separately.

## Immutable pins, regeneration, and output safety

- Approved quest architecture/tours stays at
  `749d8b5de490cc2e6a0c98c713fab3ab856da799`: 18 layers / 272 files / 415 file links.
- Old self demo remains `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93`:
  3 layers / 27 files / 20 file links. It is not today's feature map.
- Separate newer self onboarding stays at
  `a5b02554e479b5184204ab6aa7c7190d6605fe91`: 48 assignments / 3 proposed layers /
  38 links, explicitly **47/48 scanned**. The unrestricted draft still blocks on an
  archived smoke consumer of generated untracked JSON. No generated fixture injected.
- Quest folder proposals are a separate 38-layer sample. Browser-downloaded worker
  exports have review markers to exercise publication, **not Eric-approved semantics**.
- Resolve a Git ref to an immutable full commit before building. Archive, don't scan the
  mutable checkout. Source pin and verified local HEAD-at-build are separate metadata.
- Updating source requires reviewing layers and exact cited ranges/IDs before supplying
  tours. Wrong repo/commit/path/range/ID fails before promotion. Deliberately omit evidence
  with `--without-tours`; no stale attachments or automatic narrative remapping.
- Build outputs: `map.json`, `index.html`, `diff.json`, `report.json`. Staged validation
  and caught-error rollback preserve previous bytes; per-file atomic replace is **not**
  a crash-safe cross-file transaction. Use one writer and open after successful build.

## Release bundle and privacy

After successful checks, the runner packages local-only
`dist/release/v1.0.0-rc.1/manifest.json` plus approved quest navigator, old self demo,
separate grouping worker-sample builds, both layer editors, input specs/tours and docs.
Each payload has exact SHA-256 and byte size; manifest records build commit, source pins,
source-tool hashes, gate evidence hash and pending human gates. It does not recursively
include itself in its file hash list. No query-history exports are bundled.

**The quest HTML includes private source excerpts**; maps/specs expose repository paths
and architecture. Exports of queries/aliases can also disclose sensitive vocabulary.
A bounded scan checks PEM private keys / GitHub tokens / sk-token strings and quoted
credential assignments inside compiled cited excerpts, rejecting matches without printing
values. The pinned quest bundle contains82 citation occurrences /74 unique ranges /
57,405 excerpt bytes; local review metadata is in release-private-source-review.json. This is not a comprehensive credential or privacy
certification. Review cited excerpts, paths and every export before sharing. No automatic
public upload, hosted app, telemetry or browser external request is needed.

Storage is repo/version scoped, browser-profile and `file://` origin dependent. Moving
HTML, changing browsers or denied/quota storage may lose persistence. Export aliases and
feedback **before** moving/closing; import preview plus explicit confirmation restores.
Unsaved/session-only means backup is required. Recording always starts OFF after reload.
No cross-tab synchronization or cross-browser storage portability guarantee.

## Evidence, scope and remaining acceptance

Generated regression accuracy is not user accuracy. Bearer-auth abstention and mixed
layer/file route limitation remain; dynamic imports/conditional Python paths, CSS/JSON
node omission, inferred boundaries and static parser limitations remain visible.
See `SUPPORTED_SOURCES.md`, `TRUST_REPORT.md`, `ONBOARDING_REPORT.md`,
`USER_EVAL_REPORT.md`, and the locked `V1_ACCEPTANCE.md`.

The worker browser audit covers both real demo flows with **actual downloads/builds**,
not just state-hook unit tests. It does not establish unaided human usability. Accessibility
coverage is Axe WCAG2 A/AA + WCAG2.1 AA on recorded states, plus computed SVG text
contrast and actual keyboard/dialog/focus checks; Axe incomplete checks remain listed.
No screen-reader-user certification, universal browser audit or complete WCAG claim.
Performance reports separate file read/JSON parse (OS cache not flushed), cold scorer init, cold page boot, raw full-map layout and
Ask/render/paint-opportunity timing. Warm scorer p95 has a <10ms local-hardware target;
**no end-to-end <10ms claim**. Synthetic 1k/5k fixtures are explicitly generated, not repos.

### Worker audit outcomes and retained failures

- Candidate-2 full legacy + release gates passed: **180 Python / 152 JS**, both real
  sessions / **22 step groups / 70 recorded click/key events**, and **32 primary
  screenshots**. Post-commit verification/manifest is authoritative for final numbers.
- Serious observed contrast failure: original small dim text ~3.1:1, below4.5:1.
  Dim/muted colors, faded SVG text, placeholders and control borders were corrected.
  Axe23 states reported zero violations but retained incomplete color-contrast findings
  (SVG/off-screen/other manual cases); computed194 active SVG text instances min5.932:1.
- Keyboard-only architecture/file inspection was previously mouse-span based. Sidebar
  buttons, SVG role/name/focus/Enter/Space and readable zoom provide actual recovery;
  source-dialog Escape restores focus. No screen-reader-user certification.
- Screenshot inspection found readable-zoom labels drawn behind overlaid controls on
  large graphs. Separate toolbar/legend rows and clipped SVG now have1280/390 geometry
  regression checks. Paging preserves whole-map target inspection and real cycles.
- Candidate-1 timing gate genuinely failed at **10.457ms** p95 in a100-sample PATH case,
  and did not package. Failed/earlier exploratory reports remain under artifacts.
  Increased warmup/sample coverage (50 +1000/query/mode; **50,000 measured samples**)
  and actual narrow scorer optimizations are fully disclosed. Candidate-2 worst8.322ms,
  on shared M4 Pro load-average~10.7; this is a local observation, not a guarantee under
  arbitrary load. No queries or misses were relabeled to meet the target.
- Full raw layout covers all files, not the bounded canvas; sample counts and
  synchronous Ask/render vs two paint opportunities are separate. Browser scheduling
  was visibly slower than the scorer. No end-to-end<10ms assertion.
- First exploratory full smoke mixed newly edited scorer source with an older rendered
  fingerprint; feedback correctly marked8 records ineligible and failed the test. Later
  full rebuild passed; the runner now freezes input hashes during all gates.
- A later precommit run passed all8 gates but packaging hit a citation-loop variable
  shadowing the verification file path. Fixed with a dedicated immutable path name and
  positive isolated unit regression; unit fixtures are not release evidence. Package
  stdout/stderr/returncode now have separate durable receipts.
- No unrecoverable state was observed in the recorded flows. This is not a universal
  no-P0/P1 certification; severe findings from Eric/parent review can still block release.

### Eric's unaided acceptance script — still pending

- [ ] Without operational assistant help, open one real demo; find/inspect a file;
      navigate tour evidence or its explicit unavailable state; explain an impact witness.
- [ ] Correct a nickname through explicit review/confirmation; export it; edit grouping
      meaning, export actual JSON, rebuild at the same pin, and import/restore the nickname.
- [ ] Review high-level grouping/source scope/reference migrations; worker sample review
      markers do not substitute for this semantic judgment.
- [ ] Optionally consent, label a real query with confirmed intent, export; designate a
      genuine held-out subset before tuning (ideally ≥20 real labels, a soft goal).
- [ ] Record session steps, assistance needed, failures and severity. Parent independently
      reviews/reruns gates and closes severe findings. Only then decide final release.

The worker observes no unrecoverable defect in its specified flows; that is **not** a
blanket no-P0/P1 certification. Human acceptance and parent review are release blockers,
not silently ticked checkboxes.
