# Revision-bound source and agent context (M3 T1)

`app/context.py` provides local, read-only source retrieval and context assembly.
It does not invoke a model, contact a network, execute imported source, mutate a
snapshot, or grant consent to send repository data anywhere. Callers must obtain
an authoritative snapshot from their trusted publication store, not accept a
requester's self-authored snapshot as proof. Pass the acquisition-validated Git
cache directory; this helper does not repeat the acquisition cache security audit.

## Source API

```python
from app.context import read_source
source = read_source(git_dir, snapshot, 'app/main.py', start=1, end=40,
                     max_lines=400, max_bytes=256 * 1024)
```

Validation of the complete snapshot happens first. `path` must exactly equal an
inventory path: no normalization, case folding, trimming or working-tree lookup.
Only `contentKind == 'utf-8-text'` with a known line count is readable; binary or
unknown representations raise `ContextError('metadata only')`.

Git operations exclusively use `app.repositories._run_git` with fixed argv and
isolated configuration. An existing Git directory and the exact commit object's
type are checked. The blob is read at `snapshot.source.commit:path`, its original
bytes are SHA-256 checked against the inventory, then decoded as strict UTF-8.
The actual logical line count must also match the inventory. There is no checkout
or host source-file read. Git symlinks, if inventoried as text, yield only their
stored target-string blob, never the target's contents.

Result schema: `dag-gps-source/v1`, with `snapshotId`, `path`, `sha256`,
`lineCount`, `start`, `end`, `lines`, `truncated`, and `nextStart`.

- `start` and `end` are optional 1-based inclusive integers; booleans are invalid.
  Omitted start means line 1, omitted end means the last logical line. Explicit
  endpoints must be within `lineCount`; reversed ranges fail.
- Lines follow the producer's `str.splitlines()` convention. Returned strings
  omit line terminators, but byte accounting includes each original UTF-8 line
  and its original terminator (including both bytes of CRLF). No partial lines
  or partial UTF-8 characters are returned.
- `max_lines` and `max_bytes` must be positive integers. Truncation is relative
  to the requested range, not the unrequested rest of the file. `nextStart` is
  the first unreturned requested line; it is null when the range is complete.
- Empty files have `lines: []`, `lineCount: 0`, null start/end/nextStart and no
  truncation. Explicit line endpoints for empty files fail. If a nonempty line
  cannot fit, the result also has null start/end, but `truncated: true` and a
  `nextStart` pointing to that line. Increase the byte budget to make progress.
- Hash verification requires reading the full blob before selecting an excerpt.
  A separate **8 MiB verification cap** matches the importer's default file cap.
  An import configured for larger files can exist, but reading such a file here
  fails closed with `ContextError`; it never returns unverified partial bytes.
  Git size is checked before blob retrieval, which is also output-bounded.

Malformed snapshots propagate `app.contracts.ContractError`. Invalid ranges,
limits, paths, unavailable objects and stale/tampered bytes raise `ContextError`
(a `ValueError`). Hash or line-count mismatches are never downgraded to omissions.

## Context API

```python
from app.context import build_context
context = build_context(git_dir, snapshot, packet,
                        budget_bytes=64 * 1024, max_files=20, lines_per_file=80)
```

`validate_evidence_packet(packet, snapshot)` is the first operation, even before
budget validation or source I/O. Its `ContractError` propagates unchanged. Thus
another revision's packet cannot be used to obtain source excerpts.

Result schema: `dag-gps-context/v1`, with `requestId`, `projectId`, `snapshotId`,
`packetSha256`, `status`, `operation`, `files`, `omitted`, `truncated`, and
`limitations`. `packetSha256` hashes the exact `canonical_json(packet)` encoding.

Only a `matched` packet produces source. Other statuses (including needs-choice,
no-match, stale, no-path and unsupported) return no files and perform no Git I/O.
Selected file nodes retain packet order, except the selected `seedNodeId` is
first. Layers do not expand into unselected files. Duplicate paths are included
once. Every excerpt begins at line 1: a file-level citation does not identify
which source lines explain a relationship. This limitation is in every result.

Each file has `path`, `sha256`, `start`, `end`, `lines`, and `truncated`. Non-text
files and files excluded by limits have explicit `{path, reason}` omissions.
Omission or excerpt truncation sets top-level `truncated`; packet truncation is
also preserved. To continue an excerpt use the source API; to continue the query
use the original packet's continuation. Failures verifying included source abort
context assembly, rather than silently returning potentially misleading context.

### Budget semantics

- `budget_bytes` is a nonnegative integer bounding the **sum of canonical JSON
  byte lengths of included file objects**. This accounts for per-file metadata,
  Unicode and JSON escaping, not merely source character count. Each encoding
  includes the canonical serializer's final newline.
- Envelope fields, limitations and omission records are outside this excerpt
  budget. This permits an honest omission report even with a zero-byte budget;
  it is not a maximum serialized response-body size. Transport/provider callers
  must impose a separate complete-response bound if required.
- Whole lines are trimmed to fit; if even one line cannot fit, the file is
  omitted. Later smaller files can still fit. Empty files may be included when
  their metadata fits. Every source read also retains the 256 KiB excerpt cap.
- `max_files` is a nonnegative integer limiting included files. `lines_per_file`
  is a positive integer. Zero file/byte budgets explicitly omit selected files.
  Booleans and fractional values are rejected for every numeric limit.

Source remains untrusted data. A caller must not treat source comments as agent
instructions. Context creation itself is not permission for external export.

## Verification

```sh
python3 -m unittest discover -s tests -p test_agent_context.py -v
python3 -m unittest discover -s tests -q
```

Tests use local synthetic Git publications and real Node query-worker packets.
Worker-dependent tests skip only if Node is absent. Coverage includes literal
paths, revision/hash binding, strict ranges, original-byte/line truncation,
empty files, host and Git symlink safety, safety limits, uncertainty, seed order,
context omissions, and absence of model/network imports in this module.
Retained RED/GREEN evidence is in `artifacts/m3-t1/`.
