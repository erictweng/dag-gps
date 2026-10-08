"""Synthetic source fixtures: never user labels or runtime execution evidence."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ExtractionTrustTests(unittest.TestCase):
    def extract(self, files, tops=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, text in files.items():
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            out = root / 'graph.json'
            subprocess.run([sys.executable, str(ROOT / 'scripts/import_graph.py'), tmp, str(out), *(tops or list(files))], check=True, capture_output=True)
            return json.loads(out.read_text())

    def test_relative_one_two_levels_namespace_and_init(self):
        g = self.extract({'pkg/__init__.py': 'from . import worker\n',
                          'pkg/worker.py': 'from .helper import thing\n',
                          'pkg/helper.py': 'thing = 1\n',
                          'pkg/nested/main.py': 'from ..helper import thing\nfrom . import sibling\n',
                          'pkg/nested/sibling.py': ''})
        self.assertEqual(g['pyedges'], [['pkg/__init__.py', 'pkg/worker.py'], ['pkg/nested/main.py', 'pkg/helper.py'], ['pkg/nested/main.py', 'pkg/nested/sibling.py'], ['pkg/worker.py', 'pkg/helper.py']])
        self.assertEqual(g['unresolved'], [])

    def test_symbols_are_not_invented_submodules_but_real_submodules_link(self):
        g = self.extract({'pkg/__init__.py': 'value=1\n', 'pkg/sub.py': '', 'main.py': 'from pkg import value, sub\n'})
        self.assertEqual(g['pyedges'], [['main.py', 'pkg/__init__.py'], ['main.py', 'pkg/sub.py']])

    def test_missing_relative_is_local_error_and_no_suffix_guess(self):
        g = self.extract({'pkg/main.py': 'from .missing import thing\nimport helper\n', 'elsewhere/helper.py': ''})
        self.assertEqual(g['pyedges'], [])
        self.assertTrue(any('missing' in b for a, b in g['unresolved']))
        self.assertTrue(any('helper' in x[2] for x in g['unsupported']))

    def test_ambiguous_module_and_package_rejects(self):
        g = self.extract({'pkg.py': '', 'pkg/__init__.py': '', 'main.py': 'import pkg\n'})
        self.assertEqual(g['pyedges'], [])
        self.assertIn('ambiguous Python pkg', g['unresolved'][0][1])

    def test_explicit_self_import_cycle_is_retained(self):
        g=self.extract({'a.py':'import a\n','b.js':'require("./b.js");\n'})
        self.assertEqual(g['pyedges'], [['a.py','a.py']])
        self.assertEqual(g['cycles'], [['a.py','a.py'],['b.js','b.js']])

    def test_static_cycles_are_retained(self):
        g = self.extract({'pkg/a.py': 'from . import b\n', 'pkg/b.py': 'from . import a\n'})
        self.assertEqual(g['pyedges'], [['pkg/a.py', 'pkg/b.py'], ['pkg/b.py', 'pkg/a.py']])
        self.assertEqual(g['cycles'], [['pkg/a.py', 'pkg/b.py', 'pkg/a.py']])

    def test_js_whitespace_ts_import_equals_and_no_fixture_edges(self):
        g = self.extract({'a.ts': 'import B = require ("./b");\n  import "./b";\nconst fixture = "require(\'./ghost\')";\n// import "./ghost"\n', 'b.ts': ''})
        self.assertEqual(set(map(tuple, g['edges'])), {('a.ts', 'b.ts')})
        self.assertEqual(g['unresolved'], [])

    def test_explicit_static_file_relative_search_path_not_suffix_guess(self):
        g=self.extract({'tests/main.py': 'import os, sys\nROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))\nsys.path.insert(0, os.path.join(ROOT, "scripts"))\nfrom helper import thing\n', 'scripts/helper.py': 'thing=1\n', 'other/helper.py': ''})
        self.assertEqual(g['pyedges'], [['tests/main.py','scripts/helper.py']])

    def test_explicit_static_loader_path_not_fixture_string(self):
        g=self.extract({'tests/main.py': 'import importlib.util, pathlib\nspec = importlib.util.spec_from_file_location("helper", pathlib.Path(__file__).parents[1] / "scripts/helper.py")\nfixture = "import helper"\n', 'scripts/helper.py': ''})
        self.assertEqual(g['pyedges'], [['tests/main.py','scripts/helper.py']])
        self.assertEqual(g['unsupported'], [])

    def test_missing_namespace_submodule_and_beyond_package_are_errors(self):
        g=self.extract({'pkg/main.py': 'from . import missing\nfrom ..other import value\n'})
        self.assertEqual(g['pyedges'], [])
        self.assertEqual(len(g['unresolved']), 2)
        self.assertTrue(any('missing namespace submodule' in b for a,b in g['unresolved']))
        self.assertTrue(any('beyond package' in b for a,b in g['unresolved']))

    def test_pathlib_resolve_str_root_is_statically_scoped(self):
        g=self.extract({'tests/main.py': 'from pathlib import Path\nimport sys\nROOT=Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(ROOT / "scripts"))\nimport helper\n', 'scripts/helper.py': '', 'other/helper.py': ''})
        self.assertEqual(g['pyedges'], [['tests/main.py','scripts/helper.py']])
        self.assertEqual(g['unsupported'], [])

    def test_dynamic_path_and_loader_are_not_evaluated(self):
        g=self.extract({'main.py': 'import sys, importlib.util\nsys.path.insert(0, variable)\nspec = importlib.util.spec_from_file_location("helper", path)\n', 'pkg/helper.py': ''})
        self.assertEqual(g['pyedges'], [])
        self.assertTrue(any('dynamic Python import' in row[1] for row in g['unsupported']))

    def test_scope_and_dynamic_findings(self):
        g = self.extract({'a.js': 'require (name); import(path);', 'outside.js': 'require("./missing");', 'pkg/a.py': '__import__(name)\nimport importlib\nimportlib.import_module(name)\n'}, ['a.js'])
        self.assertNotIn('outside.js', g['nodes'])
        self.assertIn('pkg/a.py', g['nodes'])  # Python scope explicitly repository-wide.
        self.assertEqual(len(g['unsupported']), 4)
        self.assertEqual(g['unresolved'], [])


class TrustSchemaTests(unittest.TestCase):
    def setUp(self):
        import copy
        sys.path.insert(0, str(ROOT / 'scripts'))
        from trust import validate_trust
        self.validate = validate_trust
        self.doc = copy.deepcopy(json.loads((ROOT / 'maps/quest-coder/map.json').read_text()))

    def test_category_counts_and_inventory_partition(self):
        from collections import Counter
        t=self.doc['trust']
        self.assertEqual(self.validate(self.doc), [])
        counts=Counter(f['category'] for f in t['findings'])
        self.assertEqual(t['counts'], {c: counts[c] for c in t['categories']})
        self.assertEqual(t['scope']['inventory_files'], self.doc['meta']['counts']['files'])
        self.assertEqual(set(t['scope']['extracted_paths']) | set(t['scope']['unscanned_paths']), {n['id'] for n in self.doc['nodes'] if n['kind']=='file'})
        self.assertEqual(t['snapshot_commit'], '749d8b5de490cc2e6a0c98c713fab3ab856da799')

    def test_malformed_version_counts_category_scope_and_snapshot_rejected(self):
        import copy
        for field,value in [('version',1), ('counts',{}), ('categories',[]), ('snapshot_commit','other')]:
            doc=copy.deepcopy(self.doc);doc['trust'][field]=value
            self.assertTrue(self.validate(doc), field)
        doc=copy.deepcopy(self.doc);doc['trust']['scope']['unscanned_paths'].append('nonexistent.py')
        self.assertTrue(self.validate(doc))
        doc=copy.deepcopy(self.doc);doc['trust']['findings'][0]['category']='runtime_complete'
        self.assertTrue(self.validate(doc))

    def test_frozen_v2_pairs_are_source_audited_and_not_deleted_for_parity(self):
        from check_snapshot import check
        import copy
        edges={(e['from'],e['to'],e['type']) for e in self.doc['file_edges']}
        self.assertIn(('runner/__init__.py','runner/quest_runner.py','import'),edges)
        self.assertIn(('runner/tests/test_trusted_boundary.py','runner/quest_runner.py','import'),edges)
        self.assertEqual(len(edges),415)
        wrong=copy.deepcopy(self.doc);wrong['trust']['counts']['external_dependency']-=1
        with self.assertRaises(ValueError):check(self.doc,wrong)

    def test_version_migration_provenance_does_not_change_source_pin(self):
        import copy
        from build_project import snapshot_diff
        legacy=copy.deepcopy(self.doc);legacy['meta'].pop('extraction_version');legacy.pop('trust')
        diff=snapshot_diff(legacy,self.doc)
        self.assertEqual(diff['baseline']['commit'],diff['snapshot']['commit'])
        self.assertEqual(diff['baseline']['extraction_version'],1)
        self.assertEqual(diff['snapshot']['extraction_version'],2)
        self.assertEqual(diff['added_connections'],[])


if __name__ == '__main__':
    unittest.main()
