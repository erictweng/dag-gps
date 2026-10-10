# Workspace evidence contract — Phase 0

Status: versioned contract foundation only. No GitHub importer, workspace server/UI,
agent provider or live watcher is implemented by Phase 0. The existing offline
navigator remains unchanged except for the independently reviewed release fixes.

Implementation: `app/contracts.py`; synthetic regressions:
`tests/test_workspace_contract.py`. This contract is the starting boundary for
future phases, not a declaration that the future product is operational.

## 1. Product invariant

Deterministic code maintains source evidence; optional agents interpret a bounded
selection. Humans and agents must consume the same revision-bound evidence.
A question identifies relevant candidates, not files actually changed. Static
imports are not runtime execution, and normalized heuristic scores are not measured
accuracy. Missing links leave uncertainty, not proof of no consumers or no tests.

The current System 1 remains the existing scorer/router/impact modules. Phase 0
does not tune scoring or add an LLM. Phase 2 will integrate these guards with query
packets; guards alone do not prove an answer is useful or semantically correct.

## 2. Authority and trust boundary

`validate_evidence_packet(packet, snapshot)` requires a snapshot supplied by the
trusted local snapshot store. Do not let a request supply both its own alleged
proof and its authoritative snapshot. That store/source retrieval is future work.

The guards check finite JSON data, structure, membership and matching provenance.
They do NOT read source bytes, recompute authoritative content hashes, prove a
human reviewed architecture, implement authentication, persist immutable objects,
or verify the truth of an agent explanation. Future acquisition must compute and
verify source bytes; the store must retain immutable revision copies; legacy
build checks remain required before approved publication. Do not market this
validator as a complete importer or release certificate.

Validation is pure: no file/network/model execution, no query logging, no changes
to the supplied packet/snapshot and no silent repair/normalization. Successful
validation returns the supplied packet; callers must prevent later mutation of
trusted cached objects. Unknown extra fields must also be JSON-native finite metadata: plain dicts with
string keys, lists, UTF-8-encodable strings, integers, finite floats, booleans and
null. Tuples, sets, integer object keys, custom objects, circular references and
nonfinite numbers are rejected for BOTH packets and snapshots. Reused acyclic
native values are allowed; the helper does not silently convert/normalize them.
Only documented fields may drive behavior. Incompatible schemas fail closed.

## 3. Snapshot identity (`dag-gps-workspace/v1`)

Required wrapper fields:

| Field | Contract |
|---|---|
| `projectId`, `snapshotId` | Bounded nonempty identifiers; revision identity must be derived from actual source/map/extractor/options by the future store |
| `mapSha256`, `scorerSha256` | Full lowercase SHA-256 values computed by the trusted producer, never invented |
| `source.kind` | `git-commit` in this Phase 0 version |
| `source.repo` | Explicit repository identity |
| `source.commit` | Full lowercase 40-character resolved commit, never a short/moving ref |
| `source.worktreeId` | Null for a pinned commit; a live revision may not masquerade as committed source |
| `source.manifestSha256` | Full fingerprint of the actual source manifest |
| `state` | `inventory-ready`, `dependency-preview`, or `validated-map` |
| `grouping` | `status: proposed` with `reviewed: false`, or `status: reviewed` with `reviewed: true`; contradictory states rejected |
| `inventory` | Unique literal source paths, full file SHA-256, known `lineCount` or null |
| `map` | Legacy-compatible typed code nodes and separate layer/file edge arrays |

Required nullable fields must be explicitly PRESENT: `source.worktreeId`, every
inventory `lineCount`, both citation `start`/`end`, and packet `continuation`.
Omitting them is not the same as declaring null. Valid explicit null pairs remain
accepted; half-pairs, missing keys and invented ranges are rejected.

`validated-map` cannot have an unreviewed grouping marker. This is a consistency
guard, not proof of a real person's approval; the future UI/store must record that
explicit action. A provisional preview cannot bypass existing legacy publication
checks or be packaged as an approved architecture.

Map requirements enforced here:
- `meta.repo` and `meta.snapshot_commit` match wrapper source identity.
- Node IDs are unique; node kinds are `file` or `layer`.
- File paths are inventoried and file ownership refers to an existing layer.
- Typed links are unique and have known, same-kind endpoints in the right graph
  scope (`edges` for layers, `file_edges` for files).
- Real cycles remain data. The existing legacy DAG/publication validation still
  controls approved layer diagrams. Do not remove true edges to make a picture.
- Other-language/binary inventory is not automatically given dependency nodes or
  relationships. Generic graph kinds and live source identities require a later
  explicit contract extension; they are rejected by this version.

Source paths are literal relative POSIX paths: no absolute/drive paths, backslashes,
control characters, empty/dot/traversal components. Do not silently normalize a
malformed token into another path. A producer must disclose excluded/unsupported
paths rather than claiming universal repository coverage.

`lineCount` is the number of actual logical source lines (`len(text.splitlines())`
for the producer's decoded text), not blindly copied from legacy node newline
counts. Hash the exact original bytes before decoding or newline conversion. Binary
or uncounted sources have null ranges until a verified text representation exists.

## 4. Evidence packet (`dag-gps-evidence/v1`)

Required fields:
- `schema`, bounded `requestId`.
- Exact `projectId`, `snapshotId`, `mapSha256`, `scorerSha256`, and
  `manifestSha256` matching the authoritative snapshot. Manifest binding prevents
  old evidence being reused even if a buggy caller reuses a revision ID.
- `operation`: LOCATE / UPSTREAM / DOWNSTREAM / PATH / NOT_SURE / IMPACT.
- `status`: matched / needs-choice / no-match / no-path / unsupported / stale.
- `selectedNodeIds`, `selectedEdges`, `witnesses`, `alternatives`, `sourceRefs`.
- `highlightState`, explicit `truncated`, `continuation` (null if complete),
  bounded `limitations`.

Rules:
1. Selection/alternatives reference known IDs; no duplicate or guessed target IDs.
2. Selected links must exist in the observed graph, connect selected nodes and
   exclude realtime from default traversal. Agent guesses cannot become these links.
3. Each witness is `{nodeIds: [...], edges: [{from, to, type}, ...]}`: a contiguous
   directed, simple known chain, with one observed link per hop. A zero-hop known
   node is valid location evidence, not a relationship/impact claim.
4. Matched answers need a selected known node. Needs-choice/no-match/stale packets
   cannot highlight a guessed route. No-path has PATH operation and no claimed
   path edges/witnesses. An uncertain result may show labeled alternatives, not
   choose the top candidate as an accepted match.
5. Source references contain literal path, same `snapshotId`, exact inventoried
   `sha256`, inclusive `start`/`end` or BOTH null, and a declared evidence kind.
   Known ranges must fit the known source line count; booleans are not line numbers.
   Never invent line ranges when a parser only identified a file-level relationship.
6. Evidence kinds: observed-source, static-import, static-boundary, curated-source,
   agent-inferred. These labels describe provenance, not execution proof.
7. Overflow is an explicit error; the guard never silently drops evidence. The future
   query adapter must bound results accurately and use a revision-bound continuation.
   A boolean truncation flag plus a cursor is required for incomplete packets; a
   supposedly complete packet explicitly includes null continuation. This guard does not
   independently recompute query completeness or implement cursors.

### Highlight semantics

| State | Meaning / guard |
|---|---|
| `relevant` | Retrieval/lookup candidate; NOT actual modification |
| `potential-impact` | Matched IMPACT/DOWNSTREAM result with explicit seed and witness coverage for every selected consumer; NOT guaranteed breakage or coverage |
| `changed` | Baseline matches trusted snapshot `changes.baselineSnapshotId`; selected IDs belong to observed `changedNodeIds`, not merely question matches |
| `agent-inferred` | Interpretation only; cannot inject unobserved selected edges into factual graph |

For `potential-impact`, conditional required `seedNodeId` identifies the query
origin and must be known and selected. IMPACT has a file seed; DOWNSTREAM can
have a file/layer seed. The seed is a **query seed**, not an affected consumer.
Every other selected node must have its own nonempty directed witness beginning
at that node and ending at the seed (consumer → dependency). At least one consumer
is required: an isolated/seed-only location is `relevant`, not witnessed impact.
Additional contextual witnesses may remain, but an unrelated chain cannot justify
an isolated target or a mixed selection containing an unsupported target. Do not
blindly require all contextual chain nodes to be selected.

`unsupported` may retain bounded observed context, provided at least one limitation
is disclosed. It is not a complete/accepted answer to the unsupported request.
The producer/UI must explain that limitation; the guard checks presence/structure,
not the semantic truth of explanatory prose.

The `changes` record is optional trusted producer metadata, not something derived
from a question. Future Phase 4 computes source diffs and handles deleted-node
history explicitly; no live change tracker is implemented here.

Display using text/edge styles as well as color. Dimmed nodes must retain readable
contrast/keyboard access. Every included relationship should expose its reason;
clear/Escape must recover. Actual UI testing belongs to Phase 2, not these unit tests.

## 5. Initial safety bounds

Executable initial defaults, not throughput/latency promises:
- Packet JSON: 1 MiB, finite values; this is checked by the pure helper. Future
  transports must reject oversized bodies BEFORE decoding and enforce depth/time
  bounds; this helper is not a hostile-network request parser.
- Selected nodes: 200; selected links: 400; witnesses: 200; source refs: 200;
  alternatives: 20; limitations: 100 with bounded strings.
- Snapshot inventory/nodes: 100,000; each layer/file edge array: 1,000,000.
- JSON depth: 64 (including nested value levels); snapshot values visited: 10,000,000;
  packet values visited: 1,000,000. Whole snapshots are checked for native finite
  JSON without materializing a second full JSON encoding; no snapshot byte-size
  promise is made. Acquisition/transport resource limits are still future work.
- Identifiers: 512 characters; source paths: 4096; reasons/limitations: 2048;
  continuation: 1024. No calibrated confidence or invented timing fields.

These are conservative safety defaults for an initial protocol. Phase 2 must size
real fixtures and measure validation/cold index/query/layout separately before
claiming performance. Whole-snapshot validation currently occurs per helper call;
future caching may reuse a validated catalog only for an immutable fingerprinted
revision. Do not hide slow cases by shrinking evidence without disclosure.

The existing scorer-only <10 ms gate is unchanged and is not an end-to-end target.
Changing these contract bounds requires explicit docs/tests and does not justify
altering evaluation queries or the release gate to obtain a passing run.

## 6. Consent and agent boundary

`default_controls()` returns a fresh `{recordQueries: false, agentEnabled: false}`.
Normal indexing/lookup cannot enable recording or agents. An explicit opt-in does
not teach aliases; alias confirmation stays separate.

`require_agent_consent(value)` accepts literal boolean True only, refuses False,
and rejects truthy strings/numbers/null. It is an internal guard, NOT proof that a
person clicked an authenticated UI: the future service derives it from its own
explicit consent/capability state, not arbitrary client/agent assertions.

Phase 0 installs no provider, launcher, model network client, query logger, server,
watcher or source exporter. External source/context sending remains a separate
explicit user action in Phase 3, with authorization, budgets and unknown usage
reported honestly. A future agent response cannot execute instructions or replace
source facts merely by being displayed.

## 7. Compatibility and deferred decisions

Keep existing offline maps/scorer/router/impact/source pins stable. Generic graph
JSON adapters, live worktree identity, transport/auth details and agent execution
are later extensions, not secretly enabled by this protocol file.

Local-first/public GitHub/current-agent bridge remain proposed defaults from the
roadmap. Phase 0 approval did NOT explicitly select hosted versus local or a model
provider. Those decisions stay pending before Phase 1/agent implementation; do not
reinterpret Phase 0 as permission for accounts, public deployment or paid APIs.

## 8. Verification

```sh
python3 -m unittest discover -s tests -p test_workspace_contract.py -v
python3 -m unittest discover -s tests -q
node --test tests/*.test.cjs
```

The contract tests are explicitly synthetic. They verify invariants (including
revision/manifest drift, truthful unknown ranges, uncertainty, source membership,
edge/witness direction, grouping markers, bounds and explicit consent), NOT GitHub
import success, actual agent accuracy, human approval or the future product UX.
Final complete release verification and clean exact-commit evidence remain required
for the Phase 0 handoff; refer to `docs/WORKSPACE_ACCEPTANCE.md`.

## 9. Independent review disposition

The first independent review (`artifacts/phase0-contract-review/review.md`) FAILED
these contract bytes despite 38 passing tests: P0C-01 required nullable omissions,
P0C-02 unrelated impact witnesses, P0C-03 nonfinite/circular snapshot metadata.
All are addressed in source with explicit presence checks, seed-bound consumer
witness coverage, and bounded native finite-JSON checks. New RED retained 47 tests /
16 failing cases; focused GREEN now passes 47/47. Original source review and earlier
complete gate receipts are retained; they do not certify the corrected new bytes.
A follow-up independent review and complete final exact-commit receipt are required
before final handoff. Adjacent type-domain/unsupported-context ambiguities are now
explicitly decided above. This is a stricter contract, not weakened documentation.
