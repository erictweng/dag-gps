# Workspace query packets (M2.1)

System 1 answers questions about a published snapshot with no model calls, no
network and no imported-source execution. Browser, worker and (later) agent
consumers all use the same code: `web/query-service.js`, which wraps the
`web/scorer.js` and the unchanged `web/router.js`. Natural phrasing, synonyms and
candidate-only concept search are documented in [QUESTION_PARSER.md](QUESTION_PARSER.md).

## Pipeline

1. `app/workspace_snapshot.py::load_publication(dir)` validates the Phase 1
   ownership receipt, exact output membership and digests, then builds a
   `dag-gps-workspace/v1` envelope. It binds `mapSha256` (canonical map JSON) and
   `queryCode` (SHA-256 of scorer, router and query service). A Phase 1 preview is
   always `state: dependency-preview` with proposed, unreviewed grouping.
2. `node scripts/query_worker.cjs SNAPSHOT.json` reads JSON-lines requests
   `{requestId, query, snapshotId?, continuation?, chosenNodeId?}` and writes
   `{ok, packet}` lines. It exits with status 2 before answering if the installed
   query code differs from the bytes bound into the snapshot.
3. Every packet is a `dag-gps-evidence/v1` packet accepted by
   `app/contracts.py::validate_evidence_packet` (enforced by
   `tests/test_query_packets.py`).

## Semantics

- `matched` LOCATE: one known node, file source ref with unknown (`null`) lines.
- `needs-choice` / `no-match`: nothing is highlighted; alternatives are listed.
  `chosenNodeId` resolves an explicit user choice to a known ID only.
- `DOWNSTREAM` ("what depends on X", "what would break if X changed"):
  `potential-impact`; every selected consumer has a directed witness chain ending
  at the seed. Potentially affected is not guaranteed to break.
- `UPSTREAM` ("dependencies of X"): relevant dependencies with witness chains
  from the seed. Genuine cycles are traversed once and kept.
- `PATH` ("path from A to B"): shortest directed static route with one witness,
  or `no-path`. Group/file mixed endpoints are `unsupported`.
- `stale`: request names a different snapshot; nothing is highlighted.
- Large results are paged: each page holds at most 200 nodes. Whole witness
  chains are added, so a page may repeat an intermediate node. `continuation`
  is `offset:N` and resumes exactly; invalid or past-end continuations are errors.

## Limits

### Python function questions

Snapshots with `map.symbol_graph` support exact, case-folded symbol targets
(case-only collisions require choice):
bare unique name, qualified name, `path:qualified-name`, or full symbol ID.
`where is X defined` / `locate symbol X`, `what calls X`, `what does X call`,
`how does X reach Y`, and `trace from X` are deterministic operation templates.
CALLERS/CALLEES are direct; FLOW/TRACE traverse resolved call edges only. Duplicate
names require choice (including Python overload definitions); two ambiguous FLOW
endpoints are chosen in sequence. Alternative `query` strings preserve already
chosen endpoints. Unresolved calls and exact counts are returned separately.
Missing static paths are not proof that a runtime flow is impossible.

The legacy matching limits below remain for file/group questions.

Matching first uses normalized paths, filenames, group labels, symbols and explicit
synonyms. New snapshots with `map.search_text` can return bounded BM25 concept
choices when lexical retrieval has no evidence. They never confidently select a
BM25-only answer. Legacy snapshots have no concept index; reimport to build one.
Only static extracted relationships are traversed.

## Reproduce

```sh
node --test tests/query-service.test.cjs
python3 -m unittest discover -s tests -p test_query_packets.py -v
```
