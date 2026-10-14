[BUILD] DAG GPS — Hermes
Milestone: Question parser
Mini: benchmark-fixes — punctuation, cross-kind choices, synonym evidence
Status: verified
Output: Harness coverage corrected first (103b6e5); parser fixes f2c5197 and explicit-choice fix 2b80e8d. Same expanded grid: wrong 800→380 Honcho, 777→712 Salesroom. Period equals question-mark performance. 36 correct→choice cases per repo retain intended targets. Literal synonym conflicts and seven newly exposed parenthesized-path mistakes remain disclosed.
Verification: Full benchmark/reconciliation/source audit pass; 144,746 cases per version, 868,476 timed direct calls, 1,920 real HTTP requests. Python 458/458 and JS 212/212, zero skips; frozen holdouts 18/18 and 7/7 retained, zero new wrong; browser 6/6 with screenshots. All eight unchanged gates and packaging pass on cc69b4a, release p95 3.523 ms. First gate lacked background browser environment; unchanged rerun with explicit dependency paths passed. No performance retries.
Next: dag-consultant second opinion requested; generalist retains final approval. No next feature, server optimization, push, merge or PR.
