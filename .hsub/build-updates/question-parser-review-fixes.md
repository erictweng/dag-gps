[BUILD] DAG GPS — Hermes
Milestone: Question parser review fixes (t_e1cca752)
Mini: 1/1 — Dispatch, file hints and synonym reasons
Status: verifying
Output: Accepted and fixed all three consultant findings; separate review-regression list, frozen sets unchanged.
Verification: RED service fixtures 6 fail/1 pass; real repos 8 fail/8 pass. GREEN 7 service tests and 16 real-repo cases; 199 JS pass; initial Python 458 run with 2 browser skips before NODE_PATH setup. Both frozen evaluations retain prior per-split metrics and zero new wrong/overconfident cases. Sixteen real-app packet/highlight assertions and screenshots captured. Unchanged committed-fix release gates pending.
Next: Complete eight gates, then request dag-consultant second opinion. No push, merge or PR.
