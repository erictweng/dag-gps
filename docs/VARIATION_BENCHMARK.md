# Question-variation benchmark

This measures **robustness to phrasing on known targets**, not real-user accuracy. This receipt includes the punctuation, cross-kind ambiguity and synonym-evidence fixes.

For corrected-grid **before → after** axes, safety trade-offs and the frozen hand-written rerun, see [QUESTION_PARSER_BENCHMARK_FIXES.md](QUESTION_PARSER_BENCHMARK_FIXES.md). The tables below compare main to the fixed parser.

## Headline

| Repo | Version | Generated positive + negative | Correct | Correct or choose | Wrong | Overconfident negatives | Warm p50 / p95 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| honcho | main | 92856 + 240 | 41657/92856 (44.86%) | 54061/92856 (58.22%) | 2799/92856 (3.01%) | 0/240 (0.00%) | 0.234 / 0.480 |
| honcho | parser | 92856 + 240 | 85135/92856 (91.68%) | 89243/92856 (96.11%) | 380/92856 (0.41%) | 0/240 (0.00%) | 0.369 / 1.080 |
| salesroom | main | 51410 + 240 | 29008/51410 (56.42%) | 37712/51410 (73.36%) | 1736/51410 (3.38%) | 0/240 (0.00%) | 0.066 / 0.132 |
| salesroom | parser | 51410 + 240 | 46358/51410 (90.17%) | 48257/51410 (93.87%) | 712/51410 (1.38%) | 0/240 (0.00%) | 0.124 / 0.232 |

Percentages above use positive constructed cases, except overconfidence which uses only negatives. Timing includes both.

| Repo | Main distinct successful strings | Parser distinct successful strings | Unique generated strings | Targets (source checked) |
|---|---:|---:|---:|---|
| honcho | 51230 | 84714 | 88042 | {"file": 42, "layer": 16, "symbol": 30} |
| salesroom | 36176 | 46154 | 49454 | {"file": 30, "layer": 11} |

Counts are case-weighted, not unique-string-weighted: repeated equivalent forms remain in axis cells. Distinct successes deduplicate exact strings across correct + choose-correct cases; one successful target interpretation suffices for this requested metric.

## Frozen hand-written reference (questions unchanged, results rerun)

These author-written questions are not independently sampled user traffic. Their stricter expected-match/expected-choice labels differ from the generated evaluator.

| Repo/split | Version | Cases | Match correct / expected match | Choose correct / expected choose | Negative no-match | Wrong | Overconfident |
|---|---|---:|---:|---:|---:|---:|---:|
| honcho/dev | main | 80 | 17/46 (36.96%) | 4/18 (22.22%) | 16/16 (100.00%) | 2 | 0 |
| honcho/holdout | main | 27 | 6/18 (33.33%) | 1/5 (20.00%) | 4/4 (100.00%) | 0 | 0 |
| honcho/dev | parser | 80 | 46/46 (100.00%) | 13/18 (72.22%) | 16/16 (100.00%) | 1 | 0 |
| honcho/holdout | parser | 27 | 18/18 (100.00%) | 5/5 (100.00%) | 4/4 (100.00%) | 0 | 0 |
| salesroom/dev | main | 32 | 9/20 (45.00%) | 3/6 (50.00%) | 6/6 (100.00%) | 0 | 0 |
| salesroom/holdout | main | 11 | 3/7 (42.86%) | 0/2 (0.00%) | 2/2 (100.00%) | 0 | 0 |
| salesroom/dev | parser | 32 | 20/20 (100.00%) | 5/6 (83.33%) | 6/6 (100.00%) | 0 | 0 |
| salesroom/holdout | parser | 11 | 7/7 (100.00%) | 0/2 (0.00%) | 2/2 (100.00%) | 0 | 0 |

## Method and scope

- Versions: main `7db31cdb8e35e00ac41f9c478ffdcf1c75de669b`; parser query code at `2b80e8d370514eae40d88c35a601f22a444c30e6`. Both use the identical parser-era snapshots; this isolates query-code changes, not extraction-version changes. Baseline ignores the extra concept sidecar.
- Seed `dag-variation-v1-20261013`; templates SHA-256 `72e693930dcea20a22532532d50038f4bec51c74bc97e0f00d2173068655a388`. Frozen targets, pins, source checks and known directed-edge pairs are in `eval/variation_templates.json`.
- Targets were selected before querying: SHA-256(seed + ID) order, minimum quotas, plus all applicable synonym-name targets. Each file is checked against a pinned Git blob; Python symbols against AST name/start; folders against Git tree descendants. PATH/FLOW pairs are directed observed edges, not runtime proofs. `python3 scripts/freeze_variation_targets.py --check` rechecks source selection without querying.
- Grid is sparse and deterministic: operation phrase × target form, plus each independent perturbation on the canonical target, one axis at a time. This is not the exponential full Cartesian product or an interaction-completeness claim. No tuning or successful-target selection after running. Contractions are separate operation-phrase rows (straight/curly apostrophe and omitted apostrophe).
- Review correction at `103b6e5` added missing supported dependency phrasings and 10 source-checked file PATH edges per repo, plus route wording. Targets and seed did not change. The expanded grid was rerun before parser edits and frozen for this before/after comparison. The additional `trace X` wording is an unsupported stress case, not a claimed operation rule (`trace from X` is supported). Original receipt remains in Git at `2f7a2fb` and local `artifacts/question-parser/benchmark-fixes/original/`.
- Construction strata preserve strict labels: mismatching-kind first, then strings with multiple distinct operation/target labels, then unambiguous. These are mutually exclusive diagnostic strata, not relabeling wrong answers as successes. Correct-only operation timing conditions on actually matching the intended target and operation; its sample count differs when coverage changes.
- File/folder operations: LOCATE, UPSTREAM (dependencies), DOWNSTREAM (dependents). Python symbol operations: LOCATE, CALLERS, CALLEES, TRACE. PATH/FLOW use the chosen connected pairs. Zero-degree traversal is a valid operation; symbol dependency/import phrasings are not mislabeled as file-import operations. No TS/JS symbols exist in these snapshots.
- Target forms include path, basename, stem, folder name, symbol name, qualified name and exact symbol ID; synonyms only where the frozen table applies. Case changes affect the target, not the sentence. Kind agreement is broad file/folder/symbol agreement, not function-vs-class semantic correctness. Typo inserts one `z` at the end; findings do not generalize to arbitrary edit errors.
- Negatives: 240 per repo (80 absent-concept phrases, 80 nonsense, 80 existing-name + absent hash suffix). Exact generated names are checked absent. The concept phrases are synthetic, not a comprehensive semantic-absence oracle; the suffix near misses are easier than one-edit typos. Positive one-edit cases are measured separately.
- Correct requires matched status, exact intended seed (not incidental selected nodes), and operation. Directed path success requires a witness from intended A to B. Choose-correct requires intended candidate(s) and operation; file choice packets leave operation NOT_SURE, so the same version scorer’s requestedOperation supplies the operation outside timed regions. Alternatives missing the intended target, unsupported and no-path are unresolved, never counted as successful or confident-wrong. No-match means actual no-match status. Wrong means confidently matched wrong seed or operation. Overconfident means any matched negative.
- Confidence here means API matched status, not calibrated probability. Only the first packet/choice page is graded; no pagination or simulated human choice. The grid tests query interpretation, not completeness of all graph edges or traversal pages.

### Reproduce

From this worktree, with the existing pinned `artifacts/question-parser/{honcho,salesroom}/snapshot.json` and cached Git sources:

```sh
node scripts/bench_variations.cjs && node scripts/verify_variations.cjs && python3 scripts/report_variations.py
```

The runner checks snapshot hashes, archives local main `7db31cd` without checking out another branch, runs both services, starts real loopback WorkspaceServers, and writes raw JSONL/HTTP logs under `artifacts/variation-benchmark/`. No network import, model calls, push, merge or PR. Large artifacts are local/ignored; `eval/variation_results.json` is the committed summary. A new checkout needs the same pinned snapshot artifacts; this command does not silently rebuild a different extraction.

## Speed and variance

Machine: `{"platform": "darwin", "release": "25.1.0", "arch": "arm64", "cpu": "Apple M4 Pro", "cores": 12, "memory": 25769803776, "node": "v26.8.2"}`. Load averages before `[5.60009765625, 4.560546875, 3.89697265625]`, after `[4.4296875, 4.46533203125, 4.212890625]`.

Direct path: real createQueryService.query, the same function as query_worker.cjs; 200 seeded warmup requests and 3 measured sweeps. Cold: 3 snapshot reads/JSON parses and service/index constructions, excluding require/module compilation; OS disk cache is not flushed. First construction is process-cold; later constructions are rebuilds.
Version order is main then parser; no CPU isolation, process restart per sweep, randomized version order, or confidence intervals. Timing variance includes GC/scheduler effects. All direct raw timings are retained. Tier names are observable packet buckets: no-match status first, then BM25 fallback reason, synonym reason, otherwise literal (includes lexical/fuzzy alternatives). This is not internal stage-exclusive profiler instrumentation.

| Repo/version | Scope | n | p50 ms | p95 ms | p99 ms | max ms | mean ± population SD ms |
|---|---|---:|---:|---:|---:|---:|---|
| honcho/main | all | 279288 | 0.234 | 0.480 | 0.725 | 2.112 | 0.261 ± 0.132 |
| honcho/main | tier:literal | 174309 | 0.232 | 0.545 | 0.916 | 2.112 | 0.287 ± 0.135 |
| honcho/main | tier:synonym | 0 | n/a | n/a | n/a | n/a | n/a |
| honcho/main | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| honcho/main | tier:no-match | 104979 | 0.242 | 0.374 | 0.479 | 1.005 | 0.219 ± 0.115 |
| honcho/main | op:CALLEES | 5580 | 0.017 | 0.982 | 1.114 | 1.512 | 0.134 ± 0.298 |
| honcho/main | op:CALLERS | 13950 | 0.270 | 0.573 | 1.049 | 1.600 | 0.227 ± 0.209 |
| honcho/main | op:DOWNSTREAM | 65376 | 0.230 | 0.577 | 0.676 | 1.060 | 0.275 ± 0.120 |
| honcho/main | op:FLOW | 870 | 0.022 | 0.846 | 1.104 | 1.223 | 0.091 ± 0.244 |
| honcho/main | op:LOCATE | 115332 | 0.232 | 0.336 | 0.631 | 1.768 | 0.241 ± 0.102 |
| honcho/main | op:PATH | 17400 | 0.423 | 0.527 | 0.673 | 1.742 | 0.403 ± 0.128 |
| honcho/main | op:TRACE | 5580 | 0.250 | 0.798 | 1.286 | 2.112 | 0.215 ± 0.259 |
| honcho/main | op:UPSTREAM | 54480 | 0.236 | 0.424 | 0.510 | 1.268 | 0.273 ± 0.080 |
| honcho/main | correct-op:CALLEES | 744 | 0.918 | 1.141 | 1.346 | 1.512 | 0.866 ± 0.214 |
| honcho/main | correct-op:CALLERS | 744 | 0.934 | 1.132 | 1.232 | 1.600 | 0.879 ± 0.195 |
| honcho/main | correct-op:DOWNSTREAM | 34710 | 0.236 | 0.619 | 0.719 | 1.060 | 0.312 ± 0.150 |
| honcho/main | correct-op:FLOW | 66 | 0.991 | 1.201 | 1.223 | 1.223 | 0.921 ± 0.198 |
| honcho/main | correct-op:LOCATE | 46245 | 0.220 | 0.358 | 0.971 | 1.768 | 0.242 ± 0.117 |
| honcho/main | correct-op:PATH | 7380 | 0.429 | 0.530 | 0.673 | 1.105 | 0.441 ± 0.053 |
| honcho/main | correct-op:TRACE | 372 | 0.992 | 1.574 | 2.002 | 2.112 | 0.996 ± 0.306 |
| honcho/main | correct-op:UPSTREAM | 34710 | 0.262 | 0.443 | 0.537 | 1.268 | 0.295 ± 0.087 |
| honcho/main | repeat:1 | 93096 | 0.241 | 0.495 | 0.727 | 2.070 | 0.267 ± 0.133 |
| honcho/main | repeat:2 | 93096 | 0.233 | 0.475 | 0.738 | 2.112 | 0.260 ± 0.133 |
| honcho/main | repeat:3 | 93096 | 0.229 | 0.467 | 0.707 | 1.989 | 0.256 ± 0.130 |
| honcho/parser | all | 279288 | 0.369 | 1.080 | 1.563 | 7.343 | 0.480 ± 0.287 |
| honcho/parser | tier:literal | 268413 | 0.368 | 1.084 | 1.563 | 7.343 | 0.482 ± 0.287 |
| honcho/parser | tier:synonym | 1107 | 0.732 | 1.850 | 2.059 | 2.575 | 0.929 ± 0.416 |
| honcho/parser | tier:BM25 fallback | 210 | 0.536 | 1.630 | 1.774 | 1.860 | 0.769 ± 0.425 |
| honcho/parser | tier:no-match | 9558 | 0.396 | 0.614 | 0.859 | 1.462 | 0.364 ± 0.191 |
| honcho/parser | op:CALLEES | 5580 | 0.486 | 1.145 | 1.620 | 3.804 | 0.600 ± 0.296 |
| honcho/parser | op:CALLERS | 13950 | 0.483 | 1.164 | 1.625 | 3.543 | 0.596 ± 0.298 |
| honcho/parser | op:DOWNSTREAM | 65376 | 0.342 | 0.742 | 0.895 | 1.997 | 0.392 ± 0.172 |
| honcho/parser | op:FLOW | 870 | 0.520 | 1.619 | 2.290 | 2.666 | 0.766 ± 0.453 |
| honcho/parser | op:LOCATE | 115332 | 0.359 | 1.299 | 1.796 | 7.343 | 0.528 ± 0.368 |
| honcho/parser | op:PATH | 17400 | 0.609 | 0.798 | 0.989 | 1.986 | 0.595 ± 0.142 |
| honcho/parser | op:TRACE | 5580 | 0.482 | 1.348 | 1.828 | 3.043 | 0.600 ± 0.325 |
| honcho/parser | op:UPSTREAM | 54480 | 0.358 | 0.590 | 0.739 | 1.988 | 0.388 ± 0.116 |
| honcho/parser | correct-op:CALLEES | 5334 | 0.492 | 1.162 | 1.624 | 3.804 | 0.611 ± 0.296 |
| honcho/parser | correct-op:CALLERS | 13335 | 0.490 | 1.178 | 1.634 | 3.543 | 0.607 ± 0.297 |
| honcho/parser | correct-op:DOWNSTREAM | 58926 | 0.346 | 0.747 | 0.891 | 1.997 | 0.404 ± 0.165 |
| honcho/parser | correct-op:FLOW | 840 | 0.512 | 1.626 | 2.290 | 2.666 | 0.763 ± 0.461 |
| honcho/parser | correct-op:LOCATE | 107553 | 0.360 | 1.305 | 1.799 | 7.343 | 0.540 ± 0.369 |
| honcho/parser | correct-op:PATH | 16470 | 0.613 | 0.801 | 0.991 | 1.986 | 0.603 ± 0.127 |
| honcho/parser | correct-op:TRACE | 2667 | 0.610 | 1.542 | 1.982 | 3.043 | 0.724 ± 0.401 |
| honcho/parser | correct-op:UPSTREAM | 50280 | 0.364 | 0.588 | 0.728 | 1.988 | 0.391 ± 0.115 |
| honcho/parser | repeat:1 | 93096 | 0.376 | 1.057 | 1.512 | 3.526 | 0.487 ± 0.273 |
| honcho/parser | repeat:2 | 93096 | 0.356 | 1.067 | 1.529 | 3.804 | 0.466 ± 0.286 |
| honcho/parser | repeat:3 | 93096 | 0.372 | 1.106 | 1.645 | 7.343 | 0.485 ± 0.301 |
| salesroom/main | all | 154950 | 0.066 | 0.132 | 0.222 | 1.203 | 0.079 ± 0.038 |
| salesroom/main | tier:literal | 120588 | 0.066 | 0.136 | 0.227 | 1.203 | 0.081 ± 0.038 |
| salesroom/main | tier:synonym | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/main | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/main | tier:no-match | 34362 | 0.064 | 0.122 | 0.145 | 0.716 | 0.070 ± 0.033 |
| salesroom/main | op:DOWNSTREAM | 45900 | 0.065 | 0.115 | 0.135 | 1.203 | 0.073 ± 0.026 |
| salesroom/main | op:LOCATE | 53550 | 0.063 | 0.117 | 0.138 | 0.932 | 0.070 ± 0.029 |
| salesroom/main | op:PATH | 16530 | 0.119 | 0.231 | 0.265 | 0.919 | 0.135 ± 0.060 |
| salesroom/main | op:UPSTREAM | 38250 | 0.066 | 0.112 | 0.133 | 0.650 | 0.073 ± 0.024 |
| salesroom/main | correct-op:DOWNSTREAM | 24270 | 0.063 | 0.091 | 0.119 | 1.203 | 0.066 ± 0.020 |
| salesroom/main | correct-op:LOCATE | 31272 | 0.062 | 0.091 | 0.118 | 0.932 | 0.065 ± 0.021 |
| salesroom/main | correct-op:PATH | 7212 | 0.116 | 0.194 | 0.248 | 0.919 | 0.123 ± 0.037 |
| salesroom/main | correct-op:UPSTREAM | 24270 | 0.064 | 0.092 | 0.119 | 0.591 | 0.067 ± 0.019 |
| salesroom/main | repeat:1 | 51650 | 0.072 | 0.139 | 0.245 | 0.932 | 0.086 ± 0.043 |
| salesroom/main | repeat:2 | 51650 | 0.064 | 0.127 | 0.218 | 0.896 | 0.078 ± 0.036 |
| salesroom/main | repeat:3 | 51650 | 0.060 | 0.116 | 0.204 | 1.203 | 0.072 ± 0.032 |
| salesroom/parser | all | 154950 | 0.124 | 0.232 | 0.291 | 1.207 | 0.131 ± 0.046 |
| salesroom/parser | tier:literal | 147315 | 0.124 | 0.232 | 0.292 | 0.981 | 0.131 ± 0.045 |
| salesroom/parser | tier:synonym | 324 | 0.201 | 0.373 | 0.409 | 0.436 | 0.215 ± 0.052 |
| salesroom/parser | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/parser | tier:no-match | 7311 | 0.127 | 0.214 | 0.264 | 1.207 | 0.123 ± 0.054 |
| salesroom/parser | op:DOWNSTREAM | 45900 | 0.120 | 0.182 | 0.272 | 1.207 | 0.121 ± 0.039 |
| salesroom/parser | op:LOCATE | 53550 | 0.125 | 0.168 | 0.270 | 0.700 | 0.126 ± 0.037 |
| salesroom/parser | op:PATH | 16530 | 0.209 | 0.266 | 0.380 | 0.981 | 0.200 ± 0.057 |
| salesroom/parser | op:UPSTREAM | 38250 | 0.121 | 0.152 | 0.194 | 0.743 | 0.119 ± 0.030 |
| salesroom/parser | correct-op:DOWNSTREAM | 40500 | 0.120 | 0.181 | 0.252 | 0.661 | 0.121 ± 0.036 |
| salesroom/parser | correct-op:LOCATE | 48342 | 0.124 | 0.160 | 0.258 | 0.700 | 0.124 ± 0.035 |
| salesroom/parser | correct-op:PATH | 15702 | 0.209 | 0.266 | 0.381 | 0.981 | 0.201 ± 0.054 |
| salesroom/parser | correct-op:UPSTREAM | 34530 | 0.120 | 0.147 | 0.193 | 0.743 | 0.118 ± 0.029 |
| salesroom/parser | repeat:1 | 51650 | 0.124 | 0.232 | 0.306 | 0.981 | 0.131 ± 0.048 |
| salesroom/parser | repeat:2 | 51650 | 0.122 | 0.229 | 0.280 | 1.207 | 0.128 ± 0.044 |
| salesroom/parser | repeat:3 | 51650 | 0.127 | 0.233 | 0.293 | 0.633 | 0.133 ± 0.045 |

| Repo/version | Cold read+parse ms (3) | Cold service/index ms (3) |
|---|---|---|
| honcho/main | 26.054, 24.822, 54.670 | 35.848, 27.655, 29.884 |
| honcho/parser | 42.893, 23.694, 23.709 | 93.417, 107.602, 65.686 |
| salesroom/main | 0.375, 0.292, 0.253 | 1.698, 1.290, 1.185 |
| salesroom/parser | 0.591, 0.549, 0.460 | 5.017, 3.489, 2.886 |

### Real HTTP overhead

240 deterministic distributed questions × 2 repeats = 480 measured requests per repo/version, after 20 warmups. Serial loopback requests, fresh TCP connection per request, full JSON response read. Real Python WorkspaceServer → persistent Node worker → packet contract validation, not a mocked server. Each copied snapshot is explicitly rebound to that version’s query-code hashes and validated. No session capability is logged.
Paired overhead subtracts each question’s median direct-service time from its HTTP time. It includes snapshot loading, integrity/contract validation, IPC, serialization, TCP and Python overhead, not just network transport; direct and HTTP timings are not simultaneous. Honcho HTTP is much slower than its JS algorithm. This card does not optimize it.

| Repo/version | n | HTTP p50/p95/p99/max ms | Matched direct p50/p95 ms | Difference p50/p95 ms | Repeat p95 ms |
|---|---:|---|---|---|---|
| honcho/main | 480 | 474.076 / 546.834 / 567.340 / 585.960 | 0.233 / 0.536 | 473.795 / 546.649 | 482.101, 559.944 |
| honcho/parser | 480 | 615.107 / 818.666 / 982.871 / 1102.122 | 0.338 / 1.028 | 614.774 / 818.327 | 692.470, 850.437 |
| salesroom/main | 480 | 4.506 / 5.215 / 5.912 / 7.637 | 0.076 / 0.143 | 4.398 / 5.131 | 5.360, 5.089 |
| salesroom/parser | 480 | 5.558 / 6.279 / 6.654 / 8.790 | 0.125 / 0.230 | 5.421 / 6.153 | 6.299, 6.264 |

### Worst 10 HTTP requests per repo/version

| Repo/version | Operation | Question | ms | Response bytes |
|---|---|---|---:|---:|
| honcho/main | DOWNSTREAM | `downstream of src/backlog.py live` | 585.960 | 10839 |
| honcho/main | UPSTREAM | `upstream of kilo-honcho/src/tui/sidebar.tsx layer` | 576.016 | 1685 |
| honcho/main | PATH | `how does script src/deriver/consumer.py connect to script src/webhooks/webhook_delivery.py` | 575.639 | 2230 |
| honcho/main | PATH | `route from module src/telemetry/events/__init__.py to module src/telemetry/events/api.py` | 568.634 | 2248 |
| honcho/main | LOCATE | `show migrations/env.py layer` | 567.340 | 1550 |
| honcho/main | LOCATE | `where is folder tests/llm/test_history_adapters.py located` | 566.901 | 1614 |
| honcho/main | LOCATE | `src/config.py part` | 566.241 | 1532 |
| honcho/main | LOCATE | `where are scripts located` | 565.092 | 1315 |
| honcho/main | DOWNSTREAM | `what would break if src/llm/backends/anthropic.py logic changed` | 564.094 | 216056 |
| honcho/main | CALLEES | `what does def sdks/python/src/honcho/types.py#AsyncDialecticStreamResponse.get_final_response@166 call` | 563.393 | 1154 |
| honcho/parser | LOCATE | `database` | 1102.122 | 1390 |
| honcho/parser | DOWNSTREAM | `what imports SRC/SCHEMAS` | 1059.012 | 18057 |
| honcho/parser | CALLEES | `callees of src/config.py#ModelConfig._normalize_legacy_model_format@361 thing` | 990.673 | 4709 |
| honcho/parser | LOCATE | `where’s sdks/python/src/honcho/types.py#AsyncDialecticStreamResponse.get_final_response@166 defined` | 989.138 | 2047 |
| honcho/parser | DOWNSTREAM | `downstream of tests/vector_store/test_chroma_dependency.py located` | 982.871 | 1945 |
| honcho/parser | LOCATE | `find script migrations` | 922.043 | 1406 |
| honcho/parser | DOWNSTREAM | `downstream of method tests/integration` | 890.885 | 1604 |
| honcho/parser | LOCATE | `find method src/startup` | 882.246 | 1412 |
| honcho/parser | LOCATE | `where is examples/granola/honcho_granola.py#peer_id_from@434 defined` | 880.204 | 3087 |
| honcho/parser | LOCATE | `where is class mcp/src/config.ts` | 871.390 | 1645 |
| salesroom/main | UPSTREAM | `what does Src/Lib/Track.Ts import` | 7.637 | 1368 |
| salesroom/main | LOCATE | `file app/(seller)/seller` | 7.607 | 1362 |
| salesroom/main | PATH | `how does src/components/modules/__tests__ reach src/components/modules` | 6.789 | 1522 |
| salesroom/main | LOCATE | `locate src/server part` | 6.057 | 1460 |
| salesroom/main | UPSTREAM | `which does file app/room/[slug] use` | 5.912 | 1369 |
| salesroom/main | LOCATE | `where’s package app/api/accounts` | 5.745 | 1476 |
| salesroom/main | UPSTREAM | `which do module src/lib/types.ts import` | 5.691 | 1618 |
| salesroom/main | PATH | `how does src/lib/__tests__/progress.test.ts code connect to src/lib/progress.ts code` | 5.683 | 2217 |
| salesroom/main | DOWNSTREAM | `what would break if src/components/ui/Card.tsx live changed` | 5.652 | 1762 |
| salesroom/main | DOWNSTREAM | `where is src/components/ui live called from` | 5.615 | 1486 |
| salesroom/parser | UPSTREAM | `upstream from SRC/LIB/__TESTS__/ROBUSTNESS.TEST.TS` | 8.790 | 7849 |
| salesroom/parser | DOWNSTREAM | `who invokes app/(seller)/seller logic` | 8.656 | 1505 |
| salesroom/parser | DOWNSTREAM | `downstream of src/components/ui/Avatar.tsx lives` | 7.948 | 1776 |
| salesroom/parser | DOWNSTREAM | `where is src/lib/http.ts part called from` | 7.216 | 1717 |
| salesroom/parser | PATH | `how does the src/components/buyer get to the app/api/auth/login` | 6.654 | 1740 |
| salesroom/parser | UPSTREAM | `dependencies of function src/lib/__tests__/insights.test.ts` | 6.646 | 3468 |
| salesroom/parser | LOCATE | `show src/server thing` | 6.598 | 1321 |
| salesroom/parser | PATH | `how does dir src/components/modules/__tests__/StakeholderMap.test.tsx get to dir src/components/modules/StakeholderMap.tsx` | 6.589 | 2519 |
| salesroom/parser | UPSTREAM | `what does src/lib/__tests__/robustness.test.ts depend on.` | 6.520 | 7856 |
| salesroom/parser | LOCATE | `show me src/lib/__tests__/sections.test.ts.` | 6.493 | 1601 |

## honcho: outcome tables

Each cell: correct count; correct-or-choose count/denominator (%); wrong count. Δ is percentage-point gain in correct-or-choose.

### operation

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| CALLEES | 248/1860 (13.33%) correct; 264/1860 (14.19%); 0 wrong | 1778/1860 (95.59%) correct; 1794/1860 (96.45%); 0 wrong | +82.26 |
| CALLERS | 248/4650 (5.33%) correct; 264/4650 (5.68%); 0 wrong | 4445/4650 (95.59%) correct; 4485/4650 (96.45%); 0 wrong | +90.77 |
| DOWNSTREAM | 11570/21792 (53.09%) correct; 14948/21792 (68.59%); 2368 wrong | 19642/21792 (90.13%) correct; 20820/21792 (95.54%); 148 wrong | +26.95 |
| FLOW | 22/290 (7.59%) correct; 22/290 (7.59%); 0 wrong | 280/290 (96.55%) correct; 280/290 (96.55%); 0 wrong | +88.97 |
| LOCATE | 15415/38444 (40.10%) correct; 19873/38444 (51.69%); 211 wrong | 35851/38444 (93.26%) correct; 37537/38444 (97.64%); 112 wrong | +45.95 |
| PATH | 2460/5800 (42.41%) correct; 3820/5800 (65.86%); 0 wrong | 5490/5800 (94.66%) correct; 5580/5800 (96.21%); 0 wrong | +30.34 |
| TRACE | 124/1860 (6.67%) correct; 132/1860 (7.10%); 0 wrong | 889/1860 (47.80%) correct; 897/1860 (48.23%); 0 wrong | +41.13 |
| UPSTREAM | 11570/18160 (63.71%) correct; 14738/18160 (81.16%); 220 wrong | 16760/18160 (92.29%) correct; 17850/18160 (98.29%); 120 wrong | +17.14 |
### axis

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| case:lower | 1737/2988 (58.13%) correct; 1790/2988 (59.91%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +39.09 |
| case:Title | 102/2988 (3.41%) correct; 142/2988 (4.75%); 0 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +94.24 |
| case:UPPER | 102/2988 (3.41%) correct; 142/2988 (4.75%); 0 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +94.24 |
| filler:code | 2016/2988 (67.47%) correct; 2085/2988 (69.78%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +29.22 |
| filler:defined | 1506/2988 (50.40%) correct; 1986/2988 (66.47%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +32.53 |
| filler:layer | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| filler:live | 1590/2988 (53.21%) correct; 1631/2988 (54.59%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +44.41 |
| filler:lives | 1590/2988 (53.21%) correct; 1631/2988 (54.59%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +44.41 |
| filler:located | 1590/2988 (53.21%) correct; 1631/2988 (54.59%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +44.41 |
| filler:logic | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| filler:part | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| filler:stuff | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| filler:the | 1920/2988 (64.26%) correct; 1981/2988 (66.30%); 84 wrong | 2905/2988 (97.22%) correct; 2928/2988 (97.99%); 0 wrong | +31.69 |
| filler:thing | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| kind:class | 1536/2988 (51.41%) correct; 2016/2988 (67.47%); 84 wrong | 2822/2988 (94.44%) correct; 2822/2988 (94.44%); 0 wrong | +26.97 |
| kind:def | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2822/2988 (94.44%) correct; 2822/2988 (94.44%); 0 wrong | +28.98 |
| kind:dir | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| kind:directory | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| kind:file | 1476/2988 (49.40%) correct; 1476/2988 (49.40%); 84 wrong | 2948/2988 (98.66%) correct; 2948/2988 (98.66%); 0 wrong | +49.26 |
| kind:folder | 1476/2988 (49.40%) correct; 2094/2988 (70.08%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +28.92 |
| kind:function | 1536/2988 (51.41%) correct; 2016/2988 (67.47%); 84 wrong | 2822/2988 (94.44%) correct; 2822/2988 (94.44%); 0 wrong | +26.97 |
| kind:method | 1536/2988 (51.41%) correct; 2016/2988 (67.47%); 84 wrong | 2822/2988 (94.44%) correct; 2822/2988 (94.44%); 0 wrong | +26.97 |
| kind:module | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2948/2988 (98.66%) correct; 2948/2988 (98.66%); 0 wrong | +33.20 |
| kind:package | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +33.53 |
| kind:script | 1476/2988 (49.40%) correct; 1956/2988 (65.46%); 84 wrong | 2948/2988 (98.66%) correct; 2948/2988 (98.66%); 0 wrong | +33.20 |
| punctuation:? | 1850/2988 (61.91%) correct; 1903/2988 (63.69%); 84 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +35.31 |
| punctuation:. | 0/2988 (0.00%) correct; 1150/2988 (38.49%); 0 wrong | 2958/2988 (99.00%) correct; 2958/2988 (99.00%); 0 wrong | +60.51 |
| target-form:basename | 816/1512 (53.97%) correct; 1428/1512 (94.44%); 48 wrong | 864/1512 (57.14%) correct; 1512/1512 (100.00%); 0 wrong | +5.56 |
| target-form:folder-name | 92/576 (15.97%) correct; 218/576 (37.85%); 235 wrong | 108/576 (18.75%) correct; 446/576 (77.43%); 108 wrong | +39.58 |
| target-form:full-path | 1640/2298 (71.37%) correct; 1693/2298 (73.67%); 84 wrong | 2298/2298 (100.00%) correct; 2298/2298 (100.00%); 0 wrong | +26.33 |
| target-form:qualified-name | 203/690 (29.42%) correct; 203/690 (29.42%); 0 wrong | 638/690 (92.46%) correct; 638/690 (92.46%); 0 wrong | +63.04 |
| target-form:stem | 757/2088 (36.25%) correct; 1420/2088 (68.01%); 243 wrong | 888/2088 (42.53%) correct; 1924/2088 (92.15%); 118 wrong | +24.14 |
| target-form:symbol-id | 210/690 (30.43%) correct; 210/690 (30.43%); 0 wrong | 660/690 (95.65%) correct; 660/690 (95.65%); 0 wrong | +65.22 |
| target-form:symbol-name | 140/690 (20.29%) correct; 196/690 (28.41%); 0 wrong | 440/690 (63.77%) correct; 616/690 (89.28%); 0 wrong | +60.87 |
| target-form:synonym:config | 0/36 (0.00%) correct; 0/36 (0.00%); 2 wrong | 0/36 (0.00%) correct; 0/36 (0.00%); 2 wrong | +0.00 |
| target-form:synonym:configuration | 0/144 (0.00%) correct; 0/144 (0.00%); 112 wrong | 0/144 (0.00%) correct; 0/144 (0.00%); 80 wrong | +0.00 |
| target-form:synonym:database | 0/36 (0.00%) correct; 0/36 (0.00%); 30 wrong | 0/36 (0.00%) correct; 0/36 (0.00%); 36 wrong | +0.00 |
| target-form:synonym:db | 0/36 (0.00%) correct; 0/36 (0.00%); 29 wrong | 0/36 (0.00%) correct; 0/36 (0.00%); 36 wrong | +0.00 |
| target-form:synonym:environment | 0/72 (0.00%) correct; 0/72 (0.00%); 0 wrong | 0/72 (0.00%) correct; 72/72 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:msg | 0/144 (0.00%) correct; 0/144 (0.00%); 0 wrong | 0/144 (0.00%) correct; 132/144 (91.67%); 0 wrong | +91.67 |
| target-form:synonym:settings | 0/180 (0.00%) correct; 0/180 (0.00%); 0 wrong | 0/180 (0.00%) correct; 165/180 (91.67%); 0 wrong | +91.67 |
| typo:one-insertion | 0/2988 (0.00%) correct; 1487/2988 (49.77%); 0 wrong | 0/2988 (0.00%) correct; 1518/2988 (50.80%); 0 wrong | +1.04 |
### kindAgreement

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| matching | 4338/9600 (45.19%) correct; 6090/9600 (63.44%); 252 wrong | 9480/9600 (98.75%) correct; 9480/9600 (98.75%); 0 wrong | +35.31 |
| mismatching | 11088/20958 (52.91%) correct; 13536/20958 (64.59%); 672 wrong | 20284/20958 (96.78%) correct; 20284/20958 (96.78%); 0 wrong | +32.20 |
### constructionStratum

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| ambiguous | 178/1998 (8.91%) correct; 1014/1998 (50.75%); 301 wrong | 202/1998 (10.11%) correct; 1533/1998 (76.73%); 306 wrong | +25.98 |
| mismatching-kind | 11088/20958 (52.91%) correct; 13536/20958 (64.59%); 672 wrong | 20284/20958 (96.78%) correct; 20284/20958 (96.78%); 0 wrong | +32.20 |
| unambiguous | 30391/69900 (43.48%) correct; 39511/69900 (56.53%); 1826 wrong | 64649/69900 (92.49%) correct; 67426/69900 (96.46%); 74 wrong | +39.94 |
### matrix

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| {x} × stem | 24/58 (41.38%) correct; 33/58 (56.90%); 12 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +37.93 |
| {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| callees of {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| callees of {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| callees of {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| callers of {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| callers of {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| callers of {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| dependencies of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| dependencies of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| dependencies of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| dependencies of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| dependencies of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependencies of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| dependencies of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependencies of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependencies of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| dependents of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| dependents of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| dependents of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| dependents of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependents of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| dependents of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependents of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependents of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| downstream {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| downstream {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| downstream {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| downstream {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| downstream {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| downstream {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| downstream {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| downstream {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| downstream from {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| downstream from {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| downstream from {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| downstream from {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream from {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| downstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream from {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream from {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| downstream of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| downstream of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| downstream of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| downstream of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| downstream of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| find {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| find {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| find {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| find {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| find {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| find {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| find {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| find {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| find {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| find {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| find {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| from {x} to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| how {x} connect to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| how {x} reach {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| how does {x} connect to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| how does {x} get to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| how does {x} reach {y} × full-path | 20/30 (66.67%) correct; 20/30 (66.67%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +33.33 |
| locate {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| locate {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| locate {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| locate {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| locate {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| locate {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| locate {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| locate {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| locate {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| locate {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| locate {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| locate {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| path between {x} and {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| path from {x} to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| please find {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| please find {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| please find {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| please find {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| please find {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| please find {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| please find {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| please find {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| please find {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| please find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| please find {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| please find {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| route between {x} and {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| route from {x} to {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 20/20 (100.00%) correct; 20/20 (100.00%); 0 wrong | +50.00 |
| show {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| show {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| show {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| show {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| show {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| show {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| show {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| show {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| show {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| show me {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| show me {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| show me {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| show me {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| show me {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| show me {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| show me {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| show me {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show me {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| show me {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show me {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show me {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| trace {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | +0.00 |
| trace {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | +0.00 |
| trace {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | +0.00 |
| trace from {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| trace from {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| trace from {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| upstream {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| upstream {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| upstream {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| upstream {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| upstream {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| upstream {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| upstream {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| upstream {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| upstream from {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| upstream from {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| upstream from {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| upstream from {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream from {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| upstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream from {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream from {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| upstream of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| upstream of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| upstream of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| upstream of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| upstream of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what calls {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| what calls {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what calls {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| what depends on {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what depends on {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what depends on {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what depends on {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what depends on {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what depends on {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what depends on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what depends on {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what depends on {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what does {x} call × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| what does {x} call × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} call × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| what does {x} depend on × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what does {x} depend on × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what does {x} depend on × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what does {x} depend on × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what does {x} depend on × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} depend on × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what does {x} depend on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} depend on × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} depend on × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what does {x} import × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what does {x} import × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what does {x} import × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what does {x} import × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what does {x} import × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} import × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what does {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} import × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} import × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what does {x} use × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what does {x} use × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what does {x} use × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what does {x} use × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what does {x} use × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} use × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} use × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} use × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what does {x} use × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what does {x} use × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what imports {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what imports {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what imports {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what imports {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what imports {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what imports {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what imports {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what imports {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what imports {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what is {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what is {x} × folder-name | 5/16 (31.25%) correct; 12/16 (75.00%); 3 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +6.25 |
| what is {x} × full-path | 57/58 (98.28%) correct; 58/58 (100.00%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +0.00 |
| what is {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| what is {x} × stem | 5/58 (8.62%) correct; 12/58 (20.69%); 3 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +74.14 |
| what is {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| what is {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| what is {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| what is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what is {x} built on × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what is {x} built on × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what is {x} built on × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what is {x} built on × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} built on × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what is {x} built on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} built on × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} built on × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what uses {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what uses {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what uses {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what uses {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what uses {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what uses {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what uses {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what uses {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what uses {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what uses {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what would break if {x} changed × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| what would break if {x} changed × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| what would break if {x} changed × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| what would break if {x} changed × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what would break if {x} changed × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what would break if {x} changed × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what would break if {x} changed × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what would break if {x} changed × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| where are {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where are {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| where are {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| where are {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where are {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| where are {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where are {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where are {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where are {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where are {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where are {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where are {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| where is {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where is {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| where is {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| where is {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| where is {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where is {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × basename | 0/42 (0.00%) correct; 0/42 (0.00%); 24 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +75.00 |
| where is {x} called from × full-path | 0/58 (0.00%) correct; 0/58 (0.00%); 42 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} called from × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 0 wrong | 23/58 (39.66%) correct; 37/58 (63.79%); 8 wrong | +63.79 |
| where is {x} called from × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where is {x} called from × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} called from × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} called from × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} called from × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} called from × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} called from × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where is {x} defined × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +81.25 |
| where is {x} defined × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +5.17 |
| where is {x} defined × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| where is {x} defined × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 4 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +94.83 |
| where is {x} defined × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} defined × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| where is {x} defined × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} defined × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} defined × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | +0.00 |
| where is {x} located × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where is {x} located × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +37.50 |
| where is {x} located × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| where is {x} located × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} located × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +10.34 |
| where is {x} located × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} located × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where is {x} located × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} located × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} located × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} located × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} located × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| where's {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where’s {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where's {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +75.00 |
| where’s {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +75.00 |
| where's {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +5.17 |
| where’s {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +5.17 |
| where's {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where’s {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where's {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +93.10 |
| where’s {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +93.10 |
| where's {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where’s {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where's {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where’s {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where's {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where’s {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where's {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where’s {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where's {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where’s {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where's {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where’s {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where's {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| wheres {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| wheres {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 13/16 (81.25%); 3 wrong | +75.00 |
| wheres {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +5.17 |
| wheres {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| wheres {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 23/58 (39.66%) correct; 55/58 (94.83%); 3 wrong | +93.10 |
| wheres {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| wheres {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| wheres {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| wheres {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| wheres {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| wheres {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| wheres {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| which do {x} import × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| which do {x} import × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| which do {x} import × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| which do {x} import × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| which do {x} import × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which do {x} import × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| which do {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which do {x} import × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which do {x} import × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| which do {x} import × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| which do {x} import × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| which does {x} use × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| which does {x} use × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| which does {x} use × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| which does {x} use × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| which does {x} use × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which does {x} use × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| which does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which does {x} use × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which does {x} use × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| which files depend on {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| which files depend on {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| which files depend on {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| which files depend on {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which files depend on {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| which files depend on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which files depend on {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which files depend on {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |
| who calls {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| who calls {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| who calls {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| who invokes {x} × basename | 0/42 (0.00%) correct; 0/42 (0.00%); 24 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +75.00 |
| who invokes {x} × full-path | 0/58 (0.00%) correct; 0/58 (0.00%); 42 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| who invokes {x} × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 0 wrong | 23/58 (39.66%) correct; 37/58 (63.79%); 8 wrong | +63.79 |
| who invokes {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| who invokes {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who invokes {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| who invokes {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who invokes {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who invokes {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| who invokes {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | +0.00 |
| who uses {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| who uses {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 12/16 (75.00%); 3 wrong | +31.25 |
| who uses {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 58/58 (100.00%) correct; 58/58 (100.00%); 0 wrong | +22.41 |
| who uses {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 54/58 (93.10%); 3 wrong | +8.62 |
| who uses {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who uses {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| who uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who uses {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who uses {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 4/4 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 5/5 (100.00%); 0 wrong | +100.00 |

### Worst axes by parser success (not independent causal effects)

- target-form:synonym:config: 0/36 (0.00%).
- target-form:synonym:configuration: 0/144 (0.00%).
- target-form:synonym:database: 0/36 (0.00%).
- target-form:synonym:db: 0/36 (0.00%).
- typo:one-insertion: 1518/2988 (50.80%).
- target-form:folder-name: 446/576 (77.43%).
- target-form:symbol-name: 616/690 (89.28%).
- target-form:synonym:msg: 132/144 (91.67%).

### main: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/case:Title/no-match | 1137 | `Src/Utils/Search.Py` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/case:UPPER/no-match | 1137 | `SRC/UTILS/SEARCH.PY` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/punctuation:./no-match | 728 | `where is src/utils/search.py defined.` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/kind:file/no-match | 686 | `where is file src/utils/search.py defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/typo:one-insertion/no-match | 674 | `where is src/utils/search.pyz defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/case:Title/no-match | 628 | `what depends on Src/Utils/Search.Py` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/case:UPPER/no-match | 628 | `what depends on SRC/UTILS/SEARCH.PY` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:live/no-match | 591 | `where is src/utils/search.py live defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:lives/no-match | 591 | `where is src/utils/search.py lives defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:located/no-match | 591 | `where is src/utils/search.py located defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:the/no-match | 591 | `where is the src/utils/search.py defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| UPSTREAM/case:Title/no-match | 540 | `what does Src/Utils/Search.Py depend on` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| UPSTREAM/case:UPPER/no-match | 540 | `what does SRC/UTILS/SEARCH.PY depend on` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:layer/no-match | 538 | `where is src/utils/search.py layer defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:logic/no-match | 538 | `where is src/utils/search.py logic defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |

### main: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| TRACE | `trace from TestAnthropicClient.test_anthropic_streaming` | 2.002, 2.112, 1.614 |
| TRACE | `trace from tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199` | 1.592, 2.073, 1.989 |
| TRACE | `trace from test_anthropic_streaming` | 2.070, 1.918, 1.572 |
| TRACE | `trace from tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199?` | 1.986, 1.742, 1.627 |
| TRACE | `trace from tests/live_llm/test_live_anthropic.py#test_live_anthropic_structured_output_and_prefix_caching@29?` | 1.809, 1.726, 1.677 |
| LOCATE | `where is class src/reconciler/backfill.py` | 0.243, 1.768, 0.205 |
| PATH | `route from src/routers to src` | 0.373, 1.742, 0.391 |
| TRACE | `trace from tests/live_llm/test_live_anthropic.py#test_live_anthropic_structured_output_and_prefix_caching@29` | 1.294, 1.680, 1.240 |
| TRACE | `trace from src/deriver/scope_backfill.py#_copy_chunk@308?` | 1.552, 1.645, 1.508 |
| TRACE | `trace from tests/utils/test_filter.py#test_dict_on_jsonb_column_still_works@38` | 1.549, 1.607, 1.385 |

### parser: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/typo:one-insertion/no-match | 644 | `tests/integrationz` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| DOWNSTREAM/typo:one-insertion/no-match | 276 | `who invokes src/utils/search.pyz` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| UPSTREAM/typo:one-insertion/no-match | 160 | `what does tests/integrationz depend on` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| CALLERS/typo:one-insertion/no-match | 150 | `what calls src/utils/agent_tools.py#ObservationsCreatedResult@236z` → no-match / CALLERS; expected ['src/utils/agent_tools.py#ObservationsCreatedResult@236']; selected [] |
| DOWNSTREAM/kind:class/no-match | 116 | `who invokes class src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:def/no-match | 116 | `who invokes def src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:function/no-match | 116 | `who invokes function src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:method/no-match | 116 | `who invokes method src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| PATH/typo:one-insertion/no-match | 110 | `from tests/webhooksz to src/utilsz` → no-match / NOT_SURE; expected ['folder-083d26deb04d283a', 'folder-0f13bc3a2a5b512d']; selected [] |
| CALLEES/typo:one-insertion/no-match | 60 | `what does src/utils/agent_tools.py#ObservationsCreatedResult@236z call` → no-match / CALLEES; expected ['src/utils/agent_tools.py#ObservationsCreatedResult@236']; selected [] |
| TRACE/typo:one-insertion/no-match | 60 | `trace from src/utils/agent_tools.py#ObservationsCreatedResult@236z` → no-match / TRACE; expected ['src/utils/agent_tools.py#ObservationsCreatedResult@236']; selected [] |
| LOCATE/target-form:synonym:configuration/unresolved | 56 | `configuration` → needs-choice / LOCATE; expected ['harness-plugin-core/src/config.ts']; selected [] |
| DOWNSTREAM/target-form:stem/wrong | 46 | `who invokes backfill` → matched / CALLERS; expected ['src/reconciler/backfill.py']; selected ['src/reconciler/backfill.py#Backfill@33'] |
| LOCATE/target-form:folder-name/wrong | 42 | `src` → matched / LOCATE; expected ['folder-a103f549c63bbe7d']; selected ['folder-25a6634263c1b1f6'] |
| LOCATE/target-form:stem/wrong | 42 | `src` → matched / LOCATE; expected ['folder-a103f549c63bbe7d']; selected ['folder-25a6634263c1b1f6'] |

### parser: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| LOCATE | `wheres method tests/alembic/registry.py#register_before_upgrade.<locals>.decorator@33` | 0.353, 0.354, 7.343 |
| LOCATE | `show me dir examples/granola/honcho_granola.py#peer_id_from@434` | 1.216, 1.532, 4.394 |
| CALLEES | `what does tests/llm/test_embedding_client.py#test_openai_embedding_client_rejects_dimension_mismatch@109 live call` | 0.548, 3.804, 0.510 |
| LOCATE | `show dir tests/mock_provider/test_mock_provider.py#test_fixed_tuple_schema_round_trips@283` | 1.317, 3.647, 1.517 |
| LOCATE | `where’s module tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199` | 1.275, 1.422, 3.635 |
| CALLEES | `callees of directory tests/mock_provider/test_mock_provider.py#test_fixed_tuple_schema_round_trips@283` | 2.049, 0.849, 3.554 |
| CALLERS | `who calls directory src/schemas/api.py#ConclusionCreate@681` | 0.811, 0.782, 3.543 |
| LOCATE | `where’s script src/dreamer/trees/base.py#LeafNode@35` | 3.526, 1.023, 2.270 |
| LOCATE | `locate package src/deriver/queue_manager.py#QueueManager._advance_poll_interval@491` | 1.296, 1.371, 3.268 |
| LOCATE | `locate script honcho-cli/tests/test_start.py#test_start_requires_llm_key@72` | 1.234, 1.180, 3.226 |

### Negative outcomes

| Version | No-match | Unresolved choices | Overconfident |
|---|---:|---:|---:|
| main | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |
| parser | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |

## salesroom: outcome tables

Each cell: correct count; correct-or-choose count/denominator (%); wrong count. Δ is percentage-point gain in correct-or-choose.

### operation

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| DOWNSTREAM | 8090/15300 (52.88%) correct; 10291/15300 (67.26%); 1552 wrong | 13500/15300 (88.24%) correct; 14072/15300 (91.97%); 220 wrong | +24.71 |
| LOCATE | 10424/17850 (58.40%) correct; 13367/17850 (74.89%); 114 wrong | 16114/17850 (90.27%) correct; 16811/17850 (94.18%); 302 wrong | +19.29 |
| PATH | 2404/5510 (43.63%) correct; 3908/5510 (70.93%); 0 wrong | 5234/5510 (94.99%) correct; 5334/5510 (96.81%); 0 wrong | +25.88 |
| UPSTREAM | 8090/12750 (63.45%) correct; 10146/12750 (79.58%); 70 wrong | 11510/12750 (90.27%) correct; 12040/12750 (94.43%); 190 wrong | +14.85 |
### axis

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| case:lower | 828/1666 (49.70%) correct; 885/1666 (53.12%); 49 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +44.30 |
| case:Title | 68/1666 (4.08%) correct; 116/1666 (6.96%); 9 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +90.46 |
| case:UPPER | 68/1666 (4.08%) correct; 116/1666 (6.96%); 9 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +90.46 |
| filler:code | 1419/1666 (85.17%) correct; 1455/1666 (87.33%); 88 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +8.34 |
| filler:defined | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| filler:layer | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| filler:live | 1123/1666 (67.41%) correct; 1150/1666 (69.03%); 88 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +26.65 |
| filler:lives | 1123/1666 (67.41%) correct; 1150/1666 (69.03%); 88 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +26.65 |
| filler:located | 1123/1666 (67.41%) correct; 1150/1666 (69.03%); 88 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +26.65 |
| filler:logic | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| filler:part | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| filler:stuff | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| filler:the | 1355/1666 (81.33%) correct; 1391/1666 (83.49%); 88 wrong | 1584/1666 (95.08%) correct; 1600/1666 (96.04%); 30 wrong | +12.55 |
| filler:thing | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| kind:class | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1497/1666 (89.86%) correct; 1497/1666 (89.86%); 34 wrong | +4.86 |
| kind:def | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1497/1666 (89.86%) correct; 1497/1666 (89.86%); 34 wrong | +4.86 |
| kind:dir | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| kind:directory | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| kind:file | 1047/1666 (62.85%) correct; 1047/1666 (62.85%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 0 wrong | +32.83 |
| kind:folder | 1047/1666 (62.85%) correct; 1458/1666 (87.52%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +8.16 |
| kind:function | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1497/1666 (89.86%) correct; 1497/1666 (89.86%); 34 wrong | +4.86 |
| kind:method | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1497/1666 (89.86%) correct; 1497/1666 (89.86%); 34 wrong | +4.86 |
| kind:module | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 0 wrong | +10.68 |
| kind:package | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 36 wrong | +10.68 |
| kind:script | 1047/1666 (62.85%) correct; 1416/1666 (84.99%); 58 wrong | 1594/1666 (95.68%) correct; 1594/1666 (95.68%); 0 wrong | +10.68 |
| punctuation:? | 1154/1666 (69.27%) correct; 1211/1666 (72.69%); 67 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +24.73 |
| punctuation:. | 0/1666 (0.00%) correct; 825/1666 (49.52%); 0 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +47.90 |
| target-form:basename | 850/1080 (78.70%) correct; 1020/1080 (94.44%); 50 wrong | 900/1080 (83.33%) correct; 1080/1080 (100.00%); 0 wrong | +5.56 |
| target-form:folder-name | 211/396 (53.28%) correct; 271/396 (68.43%); 29 wrong | 252/396 (63.64%) correct; 360/396 (90.91%); 0 wrong | +22.47 |
| target-form:full-path | 1154/1666 (69.27%) correct; 1211/1666 (72.69%); 67 wrong | 1594/1666 (95.68%) correct; 1623/1666 (97.42%); 7 wrong | +24.73 |
| target-form:stem | 733/1476 (49.66%) correct; 929/1476 (62.94%); 30 wrong | 864/1476 (58.54%) correct; 1173/1476 (79.47%); 0 wrong | +16.53 |
| target-form:synonym:authentication | 0/36 (0.00%) correct; 0/36 (0.00%); 0 wrong | 0/36 (0.00%) correct; 0/36 (0.00%); 0 wrong | +0.00 |
| target-form:synonym:database | 0/36 (0.00%) correct; 0/36 (0.00%); 0 wrong | 36/36 (100.00%) correct; 36/36 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:environment | 0/36 (0.00%) correct; 0/36 (0.00%); 0 wrong | 36/36 (100.00%) correct; 36/36 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:repository | 0/36 (0.00%) correct; 0/36 (0.00%); 0 wrong | 36/36 (100.00%) correct; 36/36 (100.00%); 0 wrong | +100.00 |
| typo:one-insertion | 0/1666 (0.00%) correct; 1087/1666 (65.25%); 0 wrong | 0/1666 (0.00%) correct; 1112/1666 (66.75%); 0 wrong | +1.50 |
### kindAgreement

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| matching | 2871/4824 (59.51%) correct; 4065/4824 (84.27%); 174 wrong | 4572/4824 (94.78%) correct; 4572/4824 (94.78%); 144 wrong | +10.51 |
| mismatching | 7656/11412 (67.09%) correct; 9384/11412 (82.23%); 464 wrong | 10560/11412 (92.53%) correct; 10560/11412 (92.53%); 136 wrong | +10.30 |
### constructionStratum

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| ambiguous | 31/468 (6.62%) correct; 337/468 (72.01%); 59 wrong | 0/468 (0.00%) correct; 453/468 (96.79%); 0 wrong | +24.79 |
| mismatching-kind | 7656/11412 (67.09%) correct; 9384/11412 (82.23%); 464 wrong | 10560/11412 (92.53%) correct; 10560/11412 (92.53%); 136 wrong | +10.30 |
| unambiguous | 21321/39530 (53.94%) correct; 27991/39530 (70.81%); 1213 wrong | 35798/39530 (90.56%) correct; 37244/39530 (94.22%); 576 wrong | +23.41 |
### matrix

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 24/41 (58.54%) correct; 30/41 (73.17%); 0 wrong | +2.44 |
| {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| dependencies of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| dependencies of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| dependencies of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| dependencies of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependencies of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| dependents of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| dependents of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| dependents of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| dependents of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependents of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| downstream {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| downstream {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| downstream {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| downstream {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| downstream from {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| downstream from {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| downstream from {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| downstream from {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| downstream of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| downstream of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| downstream of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| downstream of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| find {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| find {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +21.95 |
| find {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 24/41 (58.54%) correct; 30/41 (73.17%); 0 wrong | +2.44 |
| find {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| from {x} to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| how {x} connect to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| how {x} reach {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| how does {x} connect to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| how does {x} get to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| how does {x} reach {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| locate {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| locate {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| locate {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +21.95 |
| locate {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| locate {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| locate {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| path between {x} and {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| path from {x} to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| please find {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| please find {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| please find {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +19.51 |
| please find {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| please find {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| please find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| route between {x} and {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| route from {x} to {y} × full-path | 10/19 (52.63%) correct; 10/19 (52.63%); 0 wrong | 19/19 (100.00%) correct; 19/19 (100.00%); 0 wrong | +47.37 |
| show {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| show {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| show {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +19.51 |
| show {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 24/41 (58.54%) correct; 30/41 (73.17%); 0 wrong | +2.44 |
| show {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| show me {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| show me {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +19.51 |
| show me {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| show me {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show me {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| upstream {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| upstream {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| upstream {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| upstream {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| upstream from {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| upstream from {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| upstream from {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| upstream from {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| upstream of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| upstream of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| upstream of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| upstream of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what depends on {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what depends on {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what depends on {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what depends on {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what depends on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} depend on × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what does {x} depend on × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what does {x} depend on × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what does {x} depend on × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} depend on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} import × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what does {x} import × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what does {x} import × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what does {x} import × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} use × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} use × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what does {x} use × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what does {x} use × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what does {x} use × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} use × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} use × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what imports {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what imports {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what imports {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what imports {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what imports {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what is {x} × folder-name | 8/11 (72.73%) correct; 10/11 (90.91%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +0.00 |
| what is {x} × full-path | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +0.00 |
| what is {x} × stem | 8/41 (19.51%) correct; 10/41 (24.39%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +56.10 |
| what is {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what is {x} built on × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what is {x} built on × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what is {x} built on × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what is {x} built on × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} built on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what uses {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what uses {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what uses {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what uses {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what uses {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what uses {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what uses {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what would break if {x} changed × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| what would break if {x} changed × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| what would break if {x} changed × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| what would break if {x} changed × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what would break if {x} changed × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where are {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| where are {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +19.51 |
| where are {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| where are {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where are {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| where is {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +21.95 |
| where is {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| where is {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × basename | 0/30 (0.00%) correct; 0/30 (0.00%); 25 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| where is {x} called from × full-path | 0/41 (0.00%) correct; 0/41 (0.00%); 29 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +97.56 |
| where is {x} called from × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 30/41 (73.17%); 0 wrong | +73.17 |
| where is {x} called from × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} called from × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} defined × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| where is {x} defined × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +2.44 |
| where is {x} defined × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +80.49 |
| where is {x} defined × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} located × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| where is {x} located × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | +19.51 |
| where is {x} located × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| where is {x} located × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} located × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where’s {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where's {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| where’s {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| where's {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +4.88 |
| where’s {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +4.88 |
| where's {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +80.49 |
| where’s {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +80.49 |
| where's {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where’s {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where's {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| wheres {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| wheres {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +4.88 |
| wheres {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +80.49 |
| wheres {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| wheres {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which do {x} import × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| which do {x} import × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| which do {x} import × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| which do {x} import × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| which do {x} import × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which do {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which do {x} import × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which do {x} import × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| which does {x} use × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| which does {x} use × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| which does {x} use × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| which does {x} use × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| which files depend on {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| which files depend on {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| which files depend on {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| which files depend on {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which files depend on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × basename | 0/30 (0.00%) correct; 0/30 (0.00%); 25 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +90.91 |
| who invokes {x} × full-path | 0/41 (0.00%) correct; 0/41 (0.00%); 29 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +97.56 |
| who invokes {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 24/41 (58.54%) correct; 30/41 (73.17%); 0 wrong | +73.17 |
| who invokes {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who invokes {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| who uses {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 10/11 (90.91%); 0 wrong | +9.09 |
| who uses {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 39/41 (95.12%) correct; 40/41 (97.56%); 0 wrong | +19.51 |
| who uses {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 24/41 (58.54%) correct; 33/41 (80.49%); 0 wrong | +2.44 |
| who uses {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |

### Worst axes by parser success (not independent causal effects)

- target-form:synonym:authentication: 0/36 (0.00%).
- typo:one-insertion: 1112/1666 (66.75%).
- target-form:stem: 1173/1476 (79.47%).
- kind:class: 1497/1666 (89.86%).
- kind:def: 1497/1666 (89.86%).
- kind:function: 1497/1666 (89.86%).
- kind:method: 1497/1666 (89.86%).
- target-form:folder-name: 360/396 (90.91%).

### main: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/case:Title/no-match | 509 | `Vitest.Config.Ts` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/case:UPPER/no-match | 509 | `VITEST.CONFIG.TS` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:Title/no-match | 444 | `what depends on Vitest.Config.Ts` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:UPPER/no-match | 444 | `what depends on VITEST.CONFIG.TS` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/case:Title/no-match | 380 | `what does Vitest.Config.Ts depend on` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/case:UPPER/no-match | 380 | `what does VITEST.CONFIG.TS depend on` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/punctuation:./no-match | 294 | `what does vitest.config.ts depend on.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/punctuation:./no-match | 226 | `where is vitest.config.ts defined.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/case:lower/no-match | 220 | `src/components/buyer/roomnotice.tsx` → no-match / NOT_SURE; expected ['src/components/buyer/RoomNotice.tsx']; selected [] |
| LOCATE/target-form:stem/no-match | 213 | `vitest.config` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:lower/no-match | 204 | `what depends on src/components/buyer/roomnotice.tsx` → no-match / NOT_SURE; expected ['src/components/buyer/RoomNotice.tsx']; selected [] |
| DOWNSTREAM/punctuation:./no-match | 202 | `where is vitest.config.ts called from.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/kind:file/no-match | 197 | `where is file vitest.config.ts defined` → no-match / LOCATE; expected ['vitest.config.ts']; selected [] |
| PATH/case:Title/no-match | 190 | `from Src/Lib to App/Api/Events` → no-match / NOT_SURE; expected ['folder-91be6cfb7c9129b9', 'folder-339c0fd4c4ebbcb5']; selected [] |
| PATH/case:UPPER/no-match | 190 | `from SRC/LIB to APP/API/EVENTS` → no-match / NOT_SURE; expected ['folder-91be6cfb7c9129b9', 'folder-339c0fd4c4ebbcb5']; selected [] |

### main: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| DOWNSTREAM | `dependents of dir src/components/ui/Card.tsx` | 0.063, 0.065, 1.203 |
| LOCATE | `show me function src/lib/track.ts` | 0.932, 0.070, 0.060 |
| PATH | `how does src/lib/__tests__/robustness.test.ts live connect to src/lib/deals.ts live` | 0.919, 0.102, 0.102 |
| LOCATE | `locate src/lib/insights.ts?` | 0.078, 0.896, 0.055 |
| LOCATE | `where is vitest.config.ts defined` | 0.843, 0.059, 0.062 |
| DOWNSTREAM | `what would break if src/components/auth layer changed` | 0.827, 0.098, 0.097 |
| LOCATE | `where is app/api/rooms/[slug]/route.ts located` | 0.072, 0.774, 0.052 |
| LOCATE | `show me app/(seller)/seller live` | 0.762, 0.122, 0.094 |
| PATH | `path between src/components/auth code and app/api/auth/login code` | 0.749, 0.190, 0.214 |
| PATH | `path from function src/components/modules/__tests__/StakeholderMap.test.tsx to function src/components/modules/StakeholderMap.tsx` | 0.738, 0.116, 0.107 |

### parser: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| DOWNSTREAM/typo:one-insertion/no-match | 190 | `who invokes vitest.config.tsz` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| LOCATE/typo:one-insertion/no-match | 154 | `app/(seller)/seller/page.tsxz` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| UPSTREAM/typo:one-insertion/no-match | 110 | `what does app/(seller)/seller/page.tsxz depend on` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| PATH/typo:one-insertion/no-match | 100 | `from src/libz to app/api/eventsz` → no-match / NOT_SURE; expected ['folder-91be6cfb7c9129b9', 'folder-339c0fd4c4ebbcb5']; selected [] |
| DOWNSTREAM/kind:class/no-match | 92 | `who invokes class vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:def/no-match | 92 | `who invokes def vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:function/no-match | 92 | `who invokes function vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:method/no-match | 92 | `who invokes method vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| LOCATE/target-form:stem/unresolved | 70 | `sections.test` → needs-choice / NOT_SURE; expected ['src/lib/__tests__/sections.test.ts']; selected [] |
| DOWNSTREAM/target-form:stem/unresolved | 52 | `what depends on sections.test` → needs-choice / NOT_SURE; expected ['src/lib/__tests__/sections.test.ts']; selected [] |
| LOCATE/target-form:stem/no-match | 51 | `vitest.config` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/target-form:stem/no-match | 50 | `what depends on vitest.config` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/target-form:stem/unresolved | 50 | `what does sections.test depend on` → needs-choice / NOT_SURE; expected ['src/lib/__tests__/sections.test.ts']; selected [] |
| UPSTREAM/target-form:stem/no-match | 30 | `what does vitest.config depend on` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/kind:file/no-match | 28 | `file app/(seller)/seller/page.tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |

### parser: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| DOWNSTREAM | `downstream of dir app/(seller)/seller/page.tsx` | 0.133, 1.207, 0.136 |
| PATH | `path between the src/lib/__tests__ and the src/lib` | 0.981, 0.293, 0.325 |
| PATH | `how does dir src/lib connect to dir app/api/auth/login` | 0.775, 0.151, 0.154 |
| UPSTREAM | `upstream from package app/login/page.tsx` | 0.743, 0.125, 0.150 |
| LOCATE | `wheres src/components/buyer/BuyerLoginPrompt.tsx?` | 0.129, 0.700, 0.129 |
| LOCATE | `where's file src/components/content/TrackedDocLink.tsx` | 0.696, 0.138, 0.155 |
| DOWNSTREAM | `who invokes folder src/components/ui/Card.tsx` | 0.213, 0.661, 0.240 |
| PATH | `how does directory src/components/buyer/BuyerRoom.tsx reach directory src/components/buyer/HaveAQuestion.tsx` | 0.660, 0.360, 0.361 |
| DOWNSTREAM | `where is app/(seller)/seller called from.` | 0.650, 0.295, 0.290 |
| PATH | `route from the src/lib to the app/api/auth/me` | 0.332, 0.642, 0.333 |

### Negative outcomes

| Version | No-match | Unresolved choices | Overconfident |
|---|---:|---:|---:|
| main | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |
| parser | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |

## New confident mistakes versus main

Aggregate improvement does not imply zero regressions. These cases are wrong on the fixed parser but were not confidently wrong on main; generated ambiguous/mismatching-kind cases remain in this count. They are not all confirmed real-user regressions.

- honcho: 61 newly confident-wrong generated cases.
  - `who invokes backfill`: expected DOWNSTREAM on ['src/reconciler/backfill.py']; got CALLERS on ['src/reconciler/backfill.py#Backfill@33'].
  - `where is backfill called from`: expected DOWNSTREAM on ['src/reconciler/backfill.py']; got CALLERS on ['src/reconciler/backfill.py#Backfill@33'].
  - `where's src`: expected LOCATE on ['folder-a103f549c63bbe7d']; got LOCATE on ['folder-25a6634263c1b1f6'].
- salesroom: 535 newly confident-wrong generated cases.
  - `app/(seller)/seller layer`: expected LOCATE on ['folder-999d65323a17496f']; got LOCATE on ['folder-49474c8a8485b55e'].
  - `app/(seller)/seller logic`: expected LOCATE on ['folder-999d65323a17496f']; got LOCATE on ['folder-49474c8a8485b55e'].
  - `app/(seller)/seller stuff`: expected LOCATE on ['folder-999d65323a17496f']; got LOCATE on ['folder-49474c8a8485b55e'].

## Verification and retained attempts

Generator tests cover determinism, quotas, label construction, axis coverage, directed path grading, seed vs incidental selection, choice-operation checks, negative classification, deduplication and percentile arithmetic. Full suite commands and counts are recorded in the task handoff and build update.
Raw-row construction, outcome/latency totals, ambiguity strata, correct-only timings and 1,920 HTTP response statuses reconcile. Frozen target source audit passes. The original hand-written questions and splits are unchanged. Full gate evidence is recorded in STATUS and artifacts/question-parser/benchmark-fixes/gates/verification.json.
The first after-benchmark attempt was stopped during main HTTP measurement after an added regression exposed a broken explicit file choice in a file/symbol collision. That dispatch bug was fixed at `2b80e8d` and the entire benchmark restarted; this was not a performance-selected retry. The interrupted log is retained. Browser checks briefly overlapped the first attempt. These measurements are not CPU-isolated.
Real-app setup initially lacked PLAYWRIGHT_DIR; after configuring the existing package, a browser wait incorrectly required option elements to be visible rather than attached. Correcting that test wait produced 6/6 checks without changing the app. Logs and screenshots are retained under artifacts/question-parser/benchmark-fixes/.
Remaining caveats: synthetic wording and redundant rows, no multi-axis interaction coverage, known-target bias, source graph/extractor limitations, limited typo and negative distributions, first-page grading, and non-isolated timing. Literal targets retain priority over synonyms, so a generated synonym intention can still disagree with a valid literal answer. Consultant second opinion is requested; approval remains with the generalist.
