"""Static package exports and consultant counterexamples; no target execution."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from python_symbols import extract_symbols


class FunctionReexportTests(unittest.TestCase):
    def edge(self, graph, expression):
        return next((e for e in graph['edges'] if any(s['expression'] == expression for s in e['sites'])), None)

    def test_annotation_definition_namespace(self):
        cases = [
            ('class A:\n def work(self): pass\ndef run(x: A):\n class A:\n  def work(self): pass\n x.work()\n', 'a.py#A.work@2'),
            ('class A:\n def work(self): pass\nclass Owner:\n class A:\n  def work(self): pass\n def run(self, x: A):\n  x.work()\n', 'a.py#Owner.A.work@5'),
        ]
        for source, expected in cases:
            with self.subTest(expected=expected):
                graph = extract_symbols({'a.py': source}, [])
                edge = self.edge(graph, 'x.work')
                self.assertEqual(edge['to'], expected)
                self.assertEqual(edge['confidence'], 'typed')

    def test_private_method_abstention(self):
        for receiver in ('x = B()', 'x: B'):
            for context in ('def run():\n', 'class C(B):\n def run(self):\n'):
                indent = '  ' if context.startswith('class') else ' '
                source = 'class A:\n def __work(self): pass\nclass B(A): pass\n' + context + indent + receiver + '\n' + indent + 'x.__work()\n'
                with self.subTest(source=source):
                    self.assertIsNone(self.edge(extract_symbols({'a.py': source}, []), 'x.__work'))

    def test_dunder_protocol_control(self):
        graph = extract_symbols({'a.py': 'class A:\n def __len__(self): pass\ndef run():\n x = A()\n x.__len__()\n'}, [])
        self.assertEqual(self.edge(graph, 'x.__len__')['confidence'], 'instance-local')

    def graph(self, exports='from .impl import work\n', implementation='def work(): pass\n', caller='from pkg import work\ndef run(): work()\n', extra=None):
        sources = {'a.py': caller, 'pkg/__init__.py': exports, 'pkg/impl.py': implementation}
        sources.update(extra or {})
        # The extractor receives independently observed file-import pairs.
        imports = [('a.py', 'pkg/__init__.py'), ('pkg/__init__.py', 'pkg/impl.py')]
        imports.extend((a, b) for a in sources for b in sources if a != b and a.startswith('pkg/'))
        return extract_symbols(sources, imports)

    def test_static_export_and_module_attribute(self):
        for caller, expression in [('from pkg import work\ndef run(): work()\n', 'work'), ('import pkg\ndef run(): pkg.work()\n', 'pkg.work')]:
            with self.subTest(expression=expression):
                edge = self.edge(self.graph(caller=caller), expression)
                self.assertIsNotNone(edge)
                self.assertEqual(edge['to'], 'pkg/impl.py#work@1')
                self.assertEqual(edge['confidence'], 'resolved')
                self.assertEqual(edge['sites'][0]['reexports'], [{'path': 'pkg/__init__.py', 'start': 1, 'end': 1, 'name': 'work', 'targetPath': 'pkg/impl.py', 'targetName': 'work'}])

    def test_alias_and_chained_export(self):
        graph = self.graph('from .sub import alias as work\n', extra={'pkg/sub/__init__.py': 'from ..impl import work as alias\n'})
        edge = self.edge(graph, 'work')
        self.assertIsNotNone(edge)
        self.assertEqual(edge['to'], 'pkg/impl.py#work@1')
        self.assertEqual(len(edge['sites'][0]['reexports']), 2)

    def test_unsafe_exports_abstain(self):
        for exports in ('from .impl import work\nwork = replacement\n', 'from .impl import *\n', 'if flag:\n from .impl import work\n', 'try:\n from .impl import work\nexcept ImportError: pass\n', 'from .impl import work\n__all__ += ["work"]\n', 'from .impl import work\n__all__.append("work")\n', 'work = getattr(other, "work")\n'):
            with self.subTest(exports=exports):
                self.assertIsNone(self.edge(self.graph(exports), 'work'))

    def test_reexport_cycle_abstains(self):
        graph = self.graph('from .sub import work\n', extra={'pkg/sub/__init__.py': 'from .. import work\n'})
        self.assertIsNone(self.edge(graph, 'work'))

    def test_literal_all_does_not_control_explicit_named_import(self):
        graph = self.graph('from .impl import work\n__all__ = ["work"]\n')
        self.assertEqual(self.edge(graph, 'work')['confidence'], 'resolved')

    def test_conditional_endpoint_abstains(self):
        self.assertIsNone(self.edge(self.graph(implementation='if flag:\n def work(): pass\n'), 'work'))

    def test_overload_implementation_not_stub(self):
        for declaration in ('from typing import overload\n@overload\ndef work(x: int): ...\n@overload\ndef work(x: str): ...\n', 'import typing as t\n@t.overload\ndef work(x: int): ...\n'):
            with self.subTest(declaration=declaration):
                implementation = declaration + 'def work(x): return x\n'
                graph = self.graph(implementation=implementation)
                edge = self.edge(graph, 'work')
                self.assertIsNotNone(edge)
                self.assertEqual(edge['to'], 'pkg/impl.py#work@' + str(len(implementation.splitlines())))
                self.assertEqual(edge['confidence'], 'resolved')
                self.assertIsNone(self.edge(self.graph(implementation=declaration), 'work'))

    def test_non_typing_overload_is_not_declaration(self):
        implementation = 'from custom import overload\n@overload\ndef work(x): ...\ndef work(x): return x\n'
        self.assertIsNone(self.edge(self.graph(implementation=implementation), 'work'))

    def test_conditional_caller_import_abstains(self):
        self.assertIsNone(self.edge(self.graph(caller='if flag:\n from pkg import work\ndef run(): work()\n'), 'work'))

    def test_shadowed_overload_name_and_conditional_typing_abstain(self):
        for prefix in ('from typing import overload\noverload = custom\n', 'if flag:\n from typing import overload\n'):
            self.assertIsNone(self.edge(self.graph(implementation=prefix + '@overload\ndef work(x): ...\ndef work(x): return x\n'), 'work'))

    def test_in_repo_typing_shadow_is_not_stdlib_overload(self):
        sources = {'typing.py': 'def overload(f): return f\n',
                   'a.py': 'from typing import overload\n@overload\ndef work(x): ...\ndef work(x): return x\ndef run(): work(1)\n'}
        self.assertIsNone(self.edge(extract_symbols(sources, [('a.py', 'typing.py')]), 'work'))


if __name__ == '__main__':
    unittest.main()
