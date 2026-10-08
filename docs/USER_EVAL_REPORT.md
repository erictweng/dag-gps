# V1.4 — opt-in query feedback and reproducible evaluation

Worker verified **2026-10-07 PDT**, branch `v1-feedback`, starting from clean main
`c6543f6cdc67c237469e7ec8675422a2da7414da`. Parent independently reviews/integrates;
worker does not merge/push. This is feature verification, **not a real-user accuracy
claim or v1 release**. V1.3 is integrated at c6543f6; Eric's semantic review remains pending.

## Delivered / privacy boundary (mini a)

- Query feedback disclosure starts OFF on every page load. No history storage reads
  or writes before explicit consent, including ordinary Ask. Enable loads retained
  local history and records subsequent completed scorer Ask: LOCATE, UPSTREAM,
  DOWNSTREAM, PATH and NOT_SURE. Header and disclosure show **Recording locally**;
  header remains visible while history scrolls. Disable stops capture immediately;
  reload never automatically resumes. No network/telemetry/session auto recording.
- Consent names questions, compact scorer answers, corrections, full source snapshot
  **metadata**, source-map fingerprint, scorer version/SHA, and active alias overlay.
  This is not an archive of the whole repository. Keep the matching map/source pin
  and scorer source for reproduction. No huge probability arrays are recorded.
- Tours/impact Ask are explicitly excluded and report why: curated walkthroughs and
  potential-impact findings have no compatible operation-head label. No forced LOCATE
  mapping. Aliases have separate storage and their existing review/confirmation loop;
  a query label never teaches an alias or silently rewrites an evaluation expectation.
- Correct/Wrong/Unclear are explicit judgments. Correct only prefills accepted scorer
  expectations for review; save is separate. Wrong clears guesses; a replacement may
  remain unknown. Editable operation/real node ID, separate PATH from/to IDs and
  optional directed route truth. Unclear has no gold operation (not NOT_SURE truth).
  Invalid expected IDs/mixed route truth reject without changing the record.
- After consent loads existing history, remove one record or confirmed clear-all (cancel
  preserves); destructive controls are disabled before local access consent. Actual versioned JSON
  download, bounded inert import preview and explicit replacement consent. Wrong repo,
  version, malformed schema, duplicate IDs, matching-snapshot unknown IDs and oversized
  input reject atomically. Same-repo stale source/scorer snapshots are retained visibly
  **ineligible**, never rebound to current IDs. Preview invalidates if history changes.
- Newest **200** records, **90 days**, **2 MiB** maximum; oldest entries are evicted to
  satisfy the byte bound. Age pruning occurs on enable/write, not a background deletion
  timer. Browser-origin data can remain on disk until then; clear explicitly for immediate
  removal. Storage denied/quota failures keep session data, show Unsaved/export advice,
  and do not break Ask navigation. `file://` persistence is browser-dependent/best-effort;
  export/import is the portable fallback. No cross-tab synchronization guarantee.

## Evaluation and held-out safeguards (mini b / infrastructure for c)

`node scripts/eval_user_queries.cjs MAP_JSON EXPORTED_FEEDBACK_JSON OUTPUT_JSON`

Without a dataset argument, the CLI reports an empty user collection, not fabricated
zero-error accuracy. All paths are local; no downloads or remote collection.

- Strict versioned export/record/label schema, candidate/alias/expected ID validation,
  full source pin, graph SHA-256 and scorer SHA-256 matching. Altered/stale snapshots,
  unknown IDs, incompatible routes and unreproducible original answers are explicitly
  ineligible with record/reason, not guessed/remapped or counted as successes.
- `origin`: user vs generated-fixture; `split`: unassigned vs development vs heldout.
  Metrics are separated by both. User controls split before confirming the first
  label; later designation of an already-labeled unassigned case as heldout rejects.
  Split/provenance is immutable once designated; heldout records freeze labels entirely.
  Imports cannot overwrite an existing frozen ID or change its split/origin. Exports
  retain timestamps and freeze markers. **User-editable JSON is not tamper-proof**:
  keep original exports/hashes and do not delete/recreate/relabel cases to improve results.
- Original captured scorer decisions and exact saved-overlay rerun must reproduce.
  Report original, alias-off and saved alias-on separately. Operation top1/top3, raw
  target top1/top3 (PATH counts both heads), accepted wrong targets/operations,
  unnecessary abstention, labeled directed route truth and warm scorer p95. Operation
  top3 includes stable operation-order ties; top3 is not a claim of supported intent.
  Raw target top1 can be right despite an abstention; acceptance is reported separately.
- PATH gold truth is independently checked with directed BFS, ignoring realtime;
  only real, same-kind, explicitly labeled endpoints/route expectations participate.
  A contradictory route label becomes ineligible. Scorer p95 excludes initialization,
  routing, file I/O and UI/render time, with 5 warmups and 20 measured repeats/case.
- Correct/Wrong/Unclear/unlabelled counts remain separate. Wrong without confirmed
  expected intent is not scored. Missing real labels prints **No labeled user cases yet**.

**Mini c real-user tuning is deliberately deferred.** No scorer changes or synthetic
fixture memorization. Collect ideally ≥20 confirmed Eric-authored cases (soft collection
goal, not feature blocker), designate a genuine held-out subset before tuning, then
justify broad fixes with real measurements. Existing actual `runner.py` feedback still
has **unconfirmed intent**; it is not seeded as labeled Eric data. The browser's runner.py
question is a newly generated test fixture, explicitly unlabelled/generated-fixture.

## Actual verification

All current non-null `.verify.json` recipes executed from repository root:
**build 0 / test 0 / smoke 0**, **176 Python + 150 JS tests**, including **20 feedback
unit/evaluation tests**. All legacy gates/pins unchanged; strict snapshot parity remains
10 checks. Scorer source and existing eval cases unchanged. Legacy bearer-auth lookup
miss remains reported. Initial full smoke reached the final new header assertion and
failed only because CSS uppercases visible text; assertion now case-insensitive, full
smoke rerun passed. First attempt retained separately, not hidden.

Browser: `node scripts/smoke_feedback.cjs`, **18 checks / 6 visually inspected screenshots**
at 1920×1080 and 1280×800. Actual typing/Ask/labels/endpoint edits/download/import/reload/
disable/clear/remove, six invalid imports, stale snapshot/inert markup, storage-denied
and quota contexts; zero page/console errors and zero external requests. Original eval
fixtures hash-identical. Default disclosure preserves existing Ask/tours/impact/aliases/
trust/onboarding; every legacy smoke ran on regenerated shipped HTML.

Environment: macOS 26.1 arm64, Apple M4 Pro; Python 3.9.6; Node v26.6.0;
Git 2.50.1 (Apple Git-155); Playwright 1.63.0.
Source pins unchanged:
- quest-coder `749d8b5de490cc2e6a0c98c713fab3ab856da799` (18 layers / 272 files / 415 links).
- Legacy self demo `f92d0cf9ad2fe6ef332dc5922e32c1e22dc96f93`;
  V1.3 newer onboarding snapshot/scope unchanged.
- Scorer SHA-256 `05f40049975855c9a618986f8118c08ec2b68cf844718edb5c58c944c86b329f`.
- Quest canonical scorer-map SHA-256
  `83aa44af345a1ae3b74fb38d1e2b7370ab7d9c01d4521d244c0f3724ec14caeb`.
  Hash covers repo/full pin/nodes/edges/file_edges/layers, excludes volatile build metadata
  and compiled tour status; full original metadata is separately exported.

### Actual browser-exported synthetic dataset — not Eric accuracy

`artifacts/feedback-export-generated.json`: **8 generated-fixture records**,
Correct 3 / Wrong 2 / Unclear 1 / unlabelled 2; **4** lack confirmed intent, **4** eligible,
**0 user-labeled**, **0 ineligible**. CLI evaluated this exact downloaded file:

```sh
node scripts/eval_user_queries.cjs maps/quest-coder/map.json \
  artifacts/feedback-export-generated.json artifacts/feedback-export-eval.json
```

| Generated development (3 evaluable cases) | Original | Alias off | Saved alias on |
|---|---:|---:|---:|
| Operation top1 | 2/3 | 1/3 | 2/3 |
| Operation top3 | 3/3 | 3/3 | 3/3 |
| Raw target top1 / top3 (4 endpoint heads) | 3/4 / 4/4 | 3/4 / 4/4 | 3/4 / 4/4 |
| Accepted wrong targets/operations | 0/2 | 0/1 | 0/2 |
| Unnecessary abstention | 1/3 | 2/3 | 1/3 |
| Explicit no-route truth | 1/1 | 1/1 | 1/1 |
| Warm scorer p95 ms (60 samples) | 1.4208 | 1.3197 | 1.3200 |

One generated fixture marked heldout exercises freeze infrastructure: 1/1 operation
and target top1/top3, 0/1 accepted wrong/abstention, no route-labeled case (rate null);
p95 original/off/on 0.7843/0.7530/1.1954 ms (20 samples each). **Not a genuine unseen
user holdout or statistically meaningful accuracy claim.** The bearer-auth miss remains;
separately confirmed synthetic nickname demonstrates overlay provenance, not scorer tuning.

Export SHA-256:
`83bbee31791df2e3d966aee374b336cd093f4836f58cb4c704d90cfaaa92dac5`.
Timing/export IDs vary on rerun; counts/decisions are asserted, not timing digits.

## Local evidence / next owner

- `artifacts/feedback-verification.json`: exact recipe strings, return codes, versions,
  local timestamps and baseline SHA; `feedback-{build,test,smoke}.log`;
  `feedback-smoke-attempt1.log` retains initial assertion failure.
- `artifacts/feedback-browser.json`, `feedback-export-generated.json`,
  `feedback-export-eval.json`; empty collection report `artifacts/user-query-eval.json`.
- `artifacts/feedback-{consent-1920,import-preview,history-1920,path-label-1280,
  storage-denied,storage-quota}.png`. All six inspected; actual PATH controls show
  separate runner-service/persistence IDs and No route, header recording stays visible.
- Shipped HTML `dist/quest-coder.html`, `dist/quest-refresh/index.html`, legacy self
  `dist/dag-gps/index.html`; no-tours and onboarding demos regenerated by full gates.

Artifacts are ignored/local, not bundled with a fresh clone. Export questions/aliases
and source metadata may be private: review before sharing. Parent reviews code/evidence
and independently reruns; Eric confirms intent/collects cases and performs the eventual
unaided user session. Missing labels block real-user tuning/accuracy claims, **not** this
feature; V1.5/user acceptance and v1 release remain pending.
