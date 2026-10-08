# V1.3 onboarding — final worker verification / parent handoff

`v1-onboarding` from clean main `a5b02554e479b5184204ab6aa7c7190d6605fe91`.
All non-null `.verify.json` build/test/smoke recipes rerun and exit 0. **176 Python +
130 JS tests**, strict frozen-map parity/10 checks, every legacy browser/eval gate
retained. Exact commands/exits/durations/hash evidence in
`artifacts/onboarding-verification.json`; separate stdout/stderr plus combined
`onboarding-{build,test,smoke}.log` files. Required-file presence and actual-export
sample identity checked; `git diff --check` clean. Worker commits locally with configured
Eric identity; no push/merge. Parent owns independent acceptance/integration/push.

Full offline draft/editor/export/build demonstrated with actual browser downloads on:
- Quest 749d8b5: **272 files, 38 folder layers, 76 layer links, 415 file links**.
- New self a5b0255: **48 files, 3 folder layers, 3 layer links, 38 file links**.

**14 grouped browser checks / 10 inspected screenshots**, zero page/console errors
and external requests. Real rename/search/move/split/merge/delete/undo/reset/import,
actual JSON download then builder, real-path Ask, invalid all-four-byte preservation.
Quest runner-client split exposes a real grouping cycle; UI merge repairs responsibility
without stripping any file links. Existing quest map/layers/tours and frozen old self
matrix are byte-identical; normal dist/quest-refresh user artifact still refreshed.

Read `docs/ONBOARDING_REPORT.md` for schema decisions and exact source/scope limits.
Important: self unrestricted discovery fails closed on a runtime-generated untracked
JSON fixture required by smoke_refresh.cjs. The blocked draft is retained/visible.
Supported new self demonstration explicitly scans **47/48** and excludes only that
JS consumer from extraction, retaining all **48 assignments**. No generated fixture
injection, mutable worktree source, extractor guessing or false completeness claim.

Draft schema is not publishable; reviewed exact-file export requires explicit UI
confirmation and builder pin/inventory/scope validation. Legacy hand-authored glob
specs stay compatible. IDs stay stable on rename; splits/merges/deletes require manual
alias/tour warnings with no rebinding. Imports ≤8 MiB remain inert data; mismatches
reject atomically. Cross-runtime fixtures compare JS findings to Python helpers.

Editor artifacts: `dist/onboarding-{dag-gps,quest}.html`.
Exported map demos: `dist/onboarding-{dag-gps,quest}/index.html`.
Blocked unrestricted self: `dist/onboarding-dag-gps-all-source.html`.
Actual downloads: `artifacts/onboarding-{dag-gps,quest}-layers.json`.
Browser report/screenshots: `artifacts/onboarding-browser.json`, `onboarding-*.png`.
Committed self `onboarding-layers.sample.json` is byte-identical to actual download.

**Eric semantic review remains pending.** Automated samples exercise explicit review
but do not count as Eric-approved architecture. No V1.4 query capture or v1 release
claim. Parent should review the declared new self scope and retained failure, inert
imports, cycle evidence/migration warnings, downloaded roundtrip and legacy preservation.
