[BUILD] DAG GPS — GPT-5.6 Sol security-fix worker
Milestone: Phase 1 acquisition
Mini: 1/1 — AR-01..AR-05 targeted regression-backed fixes
Status: verified
Output: Targeted source/tests only: replacement/graft/alternate rejection with replacement-disabled Git; full object hash fsck; pre-Git symlink/special-file preflight; absolute validated /usr/bin/git with no inherited PATH; fail-closed preserved stale staging under writer lock. Independent FAIL artifacts remain unchanged. Worker-green means ready for parent re-review only; inventory/preview remains gated.
Verification: RED 23 tests: exit 1, 9 failures/1 error. Final focused suite: 23/23 OK. Adapted original attacks: 5/5 rejected. Actual pallets/itsdangerous 672971d production miss/hit: commit type and full fsck exit 0. py_compile and final temporary-index git diff --check: exit 0. Source/test SHA-256: d3c40eb850f30c8deb92288f991334c94f97e32cfca9d3c70f7251b2456f6b45 / 720d5840c9ef94d7dc330f617f2385f787167650aed72e8240850e7eb4fea368.
Next: Parent verifies fingerprints and runs a fresh independent security re-review. Do not launch inventory/preview from worker evidence alone.
