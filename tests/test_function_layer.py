"""Synthetic symbol extraction regression contract; source is never executed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from python_symbols import extract_symbols


class FunctionLayerTests(unittest.TestCase):
    def graph(self, sources, imports=()):
        return extract_symbols(sources, imports)

    def test_definitions_nested_async_and_self_calls(self):
        g = self.graph({'a.py': 'def leaf(): pass\nclass A:\n    async def run(self):\n        self.work()\n    def work(self):\n        def inner():\n            leaf()\n        inner()\n'})
        self.assertEqual([n['qualname'] for n in g['nodes']], ['leaf', 'A', 'A.run', 'A.work', 'A.work.<locals>.inner'])
        pairs = {(e['from'].split('#')[1], e['to'].split('#')[1]) for e in g['edges']}
        self.assertEqual(pairs, {('A.run@3', 'A.work@5'), ('A.work@5', 'A.work.<locals>.inner@6'), ('A.work.<locals>.inner@6', 'leaf@1')})
        self.assertTrue(all(e['confidence'] == 'resolved' and e['sites'][0]['start'] > 0 for e in g['edges']))
        self.assertEqual(g['counts']['resolved'], 3)

    def test_import_calls_require_observed_repo_import(self):
        sources = {'a.py': 'from b import leaf as f\nimport b as mod\ndef run():\n    f()\n    mod.leaf()\n', 'b.py': 'def leaf(): pass\n'}
        self.assertEqual(self.graph(sources)['counts']['resolved'], 0)
        g = self.graph(sources, [('a.py', 'b.py')])
        self.assertEqual(g['counts']['resolved'], 2)
        self.assertEqual(len(g['edges']), 1)
        self.assertEqual(len(g['edges'][0]['sites']), 2)

    def test_dynamic_shadowed_decorated_and_module_calls_unresolved(self):
        source = 'def leaf(): pass\n@decorate\ndef wrapped(): pass\ndef run(leaf):\n    leaf()\n    obj.work()\n    wrapped()\nwrapped()\n'
        g = self.graph({'a.py': source})
        self.assertEqual(g['counts']['resolved'], 0)
        self.assertEqual(g['counts']['unresolved'], 3)
        self.assertEqual(g['counts']['through-decorator'], 1)
        self.assertTrue(all(c['to'] is None and c['confidence'] == 'unresolved' for c in g['unresolved']))

    def test_syntax_diagnostic_does_not_drop_other_files(self):
        g = self.graph({'bad.py': 'def (\n', 'ok.py': 'async def run(): pass\n'})
        self.assertEqual(len(g['nodes']), 1)
        self.assertEqual(g['diagnostics'][0]['path'], 'bad.py')
        self.assertEqual(g['schema'], 'dag-gps-symbols/v1')

    def test_relative_submodule_attribute_is_import_bound(self):
        g = self.graph({'pkg/a.py': 'from . import b\ndef run():\n    b.leaf()\n',
                        'pkg/b.py': 'def leaf(): pass\n'}, [('pkg/a.py', 'pkg/b.py')])
        self.assertEqual(g['counts']['resolved'], 1)
        self.assertEqual(g['edges'][0]['to'], 'pkg/b.py#leaf@1')

    def test_rebindings_and_duplicate_defs_never_guess(self):
        source = 'def leaf(): pass\ndef leaf(): pass\ndef run():\n    leaf()\ndef other():\n    f = leaf\n    f()\n'
        g = self.graph({'a.py': source})
        self.assertEqual(g['counts']['resolved'], 0)
        self.assertEqual(g['counts']['unresolved'], 2)

    def test_rebound_self_and_import_attributes_are_unresolved(self):
        source = 'import b\nclass A:\n    def work(self): pass\n    def run(self, callback):\n        self.work = callback\n        self.work()\n        b.leaf = callback\n        b.leaf()\n'
        g = self.graph({'a.py': source, 'b.py': 'def leaf(): pass\n'}, [('a.py', 'b.py')])
        self.assertEqual(g['counts']['resolved'], 0)
        self.assertEqual(g['counts']['unresolved'], 2)

    def test_lambda_and_comprehension_parameters_do_not_resolve_outer_names(self):
        source = 'def leaf(): pass\ndef run(xs):\n    f = lambda leaf: leaf()\ndef other(xs):\n    [leaf() for leaf in xs]\n'
        g = self.graph({'a.py': source})
        self.assertEqual(g['counts']['resolved'], 0)
        self.assertEqual(g['counts']['unresolved'], 2)


if __name__ == '__main__':
    unittest.main()
