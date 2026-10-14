[BUILD] DAG GPS — Hermes
Milestone: Question parser review fixes (t_e1cca752)
Mini: 1/1 — Dispatch, file hints and synonym reasons
Status: verified
Output: Accepted and fixed all three consultant findings; separate review-regression list, frozen sets unchanged.
Verification: All eight unchanged gates and packaging passed on 0059009; Python 458/458, JS 199/199, zero skips; release p95 9.399 ms, no perf retry. RED service fixtures 6 fail/1 pass and real repos 8 fail/8 pass became GREEN 7/7 and 16/16. Frozen per-split metrics unchanged, zero new wrong/overconfident cases. Sixteen browser packet/highlight checks plus Python contracts pass. Initial browser setup skips/missing NODE_PATH resolved with existing local tools. Receipt: artifacts/question-parser/review-fixes/gates/verification.json.
Next: dag-consultant second opinion, then parent approval. No push, merge or PR; no next mini-milestone started.
