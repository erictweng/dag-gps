[BUILD] DAG GPS — GPT-5.6 Sol independent reviewer
Milestone: Phase 1 repository import
Mini: acquisition security/source gate review
Status: failed
Output: Independent review FAIL on exact acquisition bytes. Five isolated counterexamples: replacement refs substitute a different tree for the advertised commit (P1); connectivity-only fsck accepts corrupted reachable blob bytes (P1); object-directory symlinks escape entry containment and are accepted (P1); inherited PATH executes a substitute production Git binary (P1); stale .staging-* bytes bypass total cache quota (P2). No production fixes or next-mini work performed. Report: .hsub/reports/phase1-acquisition-review.md.
Verification: SHA-256 repositories.py 20f2a3f59df19cd32897134c384f46929ae80ab678af62bd99e54c25700bde7a; test_repository_import.py 45d00d187298f501326743c50a3d9a4ad9846a66f3dccfc901adc6bcaeb0d849. Focused suite exit 0, 18/18 in 4.134s. Review-owned security probes exit 0 with 5/5 counterexamples. Declared real cached pin independently had type commit and full fsck exit 0, which does not cover poisoned caches. Receipts: artifacts/phase1-acquisition-review/.
Next: Acquisition gate is not ready for inventory/preview. Fix all five findings with regressions, rerun on new fingerprints, then obtain a fresh independent review.
