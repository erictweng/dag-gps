"""Run the real extractor against small static TypeScript repositories."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TypeScriptPathsTests(unittest.TestCase):
    def extract(self, config=None, spec='@/lib/x', extra=None, text=None, name='tsconfig.json'):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            files = {'main.ts': text or f'import x from "{spec}";', 'src/lib/x.ts': ''}
            if config is not None:
                files[name] = config if isinstance(config, str) else json.dumps({'compilerOptions': config})
            files.update(extra or {})
            for path, content in files.items():
                p = root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(content)
            out = root / 'graph.json'
            subprocess.run([sys.executable, str(ROOT / 'scripts/import_graph.py'), tmp, str(out), 'main.ts', 'src'], check=True, capture_output=True)
            return json.loads(out.read_text())

    def target(self, config=None, **kwargs):
        return self.extract(config, **kwargs)['edges'][0][1]

    def test_src_alias(self):
        self.assertEqual(self.target({'paths': {'@/*': ['./src/*']}}), 'src/lib/x.ts')

    def test_multiple_targets(self):
        self.assertEqual(self.target({'paths': {'@/*': ['missing/*', 'src/*']}}), 'src/lib/x.ts')

    def test_longest_prefix_and_no_shorter_fallback(self):
        config = {'paths': {'@/*': ['src/*'], '@/lib/*': ['special/*']}}
        self.assertEqual(self.target(config, extra={'special/x/index.ts': ''}), 'special/x/index.ts')
        self.assertEqual(self.target(config), 'UNRESOLVED:@/lib/x')

    def test_exact_before_pattern(self):
        self.assertEqual(self.target({'paths': {'@/*': ['missing/*'], '@/lib/x': ['src/lib/x']}}), 'src/lib/x.ts')

    def test_extends_origin_and_chain(self):
        config = '{"extends":"./config/middle"}'
        extra = {'config/middle.json': '{"extends":"./base.json"}',
                 'config/base.json': '{"compilerOptions":{"paths":{"@/*":["../src/*"]}}}'}
        self.assertEqual(self.target(config, extra=extra), 'src/lib/x.ts')

    def test_inherited_baseurl(self):
        self.assertEqual(self.target('{"extends":"./config/base","compilerOptions":{"paths":{"@/*":["lib/*"]}}}', spec='@/x',
                         extra={'config/base.json': '{"compilerOptions":{"baseUrl":"../src"}}'}), 'src/lib/x.ts')

    def test_jsonc(self):
        self.assertEqual(self.target('''{/* comment */ "compilerOptions": {
          "paths": {"@/*": ["./src/*",],}, // end
          "custom": "https://example.test/*not comment*/",
        },}'''), 'src/lib/x.ts')

    def test_baseurl_and_external(self):
        self.assertEqual(self.target({'baseUrl': 'src'}, spec='lib/x'), 'src/lib/x.ts')
        self.assertEqual(self.extract({'baseUrl': 'src'}, spec='react')['ext'], {'main.ts': ['react']})

    def test_legacy_fallback(self):
        self.assertEqual(self.target(extra={'lib/x.ts': ''}), 'lib/x.ts')
        self.assertEqual(self.target({'paths': {'other/*': ['src/*']}}, extra={'lib/x.ts': ''}), 'lib/x.ts')

    def test_matched_missing_never_falls_back(self):
        self.assertEqual(self.target({'paths': {'@/*': ['missing/*']}}, extra={'lib/x.ts': ''}), 'UNRESOLVED:@/lib/x')

    def test_literal_and_comment_ignored(self):
        graph = self.extract({'paths': {'@/*': ['src/*']}}, text='// import "@/lib/x";\nconst s = \'import "@/lib/x";\';')
        self.assertEqual(graph['edges'], [])

    def test_jsconfig_and_suffix(self):
        self.assertEqual(self.target({'paths': {'@/*/x': ['src/*/x']}}, name='jsconfig.json'), 'src/lib/x.ts')

    def test_relative_import_unaffected(self):
        self.assertEqual(self.target({'paths': {'*': ['missing/*']}}, spec='./src/lib/x'), 'src/lib/x.ts')

    def test_child_paths_replaces_parent_table(self):
        self.assertEqual(self.target('{"extends":"./base","compilerOptions":{"paths":{"other/*":["src/*"]}}}',
                         extra={'base.json': '{"compilerOptions":{"paths":{"@/*":["src/*"]}}}'}), 'UNRESOLVED:@/lib/x')

    def test_cycle_and_package_extends_diagnostics(self):
        for config, extra in [('{"extends":"./tsconfig"}', {}), ('{"extends":"some-package"}', {}),
                              ('{"extends":"../outside"}', {}), ('{broken', {})]:
            with self.subTest(config=config):
                graph = self.extract(config, extra=extra)
                self.assertTrue(graph['unsupported'])

    def test_equal_prefix_uses_declaration_order(self):
        self.assertEqual(self.target({'paths': {'@/*': ['missing/*'], '@/*/x': ['src/*/x']}}), 'UNRESOLVED:@/lib/x')

    def test_tsconfig_preferred_to_jsconfig(self):
        self.assertEqual(self.target({'paths': {'@/*': ['src/*']}},
                         extra={'jsconfig.json': '{"compilerOptions":{"paths":{"@/*":["missing/*"]}}}'}), 'src/lib/x.ts')
