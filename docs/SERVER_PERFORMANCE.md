# Server performance — validated snapshot index

Card `t_20ef91ae`; local branch `server-speed`, based on question-parser
`6928324bc47f7bd3db0fd6a12070a9531aa8b24d`. Implementation: `8277e35`.
No parser/scorer changes, push, merge, PR, imported-source execution or model calls.

## Result

Warm Honcho HTTP p95 **487.774 → 6.993 ms** (69.75×), below the 20 ms target.
Salesroom **3.078 → 1.075 ms**. All 960 paired responses have identical exact
response-byte SHA-256 hashes, not just equivalent status/selected nodes.
Cold starts remain expensive; this change amortizes validation rather than
removing it. First Honcho request was **647.058 → 786.101 ms**.

## Diagnosis and design

The old store parsed an 18.4 MB Honcho snapshot on every request. Every query
then traversed the entire snapshot again inside `validate_evidence_packet`.
Context/source and explanation routes repeated that same work, sometimes once
per source excerpt or stored explanation. Persistent Node workers were already
present; restarting Node was not the warm-path problem.

`validate_snapshot(snapshot)` keeps the full original strict validation and
returns a `SnapshotIndex`, retaining dictionary access for existing consumers.
It contains node/edge/file/symbol lookups, certain-only call edges, and per-caller
unresolved-call counts plus the first 100 position-tagged records. Packet checks
merge those bounded prefixes in original snapshot order, so repeated calls do
not scan all unresolved calls or reconstruct the entire certain-only graph.
Conditional changed-highlight validation retains its original error ordering.

`validate_evidence_packet_against(packet, index)` checks every packet's JSON
bounds, provenance, selected nodes/edges, witnesses, call sites/confidence,
entry points, unresolved evidence, alternatives/status, highlight/operation
rules, source hashes/ranges, truncation and limitations. No check is removed.
`validate_evidence_packet(packet, snapshot)` remains a full-check wrapper,
including packet-JSON errors preceding snapshot errors.

The index is a trusted Python object, not a new wire contract. Snapshot/index
objects are read-only by convention: internal callers must not mutate them.
The indexed source/context/explanation APIs reject a different snapshot object.
Unindexed public callers still validate in full. HTTP clients never supply an
index, and serialized responses do not expose one.

## Cache and invalidation

- `WorkspaceStore` retains four parsed snapshot/index pairs, LRU-ordered.
- Lookup remains project-scoped and reads the small project index on each call;
  opaque ID checks, root containment and stored project/snapshot identity checks
  remain in place.
- File identity is resolved path, device, inode, size, nanosecond mtime and ctime.
  Snapshot ID plus that identity and the SHA-256 of loaded bytes identify the
  worker generation. SHA-256 is computed once per cold load, not per request.
- A lock covers cold read/parse/validation and LRU mutation. Concurrent cold
  requests share one validated object. A metadata change removes the old entry
  before parsing; a failed reload cannot fall back to stale cached data.
- Identity is checked around the read. A racing edit returns 409/retry rather
  than caching inconsistent bytes. Replacement and same-size/restored-mtime
  edits invalidate through inode/ctime as well.
- Node verifies the optional expected content hash at startup. A disk change
  between Python loading and Node starting is rejected, not served from a
  different generation. Running workers operate on their already loaded data;
  the next request checks disk identity again.
- The worker pool remains bounded at four. Requests lease workers, preventing
  eviction during use, while different snapshots can run concurrently. An
  all-busy pool returns 429; existing per-worker queue bounds/timeouts remain.
- All query, snapshot GET, source, context, explanation write/list routes use
  the store. Import completion warms the validated disk entry before `ready`.
  Git source bytes are still retrieved and hash-checked on every source read;
  explanations are still validated on write and on read.

This is not protection against a privileged actor able to forge every filesystem
identity field or mutate process memory. There is no background watcher and no
live-repository refresh. Existing in-flight requests may finish on the generation
they already acquired. Separate four-entry Python and Node LRUs can retain up to
eight different parsed generations, plus references held by active requests.
The cache bounds entries, not total bytes. Huge snapshot GET responses and Git
source reads still cost work proportional to output/source size.
Cold snapshot loads are serialized by the store lock and can temporarily delay
warm lookups; the warm-only latency target is not a concurrent-import guarantee.

## Measurement

Same machine, serial loopback HTTP, fresh TCP connection and full response read.
Each repo/version uses the existing benchmark's identical 240 distributed
questions twice: **480 measured requests**, after one cold request and 20 warmups.
Total: **1,920 measured HTTP requests**. No synthetic replacement responses.
The snapshots are rebound only to the truthful query-code hashes, exactly as in
the existing variation HTTP benchmark. Graph and inventory bytes are unchanged.

Before ran in the untouched parser worktree at `6928324`. After ran on the
`server-speed` working tree whose source was then committed unchanged as
`8277e35`; its raw summary records the pre-commit HEAD (`6928324`), not a claim
that those dirty bytes were the baseline implementation. Baseline and after
runs did not overlap each other or a suite/benchmark run.

Nearest-rank percentiles, milliseconds:

| Repository | Version | Cold first | Warm p50 | p95 | p99 | Max |
|---|---|---:|---:|---:|---:|---:|
| Honcho | Before | 647.058 | 470.973 | 487.774 | 496.916 | 500.378 |
| Honcho | After | 786.101 | 1.181 | 6.993 | 13.929 | 15.857 |
| Salesroom | Before | 34.714 | 2.918 | 3.078 | 3.334 | 4.363 |
| Salesroom | After | 41.396 | 0.717 | 1.075 | 1.924 | 2.511 |

Instrumented warm stage means, milliseconds (not sums of independent percentiles):

| Repository/version | Store read/parse or cache lookup | Worker excluding validation | Packet validation | JSON serialization |
|---|---:|---:|---:|---:|
| Honcho before | 64.0451 | 1.1467 | 402.4169 | 0.0706 |
| Honcho after | 0.1168 | 0.8000 | 0.6657 | 0.0741 |
| Salesroom before | 0.3365 | 0.1602 | 2.0562 | 0.0095 |
| Salesroom after | 0.1176 | 0.1996 | 0.0806 | 0.0106 |

Worker timing includes IPC, queueing and JSON decoding, not just the Node service.
The before validator timing includes full snapshot validation. The cold after
store timing also includes index construction. HTTP parsing, request handling,
scheduling, socket I/O and response read explain the remaining latency. Packet
cost still varies with packet size; indexing does not make large packets free.
The unchanged release scorer p95 <10 ms gate is separate from real HTTP p95.

## Memory

Current RSS measured using `ps` immediately after 480 warm requests, MiB:

| Repository/version | Python server/harness | Node worker | Combined |
|---|---:|---:|---:|
| Honcho before | 256.953 | 124.875 | 381.828 |
| Honcho after | 209.531 | 227.219 | 436.750 |
| Salesroom before | 21.484 | 70.156 | 91.641 |
| Salesroom after | 24.000 | 70.484 | 94.484 |

The Python process includes the benchmark's original snapshot and parsed cached
copy, not just the index. Node now also verifies startup bytes; GC timing differs
between the multi-minute baseline and short after run. These are observed warm
RSS values, not isolated allocation deltas or proof of a lower total memory cost.
Caching trades memory and cold-start work for warm latency. No forced GC was used.

## Verification and reproduction

New tests cover cache hits/eviction, two alternating snapshots, concurrent cold
loads and real workers, same-ID valid replacement, invalid on-disk tampering,
same-size/restored-mtime edits, foreign indexes, missing nodes/foreign revision/
wrong ranges/hashes, unresolved ordering/counts, startup races and worker leases.
An HTTP test disables full validation after warming and exercises source,
query, context and explanation write/list; a second confirms warm tampering
returns 422 rather than a stale answer. Four initial regressions were run RED.

`verify_snapshot_equivalence.py` loads the pre-change contract directly from Git,
replays existing Python packet fixtures through both validators and the index,
and compares exact exception type names/messages or acceptance. It additionally
checks distributed real Honcho/Salesroom and certain-only function packets.
The final replay passed **473 Python tests, zero skips**, comparing **180 packet
checks (109 accepted, 71 rejected), 176 index checks, and 54 real packets**, with
zero differences. Four checks use invalid snapshots and therefore cannot produce
an index; the full-wrapper errors still match. Receipt:
`artifacts/server-performance/equivalence.json`. JS: **212/212, zero skips**.
All **eight unchanged release gates and packaging pass** on clean checkpoint
`8bfc232eca41d8af732bbd86e78f4eaf32169852`: build, test, smoke, release session,
accessibility, performance, UI performance and milestone acceptance. The gated
suites are **473 Python / 212 JS, zero skips**. Release scorer worst p95 is
**3.547 ms**, below the unchanged **10 ms** threshold. No performance retry or
threshold change. Receipts: `artifacts/server-performance/gates/verification.json`
and `package-result.json`. Subsequent changes are documentation/build-update
only; the receipt names the gated checkpoint, not a later documentation commit.
Consultant second opinion is requested; this is not final generalist approval.

```sh
# From this worktree; these paths point to existing local pinned fixtures.
PARSER=/Users/aibert/projects/dag-gps-question-parser
for REPO in honcho salesroom; do
  env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
    scripts/bench_server_performance.py --code . \
    --snapshot "$PARSER/artifacts/question-parser/$REPO/snapshot.json" \
    --inputs "$PARSER/artifacts/variation-benchmark/$REPO-parser-http-input.json" \
    --out "artifacts/server-performance/reproduced-$REPO"
done
# Use --code "$PARSER" with the same inputs to reproduce the baseline.
# Browser-backed suites/gates require these installed dependencies:
export PLAYWRIGHT_DIR=/Users/aibert/projects/quest-coder/node_modules/playwright
export NODE_PATH=/Users/aibert/projects/quest-coder/node_modules
export AXE_CORE_PATH=/Users/aibert/projects/quest-coder/node_modules/axe-core/axe.min.js
export TMPDIR=/Users/aibert/.hermes/profiles/dag-generalist/cache/scratch
export PYTHONDONTWRITEBYTECODE=1
unset PYTHONPATH
/usr/bin/python3 scripts/verify_snapshot_equivalence.py --fixtures "$PARSER" \
  --out artifacts/server-performance/equivalence.json
/usr/bin/python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
/usr/bin/python3 scripts/release_check.py --output artifacts/server-performance/gates
```

Large raw artifacts are local and ignored: `artifacts/server-performance/`.
An initial Python run skipped two browser tests; JS initially lacked the ignored
pinned snapshots. Both setup attempts were retained, then dependencies/fixtures
were supplied without changing test assertions. The first equivalence replay
needed the axe path; the next passed all 473 tests but stopped on the original
snapshot's old query-code binding. The harness now truthfully rebinds its local
copy before generating real packets, like the HTTP harness; originals are untouched.

Parser consultant findings about cross-kind traversal ambiguity and literal
parenthesized paths are accepted as separate correctness follow-ups, not fixed
or approved by this performance work. Generalist approval remains separate from
the requested consultant second opinion.
