#!/usr/bin/env python3
"""Inline a map.json into web/template.html to produce one offline HTML page.

    python3 scripts/render.py --map maps/quest-coder/map.json --out dist/quest-coder.html

The template carries a single `/*__MAP__*/null` placeholder inside its <script>.
We swap that for the map as a JSON literal. Stdlib only, no network, no build step:
the output opens from file:// with nothing else on disk.
"""
import argparse
import json
import os
import sys

PLACEHOLDER = "/*__MAP__*/null"
DEFAULT_TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "template.html"
)


def js_literal(data):
    """Serialize `data` so it is safe to paste inside an HTML <script> block.

    Escape `<` to prevent closing tags and HTML double-escaped script states,
    regardless of JS string quoting. Escape U+2028/U+2029 for JS compatibility.
    """
    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"), sort_keys=False)
    # Escape every '<' to also prevent HTML script double-escaped states (<!--).
    text = text.replace("<", "\\u003c")
    text = text.replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return text


def render(template_text, map_data, tours=None):
    """Inline trusted module source as safely encoded JS strings.

    Function executes only shipped local source, never map/query contents. This
    preserves source syntax even for closing script tags in strings or comments.
    """
    for name in ("scorer", "router", "aliases", "tours"):
        marker = "/*__%s__*/" % name.upper()
        if template_text.count(marker) > 1:
            raise ValueError("duplicate module placeholder: " + marker)
        if marker in template_text:
            with open(os.path.join(os.path.dirname(DEFAULT_TEMPLATE), name + ".js"), encoding="utf-8") as fh:
                source = fh.read()
            template_text = template_text.replace(marker, "new Function(" + js_literal(source) + ")();")
    template_text = template_text.replace("/*__TOUR_DATA__*/null", js_literal(tours))
    if "/*__TOUR_UI__*/" in template_text:
        with open(os.path.join(os.path.dirname(DEFAULT_TEMPLATE), "tour-ui.js"), encoding="utf-8") as fh:
            template_text = template_text.replace("/*__TOUR_UI__*/", "var tourUI = eval(" + js_literal(fh.read()) + "); var tourController = tourUI.controller; var resolveTourQuery = tourUI.resolve; var exitTour = tourUI.exit;")
    ui_marker = "/*__ALIAS_UI__*/"
    if template_text.count(ui_marker) > 1:
        raise ValueError("duplicate module placeholder: " + ui_marker)
    if ui_marker in template_text:
        # Direct eval binds only trusted shipped UI source to the template closure.
        # Neither alias strings, import JSON, map values nor query text are code.
        with open(os.path.join(os.path.dirname(DEFAULT_TEMPLATE), "alias-ui.js"), encoding="utf-8") as fh:
            template_text = template_text.replace(ui_marker, "eval(" + js_literal(fh.read()) + ");")
    if template_text.count(PLACEHOLDER) != 1:
        raise ValueError(
            "template must contain exactly one %r placeholder (found %d)"
            % (PLACEHOLDER, template_text.count(PLACEHOLDER))
        )
    return template_text.replace(PLACEHOLDER, js_literal(map_data))


REQUIRED_TOP = ("meta", "nodes", "edges", "file_edges", "layers")


def check_map(map_data):
    """Return a list of complaints; empty means the map has what the page reads."""
    problems = []
    for key in REQUIRED_TOP:
        if key not in map_data:
            problems.append("missing top-level %r" % key)
    if problems:
        return problems
    for key in ("repo", "commit", "built_at", "counts"):
        if key not in map_data["meta"]:
            problems.append("missing meta.%s" % key)
    layers = [n for n in map_data["nodes"] if n.get("kind") == "layer"]
    if not layers:
        problems.append("no layer nodes")
    for n in layers:
        for key in ("id", "label", "lines"):
            if key not in n:
                problems.append("layer node %r missing %r" % (n.get("id"), key))
    for lid in (n["id"] for n in layers if "id" in n):
        info = map_data["layers"].get(lid)
        if info is None:
            problems.append("layers[%r] missing" % lid)
            continue
        for key in ("files", "upstream", "downstream", "top_fan_in"):
            if key not in info:
                problems.append("layers[%r] missing %r" % (lid, key))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", required=True, help="path to map.json")
    ap.add_argument("--out", required=True, help="path of the HTML page to write")
    ap.add_argument("--template", default=DEFAULT_TEMPLATE)
    ap.add_argument("--tours", help="Reviewed tours JSON; requires --repo to validate immutable source")
    ap.add_argument("--repo", help="Local Git repository for tour evidence verification")
    args = ap.parse_args(argv)

    with open(args.map, encoding="utf-8") as fh:
        map_data = json.load(fh)
    problems = check_map(map_data)
    if problems:
        for p in problems:
            print("FAIL  %s" % p)
        return 1
    with open(args.template, encoding="utf-8") as fh:
        template_text = fh.read()

    tours = None
    if args.tours:
        if not args.repo:
            raise ValueError("--tours requires --repo")
        from tours import compile_tours
        with open(args.tours, encoding="utf-8") as fh:
            tours = compile_tours(json.load(fh), map_data, args.repo)
    html = render(template_text, map_data, tours)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(html)

    counts = map_data["meta"].get("counts", {})
    print(
        "wrote %s  %.1f KB  (%s @ %s: %s layers, %s files, %s layer edges, %s file edges)"
        % (
            args.out, len(html.encode("utf-8")) / 1024.0,
            map_data["meta"].get("repo"), map_data["meta"].get("commit"),
            counts.get("layers"), counts.get("files"),
            counts.get("edges"), counts.get("file_edges"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
