"""RED-first confidence-tier regressions, never executes fixture source."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from python_symbols import extract_symbols


class FunctionTierTests(unittest.TestCase):
    def graph(self, body):
        return extract_symbols({'a.py': body}, [])

    def edge(self, graph, expression):
        return next((e for e in graph['edges'] if any(s['expression'] == expression for s in e['sites'])), None)

    def test_instance_local_and_inherited_mro(self):
        g = self.graph('class Base:\n def work(self): pass\nclass A(Base): pass\ndef run():\n x = A()\n x.work()\n')
        e = self.edge(g, 'x.work')
        self.assertIsNotNone(e)
        self.assertEqual(e['confidence'], 'instance-local')
        self.assertEqual(e['to'], 'a.py#Base.work@2')
        self.assertEqual(g['counts']['instance-local'], 1)

    def test_stable_init_attribute(self):
        g = self.graph('class A:\n def work(self): pass\nclass Owner:\n def __init__(self):\n  self.agent = A()\n def run(self):\n  self.agent.work()\n')
        self.assertEqual(self.edge(g, 'self.agent.work')['confidence'], 'instance-local')

    def test_annotations(self):
        g = self.graph('class A:\n def work(self): pass\ndef run(x: A):\n x.work()\ndef other():\n y: A\n y.work()\n')
        self.assertEqual(self.edge(g, 'x.work')['confidence'], 'typed')
        self.assertEqual(self.edge(g, 'y.work')['confidence'], 'typed')

    def test_decorators_and_entry_points_not_callers(self):
        g = self.graph('@app.post("/chat")\ndef handler(): pass\n@wrap\ndef job(): pass\ndef run():\n job()\n')
        self.assertEqual(self.edge(g, 'job')['confidence'], 'through-decorator')
        self.assertEqual(self.edge(g, 'job')['decorators'], ['wrap'])
        node = next(n for n in g['nodes'] if n['name'] == 'handler')
        self.assertEqual(node['entryPoint'], ['app.post(\'/chat\')'])
        self.assertFalse(any(e['to'] == node['id'] for e in g['edges']))

    def test_unsafe_local_bindings_stay_unknown(self):
        cases = [
            ' x = A()\n x = other\n x.work()',
            ' if flag:\n  x = A()\n x.work()',
            ' x = A()\n for x in xs: pass\n x.work()',
            ' x = A()\n def inner(): return x\n x.work()',
            ' x.work()\n x = A()',
            ' x = A()\n x.missing()',
            ' x = A()\n getattr(x, "work")()',
            ' x: A = A()\n x = other\n x.work()',
        ]
        for body in cases:
            with self.subTest(body=body):
                g = self.graph('class A:\n def work(self): pass\ndef run(flag, other, xs):\n' + body + '\n')
                self.assertFalse(any(e['confidence'] != 'resolved' for e in g['edges']))

    def test_attribute_reassignment_stays_unknown(self):
        g = self.graph('class A:\n def work(self): pass\nclass Owner:\n def __init__(self):\n  self.agent = A()\n def reset(self):\n  self.agent = A()\n def run(self):\n  self.agent.work()\n')
        self.assertIsNone(self.edge(g, 'self.agent.work'))

    def test_c3_order(self):
        g = self.graph('class Root:\n def work(self): pass\nclass Left(Root): pass\nclass Right(Root):\n def work(self): pass\nclass Both(Left, Right): pass\ndef run():\n x = Both()\n x.work()\n')
        self.assertEqual(self.edge(g, 'x.work')['to'], 'a.py#Right.work@5')

    def test_unknown_base_and_deferred_scopes_do_not_guess(self):
        g = self.graph('class A(External): pass\ndef run(x: A):\n x.work()\n y = A()\n return lambda: y.work()\n')
        self.assertIsNone(self.edge(g, 'x.work'))
        self.assertIsNone(self.edge(g, 'y.work'))

    def test_method_mutation_not_mistaken_for_definition(self):
        for source in (
            'class A:\n def work(self): pass\n def reset(self, other):\n  self.work = other\ndef run():\n x = A()\n x.work()\n',
            'class A:\n def work(self): pass\nA.work = replacement\ndef run(x: A):\n x.work()\n',
        ):
            with self.subTest(source=source):
                self.assertIsNone(self.edge(self.graph(source), 'x.work'))


if __name__ == '__main__':
    unittest.main()
