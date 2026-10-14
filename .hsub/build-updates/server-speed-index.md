[BUILD] DAG GPS — Hermes
Milestone: server speed
Mini: 1/1 — validate snapshots once and reuse packet indexes
Status: verified
Output: Implementation 8277e35 on isolated server-speed; generation-aware snapshot LRU, packet-sized validation, all routes wired, leased persistent workers.
Verification: 473 Python and 212 JS tests pass (zero skips after dependency setup); independent frozen-validator replay 180 packet checks, 71 rejections, 54 real packets, zero differences. Real HTTP 480 requests/repo/version: Honcho p95 487.774→6.993 ms, Salesroom 3.078→1.075 ms; 960 paired response hashes identical. Initial setup attempts retained under artifacts/server-performance.
Verification: All eight unchanged release gates and packaging pass on clean 8bfc232; Python 473/473, JS 212/212, zero skips, release scorer p95 3.547 ms (<10 ms). Receipt: artifacts/server-performance/gates/verification.json. Later changes are docs only.
Next: consultant second opinion; generalist approval remains separate. Cold starts and higher measured combined RSS are disclosed. No next feature, push, merge or PR.
