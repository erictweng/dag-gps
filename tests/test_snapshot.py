import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts'))
from check_snapshot import check


class TestPinnedParity(unittest.TestCase):
    def setUp(self):
        self.original = {'meta': {'commit': 'abc', 'ref': 'origin/main', 'built_at': 'old'},
                         'nodes': [{'id': 'a', 'layer': 'a'}], 'edges': [], 'file_edges': [], 'layers': {}}

    def test_allows_only_ref_and_time_without_mutation(self):
        rebuilt = copy.deepcopy(self.original)
        rebuilt['meta'].update(ref='abc', built_at='new')
        before = copy.deepcopy(rebuilt)
        self.assertTrue(check(self.original, rebuilt))
        self.assertEqual(rebuilt, before)

    def test_rejects_membership_change(self):
        rebuilt = copy.deepcopy(self.original)
        rebuilt['nodes'][0]['layer'] = 'b'
        with self.assertRaises(ValueError):
            check(self.original, rebuilt)

    def test_rejects_snapshot_or_edge_change(self):
        for key, value in [('meta', {'commit': 'other'}), ('file_edges', [{'from': 'a', 'to': 'b'}])]:
            rebuilt = copy.deepcopy(self.original)
            rebuilt[key] = value
            with self.assertRaises(ValueError):
                check(self.original, rebuilt)
