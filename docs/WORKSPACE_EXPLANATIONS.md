# Agent explanation contract — M3 T2

`app/explanations.py` validates `dag-gps-explanation/v1` with Python 3.9 standard
library only. It does not invoke an agent, execute imported code, read files,
access the network, store results, or modify the graph.

## API and trust boundary

```python
from app.explanations import packet_digest, validate_explanation

# snapshot and packet come from the trusted local store / issued request.
validated = validate_explanation(response, snapshot, packet,
                                 allowed_paths={'src/example.py'})
assert validated is response
```

`validate_explanation(explanation, snapshot, packet, *, allowed_paths=None)`
returns the **original object unchanged**, not a normalized copy. Callers must
prevent mutation between validation, storage and display. All validation failures,
including invalid snapshot/evidence contracts, raise `ExplanationError(ValueError)`.
Snapshot validation and evidence-packet validation happen before explanation checks.

`packet_digest(packet)` returns the lowercase SHA-256 of
`app.workspace_snapshot.canonical_json(packet)`: sorted keys, compact separators,
UTF-8, unescaped Unicode and no nonfinite numbers. It checks JSON-native finite
object data, but cannot validate packet provenance without a snapshot. Every packet
field contributes to the digest, including limitations and otherwise permitted
metadata. Key insertion order does not. The validator compares requestId,
projectId and snapshotId exactly to the validated packet, and verifies this digest.
A response to a different or modified packet is rejected even if its file citations
happen to match. Foreign or stale responses cannot replace the current response.
The caller must supply the *current issued packet* and trusted snapshot, never trust
an agent-supplied pair as its own authority.

## Exact schema

All shown keys are required. Unknown keys are rejected in every explanation object,
including nested agent, paragraph, relationship, citation and usage objects. Existing
snapshot/packet contracts retain their own metadata rules.

```json
{
  "schema": "dag-gps-explanation/v1",
  "requestId": "issued-request-id",
  "projectId": "trusted-project-id",
  "snapshotId": "trusted-snapshot-id",
  "packetSha256": "<64 lowercase hexadecimal characters>",
  "agent": {"name": "external-agent", "model": null},
  "paragraphs": [
    {
      "text": "An interpretation of the supplied source.",
      "inferred": false,
      "citations": [
        {"path": "src/example.py", "sha256": "<inventory digest>", "start": 1, "end": 3}
      ]
    }
  ],
  "suggestedRelationships": [],
  "limitations": ["Static evidence does not prove runtime behavior."],
  "usage": {"inputTokens": null, "outputTokens": null}
}
```

Digest placeholders above are illustrative, not valid hash values.

| Field | Rules |
|---|---|
| agent.name | Nonempty, at most 512 characters; no Unicode control characters |
| agent.model | Explicit null or string of at most 512 characters; empty string allowed; no controls |
| paragraphs | 0–12 objects; no silent truncation |
| paragraph.text | 1–2000 characters of plaintext; newline allowed, other Unicode `Cc` control characters rejected |
| paragraph.inferred | Literal boolean; must be true if citations are empty; inferred paragraphs may also cite source |
| citations | 0–20 per paragraph, 1–20 per relationship; no duplicate `(path, sha256, start, end)` tuple within a list |
| suggestedRelationships | 0–20 objects, with exactly `from`, `to`, `type`, `reason`, `citations` |
| relationship.from / to | Known map node IDs, distinct; file or layer IDs permitted, including mixed kinds because these are suggestions, not extracted edges |
| relationship.type | Nonempty string, at most 512 characters, no controls; not an extracted-edge enum |
| relationship.reason | 1–2000 plaintext characters; same controls rule as paragraph text |
| limitations | 0–20 strings, each 1–2000 plaintext characters; same controls rule as paragraph text |
| usage.inputTokens / outputTokens | Explicit null when unknown, or integer `0 <= n < 10**9`; booleans, floats and strings rejected |

Unknown usage is represented by **both required usage fields explicitly null**,
not an omitted `usage`, `usage: null`, omitted counters, or fabricated zero values.
A real observed zero is accepted and preserved. No usage is inferred or zero-filled.

All explanation data must be JSON-native, finite and UTF-8 encodable: exact Python
dicts with string keys, lists, strings, integers, finite floats, booleans or null;
individual schema fields further narrow these types. Tuples, sets, custom objects,
nonstring keys, cycles and lone surrogates fail. The shared finite-JSON walker bounds
depth to 64 and explanation traversal to 100,000 values. Total **canonical UTF-8 JSON**
size is at most 256 KiB (262144 bytes), not 256 Ki characters. Overflow is rejected.
Transports must independently bound bytes *before* decoding; this is not a network
parser. Schema-specific checks precede final serialization, so invalid huge token
integers are rejected without converting them into strings.

## Citation validation

- Path is a literal relative POSIX inventoried path, exactly matched: no path
  normalization, traversal, absolute paths, backslashes or case folding.
- SHA-256 is full lowercase hex and equals that inventory entry's hash.
- `start` and `end` are either **both null** (file-level citation) or exact integers
  satisfying `1 <= start <= end <= lineCount`, inclusive. Booleans are not integers
  for this contract. Unknown lineCount permits only file-level citations; zero
  lines likewise cannot support a line range. Nullable keys may not be omitted.
- `allowed_paths=None` allows any inventoried path. A list, tuple, set or frozenset
  supplies the files actually provided to the agent and restricts **every** citation,
  including suggested relationships. An empty collection permits no citations.
  A bare string/dict is rejected rather than accidentally doing substring/key checks.
- Restrictions bind files, not excerpt line coverage: callers needing excerpt-level
  enforcement must check that separately. Inventory membership/hash checks do not
  read or rehash source bytes; the trusted revision-bound source reader does that.

## Display and graph isolation

All agent text remains untrusted **plaintext**. HTML-looking text is accepted as
literal text, not sanitized, parsed, or interpreted. Render it via text nodes /
`textContent`, never `innerHTML` or an unsafe Markdown renderer. Rejecting control
characters does not turn prose into trusted markup or executable instructions.

Suggested relationships are always an **agent-inferred overlay**, regardless of
whether they cite real source or resemble an existing edge. They are never merged
into extracted `edges` or `file_edges`, used as factual traversal witnesses, or
promoted into graph facts. The validator does not mutate any input or perform that
merge. This contract checks binding and citation existence, not semantic truth,
agent identity authentication, model accuracy, consent, or whether a cited passage
actually supports a claim. Integration must label inferred prose and overlays and
preserve the deterministic evidence alongside them.

## Offline verification

Tests use the existing synthetic `test_workspace_contract.fixture`, validated by
both snapshot and packet validators; there are no model/network calls.

```sh
python3 -m unittest discover -s tests -p test_agent_explanations.py -v
python3 -m unittest discover -s tests -q
```

Retained receipts: `artifacts/m3-t2/red.log`, `artifacts/m3-t2/green.log` and
`artifacts/m3-t2/full.log`. RED was captured before the module existed (import
failure), then implementation and boundary regressions were exercised to GREEN.
