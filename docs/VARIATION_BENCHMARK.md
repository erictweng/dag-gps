# Question-variation benchmark

This measures **robustness to phrasing on known targets**, not real-user accuracy. No parser behavior was changed.

## Headline

| Repo | Version | Generated positive + negative | Correct | Correct or choose | Wrong | Overconfident negatives | Warm p50 / p95 ms |
|---|---|---:|---:|---:|---:|---:|---:|
| honcho | main | 75444 + 240 | 31218/75444 (41.38%) | 40732/75444 (53.99%) | 2645/75444 (3.51%) | 0/240 (0.00%) | 0.210 / 0.383 |
| honcho | parser | 75444 + 240 | 55800/75444 (73.96%) | 59457/75444 (78.81%) | 646/75444 (0.86%) | 0/240 (0.00%) | 0.309 / 0.812 |
| salesroom | main | 38802 + 240 | 21037/38802 (54.22%) | 27610/38802 (71.16%) | 1687/38802 (4.35%) | 0/240 (0.00%) | 0.035 / 0.062 |
| salesroom | parser | 38802 + 240 | 25949/38802 (66.88%) | 27855/38802 (71.79%) | 630/38802 (1.62%) | 0/240 (0.00%) | 0.061 / 0.095 |

Percentages above use positive constructed cases, except overconfidence which uses only negatives. Timing includes both.

| Repo | Main distinct successful strings | Parser distinct successful strings | Unique generated strings | Targets (source checked) |
|---|---:|---:|---:|---|
| honcho | 38498 | 56449 | 71555 | {"file": 42, "layer": 16, "symbol": 30} |
| salesroom | 26448 | 26592 | 37331 | {"file": 30, "layer": 11} |

Counts are case-weighted, not unique-string-weighted: repeated equivalent forms remain in axis cells. Distinct successes deduplicate exact strings across correct + choose-correct cases; one successful target interpretation suffices for this requested metric.

## Frozen hand-written reference (unchanged)

These are the existing reports, not generated-grid labels. They approximate real phrasing but are author-written, not independently sampled user traffic. Their stricter expected-match/expected-choice labels differ from the generated evaluator.

| Repo/split | Version | Cases | Match correct / expected match | Choose correct / expected choose | Negative no-match | Wrong | Overconfident |
|---|---|---:|---:|---:|---:|---:|---:|
| honcho/dev | main | 80 | 17/46 (36.96%) | 4/18 (22.22%) | 16/16 (100.00%) | 2 | 0 |
| honcho/holdout | main | 27 | 6/18 (33.33%) | 1/5 (20.00%) | 4/4 (100.00%) | 0 | 0 |
| honcho/dev | parser | 80 | 46/46 (100.00%) | 12/18 (66.67%) | 16/16 (100.00%) | 2 | 0 |
| honcho/holdout | parser | 27 | 18/18 (100.00%) | 5/5 (100.00%) | 4/4 (100.00%) | 0 | 0 |
| salesroom/dev | main | 32 | 9/20 (45.00%) | 3/6 (50.00%) | 6/6 (100.00%) | 0 | 0 |
| salesroom/holdout | main | 11 | 3/7 (42.86%) | 0/2 (0.00%) | 2/2 (100.00%) | 0 | 0 |
| salesroom/dev | parser | 32 | 20/20 (100.00%) | 5/6 (83.33%) | 6/6 (100.00%) | 0 | 0 |
| salesroom/holdout | parser | 11 | 7/7 (100.00%) | 0/2 (0.00%) | 2/2 (100.00%) | 0 | 0 |

## Method and scope

- Versions: main `7db31cdb8e35e00ac41f9c478ffdcf1c75de669b`; parser query code at `4ad61d91ca81a5fd4081ef97d8ba9d55e62ed04f`. Both use the identical parser-era snapshots; this isolates query-code changes, not extraction-version changes. Baseline ignores the extra concept sidecar.
- Seed `dag-variation-v1-20261013`; templates SHA-256 `646a368ce3135d94373d26ac20da9382523b94b5249fbd2f029cec673d63fa86`. Frozen targets, pins, source checks and known directed-edge pairs are in `eval/variation_templates.json`.
- Targets were selected before querying: SHA-256(seed + ID) order, minimum quotas, plus all applicable synonym-name targets. Each file is checked against a pinned Git blob; Python symbols against AST name/start; folders against Git tree descendants. PATH/FLOW pairs are directed observed edges, not runtime proofs. `python3 scripts/freeze_variation_targets.py --check` rechecks source selection without querying.
- Grid is sparse and deterministic: operation phrase × target form, plus each independent perturbation on the canonical target, one axis at a time. This is not the exponential full Cartesian product or an interaction-completeness claim. No tuning or successful-target selection after running. Contractions are separate operation-phrase rows (straight/curly apostrophe and omitted apostrophe).
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

Machine: `{"platform": "darwin", "release": "25.1.0", "arch": "arm64", "cpu": "Apple M4 Pro", "cores": 12, "memory": 25769803776, "node": "v26.8.2"}`. Load averages before `[1.64404296875, 2.09912109375, 2.19189453125]`, after `[1.8076171875, 1.9033203125, 2.02001953125]`.

Direct path: real createQueryService.query, the same function as query_worker.cjs; 200 seeded warmup requests and 3 measured sweeps. Cold: 3 snapshot reads/JSON parses and service/index constructions, excluding require/module compilation; OS disk cache is not flushed. First construction is process-cold; later constructions are rebuilds.
Version order is main then parser; no CPU isolation, process restart per sweep, randomized version order, or confidence intervals. Timing variance includes GC/scheduler effects. All direct raw timings are retained. Tier names are observable packet buckets: no-match status first, then BM25 fallback reason, synonym reason, otherwise literal (includes lexical/fuzzy alternatives). This is not internal stage-exclusive profiler instrumentation.

| Repo/version | Scope | n | p50 ms | p95 ms | p99 ms | max ms | mean ± population SD ms |
|---|---|---:|---:|---:|---:|---:|---|
| honcho/main | all | 227052 | 0.210 | 0.383 | 0.557 | 3.374 | 0.221 ± 0.111 |
| honcho/main | tier:literal | 133365 | 0.209 | 0.446 | 0.749 | 3.374 | 0.243 ± 0.113 |
| honcho/main | tier:synonym | 0 | n/a | n/a | n/a | n/a | n/a |
| honcho/main | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| honcho/main | tier:no-match | 93687 | 0.218 | 0.295 | 0.388 | 0.657 | 0.189 ± 0.100 |
| honcho/main | op:CALLEES | 5580 | 0.014 | 0.753 | 1.153 | 1.500 | 0.107 ± 0.249 |
| honcho/main | op:CALLERS | 13950 | 0.242 | 0.399 | 1.020 | 1.409 | 0.197 ± 0.181 |
| honcho/main | op:DOWNSTREAM | 49032 | 0.208 | 0.472 | 0.539 | 1.062 | 0.238 ± 0.089 |
| honcho/main | op:FLOW | 870 | 0.018 | 0.514 | 1.108 | 1.414 | 0.073 ± 0.202 |
| honcho/main | op:LOCATE | 115332 | 0.211 | 0.287 | 0.411 | 1.308 | 0.213 ± 0.084 |
| honcho/main | op:PATH | 6090 | 0.374 | 0.440 | 0.519 | 0.707 | 0.338 ± 0.124 |
| honcho/main | op:TRACE | 2790 | 0.014 | 0.865 | 1.512 | 2.254 | 0.120 ± 0.306 |
| honcho/main | op:UPSTREAM | 32688 | 0.214 | 0.364 | 0.430 | 3.374 | 0.243 ± 0.069 |
| honcho/main | repeat:1 | 75684 | 0.217 | 0.394 | 0.589 | 3.374 | 0.227 ± 0.115 |
| honcho/main | repeat:2 | 75684 | 0.208 | 0.379 | 0.545 | 2.254 | 0.218 ± 0.110 |
| honcho/main | repeat:3 | 75684 | 0.208 | 0.379 | 0.539 | 1.952 | 0.218 ± 0.108 |
| honcho/parser | all | 227052 | 0.309 | 0.812 | 1.120 | 2.005 | 0.394 ± 0.208 |
| honcho/parser | tier:literal | 181218 | 0.317 | 0.899 | 1.129 | 2.005 | 0.418 ± 0.215 |
| honcho/parser | tier:synonym | 876 | 0.770 | 1.662 | 1.765 | 2.000 | 0.934 ± 0.428 |
| honcho/parser | tier:BM25 fallback | 84 | 0.427 | 0.692 | 0.913 | 0.913 | 0.459 ± 0.097 |
| honcho/parser | tier:no-match | 44874 | 0.261 | 0.479 | 0.546 | 1.075 | 0.285 ± 0.099 |
| honcho/parser | op:CALLEES | 5580 | 0.361 | 0.767 | 0.902 | 1.767 | 0.445 ± 0.173 |
| honcho/parser | op:CALLERS | 13950 | 0.372 | 0.757 | 0.841 | 1.802 | 0.443 ± 0.171 |
| honcho/parser | op:DOWNSTREAM | 49032 | 0.294 | 0.584 | 0.672 | 1.193 | 0.323 ± 0.127 |
| honcho/parser | op:FLOW | 870 | 0.393 | 1.150 | 1.242 | 1.554 | 0.569 ± 0.311 |
| honcho/parser | op:LOCATE | 115332 | 0.306 | 1.006 | 1.173 | 2.005 | 0.426 ± 0.250 |
| honcho/parser | op:PATH | 6090 | 0.469 | 0.570 | 0.650 | 0.853 | 0.468 ± 0.078 |
| honcho/parser | op:TRACE | 2790 | 0.403 | 1.184 | 1.393 | 1.802 | 0.541 ± 0.287 |
| honcho/parser | op:UPSTREAM | 32688 | 0.300 | 0.471 | 0.546 | 1.268 | 0.327 ± 0.084 |
| honcho/parser | repeat:1 | 75684 | 0.315 | 0.822 | 1.138 | 2.005 | 0.400 ± 0.211 |
| honcho/parser | repeat:2 | 75684 | 0.307 | 0.805 | 1.112 | 1.802 | 0.391 ± 0.207 |
| honcho/parser | repeat:3 | 75684 | 0.307 | 0.804 | 1.110 | 1.966 | 0.391 ± 0.207 |
| salesroom/main | all | 117126 | 0.035 | 0.062 | 0.112 | 0.292 | 0.040 ± 0.017 |
| salesroom/main | tier:literal | 89967 | 0.035 | 0.063 | 0.113 | 0.292 | 0.041 ± 0.017 |
| salesroom/main | tier:synonym | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/main | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/main | tier:no-match | 27159 | 0.034 | 0.061 | 0.070 | 0.228 | 0.036 ± 0.016 |
| salesroom/main | op:DOWNSTREAM | 34425 | 0.034 | 0.059 | 0.065 | 0.229 | 0.039 ± 0.011 |
| salesroom/main | op:LOCATE | 53550 | 0.034 | 0.059 | 0.066 | 0.229 | 0.037 ± 0.013 |
| salesroom/main | op:PATH | 5481 | 0.102 | 0.117 | 0.136 | 0.292 | 0.082 ± 0.035 |
| salesroom/main | op:UPSTREAM | 22950 | 0.035 | 0.057 | 0.064 | 0.178 | 0.039 ± 0.010 |
| salesroom/main | repeat:1 | 39042 | 0.036 | 0.065 | 0.115 | 0.292 | 0.041 ± 0.018 |
| salesroom/main | repeat:2 | 39042 | 0.034 | 0.061 | 0.112 | 0.190 | 0.040 ± 0.016 |
| salesroom/main | repeat:3 | 39042 | 0.034 | 0.061 | 0.111 | 0.205 | 0.039 ± 0.016 |
| salesroom/parser | all | 117126 | 0.061 | 0.095 | 0.129 | 0.684 | 0.063 ± 0.018 |
| salesroom/parser | tier:literal | 85779 | 0.062 | 0.089 | 0.133 | 0.684 | 0.065 ± 0.016 |
| salesroom/parser | tier:synonym | 261 | 0.118 | 0.220 | 0.250 | 0.277 | 0.129 ± 0.035 |
| salesroom/parser | tier:BM25 fallback | 0 | n/a | n/a | n/a | n/a | n/a |
| salesroom/parser | tier:no-match | 31086 | 0.051 | 0.096 | 0.115 | 0.268 | 0.058 ± 0.020 |
| salesroom/parser | op:DOWNSTREAM | 34425 | 0.060 | 0.106 | 0.133 | 0.289 | 0.061 ± 0.019 |
| salesroom/parser | op:LOCATE | 53550 | 0.061 | 0.079 | 0.127 | 0.684 | 0.063 ± 0.016 |
| salesroom/parser | op:PATH | 5481 | 0.088 | 0.114 | 0.182 | 0.348 | 0.092 ± 0.023 |
| salesroom/parser | op:UPSTREAM | 22950 | 0.060 | 0.073 | 0.094 | 0.207 | 0.060 ± 0.011 |
| salesroom/parser | repeat:1 | 39042 | 0.061 | 0.097 | 0.141 | 0.684 | 0.064 ± 0.019 |
| salesroom/parser | repeat:2 | 39042 | 0.061 | 0.094 | 0.127 | 0.260 | 0.063 ± 0.017 |
| salesroom/parser | repeat:3 | 39042 | 0.060 | 0.093 | 0.125 | 0.431 | 0.062 ± 0.017 |

| Repo/version | Cold read+parse ms (3) | Cold service/index ms (3) |
|---|---|---|
| honcho/main | 19.484, 22.823, 22.409 | 37.150, 24.119, 19.636 |
| honcho/parser | 23.337, 40.521, 21.489 | 97.855, 66.708, 56.662 |
| salesroom/main | 0.210, 0.140, 0.134 | 0.761, 0.635, 0.589 |
| salesroom/parser | 0.383, 0.317, 0.290 | 2.960, 2.339, 1.994 |

### Real HTTP overhead

240 deterministic distributed questions × 2 repeats = 480 measured requests per repo/version, after 20 warmups. Serial loopback requests, fresh TCP connection per request, full JSON response read. Real Python WorkspaceServer → persistent Node worker → packet contract validation, not a mocked server. Each copied snapshot is explicitly rebound to that version’s query-code hashes and validated. No session capability is logged.
Paired overhead subtracts each question’s median direct-service time from its HTTP time. It includes snapshot loading, integrity/contract validation, IPC, serialization, TCP and Python overhead, not just network transport; direct and HTTP timings are not simultaneous. Honcho HTTP is much slower than its JS algorithm. This card does not optimize it.

| Repo/version | n | HTTP p50/p95/p99/max ms | Matched direct p50/p95 ms | Difference p50/p95 ms | Repeat p95 ms |
|---|---:|---|---|---|---|
| honcho/main | 480 | 458.823 / 474.571 / 483.098 / 487.237 | 0.211 / 0.356 | 458.614 / 474.334 | 474.835, 473.937 |
| honcho/parser | 480 | 471.973 / 487.779 / 491.684 / 506.633 | 0.303 / 0.733 | 471.599 / 487.463 | 488.667, 487.394 |
| salesroom/main | 480 | 2.502 / 2.652 / 2.769 / 3.911 | 0.034 / 0.062 | 2.462 / 2.600 | 2.682, 2.598 |
| salesroom/parser | 480 | 2.772 / 2.920 / 3.051 / 4.327 | 0.061 / 0.096 | 2.712 / 2.851 | 2.947, 2.889 |

### Worst 10 HTTP requests per repo/version

| Repo/version | Operation | Question | ms | Response bytes |
|---|---|---|---:|---:|
| honcho/main | LOCATE | `what is tests/vector_store logic` | 487.237 | 1473 |
| honcho/main | UPSTREAM | `dependencies of method scripts` | 487.140 | 1324 |
| honcho/main | LOCATE | `where is folder src/backlog.py` | 485.408 | 1546 |
| honcho/main | DOWNSTREAM | `downstream from dir migrations/env.py` | 483.136 | 1701 |
| honcho/main | DOWNSTREAM | `what depends on KILO-HONCHO/SRC/TUI/SIDEBAR.TSX` | 483.098 | 1394 |
| honcho/main | LOCATE | `where is file src/llm/backends/anthropic.py` | 482.002 | 1589 |
| honcho/main | DOWNSTREAM | `who uses src/reconciler/backfill.py part` | 481.294 | 177670 |
| honcho/main | UPSTREAM | `which does src/llm/executor.py use` | 480.399 | 92356 |
| honcho/main | UPSTREAM | `what is the src/utils/search.py built on` | 480.317 | 86205 |
| honcho/main | DOWNSTREAM | `which files depend on src/db.py located` | 478.303 | 138799 |
| honcho/parser | FLOW | `how does src/utils/json_parser.py#try_line_reconstruction_repair@297 layer reach src/utils/json_parser.py#try_contextual_closure_repair@131 layer` | 506.633 | 3946 |
| honcho/parser | DOWNSTREAM | `who uses src/reconciler/backfill.py part` | 503.403 | 177778 |
| honcho/parser | LOCATE | `where is method mcp/src/tools defined` | 496.370 | 1457 |
| honcho/parser | DOWNSTREAM | `which files depend on src/db.py located` | 491.910 | 138907 |
| honcho/parser | CALLERS | `callers of SRC/UTILS/AGENT_TOOLS.PY#_HANDLE_GET_PEER_CARD@2060` | 491.684 | 8204 |
| honcho/parser | FLOW | `how does src/dialectic/core.py#dialecticagent.answer_stream@641 reach src/dialectic/core.py#_get_dialectic_level_model_config@56` | 491.524 | 4985 |
| honcho/parser | LOCATE | `show package tests/test_dependencies.py#FakeSession.close@32` | 490.579 | 1619 |
| honcho/parser | DOWNSTREAM | `downstream from script kilo-honcho/tests` | 490.377 | 1464 |
| honcho/parser | LOCATE | `locate folder hermes-plugin-honcho/session.py` | 489.449 | 1685 |
| honcho/parser | UPSTREAM | `what is tests/telemetry/test_langfuse_exporter_real_sdk.py thing built on` | 489.427 | 109613 |
| salesroom/main | DOWNSTREAM | `dependents of src/components/buyer/BuyerLoginPrompt.tsx logic` | 3.911 | 1824 |
| salesroom/main | DOWNSTREAM | `downstream from function scripts` | 3.841 | 1329 |
| salesroom/main | LOCATE | `where’s folder app` | 2.822 | 1657 |
| salesroom/main | DOWNSTREAM | `what would break if src/lib/env.ts changed` | 2.790 | 4887 |
| salesroom/main | PATH | `how folder src/lib/__tests__ connect to folder src/lib` | 2.769 | 1908 |
| salesroom/main | DOWNSTREAM | `what imports src/lib/env.ts layer` | 2.738 | 4878 |
| salesroom/main | PATH | `route between class src/components/auth and class app/api/auth/login` | 2.732 | 1924 |
| salesroom/main | PATH | `path between the src/lib and the app/api/accounts` | 2.732 | 1625 |
| salesroom/main | LOCATE | `where is InsightsPanel defined` | 2.732 | 1009 |
| salesroom/main | DOWNSTREAM | `dependents of src/lib/env.ts` | 2.729 | 4873 |
| salesroom/parser | LOCATE | `where is script src/components/modules/__tests__/StakeholderMap.test.tsx defined` | 4.327 | 1682 |
| salesroom/parser | DOWNSTREAM | `downstream from function scripts` | 4.195 | 1496 |
| salesroom/parser | PATH | `path between the src/lib and the app/api/accounts` | 3.160 | 1709 |
| salesroom/parser | DOWNSTREAM | `where is Src/Lib/Types.Ts called from` | 3.082 | 7630 |
| salesroom/parser | DOWNSTREAM | `where is Src/Lib/Types.Ts called from` | 3.051 | 7630 |
| salesroom/parser | DOWNSTREAM | `what imports src/lib/env.ts layer` | 3.032 | 4895 |
| salesroom/parser | DOWNSTREAM | `dependents of src/lib/env.ts` | 3.011 | 4890 |
| salesroom/parser | UPSTREAM | `dependencies of def src/lib/http.ts` | 3.006 | 5070 |
| salesroom/parser | UPSTREAM | `dependencies of def src/lib/http.ts` | 3.004 | 5070 |
| salesroom/parser | DOWNSTREAM | `what would break if src/lib/env.ts defined changed` | 3.000 | 4912 |

## honcho: outcome tables

Each cell: correct count; correct-or-choose count/denominator (%); wrong count. Δ is percentage-point gain in correct-or-choose.

### operation

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| CALLEES | 248/1860 (13.33%) correct; 264/1860 (14.19%); 0 wrong | 1718/1860 (92.37%) correct; 1734/1860 (93.23%); 0 wrong | +79.03 |
| CALLERS | 248/4650 (5.33%) correct; 264/4650 (5.68%); 0 wrong | 4295/4650 (92.37%) correct; 4335/4650 (93.23%); 0 wrong | +87.55 |
| DOWNSTREAM | 8099/16344 (49.55%) correct; 10451/16344 (63.94%); 2302 wrong | 11154/16344 (68.25%) correct; 12146/16344 (74.31%); 202 wrong | +10.37 |
| FLOW | 22/290 (7.59%) correct; 22/290 (7.59%); 0 wrong | 270/290 (93.10%) correct; 270/290 (93.10%); 0 wrong | +85.52 |
| LOCATE | 15415/38444 (40.10%) correct; 19873/38444 (51.69%); 211 wrong | 29754/38444 (77.40%) correct; 31695/38444 (82.44%); 312 wrong | +30.75 |
| PATH | 120/2030 (5.91%) correct; 900/2030 (44.33%); 0 wrong | 70/2030 (3.45%) correct; 70/2030 (3.45%); 0 wrong | -40.89 |
| TRACE | 124/930 (13.33%) correct; 132/930 (14.19%); 0 wrong | 859/930 (92.37%) correct; 867/930 (93.23%); 0 wrong | +79.03 |
| UPSTREAM | 6942/10896 (63.71%) correct; 8826/10896 (81.00%); 132 wrong | 7680/10896 (70.48%) correct; 8340/10896 (76.54%); 132 wrong | -4.46 |
### axis

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| case:lower | 1322/2422 (54.58%) correct; 1375/2422 (56.77%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +24.77 |
| case:Title | 81/2422 (3.34%) correct; 121/2422 (5.00%); 0 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +76.55 |
| case:UPPER | 81/2422 (3.34%) correct; 121/2422 (5.00%); 0 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +76.55 |
| filler:code | 1497/2422 (61.81%) correct; 1559/2422 (64.37%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +17.18 |
| filler:defined | 1122/2422 (46.33%) correct; 1487/2422 (61.40%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +20.15 |
| filler:layer | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| filler:live | 1185/2422 (48.93%) correct; 1226/2422 (50.62%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +30.92 |
| filler:lives | 1185/2422 (48.93%) correct; 1226/2422 (50.62%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +30.92 |
| filler:located | 1185/2422 (48.93%) correct; 1226/2422 (50.62%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +30.92 |
| filler:logic | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| filler:part | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| filler:stuff | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| filler:the | 1401/2422 (57.84%) correct; 1455/2422 (60.07%); 84 wrong | 2207/2422 (91.12%) correct; 2223/2422 (91.78%); 0 wrong | +31.71 |
| filler:thing | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| kind:class | 1152/2422 (47.56%) correct; 1517/2422 (62.63%); 84 wrong | 1885/2422 (77.83%) correct; 1885/2422 (77.83%); 0 wrong | +15.19 |
| kind:def | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1885/2422 (77.83%) correct; 1885/2422 (77.83%); 0 wrong | +17.67 |
| kind:dir | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| kind:directory | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| kind:file | 1092/2422 (45.09%) correct; 1092/2422 (45.09%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +36.46 |
| kind:folder | 1092/2422 (45.09%) correct; 1568/2422 (64.74%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +16.80 |
| kind:function | 1152/2422 (47.56%) correct; 1517/2422 (62.63%); 84 wrong | 1885/2422 (77.83%) correct; 1885/2422 (77.83%); 0 wrong | +15.19 |
| kind:method | 1152/2422 (47.56%) correct; 1517/2422 (62.63%); 84 wrong | 1885/2422 (77.83%) correct; 1885/2422 (77.83%); 0 wrong | +15.19 |
| kind:module | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| kind:package | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| kind:script | 1092/2422 (45.09%) correct; 1457/2422 (60.16%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +21.39 |
| punctuation:? | 1435/2422 (59.25%) correct; 1488/2422 (61.44%); 84 wrong | 1975/2422 (81.54%) correct; 1975/2422 (81.54%); 0 wrong | +20.11 |
| punctuation:. | 0/2422 (0.00%) correct; 840/2422 (34.68%); 0 wrong | 0/2422 (0.00%) correct; 840/2422 (34.68%); 0 wrong | +0.00 |
| target-form:basename | 648/1218 (53.20%) correct; 1134/1218 (93.10%); 48 wrong | 696/1218 (57.14%) correct; 1218/1218 (100.00%); 0 wrong | +6.90 |
| target-form:folder-name | 71/464 (15.30%) correct; 169/464 (36.42%); 179 wrong | 87/464 (18.75%) correct; 217/464 (46.77%); 232 wrong | +10.34 |
| target-form:full-path | 1225/1762 (69.52%) correct; 1278/1762 (72.53%); 84 wrong | 1315/1762 (74.63%) correct; 1315/1762 (74.63%); 0 wrong | +2.10 |
| target-form:qualified-name | 203/660 (30.76%) correct; 203/660 (30.76%); 0 wrong | 638/660 (96.67%) correct; 638/660 (96.67%); 0 wrong | +65.91 |
| target-form:stem | 575/1682 (34.19%) correct; 1077/1682 (64.03%); 187 wrong | 742/1682 (44.11%) correct; 1367/1682 (81.27%); 252 wrong | +17.24 |
| target-form:symbol-id | 210/660 (31.82%) correct; 210/660 (31.82%); 0 wrong | 660/660 (100.00%) correct; 660/660 (100.00%); 0 wrong | +68.18 |
| target-form:symbol-name | 140/660 (21.21%) correct; 196/660 (29.70%); 0 wrong | 440/660 (66.67%) correct; 616/660 (93.33%); 0 wrong | +63.64 |
| target-form:synonym:config | 0/29 (0.00%) correct; 0/29 (0.00%); 2 wrong | 0/29 (0.00%) correct; 0/29 (0.00%); 4 wrong | +0.00 |
| target-form:synonym:configuration | 0/116 (0.00%) correct; 0/116 (0.00%); 84 wrong | 0/116 (0.00%) correct; 0/116 (0.00%); 100 wrong | +0.00 |
| target-form:synonym:database | 0/29 (0.00%) correct; 0/29 (0.00%); 23 wrong | 0/29 (0.00%) correct; 0/29 (0.00%); 29 wrong | +0.00 |
| target-form:synonym:db | 0/29 (0.00%) correct; 0/29 (0.00%); 22 wrong | 0/29 (0.00%) correct; 0/29 (0.00%); 29 wrong | +0.00 |
| target-form:synonym:environment | 0/58 (0.00%) correct; 0/58 (0.00%); 0 wrong | 0/58 (0.00%) correct; 58/58 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:msg | 0/116 (0.00%) correct; 0/116 (0.00%); 0 wrong | 0/116 (0.00%) correct; 78/116 (67.24%); 0 wrong | +67.24 |
| target-form:synonym:settings | 0/145 (0.00%) correct; 0/145 (0.00%); 0 wrong | 0/145 (0.00%) correct; 78/145 (53.79%); 0 wrong | +53.79 |
| typo:one-insertion | 0/2422 (0.00%) correct; 1103/2422 (45.54%); 0 wrong | 0/2422 (0.00%) correct; 1134/2422 (46.82%); 0 wrong | +1.28 |
### kindAgreement

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| matching | 3456/8150 (42.40%) correct; 4823/8150 (59.18%); 252 wrong | 6642/8150 (81.50%) correct; 6642/8150 (81.50%); 0 wrong | +22.32 |
| mismatching | 8736/17612 (49.60%) correct; 10638/17612 (60.40%); 672 wrong | 14613/17612 (82.97%) correct; 14613/17612 (82.97%); 0 wrong | +22.57 |
### matrix

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| {x} × stem | 24/58 (41.38%) correct; 33/58 (56.90%); 12 wrong | 23/58 (39.66%) correct; 33/58 (56.90%); 13 wrong | +0.00 |
| {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| callees of {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| callees of {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| callees of {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| callers of {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| callers of {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| callers of {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| dependencies of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| dependencies of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| dependencies of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| dependencies of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| dependencies of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependencies of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| dependencies of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependencies of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependencies of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| dependencies of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| dependents of {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| dependents of {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| dependents of {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| dependents of {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| dependents of {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependents of {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| dependents of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependents of {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| dependents of {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| dependents of {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| downstream from {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| downstream from {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| downstream from {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| downstream from {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| downstream from {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream from {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| downstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream from {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| downstream from {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| downstream from {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| find {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| find {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| find {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| find {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| find {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| find {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| find {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| find {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| find {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| find {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| find {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| find {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| from {x} to {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| how {x} connect to {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| how does {x} get to {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| how does {x} reach {y} × full-path | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | 10/20 (50.00%) correct; 10/20 (50.00%); 0 wrong | +0.00 |
| locate {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| locate {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| locate {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| locate {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| locate {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| locate {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| locate {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| locate {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| locate {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| locate {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| locate {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| locate {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| locate {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| path between {x} and {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| path from {x} to {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| please find {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| please find {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| please find {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| please find {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| please find {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| please find {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| please find {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| please find {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| please find {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| please find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| please find {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| please find {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| please find {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| route between {x} and {y} × full-path | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | 0/10 (0.00%) correct; 0/10 (0.00%); 0 wrong | +0.00 |
| show {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| show {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| show {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| show {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| show {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| show {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| show {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| show {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| show {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| show {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| show me {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| show me {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| show me {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| show me {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| show me {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| show me {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| show me {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| show me {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show me {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| show me {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show me {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| show me {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| show me {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| trace from {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| trace from {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| trace from {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| upstream from {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| upstream from {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| upstream from {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| upstream from {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| upstream from {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream from {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| upstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream from {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| upstream from {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| upstream from {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what calls {x} × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| what calls {x} × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what calls {x} × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| what depends on {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what depends on {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what depends on {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what depends on {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what depends on {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what depends on {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what depends on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what depends on {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what depends on {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what depends on {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what does {x} call × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| what does {x} call × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} call × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| what does {x} depend on × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what does {x} depend on × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what does {x} depend on × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what does {x} depend on × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what does {x} depend on × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} depend on × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what does {x} depend on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} depend on × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} depend on × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what does {x} depend on × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what does {x} import × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what does {x} import × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what does {x} import × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what does {x} import × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what does {x} import × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} import × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what does {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} import × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what does {x} import × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what does {x} import × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what imports {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what imports {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what imports {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what imports {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what imports {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what imports {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what imports {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what imports {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what imports {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what imports {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what is {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what is {x} × folder-name | 5/16 (31.25%) correct; 12/16 (75.00%); 3 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | -25.00 |
| what is {x} × full-path | 57/58 (98.28%) correct; 58/58 (100.00%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | -22.41 |
| what is {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| what is {x} × stem | 5/58 (8.62%) correct; 12/58 (20.69%); 3 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +65.52 |
| what is {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| what is {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| what is {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what is {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what is {x} built on × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what is {x} built on × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what is {x} built on × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what is {x} built on × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what is {x} built on × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} built on × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what is {x} built on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} built on × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what is {x} built on × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what is {x} built on × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| what would break if {x} changed × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| what would break if {x} changed × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| what would break if {x} changed × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| what would break if {x} changed × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| what would break if {x} changed × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what would break if {x} changed × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| what would break if {x} changed × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what would break if {x} changed × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| what would break if {x} changed × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| what would break if {x} changed × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| where are {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where are {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| where are {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| where are {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where are {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| where are {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where are {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where are {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where are {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| where are {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where are {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where are {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| where are {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| where is {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where is {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| where is {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| where is {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| where is {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where is {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| where is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| where is {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| where is {x} called from × basename | 0/42 (0.00%) correct; 0/42 (0.00%); 24 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +43.75 |
| where is {x} called from × full-path | 0/58 (0.00%) correct; 0/58 (0.00%); 42 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +77.59 |
| where is {x} called from × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} called from × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 0 wrong | 23/58 (39.66%) correct; 32/58 (55.17%); 13 wrong | +55.17 |
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
| where is {x} defined × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +50.00 |
| where is {x} defined × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | -17.24 |
| where is {x} defined × qualified-name | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +0.00 |
| where is {x} defined × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 4 wrong | 23/58 (39.66%) correct; 33/58 (56.90%); 13 wrong | +56.90 |
| where is {x} defined × symbol-id | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} defined × symbol-name | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +0.00 |
| where is {x} defined × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} defined × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} defined × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} defined × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | +0.00 |
| where is {x} located × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where is {x} located × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +6.25 |
| where is {x} located × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| where is {x} located × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where is {x} located × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +1.72 |
| where is {x} located × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} located × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where is {x} located × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} located × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| where is {x} located × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} located × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where is {x} located × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| where is {x} located × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| where's {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where’s {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| where's {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +43.75 |
| where’s {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +43.75 |
| where's {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | -17.24 |
| where’s {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | -17.24 |
| where's {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where’s {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| where's {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +84.48 |
| where’s {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +84.48 |
| where's {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where’s {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where's {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where’s {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| where's {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where’s {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where's {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| where’s {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| where's {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where’s {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where's {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where’s {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| where's {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| where’s {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| where's {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| where’s {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| wheres {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| wheres {x} × folder-name | 0/16 (0.00%) correct; 1/16 (6.25%); 0 wrong | 3/16 (18.75%) correct; 8/16 (50.00%); 8 wrong | +43.75 |
| wheres {x} × full-path | 42/58 (72.41%) correct; 55/58 (94.83%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | -17.24 |
| wheres {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| wheres {x} × stem | 0/58 (0.00%) correct; 1/58 (1.72%); 0 wrong | 26/58 (44.83%) correct; 50/58 (86.21%); 8 wrong | +84.48 |
| wheres {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| wheres {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| wheres {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| wheres {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| wheres {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| wheres {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| wheres {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| wheres {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| which does {x} use × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| which does {x} use × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| which does {x} use × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| which does {x} use × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| which does {x} use × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which does {x} use × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| which does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which does {x} use × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which does {x} use × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| which does {x} use × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| which files depend on {x} × basename | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +0.00 |
| which files depend on {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| which files depend on {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| which files depend on {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| which files depend on {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which files depend on {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| which files depend on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which files depend on {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| which files depend on {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| which files depend on {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |
| who calls {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| who calls {x} × symbol-id | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 30/30 (100.00%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| who calls {x} × symbol-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 20/30 (66.67%) correct; 28/30 (93.33%); 0 wrong | +93.33 |
| who invokes {x} × basename | 0/42 (0.00%) correct; 0/42 (0.00%); 24 wrong | 24/42 (57.14%) correct; 42/42 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × folder-name | 0/16 (0.00%) correct; 0/16 (0.00%); 0 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +43.75 |
| who invokes {x} × full-path | 0/58 (0.00%) correct; 0/58 (0.00%); 42 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +77.59 |
| who invokes {x} × qualified-name | 0/30 (0.00%) correct; 0/30 (0.00%); 0 wrong | 29/30 (96.67%) correct; 29/30 (96.67%); 0 wrong | +96.67 |
| who invokes {x} × stem | 0/58 (0.00%) correct; 0/58 (0.00%); 0 wrong | 23/58 (39.66%) correct; 32/58 (55.17%); 13 wrong | +55.17 |
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
| who uses {x} × folder-name | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | 3/16 (18.75%) correct; 7/16 (43.75%); 8 wrong | +0.00 |
| who uses {x} × full-path | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | 45/58 (77.59%) correct; 45/58 (77.59%); 0 wrong | +0.00 |
| who uses {x} × stem | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | 26/58 (44.83%) correct; 49/58 (84.48%); 8 wrong | +0.00 |
| who uses {x} × synonym:config | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who uses {x} × synonym:configuration | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | 0/4 (0.00%) correct; 0/4 (0.00%); 4 wrong | +0.00 |
| who uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who uses {x} × synonym:db | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 1 wrong | +0.00 |
| who uses {x} × synonym:environment | 0/2 (0.00%) correct; 0/2 (0.00%); 0 wrong | 0/2 (0.00%) correct; 2/2 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:msg | 0/4 (0.00%) correct; 0/4 (0.00%); 0 wrong | 0/4 (0.00%) correct; 3/4 (75.00%); 0 wrong | +75.00 |
| who uses {x} × synonym:settings | 0/5 (0.00%) correct; 0/5 (0.00%); 0 wrong | 0/5 (0.00%) correct; 3/5 (60.00%); 0 wrong | +60.00 |

### Worst axes by parser success (not independent causal effects)

- target-form:synonym:config: 0/29 (0.00%).
- target-form:synonym:configuration: 0/116 (0.00%).
- target-form:synonym:database: 0/29 (0.00%).
- target-form:synonym:db: 0/29 (0.00%).
- punctuation:.: 840/2422 (34.68%).
- target-form:folder-name: 217/464 (46.77%).
- typo:one-insertion: 1134/2422 (46.82%).
- target-form:synonym:settings: 78/145 (53.79%).

### main: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/case:Title/no-match | 1137 | `Src/Utils/Search.Py` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/case:UPPER/no-match | 1137 | `SRC/UTILS/SEARCH.PY` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/punctuation:./no-match | 728 | `where is src/utils/search.py defined.` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/kind:file/no-match | 686 | `where is file src/utils/search.py defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/typo:one-insertion/no-match | 674 | `where is src/utils/search.pyz defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:live/no-match | 591 | `where is src/utils/search.py live defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:lives/no-match | 591 | `where is src/utils/search.py lives defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:located/no-match | 591 | `where is src/utils/search.py located defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:the/no-match | 591 | `where is the src/utils/search.py defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:layer/no-match | 538 | `where is src/utils/search.py layer defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:logic/no-match | 538 | `where is src/utils/search.py logic defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:part/no-match | 538 | `where is src/utils/search.py part defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:stuff/no-match | 538 | `where is src/utils/search.py stuff defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:thing/no-match | 538 | `where is src/utils/search.py thing defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |
| LOCATE/kind:def/no-match | 538 | `where is def src/utils/search.py defined` → no-match / LOCATE; expected ['src/utils/search.py']; selected [] |

### main: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| UPSTREAM | `dependencies of migrations/env.py logic` | 3.374, 0.303, 0.297 |
| TRACE | `trace from tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199?` | 2.089, 2.254, 1.952 |
| TRACE | `trace from TestAnthropicClient.test_anthropic_streaming` | 2.233, 2.106, 1.943 |
| TRACE | `trace from src/deriver/scope_backfill.py#_copy_chunk@308` | 1.778, 1.594, 1.595 |
| TRACE | `trace from test_live_anthropic_structured_output_and_prefix_caching` | 1.378, 1.741, 1.366 |
| TRACE | `trace from tests/live_llm/test_live_anthropic.py#test_live_anthropic_structured_output_and_prefix_caching@29` | 1.733, 1.327, 1.639 |
| TRACE | `trace from tests/utils/test_filter.py#test_dict_on_jsonb_column_still_works@38` | 1.649, 1.695, 1.211 |
| TRACE | `trace from src/deriver/scope_backfill.py#_copy_chunk@308?` | 1.499, 1.684, 1.401 |
| TRACE | `trace from tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199` | 1.607, 1.680, 1.518 |
| TRACE | `trace from tests/mock_provider/test_mock_provider.py#test_fixed_tuple_schema_round_trips@283` | 1.677, 1.649, 1.594 |

### parser: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/punctuation:./no-match | 728 | `where is src/utils/search.py defined.` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| LOCATE/typo:one-insertion/no-match | 644 | `tests/integrationz` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| DOWNSTREAM/punctuation:./no-match | 270 | `who invokes src/utils/search.py.` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| UPSTREAM/punctuation:./no-match | 264 | `what does src/utils/search.py depend on.` → no-match / NOT_SURE; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/typo:one-insertion/no-match | 228 | `who invokes src/utils/search.pyz` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:class/no-match | 207 | `who invokes class src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:def/no-match | 207 | `who invokes def src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:function/no-match | 207 | `who invokes function src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| DOWNSTREAM/kind:method/no-match | 207 | `who invokes method src/utils/search.py` → no-match / CALLERS; expected ['src/utils/search.py']; selected [] |
| LOCATE/filler:the/no-match | 199 | `where is the tests/integration` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| LOCATE/case:lower/no-match | 182 | `tests/integration` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| LOCATE/case:Title/no-match | 182 | `Tests/Integration` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| LOCATE/case:UPPER/no-match | 182 | `TESTS/INTEGRATION` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| LOCATE/filler:code/no-match | 182 | `tests/integration code` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |
| LOCATE/filler:defined/no-match | 182 | `tests/integration defined` → no-match / NOT_SURE; expected ['folder-b40bc1374968e42b']; selected [] |

### parser: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| LOCATE | `show me file tests/bench/longmem_common.py#load_test_file@126` | 2.005, 0.882, 0.878 |
| LOCATE | `please find settings` | 2.000, 1.615, 1.848 |
| LOCATE | `wheres package tests/live_llm/test_live_anthropic.py#test_live_anthropic_structured_output_and_prefix_caching@29` | 1.164, 1.234, 1.966 |
| LOCATE | `show me settings` | 1.903, 1.633, 1.611 |
| LOCATE | `where's settings` | 1.897, 1.524, 1.623 |
| LOCATE | `show me settings` | 1.821, 1.535, 1.646 |
| LOCATE | `what is package sdks/python/src/honcho/scope.py#Scope.__repr__@229` | 1.816, 1.091, 1.082 |
| LOCATE | `where is settings located` | 1.811, 1.644, 1.636 |
| CALLERS | `who calls folder sdks/python/src/honcho/scope.py#Scope.__repr__@229` | 0.678, 1.802, 0.640 |
| TRACE | `trace from directory tests/utils/test_clients.py#TestAnthropicClient.test_anthropic_streaming@199` | 1.802, 1.624, 1.652 |

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
| DOWNSTREAM | 5663/11475 (49.35%) correct; 7195/11475 (62.70%); 1531 wrong | 7897/11475 (68.82%) correct; 8448/11475 (73.62%); 181 wrong | +10.92 |
| LOCATE | 10424/17850 (58.40%) correct; 13367/17850 (74.89%); 114 wrong | 12566/17850 (70.40%) correct; 13562/17850 (75.98%); 323 wrong | +1.09 |
| PATH | 96/1827 (5.25%) correct; 972/1827 (53.20%); 0 wrong | 56/1827 (3.07%) correct; 63/1827 (3.45%); 0 wrong | -49.75 |
| UPSTREAM | 4854/7650 (63.45%) correct; 6076/7650 (79.42%); 42 wrong | 5430/7650 (70.98%) correct; 5782/7650 (75.58%); 126 wrong | -3.84 |
### axis

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| case:lower | 594/1252 (47.44%) correct; 644/1252 (51.44%); 49 wrong | 899/1252 (71.81%) correct; 921/1252 (73.56%); 7 wrong | +22.12 |
| case:Title | 54/1252 (4.31%) correct; 95/1252 (7.59%); 9 wrong | 899/1252 (71.81%) correct; 921/1252 (73.56%); 7 wrong | +65.97 |
| case:UPPER | 54/1252 (4.31%) correct; 95/1252 (7.59%); 9 wrong | 899/1252 (71.81%) correct; 921/1252 (73.56%); 7 wrong | +65.97 |
| filler:code | 1032/1252 (82.43%) correct; 1065/1252 (85.06%); 81 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -13.26 |
| filler:defined | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| filler:layer | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| filler:live | 816/1252 (65.18%) correct; 843/1252 (67.33%); 81 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | +4.47 |
| filler:lives | 816/1252 (65.18%) correct; 843/1252 (67.33%); 81 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | +4.47 |
| filler:located | 816/1252 (65.18%) correct; 843/1252 (67.33%); 81 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | +4.47 |
| filler:logic | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| filler:part | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| filler:stuff | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| filler:the | 968/1252 (77.32%) correct; 1001/1252 (79.95%); 81 wrong | 1083/1252 (86.50%) correct; 1096/1252 (87.54%); 23 wrong | +7.59 |
| filler:thing | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| kind:class | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 837/1252 (66.85%) correct; 837/1252 (66.85%); 27 wrong | -15.65 |
| kind:def | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 837/1252 (66.85%) correct; 837/1252 (66.85%); 27 wrong | -15.65 |
| kind:dir | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| kind:directory | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| kind:file | 754/1252 (60.22%) correct; 754/1252 (60.22%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 0 wrong | +11.58 |
| kind:folder | 754/1252 (60.22%) correct; 1068/1252 (85.30%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -13.50 |
| kind:function | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 837/1252 (66.85%) correct; 837/1252 (66.85%); 27 wrong | -15.65 |
| kind:method | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 837/1252 (66.85%) correct; 837/1252 (66.85%); 27 wrong | -15.65 |
| kind:module | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 0 wrong | -10.70 |
| kind:package | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 29 wrong | -10.70 |
| kind:script | 754/1252 (60.22%) correct; 1033/1252 (82.51%); 58 wrong | 899/1252 (71.81%) correct; 899/1252 (71.81%); 0 wrong | -10.70 |
| punctuation:? | 837/1252 (66.85%) correct; 887/1252 (70.85%); 67 wrong | 899/1252 (71.81%) correct; 921/1252 (73.56%); 7 wrong | +2.72 |
| punctuation:. | 0/1252 (0.00%) correct; 580/1252 (46.33%); 0 wrong | 0/1252 (0.00%) correct; 580/1252 (46.33%); 0 wrong | +0.00 |
| target-form:basename | 675/870 (77.59%) correct; 810/870 (93.10%); 50 wrong | 725/870 (83.33%) correct; 870/870 (100.00%); 0 wrong | +6.90 |
| target-form:folder-name | 162/319 (50.78%) correct; 208/319 (65.20%); 22 wrong | 203/319 (63.64%) correct; 261/319 (81.82%); 29 wrong | +16.61 |
| target-form:full-path | 837/1252 (66.85%) correct; 887/1252 (70.85%); 67 wrong | 899/1252 (71.81%) correct; 921/1252 (73.56%); 7 wrong | +2.72 |
| target-form:stem | 558/1189 (46.93%) correct; 705/1189 (59.29%); 23 wrong | 725/1189 (60.98%) correct; 913/1189 (76.79%); 29 wrong | +17.49 |
| target-form:synonym:authentication | 0/29 (0.00%) correct; 0/29 (0.00%); 0 wrong | 0/29 (0.00%) correct; 0/29 (0.00%); 0 wrong | +0.00 |
| target-form:synonym:database | 0/29 (0.00%) correct; 0/29 (0.00%); 0 wrong | 29/29 (100.00%) correct; 29/29 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:environment | 0/29 (0.00%) correct; 0/29 (0.00%); 0 wrong | 29/29 (100.00%) correct; 29/29 (100.00%); 0 wrong | +100.00 |
| target-form:synonym:repository | 0/29 (0.00%) correct; 0/29 (0.00%); 0 wrong | 29/29 (100.00%) correct; 29/29 (100.00%); 0 wrong | +100.00 |
| typo:one-insertion | 0/1252 (0.00%) correct; 787/1252 (62.86%); 0 wrong | 0/1252 (0.00%) correct; 812/1252 (64.86%); 0 wrong | +2.00 |
### kindAgreement

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| matching | 2262/3886 (58.21%) correct; 3197/3886 (82.27%); 174 wrong | 2755/3886 (70.90%) correct; 2755/3886 (70.90%); 116 wrong | -11.37 |
| mismatching | 6032/9193 (65.62%) correct; 7382/9193 (80.30%); 464 wrong | 6886/9193 (74.90%) correct; 6886/9193 (74.90%); 108 wrong | -5.40 |
### matrix

| Axis / operation / phrase × form | Main | Parser | Δ pp |
|---|---|---|---:|
| {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | +0.00 |
| {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| dependencies of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| dependencies of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| dependencies of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| dependencies of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependencies of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependencies of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| dependents of {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| dependents of {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| dependents of {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| dependents of {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| dependents of {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| dependents of {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| downstream from {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| downstream from {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| downstream from {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| downstream from {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| downstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| downstream from {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| find {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| find {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +2.44 |
| find {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | +0.00 |
| find {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| find {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| from {x} to {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| how {x} connect to {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| how does {x} get to {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| how does {x} reach {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| locate {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| locate {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| locate {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +2.44 |
| locate {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| locate {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| locate {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| locate {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| path between {x} and {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| path from {x} to {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| please find {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| please find {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| please find {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | +0.00 |
| please find {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| please find {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| please find {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| please find {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| route between {x} and {y} × full-path | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | 0/9 (0.00%) correct; 0/9 (0.00%); 0 wrong | +0.00 |
| show {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| show {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| show {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | +0.00 |
| show {x} × stem | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | +0.00 |
| show {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| show me {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| show me {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | +0.00 |
| show me {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| show me {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| show me {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| show me {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| upstream from {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| upstream from {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| upstream from {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| upstream from {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| upstream from {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| upstream from {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what depends on {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what depends on {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what depends on {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what depends on {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what depends on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what depends on {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} depend on × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what does {x} depend on × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what does {x} depend on × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what does {x} depend on × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} depend on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} depend on × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what does {x} import × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what does {x} import × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what does {x} import × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what does {x} import × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what does {x} import × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what does {x} import × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what imports {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what imports {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what imports {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what imports {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what imports {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what imports {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what is {x} × folder-name | 8/11 (72.73%) correct; 10/11 (90.91%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | -9.09 |
| what is {x} × full-path | 39/41 (95.12%) correct; 39/41 (95.12%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | -19.51 |
| what is {x} × stem | 8/41 (19.51%) correct; 10/41 (24.39%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +53.66 |
| what is {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what is {x} built on × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what is {x} built on × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what is {x} built on × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what is {x} built on × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what is {x} built on × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what is {x} built on × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| what would break if {x} changed × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| what would break if {x} changed × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| what would break if {x} changed × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| what would break if {x} changed × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| what would break if {x} changed × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| what would break if {x} changed × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where are {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| where are {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | +0.00 |
| where are {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| where are {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where are {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where are {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| where is {x} × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +2.44 |
| where is {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| where is {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × basename | 0/30 (0.00%) correct; 0/30 (0.00%); 25 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| where is {x} called from × full-path | 0/41 (0.00%) correct; 0/41 (0.00%); 29 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +78.05 |
| where is {x} called from × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | +70.73 |
| where is {x} called from × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} called from × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} called from × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} defined × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| where is {x} defined × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | -17.07 |
| where is {x} defined × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +78.05 |
| where is {x} defined × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} defined × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} defined × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where is {x} located × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| where is {x} located × full-path | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | 31/41 (75.61%) correct; 31/41 (75.61%); 1 wrong | +0.00 |
| where is {x} located × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| where is {x} located × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where is {x} located × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where is {x} located × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where’s {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| where's {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| where’s {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| where's {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | -14.63 |
| where’s {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | -14.63 |
| where's {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +78.05 |
| where’s {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +78.05 |
| where's {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where’s {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| where's {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where's {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| where’s {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| wheres {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| wheres {x} × full-path | 29/41 (70.73%) correct; 38/41 (92.68%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | -14.63 |
| wheres {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +78.05 |
| wheres {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| wheres {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| wheres {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| which does {x} use × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| which does {x} use × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| which does {x} use × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| which does {x} use × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which does {x} use × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which does {x} use × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| which files depend on {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| which files depend on {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| which files depend on {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| which files depend on {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| which files depend on {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| which files depend on {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × basename | 0/30 (0.00%) correct; 0/30 (0.00%); 25 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × folder-name | 0/11 (0.00%) correct; 0/11 (0.00%); 0 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +81.82 |
| who invokes {x} × full-path | 0/41 (0.00%) correct; 0/41 (0.00%); 29 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +78.05 |
| who invokes {x} × stem | 0/41 (0.00%) correct; 0/41 (0.00%); 0 wrong | 25/41 (60.98%) correct; 29/41 (70.73%); 1 wrong | +70.73 |
| who invokes {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who invokes {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who invokes {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × basename | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | 25/30 (83.33%) correct; 30/30 (100.00%); 0 wrong | +0.00 |
| who uses {x} × folder-name | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | 7/11 (63.64%) correct; 9/11 (81.82%); 1 wrong | +0.00 |
| who uses {x} × full-path | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | 31/41 (75.61%) correct; 32/41 (78.05%); 0 wrong | +0.00 |
| who uses {x} × stem | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | 25/41 (60.98%) correct; 32/41 (78.05%); 1 wrong | +0.00 |
| who uses {x} × synonym:authentication | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | +0.00 |
| who uses {x} × synonym:database | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:environment | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |
| who uses {x} × synonym:repository | 0/1 (0.00%) correct; 0/1 (0.00%); 0 wrong | 1/1 (100.00%) correct; 1/1 (100.00%); 0 wrong | +100.00 |

### Worst axes by parser success (not independent causal effects)

- target-form:synonym:authentication: 0/29 (0.00%).
- punctuation:.: 580/1252 (46.33%).
- typo:one-insertion: 812/1252 (64.86%).
- kind:class: 837/1252 (66.85%).
- kind:def: 837/1252 (66.85%).
- kind:function: 837/1252 (66.85%).
- kind:method: 837/1252 (66.85%).
- filler:code: 899/1252 (71.81%).

### main: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/case:Title/no-match | 509 | `Vitest.Config.Ts` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/case:UPPER/no-match | 509 | `VITEST.CONFIG.TS` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:Title/no-match | 330 | `what depends on Vitest.Config.Ts` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:UPPER/no-match | 330 | `what depends on VITEST.CONFIG.TS` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/case:Title/no-match | 228 | `what does Vitest.Config.Ts depend on` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/case:UPPER/no-match | 228 | `what does VITEST.CONFIG.TS depend on` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/punctuation:./no-match | 226 | `where is vitest.config.ts defined.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/case:lower/no-match | 220 | `src/components/buyer/roomnotice.tsx` → no-match / NOT_SURE; expected ['src/components/buyer/RoomNotice.tsx']; selected [] |
| LOCATE/target-form:stem/no-match | 213 | `vitest.config` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/kind:file/no-match | 197 | `where is file vitest.config.ts defined` → no-match / LOCATE; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/punctuation:./no-match | 188 | `what does vitest.config.ts depend on.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| LOCATE/typo:one-insertion/no-match | 175 | `where is vitest.config.tsz defined` → no-match / LOCATE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/punctuation:./no-match | 166 | `where is vitest.config.ts called from.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/case:lower/no-match | 150 | `what depends on src/components/buyer/roomnotice.tsx` → no-match / NOT_SURE; expected ['src/components/buyer/RoomNotice.tsx']; selected [] |
| LOCATE/filler:live/no-match | 124 | `where is vitest.config.ts live defined` → no-match / LOCATE; expected ['vitest.config.ts']; selected [] |

### main: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| PATH | `route between src/lib part and app/api/events part` | 0.292, 0.106, 0.106 |
| PATH | `path between script src/components/buyer and script app/api/auth/login` | 0.235, 0.175, 0.105 |
| LOCATE | `please find src/lib/insights.tsz` | 0.229, 0.034, 0.034 |
| DOWNSTREAM | `who invokes folder app/api/events` | 0.229, 0.062, 0.061 |
| LOCATE | `show me src/lib/__tests__/insights.test.ts part` | 0.229, 0.033, 0.033 |
| PATH | `path from src/components/buyerz to app/api/auth/loginz` | 0.228, 0.067, 0.060 |
| PATH | `from src/components/buyer thing to app/api/auth/login thing` | 0.223, 0.110, 0.109 |
| PATH | `path from class src/components/buyer to class app/api/auth/login` | 0.222, 0.113, 0.111 |
| LOCATE | `what is Src/Lib/__tests__/Robustness.Test.Ts` | 0.221, 0.034, 0.095 |
| PATH | `how script src/components/modules/__tests__ connect to script src/components/modules` | 0.219, 0.109, 0.111 |

### parser: 15 most frequent failure patterns

| Pattern | Count | Example → observed status / operation |
|---|---:|---|
| LOCATE/punctuation:./no-match | 226 | `where is vitest.config.ts defined.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/punctuation:./no-match | 195 | `who invokes vitest.config.ts.` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| UPSTREAM/punctuation:./no-match | 188 | `what does vitest.config.ts depend on.` → no-match / NOT_SURE; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/typo:one-insertion/no-match | 157 | `who invokes vitest.config.tsz` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| LOCATE/typo:one-insertion/no-match | 154 | `app/(seller)/seller/page.tsxz` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| DOWNSTREAM/kind:class/no-match | 145 | `who invokes class vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:def/no-match | 145 | `who invokes def vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:function/no-match | 145 | `who invokes function vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| DOWNSTREAM/kind:method/no-match | 145 | `who invokes method vitest.config.ts` → no-match / CALLERS; expected ['vitest.config.ts']; selected [] |
| LOCATE/kind:file/no-match | 140 | `file app/(seller)/seller/page.tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| LOCATE/kind:module/no-match | 140 | `module app/(seller)/seller/page.tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| LOCATE/kind:script/no-match | 140 | `script app/(seller)/seller/page.tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| LOCATE/case:lower/no-match | 126 | `app/(seller)/seller/page.tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| LOCATE/case:Title/no-match | 126 | `App/(Seller)/Seller/Page.Tsx` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |
| LOCATE/case:UPPER/no-match | 126 | `APP/(SELLER)/SELLER/PAGE.TSX` → no-match / NOT_SURE; expected ['app/(seller)/seller/page.tsx']; selected [] |

### parser: worst 10 direct queries

| Operation | Question | Three timings (ms) |
|---|---|---|
| LOCATE | `please find Src/Lib/Progress.Ts` | 0.684, 0.059, 0.057 |
| LOCATE | `please find src/lib/types.ts lives` | 0.068, 0.061, 0.431 |
| PATH | `from the src/lib to the app/api/auth/me` | 0.348, 0.166, 0.162 |
| DOWNSTREAM | `who invokes app/(seller)/seller stuff` | 0.289, 0.141, 0.139 |
| DOWNSTREAM | `where is repository called from` | 0.223, 0.221, 0.277 |
| PATH | `path between src/lib located and app/api/events located` | 0.268, 0.086, 0.085 |
| LOCATE | `where is src/components/seller/RoomControls.tsx defined defined` | 0.267, 0.123, 0.121 |
| LOCATE | `show me BuyerLoginPrompt.tsx` | 0.265, 0.056, 0.056 |
| LOCATE | `where is repository defined` | 0.250, 0.260, 0.244 |
| LOCATE | `find src/lib/__tests__/insights.test.ts thing` | 0.064, 0.065, 0.257 |

### Negative outcomes

| Version | No-match | Unresolved choices | Overconfident |
|---|---:|---:|---:|
| main | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |
| parser | 240/240 (100.00%) | 0/240 (0.00%) | 0/240 (0.00%) |

## New confident mistakes versus main

Aggregate improvement does not imply zero regressions. These cases are wrong on the parser but were not confidently wrong on main; generated ambiguous/mismatching-kind cases remain in this count. No parser fixes were made.

- honcho: 149 newly confident-wrong generated cases.
  - `backfill`: expected LOCATE on ['src/reconciler/backfill.py']; got LOCATE on ['src/reconciler/backfill.py#Backfill@33'].
  - `where is backfill defined`: expected LOCATE on ['src/reconciler/backfill.py']; got LOCATE on ['src/reconciler/backfill.py#Backfill@33'].
  - `who invokes backfill`: expected DOWNSTREAM on ['src/reconciler/backfill.py']; got CALLERS on ['src/reconciler/backfill.py#Backfill@33'].
- salesroom: 444 newly confident-wrong generated cases.
  - `what is events`: expected LOCATE on ['folder-339c0fd4c4ebbcb5']; got LOCATE on ['src/lib/events.ts'].
  - `what is events`: expected LOCATE on ['folder-339c0fd4c4ebbcb5']; got LOCATE on ['src/lib/events.ts'].
  - `where's events`: expected LOCATE on ['folder-339c0fd4c4ebbcb5']; got LOCATE on ['src/lib/events.ts'].

## Verification and retained attempts

Generator tests cover determinism, quotas, label construction, axis coverage, directed path grading, seed vs incidental selection, choice-operation checks, negative classification, deduplication and percentile arithmetic. Full suite commands and counts are recorded in the task handoff and build update.
Verified: Python 458/458, JS 204/204 (including five new benchmark tests), zero final skips; scorer 47/47, alias 15/15, lookup 39/40 (existing bearer-auth expected-label limitation). Raw-row construction, all outcome/latency totals and 1,920 HTTP response statuses reconcile. Frozen target source audit passes. Product code and frozen hand-written eval files have no changes.
Python first passed with two browser skips; enabling Playwright exposed missing axe-core at an old default path. Installed axe-core in ignored benchmark tooling and set PLAYWRIGHT_DIR/AXE_CORE_PATH; final unchanged full suite passed with zero skips. These environment attempts remain in the logs; no tests were relaxed.
During harness development an HTTP workspace directory was missing; fixed in the harness only. A 180-second HTTP probe and a 420-second foreground run were interrupted by tool deadlines. Their logs remain local; no timing pass/fail threshold or performance-driven retries were used. Headline numbers come from the completed background run, not a selection of the fastest attempts.
Remaining caveats: synthetic wording and redundant rows, no multi-axis interaction coverage, known-target bias, source graph/extractor limitations, limited typo and negative distributions, first-page grading, and non-isolated timing. Findings are measurements, not parser fixes or a claim that arbitrary questions work. Consultant second opinion is requested; approval remains with the generalist.
