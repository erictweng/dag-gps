"""M2 alias persistence regression; layer node factory is used by build()."""
import importlib.util
import pathlib
import unittest

spec = importlib.util.spec_from_file_location('m2_build_map', pathlib.Path(__file__).parents[1] / 'scripts/build_map.py')
assert spec is not None and spec.loader is not None
bm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bm)


class AliasPersistence(unittest.TestCase):
    def test_retains_phrases_without_mutating_spec_or_ids(self):
        layer = {'id': 'a', 'label': 'Alpha', 'aliases': ['magic link', 'sign in'], 'globs': ['lib/**']}
        node = bm.layer_node(layer, 7, ['lib/a.ts'], {'lib/a.ts': 'one\ntwo\n'})
        self.assertEqual(node['aliases'], ['magic link', 'sign in'])
        self.assertEqual((node['id'], node['idx'], node['lines']), ('a', '7', 2))
        self.assertIn('magic', node['tokens'])
        node['aliases'].append('new')
        self.assertEqual(layer['aliases'], ['magic link', 'sign in'])

    def test_missing_aliases_is_explicit_empty_list(self):
        node = bm.layer_node({'id': 'a', 'label': 'Alpha', 'globs': []}, 1, [], {})
        self.assertEqual(node['aliases'], [])
