# Workspace question log and persistent session

Card `t_44e9d449`; local `question-log`, manually ported from playground `75c2bfb`
onto server-speed plus parser-collisions. Parent consultant point 1 (chosen-ID
pagination) accepted through parent's `1adb892`, merged before touching the UI.
The live playground and main checkout are untouched. No push or PR.

## Journal contract

Every successful, validated POST `/api/projects/<id>/query` without a continuation
appends a question. Every new ask gets a server-generated `q-` + 32 hex entry ID,
returned in `X-DAG-GPS-Question-ID`; evidence packet JSON is unchanged. Reusing a
client requestId cannot overwrite a question or redirect a verdict. Choosing an
alternative is another answer/question record; paging is not. Source, context,
explanation replay, agent-bridge CLI calls, invalid requests and failed workers
are not questions in this HTTP journal.

`<root>/query-log.jsonl` records:

- UTC `at`, `entryId`, `requestId`, `projectId`, `snapshotId`, exact source `commit`;
- original `query`, operation/status, automatic `label`, server processing `latencyMs`;
- first ten selected IDs and first ten alternative IDs, omitting individual IDs
  longer than 256 characters rather than truncating them into false identifiers.

Labels: matched → match; no-match → no match; all other packet statuses → unsure.
These describe routing, not correctness. `latencyMs` includes snapshot/worker/
validation, excludes log append and HTTP serialization; the separate benchmark
measures full HTTP including append. Source contents, capability headers/keys,
client IPs and raw packets are never automatically copied into records. Question
text is recorded verbatim: a user who types a secret puts it in the log. Keep the
workspace private and review exports before sharing.

One process owns a workspace root. A thread lock covers complete JSONL appends,
rotation, reading and verdict updates. Lines are capped at 128 KiB including
worst-case JSON-escaped Unicode. Files rotate before exceeding 10 MiB, keeping
only `query-log.jsonl` and `query-log.jsonl.1` (at most 20 MiB total). Older entries
expire. Appends are flushed on close without per-request fsync; a crash may lose
the latest write. A torn line is ignored and separated from the next append.
This is bounded local retention, not a crash-proof audit log or multi-process DB.

GET `/api/projects/<id>/questions` folds retained generations newest-first with
`verdict` and `verdictAt` (null before labeling). My questions shows the newest
200 retained records, their source commit and editable verdict buttons; export
includes all retained records. The API may return up to the retained 20 MiB.

POST `/api/projects/<id>/verdict` accepts exactly `{entryId, label}`. Both routes
require the existing session/Host/origin boundary. Invalid shapes/labels/IDs are
400, unknown/expired/foreign-project entries 404, missing session 401. Repeating
the saved label is a byte-for-byte no-op, retaining its time. Changes append a
question checkpoint plus verdict under the lock, retaining the corrected question
across a rotation. Automatic labels are never overwritten. UI changes use the
server-confirmed verdict; project switches and stale history replies are guarded.

## Persistent session / proxy

See the README run section or `python3 -m app.server --help`.
`--session-file` creates a URL-safe random key in a new 0600 file. Existing files
must be regular, non-symlink, exactly 0600, with a 32–128 character URL-safe key
and optional final newline. Unsafe/malformed files are refused with a clear startup
error, not repaired or replaced. Default remains a new key every process run.
Keep the port, hostname and key file stable for a stable link. Deleting the key
and restarting intentionally revokes it. The key is a bearer capability.

`--allow-host` is repeatable and exact; accepts a bare hostname, no wildcard,
scheme or port. Only explicitly listed HTTPS proxy origins are added. Loopback
Host/origin checks stay the default and the server still binds only to loopback.
Use Tailscale Serve, not Funnel. No real tailnet deployment was performed here;
HTTP boundary tests exercise accepted and rejected Host/Origin combinations.

## Evaluation export

```sh
python3 scripts/export_query_log.py /private/workspace/query-log.jsonl \
  --out /private/questions-review.json
# Mixed projects/pins require selection:
python3 scripts/export_query_log.py /private/workspace/query-log.jsonl \
  --project-id p-EXACT_ID --commit FULL_COMMIT --out /private/questions-review.json
```

The exporter reads both retained generations, folds verdicts, preserves unique
questions, and emits the frozen question-set `schema`/`pin`/`rows` shape with
`question`, `autoLabel`, `verdict` and provenance. It is explicitly a review draft:
`reviewRequired: true`, expected/split null, targets/evidence empty, observed
results separate. A match verdict cannot supply independent target/operation truth;
review those and assign splits before any benchmark inclusion. Mixed project/pin
exports are refused unless filtered. Existing output files are never overwritten.
No frozen sets are edited, and no model calls or automatic tuning occurs.

## Verification

- All eight original playground behaviors ported into `tests/test_question_log.py`,
  plus rotation, idempotency, entry identity, concurrency, malformed/unsafe keys,
  hostile verdict bodies, export and Unicode/torn-write tests.
- 492 Python / 266 JS tests pass, zero skips. First Python run hit the pre-existing
  oversized-body socket-reset race; original `python.log` retained, unchanged
  full rerun passed (`python-rerun.log`). No assertion/threshold changes.
- Real Chromium Honcho: five questions (three matches, one no-match, one choice),
  verdicts saved, server restarted on same port/key, same original link loaded in
  a fresh browser context, all five questions/verdicts persisted. An older verdict
  was corrected without creating a new question. No page errors.
  `artifacts/question-log/browser-1/receipt.json`, six screenshots and question rows.
  This uses a copied pinned Honcho snapshot, rebound to truthful query-code hashes;
  the live playground is untouched. Browser shows the real app/graph, not mocks.
- All eight unchanged release gates and packaging pass on implementation checkpoint
  `365197b8fd313cd5d75188f62c1f34f31c3b4c62`: build, test, smoke, release session,
  accessibility, performance, UI performance and milestone acceptance. Gated suites:
  492 Python / 266 JS, zero skips. Release scorer worst p95 3.873 ms (<10 ms).
  Receipt: `artifacts/question-log/gates/verification.json`. Gates passed on their
  first complete attempt; no threshold changes or performance-failure retries.
  Later documentation commits are not misrepresented as the gated checkpoint.

### Warm HTTP latency

Existing `bench_server_performance.py`, identical 240 Honcho inputs twice (480
measured requests per run), one cold request and 20 warmups, serial local HTTP.
Same pinned snapshot, truthful code bindings. No suites ran concurrently with
these measurements. Full response bodies were read; logging stays in the timed path.

| Version | p50 ms | p95 ms | p99 ms |
|---|---:|---:|---:|
| Stacked base before implementation | 1.402 | 8.139 | 15.583 |
| Final question-log implementation | 1.196 | 6.070 | 12.694 |
| Fresh server-speed reference `cebe7c4` | 1.066 | 6.246 | 12.258 |

Final p95 is 0.175 ms below the fresh server-speed reference, meeting the +1 ms
limit; also 0.923 ms below its historical 6.993 ms. This is evidence of no measured
regression, not a claim that disk logging accelerates queries. Machine/GC variance
is visible in the base comparison. All 480 stacked-base/final packet byte hashes
match; the added question identity is an HTTP header, not a packet mutation.

Artifacts: `artifacts/question-log/{before,after-final,server-speed-reference}/`.
The preliminary `after/` run (p95 5.514 ms) is retained, but is not the final result:
torn-line append recovery and the Unicode line cap were hardened afterward. There
were no discarded failing performance attempts. Before/final summaries record the
then-current merge HEAD because measurement preceded the implementation commit;
the final measured source was subsequently committed unchanged as `365197b`.

Dag-consultant second opinion requested; final approval remains with the generalist.
No next feature, public deployment, main merge, push or PR was started.

Reproduction (installed local test dependencies, not runtime dependencies):

```sh
export PLAYWRIGHT_DIR=/Users/aibert/projects/quest-coder/node_modules/playwright
export NODE_PATH=/Users/aibert/projects/quest-coder/node_modules
export AXE_CORE_PATH=/Users/aibert/projects/quest-coder/node_modules/axe-core/axe.min.js
export TMPDIR=/Users/aibert/.hermes/profiles/dag-generalist/cache/scratch
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH
/usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
/usr/bin/python3 scripts/verify_question_log.py --snapshot /path/to/honcho/snapshot.json \
  --out artifacts/question-log/browser-fresh
/usr/bin/python3 scripts/bench_server_performance.py --code . \
  --snapshot /path/to/honcho/snapshot.json --inputs /path/to/honcho-parser-http-input.json \
  --out artifacts/question-log/perf-fresh
/usr/bin/python3 scripts/release_check.py --output artifacts/question-log/gates
```
