[BUILD] DAG GPS — Hermes
Milestone: Question parser
Mini: 1/1 — rules, synonyms and deterministic concept candidates
Status: verified
Output: Frozen Honcho and late-added Salesroom benchmarks; normalized phrasing/kind hints, explicit synonym fallback, bounded Python docstring/name/path index and candidate-only BM25. No model fallback or side features.
Verification: Exact implementation commit a54fbca: all eight project/release gates passed; 458 Python / 192 JS tests; scorer 47/47, alias 15/15, lookup 39/40; release p95 8.847 ms. 13-question Honcho browser proof/source audit passed. Frozen reports show zero new wrong answers and all 28 negative cases remain no-match. Transient socket/performance failures are retained with passing unchanged reruns. Remaining concept misses and two baseline wrong decisions are documented.
Next: dag-consultant second opinion, then parent approval; no push/merge/PR.
