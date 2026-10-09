[BUILD] DAG GPS — GPT-5.6 Sol worker
Milestone: Phase 1 inventory/preview independent-review fixes
Mini: 1/1 — IRP-01..IRP-05 and adjacent portable-path policy
Status: verified
Output: Targeted regression-backed fixes are complete in six source/test/doc/browser paths. Exact handoff: .hsub/reports/phase1-inventory-preview-fixes.md (SHA-256 9f897162fab5c35f1a33e7e8753960b1fc849e0c773b88d7851d1d591b96bdb4). Prior FAIL/output receipts and accepted acquisition/extractor bytes are unchanged.
Verification: RED retained (snapshot 9 failures/2 errors; preview 1 failure). GREEN: 15 snapshot + 9 preview + 25 acquisition focused tests and all 288 normal Python tests. py_compile/node --check/diff-check passed. Independent adversarial probes passed. Actual pinned itsdangerous import/reuse: 50 files, 282547 bytes, 21 links, producer-bound snapshot e94cc59d…. Chromium 153 click + real Enter detail checks passed on real/unsupported/hostile-cycle rows with zero HTTP(S), console, or page errors.
Next: Parent fresh independent source/browser re-review and acceptance decision. No finding closure, Phase 1 acceptance, full performance/release gate, commit, push, merge, or Phase 2 claim.
