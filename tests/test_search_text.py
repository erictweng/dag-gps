import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tests'))
from python_symbols import extract_symbols, extract_search_text
from app.contracts import ContractError, validate_snapshot
from test_workspace_contract import fixture


class SearchTextTests(unittest.TestCase):
    def test_first_paragraph_caps_and_names(self):
        source = '\"\"\"Module paragraph.\\n\\nPrivate second paragraph.\"\"\"\nclass StoreThing:\n    \"\"\"Stores messages.\\n\\nIgnored details.\"\"\"\n    def make_item(self):\n        \"\"\"' + ('x' * 400) + '\"\"\"\n        pass\n'
        symbols = extract_symbols({'a.py': source}, [])['nodes']
        text = extract_search_text(['a.py', 'someThing.ts'], {'a.py': source}, symbols)
        self.assertEqual(text['nodes']['a.py']['docstring'], 'Module paragraph.')
        cls = next(n for n in symbols if n['name'] == 'StoreThing')
        method = next(n for n in symbols if n['name'] == 'make_item')
        self.assertEqual(text['nodes'][cls['id']]['name'], 'store thing')
        self.assertEqual(text['nodes'][cls['id']]['docstring'], 'Stores messages.')
        self.assertEqual(len(text['nodes'][method['id']]['docstring']), 300)
        self.assertEqual(text['nodes']['someThing.ts']['docstring'], '')
        self.assertEqual(text['nodes']['someThing.ts']['name'], 'some thing ts')

    def test_byte_budget_and_failed_parse(self):
        paths = ['long/path/' + str(i) + '.ts' for i in range(1000)]
        result = extract_search_text(paths, {'bad.py': 'def ('}, [], budget=1000)
        self.assertLessEqual(len(json.dumps(result, separators=(',', ':')).encode()), 1000)
        self.assertGreater(result['omitted'], 0)
        self.assertEqual(len(result['nodes']) + result['omitted'], len(paths))

    def test_contract_and_legacy(self):
        s, _ = fixture()
        validate_snapshot(s)
        ident = next(n['id'] for n in s['map']['nodes'] if n['kind'] == 'file')
        s['map']['search_text'] = {'schema': 'dag-gps-search-text/v1', 'nodes': {
            ident: {'name': 'store', 'path': 'source', 'docstring': 'Stores messages.'}}, 'omitted': 0}
        validate_snapshot(s)
        for field, value in [('name', 'x' * 81), ('path', 'x' * 121), ('docstring', 'x' * 301), ('docstring', '\n')]:
            bad = copy.deepcopy(s)
            bad['map']['search_text']['nodes'][ident][field] = value
            with self.assertRaises(ContractError):
                validate_snapshot(bad)
        for key, value in [('schema', 'unknown'), ('omitted', -1), ('omitted', True)]:
            bad = copy.deepcopy(s)
            bad['map']['search_text'][key] = value
            with self.assertRaises(ContractError):
                validate_snapshot(bad)
        bad = copy.deepcopy(s)
        bad['map']['search_text']['nodes']['invented'] = bad['map']['search_text']['nodes'].pop(ident)
        with self.assertRaises(ContractError):
            validate_snapshot(bad)
