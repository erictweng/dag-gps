[BUILD] DAG GPS — Hermes
Milestone: Filename lookup + evidence-first answers
Mini: 1/1 — lookup-evidence
Status: verified
Output: Separate file/architecture retrieval, exact path/basename/stem/partial tiers, suggestion-only missing/typo matches, every duplicate full path, explicit overrides, four evidence labels and uncalibrated Details. Grading/authentication handled by declared concept morphology, not query-specific aliases. No persistence or map/router changes.
Verification: Final .verify.json build/test/smoke all exit 0. 104 Python + 73 JS tests; pinned snapshot parity and map 10/10. Existing canvas interactions and M3 5 canonical + 11 extras pass. Lookup 19 UI checks; shipped parity 47 original + 40 lookup; zero errors/requests. Nine lookup screenshots inspected. Original eval op 47/47, target 44/44; separate lookup op/labels 39/40, target top-1 16/17, top-3 17/17, suggestion recall 15/15, false accepted negatives 0/24, wrong accepted requests 0/15. Retained bearer-auth responsibility abstention, not hidden. Full logs: artifacts/lookup-final-verification.json; report: docs/LOOKUP_REPORT.md.
Next: Parent independently verifies the local-only lookup-evidence branch and performs the selective read-only goal check before acceptance. No push/merge or next milestone launch.
