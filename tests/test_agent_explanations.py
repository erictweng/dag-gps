"""Synthetic, offline explanation contract tests; no agent accuracy claims."""
import copy
import hashlib
import unittest
from unittest import mock

from app.contracts import validate_evidence_packet, validate_snapshot
from app.explanations import (EXPLANATION_SCHEMA, ExplanationError, packet_digest,
                              validate_explanation)
from app.workspace_snapshot import canonical_json
from test_workspace_contract import fixture


def explanation(packet):
    citation = {'path': 'a.py', 'sha256': 'a' * 64, 'start': 1, 'end': 3}
    return {
        'schema': EXPLANATION_SCHEMA, 'requestId': packet['requestId'],
        'projectId': packet['projectId'], 'snapshotId': packet['snapshotId'],
        'packetSha256': packet_digest(packet),
        'agent': {'name': 'synthetic-agent', 'model': None},
        'paragraphs': [{'text': 'Observed source.\nNot execution proof.',
                        'inferred': False, 'citations': [citation]}],
        'suggestedRelationships': [{'from': 'a.py', 'to': 'b.py',
                                   'type': 'possible-use', 'reason': 'An inference.',
                                   'citations': [copy.deepcopy(citation)]}],
        'limitations': ['Synthetic fixture only.'],
        'usage': {'inputTokens': None, 'outputTokens': None}}


class AgentExplanationTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.packet = fixture()
        self.value = explanation(self.packet)

    def validate(self, **kwargs):
        return validate_explanation(self.value, self.snapshot, self.packet, **kwargs)

    def reject(self, **kwargs):
        with self.assertRaises(ExplanationError):
            self.validate(**kwargs)

    def test_valid_identity_purity_and_no_io(self):
        validate_snapshot(self.snapshot)
        validate_evidence_packet(self.packet, self.snapshot)
        before = copy.deepcopy((self.value, self.snapshot, self.packet))
        with mock.patch('builtins.open', side_effect=AssertionError('No IO')):
            self.assertIs(self.validate(), self.value)
        self.assertEqual(before, (self.value, self.snapshot, self.packet))
        self.assertNotIn('possible-use', {e['type'] for e in self.snapshot['map']['file_edges']})

    def test_digest_canonical_exact_and_order_independent(self):
        self.assertEqual(packet_digest(self.packet), hashlib.sha256(canonical_json(self.packet)).hexdigest())
        self.assertEqual(packet_digest(dict(reversed(list(self.packet.items())))), packet_digest(self.packet))
        changed = copy.deepcopy(self.packet)
        changed['limitations'].append('New limitation')
        self.assertNotEqual(packet_digest(changed), packet_digest(self.packet))

    def test_foreign_identifiers_and_schema(self):
        for field in ('schema', 'requestId', 'projectId', 'snapshotId', 'packetSha256'):
            for bad in ('foreign', None, [], True):
                with self.subTest(field=field, bad=bad):
                    self.value = explanation(self.packet)
                    self.value[field] = bad
                    self.reject()

    def test_modified_valid_packet_rejected_until_rebound(self):
        self.packet['limitations'].append('Modified packet')
        self.reject()
        self.value['packetSha256'] = packet_digest(self.packet)
        self.validate()

    def test_invalid_snapshot_and_packet_checked_first(self):
        self.snapshot['source']['commit'] = 'bad'
        self.reject()
        self.snapshot, self.packet = fixture()
        self.packet['selectedNodeIds'] = ['unknown']
        self.value['packetSha256'] = packet_digest(self.packet)
        self.reject()

    def test_unknown_and_missing_keys_at_every_level(self):
        selectors = [lambda e: e, lambda e: e['agent'], lambda e: e['usage'],
                     lambda e: e['paragraphs'][0], lambda e: e['paragraphs'][0]['citations'][0],
                     lambda e: e['suggestedRelationships'][0],
                     lambda e: e['suggestedRelationships'][0]['citations'][0]]
        for select in selectors:
            self.value = explanation(self.packet)
            keys = list(select(self.value))
            for key in keys + ['unknown']:
                with self.subTest(keys=keys, key=key):
                    self.value = explanation(self.packet)
                    obj = select(self.value)
                    if key == 'unknown':
                        obj[key] = None
                    else:
                        del obj[key]
                    self.reject()

    def test_citation_exact_inventory_and_hash(self):
        for field, bad in [('path', 'missing.py'), ('path', './a.py'), ('path', '../a.py'),
                           ('path', 'A.py'), ('sha256', 'b' * 64), ('sha256', 'A' * 64),
                           ('path', []), ('sha256', None)]:
            with self.subTest(field=field, bad=bad):
                self.value = explanation(self.packet)
                self.value['paragraphs'][0]['citations'][0][field] = bad
                self.reject()

    def test_citation_ranges(self):
        for start, end in [(0, 1), (2, 1), (1, 4), (True, 2), (1, False),
                           (1.0, 2), (1, 2.0), ('1', 2), (None, 2), (1, None)]:
            with self.subTest(start=start, end=end):
                self.value['paragraphs'][0]['citations'][0].update(start=start, end=end)
                self.reject()
        for start, end in [(1, 1), (1, 3), (3, 3), (None, None)]:
            self.value['paragraphs'][0]['citations'][0].update(start=start, end=end)
            self.validate()

    def test_unknown_and_zero_line_count_allow_only_file_level(self):
        self.packet['sourceRefs'][0].update(start=None, end=None)
        self.value = explanation(self.packet)
        for count in (None, 0):
            self.snapshot['inventory'][0]['lineCount'] = count
            self.reject()
            for obj in (self.value['paragraphs'][0], self.value['suggestedRelationships'][0]):
                obj['citations'][0].update(start=None, end=None)
            self.validate()
            self.value = explanation(self.packet)

    def test_allowed_paths_applies_to_all_citations(self):
        self.validate(allowed_paths={'a.py'})
        self.validate(allowed_paths=['a.py', 'b.py'])
        self.reject(allowed_paths=set())
        self.reject(allowed_paths={'b.py'})
        self.value['paragraphs'][0].update(inferred=True, citations=[])
        self.reject(allowed_paths={'b.py'})
        self.value['suggestedRelationships'] = []
        self.validate(allowed_paths=set())

    def test_duplicate_citations_and_per_list_limit(self):
        for field in ('paragraphs', 'suggestedRelationships'):
            self.value = explanation(self.packet)
            citations = self.value[field][0]['citations']
            citations.append(copy.deepcopy(citations[0]))
            self.reject()
            self.snapshot['inventory'][0]['lineCount'] = 21
            self.value[field][0]['citations'] = [dict(citations[0], start=n, end=n) for n in range(1, 21)]
            self.validate()
            self.value[field][0]['citations'].append(dict(citations[0], start=21, end=21))
            self.reject()

    def test_uncited_paragraph_requires_literal_inferred_true(self):
        paragraph = self.value['paragraphs'][0]
        paragraph['citations'] = []
        self.reject()
        paragraph['inferred'] = True
        self.validate()
        for bad in (1, 'true', None):
            paragraph['inferred'] = bad
            self.reject()
        paragraph.update(inferred=True, citations=[{'path': 'a.py', 'sha256': 'a' * 64, 'start': None, 'end': None}])
        self.validate()

    def test_paragraph_bounds_and_html_is_literal_text(self):
        paragraph = self.value['paragraphs'][0]
        for text in ('x', 'x' * 2000, '<script>alert(1)</script>', 'line one\nline two'):
            paragraph['text'] = text
            self.validate()
        for text in ('', 'x' * 2001, None, 42):
            paragraph['text'] = text
            self.reject()
        paragraph['text'] = 'x'
        self.value['paragraphs'] = [copy.deepcopy(paragraph) for _ in range(12)]
        self.validate()
        self.value['paragraphs'].append(copy.deepcopy(paragraph))
        self.reject()
        self.value['paragraphs'] = []
        self.validate()

    def test_control_characters_rejected_but_newline_allowed(self):
        for control in [chr(i) for i in range(32) if i != 10] + [chr(127), chr(128), chr(159)]:
            for field in ('text', 'reason', 'limitation'):
                with self.subTest(control=repr(control), field=field):
                    self.value = explanation(self.packet)
                    text = 'before' + control + 'after'
                    if field == 'text': self.value['paragraphs'][0]['text'] = text
                    elif field == 'reason': self.value['suggestedRelationships'][0]['reason'] = text
                    else: self.value['limitations'] = [text]
                    self.reject()
        self.value = explanation(self.packet)
        self.value['suggestedRelationships'][0]['reason'] = 'one\ntwo'
        self.value['limitations'] = ['one\ntwo']
        self.validate()

    def test_agent_metadata_bounds(self):
        for field in ('name', 'model'):
            for bad in ('x' * 513, 'bad\nname', [], 1):
                self.value = explanation(self.packet)
                self.value['agent'][field] = bad
                self.reject()
        self.value = explanation(self.packet)
        self.value['agent']['name'] = ''
        self.reject()
        self.value['agent'].update(name='x' * 512, model='x' * 512)
        self.validate()
        self.value['agent']['model'] = ''
        self.validate()

    def test_relationship_nodes_type_and_reason(self):
        for field, bad in [('from', 'missing'), ('to', 'missing'), ('to', 'a.py'),
                           ('from', []), ('type', ''), ('type', 'x' * 513),
                           ('reason', ''), ('reason', 'x' * 2001)]:
            self.value = explanation(self.packet)
            self.value['suggestedRelationships'][0][field] = bad
            self.reject()
        self.value = explanation(self.packet)
        self.value['suggestedRelationships'][0].update(type='x' * 512, reason='x' * 2000, to='folder-root')
        self.validate()

    def test_relationship_requires_citation_and_bounded_count(self):
        relationship = self.value['suggestedRelationships'][0]
        relationship['citations'] = []
        self.reject()
        self.value = explanation(self.packet)
        self.value['suggestedRelationships'] *= 20
        self.validate()
        self.value['suggestedRelationships'].append(copy.deepcopy(self.value['suggestedRelationships'][0]))
        self.reject()
        self.value['suggestedRelationships'] = []
        self.validate()

    def test_limitations_bounds(self):
        self.value['limitations'] = ['x' * 2000] * 20
        self.validate()
        self.value['limitations'].append('extra')
        self.reject()
        for bad in ('', 'x' * 2001, None, 42):
            self.value['limitations'] = [bad]
            self.reject()
        self.value['limitations'] = []
        self.validate()

    def test_usage_explicit_null_zero_and_integer_boundaries(self):
        for field in ('inputTokens', 'outputTokens'):
            for good in (None, 0, 999999999):
                self.value['usage'][field] = good
                self.validate()
                self.assertIs(self.value['usage'][field], good)
            for bad in (-1, 1000000000, True, 0.0, '0', []):
                self.value['usage'][field] = bad
                self.reject()
            self.value['usage'][field] = None
        self.value['usage'] = None
        self.reject()

    def test_json_native_finite_unicode_and_structure_bounds(self):
        cyclic = []
        cyclic.append(cyclic)
        deep = []
        for _ in range(70): deep = [deep]
        for bad in (float('nan'), float('inf'), (1,), {1: 'x'}, {1}, object(),
                    '\ud800', cyclic, deep):
            self.value = explanation(self.packet)
            self.value['limitations'] = bad
            self.reject()
        self.value = explanation(self.packet)
        self.value['usage']['inputTokens'] = 10 ** 10000
        self.reject()

    def test_digest_rejects_non_native_or_nonfinite_data(self):
        for bad in (None, [], {'extra': float('nan')}, {'extra': (1,)},
                    {'extra': '\ud800'}):
            with self.subTest(bad=repr(bad)):
                with self.assertRaises(ExplanationError):
                    packet_digest(bad)

    def test_allowed_paths_are_literal_collections_not_substrings(self):
        for bad in ('a.py', {'a.py': True}, ['../a.py'], [None]):
            with self.subTest(bad=bad):
                self.reject(allowed_paths=bad)
        self.validate(allowed_paths=('a.py',))
        self.validate(allowed_paths=frozenset({'a.py'}))

    def test_wrong_container_types(self):
        for field in ('agent', 'paragraphs', 'suggestedRelationships', 'limitations', 'usage'):
            self.value = explanation(self.packet)
            self.value[field] = None
            self.reject()
        for field in ('paragraphs', 'suggestedRelationships'):
            self.value = explanation(self.packet)
            self.value[field] = [None]
            self.reject()
            self.value = explanation(self.packet)
            self.value[field][0]['citations'] = [None]
            self.reject()

    def test_encoded_byte_limit_not_character_count(self):
        self.value['paragraphs'] = [copy.deepcopy(self.value['paragraphs'][0]) for _ in range(12)]
        self.value['suggestedRelationships'] = [copy.deepcopy(self.value['suggestedRelationships'][0]) for _ in range(20)]
        for p in self.value['paragraphs']: p['text'] = 'x' * 2000
        for r in self.value['suggestedRelationships']: r['reason'] = 'x' * 2000
        self.value['limitations'] = ['x' * 2000] * 20
        self.assertLess(len(canonical_json(self.value)), 256 * 1024)
        self.validate()
        for p in self.value['paragraphs']: p['text'] = '\U0001f600' * 2000
        for r in self.value['suggestedRelationships']: r['reason'] = '\U0001f600' * 2000
        self.value['limitations'] = ['\U0001f600' * 2000] * 20
        self.assertGreater(len(canonical_json(self.value)), 256 * 1024)
        self.reject()


if __name__ == '__main__':
    unittest.main()
