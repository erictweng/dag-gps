# Explicit correction-driven alias learning

Locally verified on `alias-learning`, branched from verified lookup `ba72d1b`.
Eric git identity retained. Parent independently verifies and opens the PR;
this worker does not push or merge. Initially clean worktree. No Claude use,
quest-coder changes, map/layer edits, network learning, backend or model training.

## Behavior and consent

- Only selecting a supported real alternative exposes **Remember this name for
  this node?**. The user enters the specific name, reviews the exact alias text
  and real target ID/path and layer, then separately clicks **Confirm remember**.
  No automatic query harvesting. Override alone, review, cancel, new typing and
  ordinary Ask never save. Editing reviewed text invalidates the pending consent.
- NOT_SURE without a valid explicit choice has no learning controls. PATH learning
  is deliberately disabled for all parses in this milestone, with honest guidance
  to ask about each endpoint separately. This conservative restriction prevents
  storing an entire route question and avoids inventing endpoint phrase selection.
- An immutable overlay is supplied to `createScorer(map, aliases)`; generated map
  and built-in aliases stay unchanged. Exact endpoint phrase matches use
  case/whitespace normalization only, not automatic fuzzy synonyms. A unique
  confirmed nickname contributes a separately explained `learnedAlias` component.
  Scores remain heuristic, not measured correctness probabilities.
- Real exact file paths/basenames outrank learned nicknames, even when basename
  ambiguity must abstain. Dynamic-route bracket paths are recognized as literal
  paths too. Every one of the 272 real file paths is tested against alias hijacking.
- Duplicate normalized name + same node is idempotent. Same normalized name bound
  to different active real nodes produces tied evidence and **Needs your choice**,
  with all conflicting IDs offered (including beyond top three). No silent
  overwrites, structural-prior tie-breaking or duplicate confidence inflation.

## Store, validation and management

`web/aliases.js` is pure, dependency-free validation/store logic; `web/alias-ui.js`
wires the UI. LocalStorage key is `dag-gps:aliases:v1:` plus URL-encoded repository
identity. Schema is `{version: 1, repo, aliases: [{alias, nodeId}]}`. It is not
commit-scoped, so a same-repository rebuild can retain aliases. Tests change commit
metadata and delete nodes without changing the namespace.

Limits: 262,144 UTF-8 bytes (256 KiB), 1,000 input entries, alias length 1–160
characters; empty, overlong, untrimmed, control-character or malformed alias
strings are rejected. Root and entry fields, repo, version, types, node ID string
shape and file size are validated. No secrets should be stored.

**Manage learned aliases** displays exact names, actual paths/layers, conflicts and
orphans. Remove acts on the exact binding. Clear all requires browser confirmation;
cancel preserves the store. Export is an actual JSON browser download, verified by
reading the downloaded file. Import requires a user-selected file, validates the
entire prospective result before any application, and previews all resulting
bindings, mode, conflicts and orphan count. **Merge** is the default; **Replace
all** is explicit and cancellable. Confirm applies the preview; a changed merge
state is re-previewed before application. Invalid imports are atomic: no partial
mutation or writes. Duplicate imports are idempotent.

Unknown/deleted IDs remain visible as quarantined **ORPHAN — not used; no
rebinding** entries, preserved for inspection/export/removal but excluded from
scoring. Counts are shown in preview and import completion. No guessed node
substitution. UI text is escaped; malicious markup is rendered literally, not as
elements, and triggers neither execution nor requests.

Writes are read back before reporting Saved. Inaccessible storage, quota errors or
read-back mismatch report **Unsaved — active this session only**, while navigation
and export continue. `file://` localStorage is browser-dependent and best-effort;
this is not a promise of portability across file paths or browsers. Export/import
is the backup/transfer fallback. Cross-tab concurrent edit synchronization is not
implemented; import confirmation protects only changes within the current page.

## Trust boundary

Renderer safely JSON-encodes trusted shipped scorer/router/alias source. Trusted
alias UI source uses a direct eval of that fixed build-time source string to bind
to the template's private closure, under the same dynamic-source/CSP constraint
as existing `new Function` modules. Neither aliases, import JSON, map values nor
query text are ever passed as code. Safe inline serialization escapes all `<`,
U+2028 and U+2029. New renderer tests execute closing-tag/comment payloads and
confirm data stays data; duplicate module markers are rejected. This remains a
standalone offline HTML file with no companion resource or network hot path.

## Actual verification

All non-null `.verify.json` commands exited **0**. Exact commands, exit codes and
logs are retained in `artifacts/alias-final-verification.json` and
`alias-{build,test,smoke}.log`. The recipe is extended, not replaced:

```sh
# build
python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html

# test
python3 -m unittest discover -s tests -q && node --test tests/scorer.test.cjs tests/eval.test.cjs tests/router.test.cjs tests/lookup.test.cjs tests/alias.test.cjs && node scripts/eval_scorer.cjs && node scripts/eval_lookup.cjs && node scripts/eval_alias.cjs

# smoke
python3 scripts/build_map.py --repo /Users/aibert/projects/quest-coder --ref 749d8b5de490cc2e6a0c98c713fab3ab856da799 --layers maps/quest-coder/layers.json --out artifacts/lookup-map-smoke.json && python3 scripts/check_snapshot.py maps/quest-coder/map.json artifacts/lookup-map-smoke.json && python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html && node scripts/smoke_canvas.mjs dist/quest-coder.html artifacts/ && node scripts/check_interactions.cjs && node scripts/smoke_scorer.cjs && node scripts/smoke_m3.cjs && node scripts/smoke_lookup.cjs && node scripts/smoke_alias.cjs
```

- **106 Python tests** and **87 JS tests** pass, including 14 pure alias tests.
  Existing negative renderer test prints `FAIL missing top-level 'layers'` while
  its assertion succeeds and the suite exits 0; this is expected, not a gate error.
- Pinned rebuild: **10/10 checks** and full snapshot parity ignoring only existing
  documented provenance fields. Map remains 290 nodes: 18 layers, 272 files,
  52 layer edges and 413 file edges. HTML build reports **318.8 KB**.
- Legacy canvas states and real interactions pass (focus/expand/details/Escape,
  tests toggle, double-click, Back, zoom/Fit). M3 **5 canonical + 11 extra checks**,
  lookup **19 checks**, original **47** and lookup **40** shipped-source parity
  cases pass. Prior no-persistence assertion is retained and explicitly labeled
  **WITHOUT explicit consent**, including override alone.
- Alias browser smoke: **19 checks**, real typing/Enter/buttons, consent/cancel,
  empty alias rejection, edit-invalidated consent, same-file reload, removal,
  actual export download, import preview/confirmation/default merge/explicit
  replace/cancel, duplicate handling, six invalid-import classes, escaped markup,
  orphan quarantine, conflict abstention, filename priority, unrelated-query
  abstention, PATH restriction, 1280 viewport Fit, denied storage and quota storage.
  **5** shipped overlay parity cases use the existing 1e-12 numeric tolerance.
  Reports contain **zero page/console errors and zero external requests**.
- `artifacts/alias-scope.json` records byte equality and SHA-256 for map, layers,
  router and both existing eval datasets against `ba72d1b`. No membership changes.

## Synthetic evaluation, not user evidence

`Python judge` already resolves to runner-service with baseline metadata. This is
reported honestly: the required consent/repeat/reload/remove flow demonstrates
explicit learned evidence and returns the exact baseline result on removal; it
does not pretend to correct a previously wrong target. The harder synthetic
`Python judge station` really abstains initially, offers runner-service, and
becomes accepted only after the user chooses and confirms that exact name.

`scripts/eval_alias.cjs` contains **15 worker-draft regression cases**, all retained:
**15/15 pass**, zero wrong accepted requests and zero false accepts on negative
requests. Includes locate/dependencies/dependents, real file aliases, filename
precedence, conflicts, removal, unrelated names and independent PATH endpoints.
450 warm samples are reported in `artifacts/alias-eval.json`; actual current p95
is in that artifact, not a universal latency guarantee.

Existing original generated eval remains **47/47 operation**, **44/44 target
first/top-three**, **14/14 PATH endpoints**, **0/10 negative false accepts**.
Existing lookup challenge remains **39/40 operation/label**, **16/17 top-one**,
**17/17 top-three**, suggestion recall **15/15**, **0/24 negative false accepts**,
**0/15 wrong accepts**. The existing bearer-auth challenge abstention stays a
reported failure; no row was removed, relabeled or tailored to hide current misses.
These datasets informed development and are not held-out or Eric-approved truth.

## Evidence inspection and limits

Nine actual screenshots, all inspected:

- `artifacts/alias-consent.png`
- `artifacts/alias-persisted.png`
- `artifacts/alias-file.png`
- `artifacts/alias-import-preview.png`
- `artifacts/alias-manager.png`
- `artifacts/alias-conflict.png`
- `artifacts/alias-1280.png`
- `artifacts/alias-storage-denied.png`
- `artifacts/alias-storage-quota.png`

Consent text and real target are legible, file IDs and highlights stay real,
malicious markup stays literal, conflicts/orphans and unsaved status are visible.
The sidebar remains scrollable. Initial unstyled controls were brought into the
existing dark theme. One smaller-viewport run retained a zoomed canvas; the final
smoke explicitly exercises the existing **Fit** button and waits before capture,
without altering pan/zoom or resize runtime. The final fitted canvas and choices
show no obvious overlapping/clipped controls. Initial smoke assertion failures
were uppercase heading comparison and strict cross-engine floating equality;
resolved with case-insensitive text and existing parity tolerance, not new scorer
behavior or fabricated output. No unresolved tool blocker.

Remaining limits: endpoint-only learning flow for PATH; exact-phrase nicknames
rather than semantic generalization; browser/file storage portability and
cross-tab edits; sparse responsibility metadata still causes honest abstentions;
static graph reachability and mixed layer/file route restrictions remain unchanged.
Eric's actual failed queries/map review and parent independent rerun remain pending.
