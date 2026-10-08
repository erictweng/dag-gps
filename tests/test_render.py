#!/usr/bin/env python3
"""Unit tests for scripts/render.py — the map.json -> standalone HTML inliner."""
import json
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import render  # noqa: E402


def small_map(**over):
    data = {
        "meta": {
            "repo": "me/repo", "ref": "origin/main", "commit": "abc1234",
            "built_at": "2026-10-07T00:00:00Z",
            "counts": {"layers": 1, "files": 1, "edges": 0, "file_edges": 0},
        },
        "nodes": [
            {"idx": "1", "id": "ui", "kind": "layer", "layer": "ui", "label": "UI",
             "desc": "screens", "path": "", "lines": 10, "tokens": ["ui"]},
            {"idx": "2", "id": "a.ts", "kind": "file", "layer": "ui", "label": "a.ts",
             "desc": "", "path": "a.ts", "lines": 10, "tokens": ["a"]},
        ],
        "edges": [],
        "file_edges": [],
        "layers": {"ui": {"files": ["a.ts"], "upstream": [], "downstream": [],
                          "top_fan_in": []}},
    }
    data.update(over)
    return data


class TestJsLiteral(unittest.TestCase):
    def test_round_trips(self):
        data = small_map()
        text = render.js_literal(data)
        self.assertEqual(json.loads(text.replace("<\\/", "</")), data)

    def test_breaks_up_closing_tags(self):
        data = small_map()
        data["nodes"][1]["desc"] = "ends a block with </script> inside a string"
        text = render.js_literal(data)
        self.assertNotIn("</", text)
        self.assertIn("<\\/script>", text)
        # still parses as JS once the escape is honoured
        self.assertEqual(json.loads(text.replace("<\\/", "</")), data)

    def test_escapes_js_line_terminators(self):
        data = small_map()
        data["nodes"][1]["desc"] = "a b c"
        text = render.js_literal(data)
        self.assertNotIn(" ", text)
        self.assertNotIn(" ", text)
        self.assertIn("\\u2028", text)

    def test_keeps_unicode_readable(self):
        data = small_map()
        data["nodes"][0]["label"] = "Réplay · scènes"
        self.assertIn("Réplay · scènes", render.js_literal(data))

    def test_is_compact(self):
        self.assertNotIn(", ", render.js_literal(small_map()))


class TestRender(unittest.TestCase):
    def test_replaces_the_placeholder(self):
        html = render.render("before" + render.PLACEHOLDER + "after", small_map())
        self.assertNotIn(render.PLACEHOLDER, html)
        self.assertTrue(html.startswith("before{"))
        self.assertTrue(html.endswith("}after"))

    def test_rejects_a_template_without_a_placeholder(self):
        with self.assertRaises(ValueError):
            render.render("<html></html>", small_map())

    def test_rejects_an_ambiguous_template(self):
        with self.assertRaises(ValueError):
            render.render(render.PLACEHOLDER + render.PLACEHOLDER, small_map())

    def test_real_template_has_exactly_one_placeholder(self):
        with open(render.DEFAULT_TEMPLATE, encoding="utf-8") as fh:
            text = fh.read()
        self.assertEqual(text.count(render.PLACEHOLDER), 1)

    def test_output_is_deterministic(self):
        with open(render.DEFAULT_TEMPLATE, encoding="utf-8") as fh:
            text = fh.read()
        data = small_map()
        self.assertEqual(render.render(text, data), render.render(text, data))

    def test_page_pulls_nothing_from_the_network(self):
        with open(render.DEFAULT_TEMPLATE, encoding="utf-8") as fh:
            text = fh.read().lower()
        # SVG namespace identifiers are not fetched resources.
        text = text.replace('http://www.w3.org/2000/svg', '')
        for needle in ("http://", "https://", "<script src", "<link rel=\"stylesheet\""):
            self.assertNotIn(needle, text, "template reaches outside: %r" % needle)


class TestCheckMap(unittest.TestCase):
    def test_accepts_a_good_map(self):
        self.assertEqual(render.check_map(small_map()), [])

    def test_reports_a_missing_top_level_key(self):
        data = small_map()
        del data["file_edges"]
        self.assertEqual(render.check_map(data), ["missing top-level 'file_edges'"])

    def test_reports_a_missing_meta_field(self):
        data = small_map()
        del data["meta"]["commit"]
        self.assertIn("missing meta.commit", render.check_map(data))

    def test_reports_a_layer_without_a_layers_entry(self):
        data = small_map()
        data["layers"] = {}
        self.assertIn("layers['ui'] missing", render.check_map(data))

    def test_reports_a_layers_entry_missing_a_precomputed_field(self):
        data = small_map()
        del data["layers"]["ui"]["top_fan_in"]
        self.assertIn("layers['ui'] missing 'top_fan_in'", render.check_map(data))

    def test_reports_a_map_with_no_layers(self):
        data = small_map()
        data["nodes"] = [n for n in data["nodes"] if n["kind"] != "layer"]
        self.assertIn("no layer nodes", render.check_map(data))


class TestMain(unittest.TestCase):
    def test_writes_a_page_and_creates_the_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            map_path = os.path.join(tmp, "map.json")
            with open(map_path, "w", encoding="utf-8") as fh:
                json.dump(small_map(), fh)
            out = os.path.join(tmp, "nested", "page.html")
            rc = render.main(["--map", map_path, "--out", out])
            self.assertEqual(rc, 0)
            with open(out, encoding="utf-8") as fh:
                html = fh.read()
            self.assertIn('"me/repo"', html)
            self.assertNotIn(render.PLACEHOLDER, html)

    def test_exits_non_zero_on_a_broken_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            map_path = os.path.join(tmp, "map.json")
            data = small_map()
            del data["layers"]
            with open(map_path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            out = os.path.join(tmp, "page.html")
            self.assertEqual(render.main(["--map", map_path, "--out", out]), 1)
            self.assertFalse(os.path.exists(out))


if __name__ == "__main__":
    unittest.main()
