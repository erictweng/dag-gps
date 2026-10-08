# Alias learning final verification

Complete locally on `alias-learning`, based on `ba72d1b`; parent independent verification and PR creation remain. No push/merge.

Final `.verify.json` build/test/smoke all exit 0; required files all present; `git diff --check` passes. Exact commands/logs: `artifacts/alias-final-verification.json` and `alias-{build,test,smoke}.log`.

- 106 Python + 87 JS tests, including 14 pure alias tests and all 272 literal real-file-path precedence cases.
- Alias browser: 19 checks, 5 shipped overlay parity cases, nine screenshots; 0 page/console errors and 0 external requests. Real download: `artifacts/alias-export.json`.
- Synthetic alias eval 15/15; 0 negative false accepts / wrong accepted requests; warm p95 1.036625 ms, 450 samples. Not held-out or user-provided evidence.
- Original regression op47/47, top1/top3 44/44, PATH14/14, negative false accepts0/10. Lookup challenge op/label39/40, top1 16/17, top3 17/17, false accepts0/24; bearer-auth miss retained. Node original p95 1.429459 ms (940), lookup0.961917 ms (800).
- Legacy canvas/interactions, M3 canonical5+extras11, lookup19, original47+lookup40 shipped parity, pinned map10/10 + full snapshot parity remain passing.
- Map/layers/router/both old eval datasets byte-equal to `ba72d1b`: `artifacts/alias-scope.json`.

Inspected consent, persisted, file, preview, manager, conflict, 1280 and denied/quota storage screenshots. Final 1280 smoke clicks the existing Fit button to avoid retaining a zoomed canvas; no canvas/zoom/resize runtime edits. Repeated final image loading reached the vision tool's per-image limit after prior inspection, not a test/runtime blocker.

README/STATUS/TASKS/verification recipe/report updated. `docs/ALIAS_LEARNING_REPORT.md` documents semantics, exact gates and trust boundary. PATH learning intentionally disabled with single-endpoint guidance; file:// persistence best-effort with export/import fallback; cross-tab synchronization not implemented; actual Eric queries still pending. `Python judge` was already correct at baseline; harder synthetic `Python judge station` demonstrates real abstention → consent → match. Reusable consent/filename-corpus/synthetic-evidence lessons saved to the offline graph verification skill.
