[BUILD] DAG GPS — Hermes
Milestone: parser collision choices
Mini: 1/1 — operation-preserving target choices and clean-checkout tests
Status: verified
Output: Resolve cross-kind names before operation dispatch; preserve choices across graph operations and both endpoints. Optional pinned tests skip explicitly without artifacts; committed mechanics and contract tests remain active.
Verification: 01dfb1b passes all eight unchanged gates and packaging on first attempt: 474 Python / 265 JS, zero skips; release scorer worst p95 4.307 ms. Clean detached checkout: 474 Python pass, 225 JS pass / 8 explicit optional-data skips, removed afterward. Corrected frozen grid: 868,476 timed calls, wrong Honcho 380→288 / Salesroom 712→682, no newly wrong cases. 152/30 matched answers become choices, including 60 formerly correct Honcho matches; frozen hand-written sets unchanged. 160 real-repo packets pass Python contracts. Full report: docs/PARSER_COLLISIONS.md.
Next: Dag-consultant second opinion; final approval remains with generalist. No next feature, push, merge or PR.
