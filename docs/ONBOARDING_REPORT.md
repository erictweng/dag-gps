# V1.3 — Reviewable project onboarding (worker verified)

Implemented on `v1-onboarding` from clean main
`a5b02554e479b5184204ab6aa7c7190d6605fe91`. Verification recorded
2026-10-07 PDT (2026-10-08 UTC; exact execution timestamp in verification JSON). Parent independent review/rerun/integration
is still required. **Eric semantic approval and unaided release session remain pending.**
The browser roundtrips below are automated worker review samples, not Eric-approved
architecture. No V1.4 query capture or release expansion.

## Workflow

```sh
# Resolve/record an immutable source SHA, not a mutable worktree.
python3 scripts/draft_layers.py --repo /path/to/repo --ref <commit> \
  --out artifacts/my-layer-draft.json
python3 scripts/render_layer_editor.py --draft artifacts/my-layer-draft.json \
  --out dist/my-layer-editor.html
open dist/my-layer-editor.html
```

Inspect folder proposals, ownership reasons and the complete pinned source inventory.
Search paths; select files; rename labels, move files, split a proper subset, merge
selected layers or delete a layer. Undo retains 50 edits; Reset returns to the pinned
proposal. Save a **draft** to resume; imported reviewed JSON still requires fresh
confirmation. Review high-level meaning and migration warnings, explicitly check the
review box, then download `layers.json`. The browser never writes repository files.
Use the command shown in the editor, retaining its exact `--tops` scope:

```sh
python3 scripts/build_project.py --repo /path/to/repo --ref <same-full-commit> \
  --layers /path/to/downloaded/layers.json --tops <scope-shown-by-editor> \
  --without-tours --out-dir dist/my-reviewed-map
```

For an all-source draft, omitting `--tops` reproduces generic discovery. For a scoped
draft, the declared scope is mandatory; a scope mismatch rejects instead of silently
changing evidence. Use a **separate output directory** for a new grouping. If attaching
tours, supply reviewed `--tours` at the exact pin and manually reconcile layer IDs;
existing tour builds still require explicit validated tours or `--without-tours`.

## Contract and implementation decisions

- `scripts/draft_layers.py` resolves the ref once; calls **the same** Git inventory,
  exclusions, archived extraction, assignment, rollup and cycle pipeline as the builder.
  Folder grouping uses exact parent directories. `(root)` explicitly handles flat
  roots; helper-named directories get an explicit non-inference reason. No LLM,
  architectural truth claim, repository-source execution or generated fixture injection.
- IDs are `folder-` plus 16 SHA-256 hex characters of the parent path. The same folder
  keeps its ID across sorted file-order changes/additions and label-only renames.
  Split keeps the original ID with remaining files and allocates a deterministic unused
  `-split-N` ID. Merge retains the first selected ID (visible confirmation), removes
  the others and reports them. Delete leaves owned files visibly unmapped.
- Draft schema **`dag-gps-layer-draft/v1`**, `reviewed: false`: repository/full commit,
  exact source inventory/scope, layers/files/reasons, real typed file links, diagnostics,
  trust and migration warnings. It is **not publishable**. Folder drafts can have
  complete assignments while unresolved extraction or layer cycles block publication.
- Export schema **`dag-gps-reviewed-layers/v1`**: exact `files` ownership, labels/IDs,
  `onboarding.reviewed: true`, repo/commit/inventory/tops and reference warnings.
  The marker records explicit reviewer acknowledgement, **not proof of architectural
  correctness or an authenticated human signature**. An automated smoke can exercise
  that UI but cannot satisfy Eric's semantic gate. Neither draft nor unreviewed export
  can publish through the builder.
- Exact per-file ownership avoids glob metacharacter reinterpretation, especially
  literal `app/api/packs/[slug]/route.ts`. A layer uses `files` **or** `globs`, never
  both. Existing hand-authored legacy specs without schema/onboarding markers remain
  compatible; compatibility is not a new automatic-approval route in the editor.
- Python `onboarding.validate_spec` is shared by draft/build pipelines; assignment and
  cycle logic comes from `build_map`. Dependency-free JS pure operations mirror the
  reviewed contract. Cross-runtime fixtures compare coverage/double ownership and
  first-cycle logic against the actual Python helper across 18 graph variants; actual
  downloads validate through the builder as the final authority.
- Missing/double ownership, empty layers, unresolved local imports and layer cycles
  appear before export. Cycle witnesses show **real file pairs and types**. Same-layer
  file cycles remain in evidence and are not erased. No SCC design, edge stripping or
  invented dependency to make a high-level DAG validate.
- Split/merge/delete require migration warnings; removed IDs never rebound to another
  layer. Imported ownership/ID changes regenerate warnings even if an import drops them.
  Aliases still target stable literal file IDs. Existing layer aliases/tours require
  manual review; the editor does not migrate or auto-edit any overlay or narrative.
- Imports are bounded to **8 MiB**, parsed as JSON, atomically validated, and rendered
  with textContent rather than HTML/eval. Repo/commit/inventory/scope/evidence mismatch
  rejects without replacing edits; imported data cannot alter pinned links/findings.
  Data embedded in HTML escapes `<` and unicode separators; no data executes as source.
  Existing trusted inline JS is repository-owned. No browser requests required.
- Staged build validation and caught-error rollback remain unchanged. Invalid reviewed
  candidates preserve map/HTML/diff/report bytes. Per-file atomic publication is still
  **not a power-loss-safe cross-file transaction**. Use one writer.

## Two real repositories — deliberately separate demo scopes

| Demonstration | Immutable source | Assigned files | Folder layers | Layer links | File links | Scanned / inventory |
|---|---|---:|---:|---:|---:|---:|
| New self onboarding | `a5b02554e479b5184204ab6aa7c7190d6605fe91` | 48 | 3 | 3 | 38 | 47 / 48 |
| New quest onboarding | `749d8b5de490cc2e6a0c98c713fab3ab856da799` | 272 | 38 | 76 | 415 | 182 / 272 |
| Existing frozen self matrix, preserved | `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93` | 27 | 3 | 3 | 20 | 27 / 27 |
| Existing approved quest map/tours, preserved | `749d8b5de490cc2e6a0c98c713fab3ab856da799` | 272 | 18 | 52 | 415 | 182 / 272 |

Counts are distinct typed links, not runtime completeness. The new self pin captures
existing impact/trust/editing modules but intentionally **does not include uncommitted
V1.3 additions**. It is a named supported snapshot, not a claim to audit today's live
worktree. New folder IDs do not overwrite the old `pipeline/browser/tests` matrix.

### Real self full-discovery failure and declared supported scope

Unrestricted new self discovery correctly **rejects** the archived
`scripts/smoke_refresh.cjs` literal `require('../artifacts/refresh-fixture.json')`:
that file is generated by `smoke_refresh.py`, untracked/excluded and absent from the
Git archive. Grouping cannot repair a missing source target. We did not invent its
contents, inject the mutable artifacts directory, delete a dependency or relax unresolved
validation. The full-discovery draft is saved to
`artifacts/onboarding-self-all-source-draft.json`, rendered at
`dist/onboarding-dag-gps-all-source.html`, and demonstrably cannot export.

The supported new self demo declares **47 exact extraction inputs**, excluding only
`scripts/smoke_refresh.cjs`; the **full 48-file assignment inventory is retained**.
The explicit scope is recorded in the draft/export/map/trust and passed unchanged to
build. One unscanned source file is disclosed. This is a bounded demonstration, not
unrestricted whole-repo extraction success. Generic APIs contain no quest-specific
logic; the real-repo demonstration script owns its fixed pins/scope assertion.

New self trust findings: **38 resolved, 19 non-source, 0 unresolved, 11 unsupported,
164 external**. Unsupported includes computed Playwright requires and unmodeled
conditional Python test search paths. Those imports are not suffix-guessed. Quest
scope stays its existing explicit tops `app components lib proxy.ts scripts
browser-runtime runner`: **415 resolved, 14 non-source, 1 unresolved literal HTTP
reference (0 unresolved imports), 8 unsupported, 280 external**.

### Real grouping-cycle review and correction

Both initial real folder drafts have zero grouping cycles. In the actual quest editor,
splitting `lib/runner-client.ts` creates a **real high-level cycle**:
`lib/party-boss-server.ts → lib/runner-client.ts` in one direction and
`lib/runner-client.ts → lib/run-contract.ts` in the other. UI displays exact evidence,
disables reviewed export and retains all **415** typed file links. A real UI merge
back into the original lib ID repairs the grouping cycle and warns about the removed
split ID; it does not claim those imports are false. The new self editor also exercises
real split/merge and file movement. Synthetic fixtures separately retain true file
cycles including self-imports and prove a cyclic reviewed candidate preserves outputs.

Final automated exports apply label-only sample renames after Reset, preserve all
original proposal IDs/ownership, and explicitly acknowledge review through the UI.
**Eric still needs to assess these folder proposals and change responsibilities as
appropriate.** No sample replaces the approved quest architecture or tours.

## Actual export → build → Ask evidence

`node scripts/smoke_onboarding.cjs` regenerates pinned drafts, renders offline HTML,
performs actual clicks/search/rename/split/merge/move/delete/undo/reset/import, and saves
**real browser downloads**:

- `artifacts/onboarding-dag-gps-layers.json`
- `artifacts/onboarding-quest-layers.json`

Those downloaded files, not fabricated in-memory specs, feed `build_project.py` with
recorded pins/tops and new output directories. Source assignments/typed file links,
zero missing/double ownership/empty layers/cycles, and exact source pin are asserted.
Real Ask resolves `scripts/build_map.py` and `lib/runner-client.ts` in built pages.
Corrupted copies of each downloaded spec are rejected with **all four published
outputs byte-identical**. Reimporting a reviewed download clears confirmation.

`maps/dag-gps/onboarding-draft.json` is the deterministic new self proposal.
`maps/dag-gps/onboarding-layers.sample.json` is an **exact copy of the actual browser
export**, retained as a worker smoke sample, **not Eric-approved semantics**.
The old `maps/dag-gps/layers.json` and quest map/layers/tours remain byte-identical.
The normal user artifact `dist/quest-refresh/index.html` remains refreshed with existing
tours, independently of new demo pages:

- `dist/onboarding-dag-gps.html` / `dist/onboarding-quest.html`: editor pages.
- `dist/onboarding-dag-gps/index.html` / `dist/onboarding-quest/index.html`: exported builds.
- `dist/onboarding-dag-gps-all-source.html`: explicit blocked full-discovery example.

## Verification and remaining boundaries

All `.verify.json` non-null **build / test / smoke exit 0**; exact commands, exits,
durations, platform, immutable-input hashes and stdout/stderr:
`artifacts/onboarding-verification.json`, `onboarding-{build,test,smoke}.log`,
plus `.stdout.log` and `.stderr.log`. Worker automated verification:

- **176 Python tests / 130 JS tests**, all pass: 15 new Python and 21 new pure JS tests.
  Stable IDs, exact bracket paths, coverage/movement, split/merge/deletion warnings,
  cycles/witness parity, stale pin/scope rejection, malformed/malicious imports,
  reviewed-marker compatibility and byte preservation. Initial failing reference-
  warning regression preserved in `artifacts/onboarding-red.log` before its fix.
- Strict frozen map parity and quest **10/10 checks**. All legacy canvas/interactions,
  shipped scorer/M3/lookup/alias/refresh/tours/impact/trust gates remain in the recipe.
- Original generated scorer 47/47 operations, 44/44 top1/top3, 14/14 path endpoints;
  lookup challenge **39/40 operation/labels, 16/17 top1, 17/17 top3**, retained bearer-auth
  abstention; alias **15/15 synthetic cases**. Not real-user/held-out accuracy.
- Onboarding browser **14 grouped checks / 10 visually inspected screenshots**,
  **zero page/console errors and zero external requests**. Real UI and file downloads,
  not injected edit-state hooks. 1280/1920 layouts inspected; source file lists scroll,
  long scope commands wrap, warnings expand after ID changes, review stays explicit.
  Existing canvas fit can make large folder file graphs visually dense; source details
  and exact Ask remain readable. Broader scale/accessibility is V1.5, not newly claimed.

Screenshots under `artifacts/onboarding-*.png`: both initial 1920 editors, both review
1280/1920 states, both built Ask states, quest real-cycle evidence and self blocked
full-discovery state. Detailed assertions and counts: `artifacts/onboarding-browser.json`.
Per-demo draft/render/build/rejected logs: `artifacts/onboarding-{self-draft,
self-all-source,quest-draft,render-dag-gps,render-quest,build-dag-gps,build-quest,
rejected-dag-gps,rejected-quest}.log`.

No quest source edits (its pre-existing untracked AGENTS.md/CLAUDE.md preserved), no
remote write/push/merge, no automatic alias/tour migration, no dependency/parser/LLM,
no query logging or release claim. Remaining limits: folder-only proposed responsibility,
bounded static extraction, one explicitly unscanned new self generator consumer,
unknown runtime/coverage, manual semantic and reference review, best-effort file storage
and per-file publication. Parent independent acceptance and Eric's semantic/unaided
session gates remain.
