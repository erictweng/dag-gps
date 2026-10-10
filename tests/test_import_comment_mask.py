"""Lexical-start regressions; fixtures are static evidence, not runtime traces."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImportCommentMaskTests(unittest.TestCase):
    def extract(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'main.ts').write_text(text)
            (root / 'y.json').write_text('{}')
            out = root / 'graph.json'
            subprocess.run([sys.executable, str(ROOT / 'scripts/import_graph.py'),
                            tmp, str(out), 'main.ts'], check=True, capture_output=True)
            return json.loads(out.read_text())

    def test_block_comment_before_import(self):
        for keyword in ('import', 'export'):
            with self.subTest(keyword=keyword):
                graph = self.extract(f'/* one {keyword} here */\nimport x from "./y.json";')
                self.assertEqual(graph['edges'], [['main.ts', 'y.json']])

    def test_line_comment_before_import(self):
        for keyword in ('import', 'export'):
            with self.subTest(keyword=keyword):
                graph = self.extract(f'// one {keyword} here\nimport x from "./y.json";')
                self.assertEqual(graph['edges'], [['main.ts', 'y.json']])

    def test_comment_only_imports_are_ignored(self):
        graph = self.extract('/* import x from "./y.json"; */\n// import "./y.json";')
        self.assertEqual(graph['edges'], [])
        self.assertEqual(graph['unsupported'], [])

    def test_string_only_imports_are_ignored(self):
        for quote in ("'", '`'):
            with self.subTest(quote=quote):
                graph = self.extract(f'const fixture = {quote}import x from "./y.json";{quote};')
                self.assertEqual(graph['edges'], [])
                self.assertEqual(graph['unsupported'], [])

    def test_normal_import_syntax_is_unchanged(self):
        for text in ('import x from "./y.json";', 'export {x} from "./y.json";',
                     'import "./y.json";', 'import("./y.json");',
                     'const x = require ("./y.json");', 'import x = require("./y.json");'):
            with self.subTest(text=text):
                graph = self.extract(text)
                self.assertEqual(graph['edges'], [['main.ts', 'y.json']])
                self.assertEqual(graph['unsupported'], [])

    def test_computed_scan_retries_after_masked_start(self):
        for keyword in ('require', 'import'):
            with self.subTest(keyword=keyword):
                graph = self.extract(f'/* {keyword}( */\n{keyword}(target);')
                self.assertEqual(graph['unsupported'], [['main.ts', 'nonliteral ' + keyword, 'target']])
                self.assertEqual(graph['edges'], [])

    def test_require_in_comments_and_strings_does_not_hide_real_call(self):
        for prefix in ('/* require("./ghost") */', '// require("./ghost")',
                       "const fixture = 'require(\"./ghost\")';"):
            with self.subTest(prefix=prefix):
                graph = self.extract(prefix + '\nrequire("./y.json");')
                self.assertEqual(graph['edges'], [['main.ts', 'y.json']])
                self.assertEqual(graph['unsupported'], [])


if __name__ == '__main__':
    unittest.main()
