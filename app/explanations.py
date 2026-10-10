"""Pure, strict validation of untrusted agent prose beside revision-bound evidence.

Success returns the original explanation unchanged. Callers own immutable storage,
consent, source retrieval, and text-only rendering; this module performs no IO and
never promotes suggested relationships into extracted graph facts.
"""
import hashlib
import unicodedata

from app.contracts import (ContractError, _array, _finite_json, _hash, _obj,
                           _path, validate_evidence_packet, validate_snapshot)
from app.workspace_snapshot import canonical_json

EXPLANATION_SCHEMA = 'dag-gps-explanation/v1'
MAX_EXPLANATION_BYTES = 256 * 1024
MAX_EXPLANATION_VALUES = 100000
MAX_PARAGRAPHS = 12
MAX_CITATIONS = 20
MAX_RELATIONSHIPS = 20
MAX_LIMITATIONS = 20
MAX_TEXT = 2000
MAX_LABEL = 512


class ExplanationError(ValueError):
    """An explanation, its evidence, or its context fails the trust boundary."""


def packet_digest(packet) -> str:
    """SHA-256 of the exact packet's canonical UTF-8 JSON (no normalization).

    This checks native finite JSON, not packet validity against a snapshot.
    """
    try:
        _obj(packet, 'Evidence packet')
        _finite_json(packet, 'Evidence packet', 1000000)
        return hashlib.sha256(canonical_json(packet)).hexdigest()
    except (ContractError, TypeError, ValueError, RecursionError) as error:
        raise ExplanationError('Cannot digest evidence packet: ' + str(error)) from error


def _fields(value, keys, name):
    _obj(value, name)
    if set(value) != set(keys.split()):
        raise ExplanationError(name + ' requires exactly: ' + keys)
    return value


def _text(value, name, limit=MAX_LABEL, *, newline=False, empty=False):
    if (type(value) is not str or (not empty and not value) or len(value) > limit
            or any(unicodedata.category(c) == 'Cc' and not (newline and c == '\n')
                   for c in value)):
        raise ExplanationError(name + ' must be bounded plaintext without control characters')
    return value


def _citations(value, graph, allowed):
    seen = set()
    for citation in _array(value, 'Citations', MAX_CITATIONS):
        _fields(citation, 'path sha256 start end', 'Citation')
        path = _path(citation['path'])
        digest = _hash(citation['sha256'], 'Citation digest')
        file = graph['files'].get(path)
        if file is None or digest != file['sha256']:
            raise ExplanationError('Citation must match exact inventoried path and hash')
        if allowed is not None and path not in allowed:
            raise ExplanationError('Citation path was not provided in agent context')
        start, end = citation['start'], citation['end']
        if start is not None or end is not None:
            count = file['lineCount']
            if (type(start) is not int or type(end) is not int or start < 1
                    or end < start or count is None or end > count):
                raise ExplanationError('Citation needs an inclusive known in-bounds range or two nulls')
        key = (path, digest, start, end)
        if key in seen:
            raise ExplanationError('Duplicate citation within one citation list')
        seen.add(key)
    return value


def validate_explanation(explanation, snapshot, packet, *, allowed_paths=None) -> dict:
    """Validate against a trusted snapshot and the exact issued evidence packet.

    ``allowed_paths`` optionally restricts citations to context files (a list,
    tuple, set, or frozenset of literal paths). None disables this extra filter;
    an empty collection permits no citations. This checks references, not whether
    cited source supports prose, nor whether cited lines were in an excerpt.
    Returns the supplied object, without mutation; all failures use ExplanationError.
    """
    try:
        # Validate trusted provenance before considering any untrusted prose.
        graph = validate_snapshot(snapshot)
        validate_evidence_packet(packet, snapshot)
        _finite_json(explanation, 'Explanation', MAX_EXPLANATION_VALUES)
        _fields(explanation, 'schema requestId projectId snapshotId packetSha256 agent '
                'paragraphs suggestedRelationships limitations usage', 'Explanation')
        if explanation['schema'] != EXPLANATION_SCHEMA:
            raise ExplanationError('Unsupported explanation schema')
        for field in ('requestId', 'projectId', 'snapshotId'):
            if explanation[field] != packet[field]:
                raise ExplanationError('Explanation differs from evidence packet: ' + field)
        _hash(explanation['packetSha256'], 'Packet digest')
        if explanation['packetSha256'] != packet_digest(packet):
            raise ExplanationError('Explanation packet digest differs from exact evidence packet')

        allowed = None
        if allowed_paths is not None:
            if type(allowed_paths) not in (list, tuple, set, frozenset):
                raise ExplanationError('Allowed paths must be a collection of literal paths')
            allowed = set(_path(path) for path in allowed_paths)

        agent = _fields(explanation['agent'], 'name model', 'Agent')
        _text(agent['name'], 'Agent name')
        if agent['model'] is not None:
            _text(agent['model'], 'Agent model', empty=True)
        for paragraph in _array(explanation['paragraphs'], 'Paragraphs', MAX_PARAGRAPHS):
            _fields(paragraph, 'text inferred citations', 'Paragraph')
            _text(paragraph['text'], 'Paragraph text', MAX_TEXT, newline=True)
            if type(paragraph['inferred']) is not bool:
                raise ExplanationError('Paragraph inferred must be an explicit boolean')
            citations = _citations(paragraph['citations'], graph, allowed)
            if not citations and not paragraph['inferred']:
                raise ExplanationError('Uncited paragraph must be explicitly inferred')
        for relationship in _array(explanation['suggestedRelationships'],
                                   'Suggested relationships', MAX_RELATIONSHIPS):
            _fields(relationship, 'from to type reason citations', 'Suggested relationship')
            for field in ('from', 'to'):
                node_id = _text(relationship[field], 'Relationship ' + field)
                if node_id not in graph['nodeIds']:
                    raise ExplanationError('Suggested relationship references unknown node')
            if relationship['from'] == relationship['to']:
                raise ExplanationError('Suggested relationship cannot reference itself')
            _text(relationship['type'], 'Relationship type')
            _text(relationship['reason'], 'Relationship reason', MAX_TEXT, newline=True)
            if not _citations(relationship['citations'], graph, allowed):
                raise ExplanationError('Suggested relationship requires at least one citation')
        for limitation in _array(explanation['limitations'], 'Limitations', MAX_LIMITATIONS):
            _text(limitation, 'Limitation', MAX_TEXT, newline=True)
        usage = _fields(explanation['usage'], 'inputTokens outputTokens', 'Usage')
        for count in usage.values():
            if count is not None and (type(count) is not int or not 0 <= count < 10 ** 9):
                raise ExplanationError('Usage must be a nonnegative integer below 10**9 or null')
        if len(canonical_json(explanation)) > MAX_EXPLANATION_BYTES:
            raise ExplanationError('Explanation exceeds 256 KiB canonical JSON byte limit')
    except ContractError as error:
        raise ExplanationError(str(error)) from error
    return explanation
