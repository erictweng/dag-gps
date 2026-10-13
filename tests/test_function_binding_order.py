"""RED-first regressions from t_d663095e's independent probes."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from python_symbols import extract_symbols


class BindingOrderTests(unittest.TestCase):
    def graph(self, source, extra=None):
        sources = {'a.py': source}
        sources.update(extra or {})
        return extract_symbols(sources, [('a.py', p) for p in (extra or {})])

    def edge(self, graph, expression):
        return next((e for e in graph['edges'] if any(s['expression'] == expression for s in e['sites'])), None)

    def test_future_class_annotation_binding_abstains(self):
        for annotation in ('A', '"A"'):
            for binding in ('class A:\n  def work(self): pass', 'from b import A'):
                source = ('class A:\n def work(self): pass\nclass Owner:\n'
                          ' def run(self, x: ' + annotation + '):\n  return x.work()\n '
                          + binding + '\n')
                with self.subTest(annotation=annotation, binding=binding):
                    graph = self.graph(source, {'b.py': 'class A:\n def work(self): pass\n'})
                    self.assertIsNone(self.edge(graph, 'x.work'))

    def test_prior_class_annotation_binding_control(self):
        source = ('class A:\n def work(self): pass\nclass Owner:\n'
                  ' class A:\n  def work(self): pass\n'
                  ' def run(self, x: A):\n  return x.work()\n')
        self.assertEqual(self.edge(self.graph(source), 'x.work')['to'], 'a.py#Owner.A.work@5')

    def test_reversed_overload_abstains(self):
        source = ('from typing import overload\ndef work(x): return x\n'
                  '@overload\ndef work(x: int): ...\ndef run(): return work(1)\n')
        self.assertIsNone(self.edge(self.graph(source), 'work'))

    def test_mutated_overload_markers_abstain(self):
        for imports, marker, mutation in (
            ('import typing', 'typing.overload', 'typing.overload = lambda f: f'),
            ('import typing as t', 't.overload', 'del t.overload'),
            ('import typing as t\nimport typing as other', 't.overload', 'other.overload = custom'),
            ('import typing\nfrom typing import overload', 'overload', 'typing.overload = custom'),
            ('from typing import overload', 'overload', 'overload = custom'),
            ('import typing as t', 't.overload', 't = custom'),
        ):
            with self.subTest(mutation=mutation):
                source = (imports + '\n' + mutation + '\n@' + marker + '\n'
                          'def work(x: int): ...\ndef work(x): return x\n'
                          'def run(): return work(1)\n')
                self.assertIsNone(self.edge(self.graph(source), 'work'))

    def test_conditional_overload_group_abstains(self):
        for group in (
            '@overload\ndef work(x: int): ...\nif flag:\n def work(x): return x\n',
            'if flag:\n @overload\n def work(x: int): ...\ndef work(x): return x\n',
        ):
            with self.subTest(group=group):
                self.assertIsNone(self.edge(self.graph('from typing import overload\n' + group + 'def run(): return work(1)\n'), 'work'))

    def test_future_overload_import_abstains(self):
        source = ('@overload\ndef work(x: int): ...\nfrom typing import overload\n'
                  'def work(x): return x\ndef run(): return work(1)\n')
        self.assertIsNone(self.edge(self.graph(source), 'work'))

    def test_declaration_only_and_multiple_implementations_abstain(self):
        for group in ('@overload\ndef work(x: int): ...\n',
                      '@overload\ndef work(x: int): ...\ndef work(x): pass\ndef work(x): pass\n'):
            with self.subTest(group=group):
                self.assertIsNone(self.edge(self.graph('from typing import overload\n' + group + 'def run(): return work(1)\n'), 'work'))

    def test_normal_overload_aliases_and_scopes(self):
        for imports, marker in (('from typing import overload as ov', 'ov'), ('import typing as t', 't.overload')):
            for wrapper, indent, caller in (('', '', 'def run(): return work(1)\n'),
                                            ('class Owner:\n', ' ', ' def run(self): return self.work(1)\n')):
                source = imports + '\n' + wrapper + ''.join(indent + line + '\n' for line in (
                    '@' + marker, 'def work(x: int): ...', 'def work(x): return x')) + caller
                with self.subTest(source=source):
                    expression = 'self.work' if wrapper else 'work'
                    edge = self.edge(self.graph(source), expression)
                    self.assertIsNotNone(edge)
                    self.assertEqual(edge['confidence'], 'resolved')
                    self.assertTrue(edge['to'].endswith('@5' if wrapper else '@4'))


if __name__ == '__main__':
    unittest.main()
