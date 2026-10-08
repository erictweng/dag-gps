#!/usr/bin/env python3
"""Merge the hand-drawn layer map with the auto-extracted import graph into map.json.

Usage: build_map.py --repo <path> --ref <git ref> --layers <layers.json> --out <map.json>

Exports the repo at <ref> into a temp dir, runs the vendored import_graph.py over it,
assigns every source file to exactly one layer by glob, rolls file import edges up into
typed layer edges, indexes every node the way Jev indexes an observation, and writes
map.json. Prints a check report; exits non-zero if any check FAILs.
"""
import argparse
import collections
import datetime
import fnmatch
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IMPORT_GRAPH = os.path.join(HERE, "import_graph.py")
SOURCE_EXTS = ("ts", "tsx", "js", "jsx", "mjs", "cjs", "py", "sql")
EXCLUDED_DIRS = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', 'vendor', 'dist', 'artifacts', 'build', '.next'}


def included(path):
    return not (set(path.split('/')[:-1]) & EXCLUDED_DIRS)
DEFAULT_TOPS = ["app", "components", "lib", "proxy.ts", "scripts", "browser-runtime", "runner"]
# Edge types that are a draw, not a dependency: skipped for closure and cycle checks.
IGNORED_FOR_CLOSURE = ("realtime",)


# ---------------------------------------------------------------- glob + tokens

def match(path, glob):
    """Glob semantics from scripts/check_layers.py: `dir/**` is a prefix match,
    anything else is an fnmatch with the same number of `/`."""
    if glob.endswith("/**"):
        return path.startswith(glob[:-2])
    return fnmatch.fnmatchcase(path, glob) and path.count("/") == glob.count("/")


WORD_RE = re.compile(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]+(?![a-zA-Z])|[A-Z][a-z0-9]*|[a-z0-9]+")


def chunks(text):
    """The alphanumeric runs of `text`, split on every non-alphanumeric character."""
    return [c for c in re.split(r"[^A-Za-z0-9]+", text or "") if c]


def split_words(text):
    """Lowercase words, splitting on non-alphanumerics, camelCase and -/_."""
    return [w.lower() for c in chunks(text) for w in WORD_RE.findall(c)]


def tokens_of(*texts):
    """Deduped tokens from the given texts, 1-char tokens dropped, order preserved.

    A chunk that camel-splits also keeps its whole lowercased form, so "SQLite"
    offers `sqlite` alongside the split `sq`/`lite`.
    """
    seen = {}
    for t in texts:
        for c in chunks(t):
            words = [w.lower() for w in WORD_RE.findall(c)]
            for w in words + ([c.lower()] if len(words) > 1 else []):
                if len(w) > 1:
                    seen[w] = None
    return list(seen)


# ------------------------------------------------------------------ assignment

def assign_layers(files, layers):
    """-> (layer_of, unmapped, double). Every file lands in exactly one layer or is reported."""
    owners = {f: [l["id"] for l in layers if any(match(f, g) for g in l["globs"])] for f in files}
    unmapped = sorted(f for f, o in owners.items() if not o)
    double = {f: o for f, o in sorted(owners.items()) if len(o) > 1}
    layer_of = {f: o[0] for f, o in owners.items() if o}
    return layer_of, unmapped, double


def rollup(file_edges, layer_of, edge_type="import"):
    """Roll file->file edges up into layer->layer edges, dropping same-layer edges."""
    weight = collections.Counter()
    sample = {}
    for a, b in file_edges:
        la, lb = layer_of.get(a), layer_of.get(b)
        if not la or not lb or la == lb:
            continue
        weight[(la, lb)] += 1
        sample.setdefault((la, lb), [a, b])
    return [
        {"from": a, "to": b, "type": edge_type, "weight": n, "sample": sample[(a, b)]}
        for (a, b), n in sorted(weight.items())
    ]


# ----------------------------------------------------------------- typed edges

def resolve_api_route(api_path, route_files):
    """Map a fetch path like /api/party/assist to its app/api/.../route.ts file.

    Exact segment match wins; then a `[dynamic]` segment match; then the longest
    route whose own segments are a prefix of the call (covers `/api/packs/`).
    """
    want = [s for s in api_path.strip("/").split("/") if s]
    dynamic, prefix = None, None
    for rf in sorted(route_files):
        got = rf.split("/")[1:-1]  # drop leading "app" and trailing "route.ts"
        if got == want:
            return rf
        if len(got) == len(want) and all(
                g == w or (g.startswith("[") and g.endswith("]")) for g, w in zip(got, want)):
            dynamic = dynamic or rf
        elif len(got) <= len(want) and got == want[: len(got)]:
            if prefix is None or len(got) > len(prefix.split("/")[1:-1]):
                prefix = rf
    return dynamic or prefix


def http_edges(api_calls, layer_of, route_files):
    """fetch('/api/...') caller layer -> the layer owning the matching route handler."""
    weight, samples, misses = collections.Counter(), {}, []
    for caller, paths in sorted(api_calls.items()):
        la = layer_of.get(caller)
        for p in paths:
            route = resolve_api_route(p, route_files)
            lb = layer_of.get(route) if route else None
            if not la or not lb:
                misses.append([caller, p])
                continue
            if la == lb:
                continue
            weight[(la, lb)] += 1
            samples.setdefault((la, lb), [caller, p])
    edges = [
        {"from": a, "to": b, "type": "http", "weight": n, "sample": samples[(a, b)]}
        for (a, b), n in sorted(weight.items())
    ]
    return edges, misses


def rpc_edges(rpcs, sqlfns, layer_of):
    """`.rpc('fn')` caller layer -> the layer owning the migration that last defines fn."""
    weight, samples, whys, misses = collections.Counter(), {}, {}, []
    for caller, fns in sorted(rpcs.items()):
        la = layer_of.get(caller)
        for fn in fns:
            defs = sqlfns.get(fn) or []
            target = defs[-1] if defs else None  # migrations sort chronologically by name
            lb = layer_of.get(target) if target else None
            if not la or not lb:
                misses.append([caller, fn])
                continue
            if la == lb:
                continue
            weight[(la, lb)] += 1
            samples.setdefault((la, lb), [caller, target])
            whys.setdefault((la, lb), f".rpc('{fn}')")
    edges = [
        {"from": a, "to": b, "type": "rpc", "weight": n, "sample": samples[(a, b)],
         "why": whys[(a, b)]}
        for (a, b), n in sorted(weight.items())
    ]
    return edges, misses


def file_level_edges(import_pairs, api_calls, route_files, rpcs, sqlfns, layer_of, files):
    """-> (edges, dropped). file->file edges, so the canvas can expand a layer into files.

    `import` from every JS/TS and Python pair, `http` from a fetch('/api/...') caller to
    the matching route handler, `rpc` from a `.rpc('fn')` caller to the migration that
    last defines fn. Unlike the layer rollup, same-layer edges are kept and carry
    `cross_layer: False`. Identical (from, to, type) triples are deduped; an endpoint
    that is not a file node id (an `UNRESOLVED:` target, a `.jsx` file the map does not
    index) is dropped and reported.
    """
    known = set(files)
    seen, out, dropped = set(), [], []

    def add(a, b, etype):
        if a == b:
            return
        if a not in known or b not in known:
            dropped.append([a, b, etype])
            return
        if (a, b, etype) in seen:
            return
        seen.add((a, b, etype))
        out.append({"from": a, "to": b, "type": etype,
                    "cross_layer": layer_of.get(a) != layer_of.get(b)})

    for a, b in import_pairs:
        add(a, b, "import")
    for caller, paths in sorted(api_calls.items()):
        for p in paths:
            route = resolve_api_route(p, route_files)
            if route:
                add(caller, route, "http")
    for caller, fns in sorted(rpcs.items()):
        for fn in fns:
            defs = sqlfns.get(fn) or []
            if defs:  # migrations sort chronologically by name; the last one wins
                add(caller, defs[-1], "rpc")
    out.sort(key=lambda e: (e["from"], e["to"], e["type"]))
    return out, dropped


def manual_edges(spec):
    return [
        {"from": e["from"], "to": e["to"], "type": e.get("type", "manual"),
         "weight": 1, "sample": None, "why": e.get("why", "")}
        for e in spec.get("manual_edges", [])
    ]


# -------------------------------------------------------------------- graph ops

def adjacency(edges, ids):
    adj = {i: set() for i in ids}
    for e in edges:
        if e["type"] in IGNORED_FOR_CLOSURE:
            continue
        if e["from"] in adj and e["to"] in adj:
            adj[e["from"]].add(e["to"])
    return adj


def find_cycle(adj):
    """-> the first cycle found as a list of ids (closing node repeated), or None."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = collections.defaultdict(int)
    for root in sorted(adj):
        if color[root] != WHITE:
            continue
        stack = [(root, iter(sorted(adj[root])))]
        color[root] = GREY
        path = [root]
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                color[node] = BLACK
                stack.pop()
                path.pop()
                continue
            if color[nxt] == GREY:
                return path[path.index(nxt):] + [nxt]
            if color[nxt] == WHITE:
                color[nxt] = GREY
                path.append(nxt)
                stack.append((nxt, iter(sorted(adj.get(nxt, ())))))
    return None


def reachable(adj, start):
    seen, queue = set(), collections.deque(adj.get(start, ()))
    while queue:
        n = queue.popleft()
        if n in seen or n == start:
            continue
        seen.add(n)
        queue.extend(adj.get(n, ()))
    return sorted(seen)


# ------------------------------------------------------------------ file descs

COMMENTS = {
    "ts": ("//", ("/*", "*/")), "tsx": ("//", ("/*", "*/")),
    "js": ("//", ("/*", "*/")), "mjs": ("//", ("/*", "*/")),
    "py": ("#", ('"""', '"""')), "sql": ("--", ("/*", "*/")),
}
DIRECTIVE_RE = re.compile(
    r"""^(?:['"]use (?:client|server)['"];?|#!.*|from\s+__future__\b.*|/\*\s*eslint.*?\*/)$""")
IMPORTISH_RE = re.compile(
    r"""^(?:import\b.*|export\s+(?:type\s+)?\*?\s*\{?[^;]*\}?\s*from\b.*)$""")
EXPORT_RES = [
    re.compile(r"^export\s+(?:async\s+)?function\s+(\w+)", re.M),
    re.compile(r"^export\s+(?:const|let|var)\s+(\w+)", re.M),
    re.compile(r"^export\s+(?:type|interface|class|enum)\s+(\w+)", re.M),
    re.compile(r"^export\s+default\s+(?:async\s+)?(?:function\s+)?(\w+)?", re.M),
]
IMPORT_LINE_RE = re.compile(r"^import[\s{*]")
PY_DEF_RE = re.compile(r"^(?:async\s+)?(?:def|class)\s+([A-Za-z]\w*)", re.M)
SQL_FN_RE = re.compile(r"create\s+(?:or\s+replace\s+)?function\s+(?:\w+\.)?([a-z0-9_]+)", re.I)


def clean_comment(lines):
    out = []
    for ln in lines:
        ln = re.sub(r"^\s*\*+\s?|^\s*//\s?|^\s*#\s?|^\s*--\s?", "", ln).strip()
        if ln:
            out.append(ln)
    text = " ".join(out).strip()
    return re.sub(r"\s+", " ", text)


def next_code_line(lines, i):
    for ln in lines[i:]:
        if ln.strip():
            return ln.strip()
    return ""


def extract_desc(text, path):
    """Top-of-file block comment or line-comment run; else `exports: A, B`; else "".

    Directives (`"use client"`) and the import block are skipped first. A comment that
    sits *after* the imports is usually the real file header in this repo
    (components/solve/action-bar.tsx, tests/e2e/*.spec.ts), so it counts -- unless more
    imports follow it, which means the comment is interleaved in the import block and
    documents one lazy declaration, not the file (app/page.tsx's `const BossTogether =
    dynamic(...)`, with the import list resuming right after).
    """
    ext = path.rsplit(".", 1)[-1]
    line_tok, (block_open, block_close) = COMMENTS.get(ext, ("//", ("/*", "*/")))
    lines = text.split("\n")
    i, skipped = 0, False

    def accept(body, after):
        if skipped and any(IMPORT_LINE_RE.match(ln) for ln in lines[after:]):
            return exports_desc(text, path)
        return clean_comment(body) or exports_desc(text, path)

    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if DIRECTIVE_RE.match(s):
            i += 1
            continue
        if IMPORTISH_RE.match(s):
            # a multi-line import keeps going until its `from` / closing brace
            if s.startswith("import") and " from " not in s and not s.endswith(";"):
                while i < len(lines) and " from " not in lines[i] and "}" not in lines[i]:
                    i += 1
            skipped = True
            i += 1
            continue
        if s.startswith(block_open):
            first = s[len(block_open):]
            if block_close in first:
                return accept([first.split(block_close)[0]], i + 1)
            body = [first]
            i += 1
            while i < len(lines):
                if block_close in lines[i]:
                    body.append(lines[i].split(block_close)[0])
                    break
                body.append(lines[i])
                i += 1
            return accept(body, i + 1)
        if s.startswith(line_tok):
            body = []
            while i < len(lines) and lines[i].strip().startswith(line_tok):
                body.append(lines[i])
                i += 1
            return accept(body, i)
        break
    return exports_desc(text, path)


def exports_desc(text, path):
    ext = path.rsplit(".", 1)[-1]
    if ext == "py":
        names = [n for n in PY_DEF_RE.findall(text) if not n.startswith("_")]
    elif ext == "sql":
        names = SQL_FN_RE.findall(text)
    else:
        names = []
        for rx in EXPORT_RES:
            names.extend(n for n in rx.findall(text) if n)
        for m in re.finditer(r"^export\s*\{([^}]*)\}", text, re.M):
            for part in m.group(1).split(","):
                part = part.strip().split(" as ")[-1].strip()
                if part and part != "default":
                    names.append(part)
    seen = list(dict.fromkeys(names))
    if not seen:
        return ""
    shown = seen[:6]
    return "exports: " + ", ".join(shown) + (", …" if len(seen) > 6 else "")


# --------------------------------------------------------------------- pipeline

def load_json(path):
    with open(path) as fh:
        return json.load(fh)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", repo, *args], text=True)


def source_files(repo, ref):
    names = git(repo, "ls-tree", "-r", "--name-only", ref).split("\n")
    return sorted(f for f in names if f and included(f) and f.rsplit(".", 1)[-1] in SOURCE_EXTS)


def read_export(root, rel):
    p = os.path.join(root, rel)
    try:
        with open(p, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def layer_node(layer, idx, files, texts):
    """Retain alias phrases as well as tokens for the local/browser scorer."""
    return {
        "idx": str(idx), "id": layer["id"], "kind": "layer", "layer": layer["id"],
        "label": layer["label"], "desc": layer.get("desc", ""), "path": "",
        "aliases": list(layer.get("aliases", [])),
        "lines": sum(texts[f].count("\n") for f in files),
        "tokens": tokens_of(layer["label"], *layer.get("aliases", []), layer.get("desc", ""),
                            *[g.replace("/**", "") for g in layer["globs"]]),
    }


def build(repo, ref, layers_path, out_path, tops):
    spec = load_json(layers_path)
    layers = spec["layers"]
    pinned = git(repo, "rev-parse", "--verify", ref + '^{commit}').strip()
    commit = git(repo, "rev-parse", "--short", pinned).strip()
    files = source_files(repo, pinned)

    tmp = tempfile.mkdtemp(prefix="dag-gps-")
    try:
        archive = subprocess.Popen(["git", "-C", repo, "archive", pinned], stdout=subprocess.PIPE)
        tar = subprocess.Popen(["tar", "-x", "-C", tmp], stdin=archive.stdout)
        archive.stdout.close()
        tar.communicate()
        if archive.wait() != 0 or tar.returncode != 0:
            raise SystemExit(f"export of {repo}@{ref} failed")

        graph_path = os.path.join(tmp, "_import_graph.json")
        proc = subprocess.run([sys.executable, IMPORT_GRAPH, tmp, graph_path, *tops],
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise SystemExit(f"import_graph.py failed:\n{proc.stderr}")
        graph = load_json(graph_path)
        extract_log = proc.stdout.strip().split("\n")[0]
        texts = {f: read_export(tmp, f) for f in files}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    layer_of, unmapped, double = assign_layers(files, layers)
    per_layer = collections.Counter(layer_of.values())
    empty = [l["id"] for l in layers if not per_layer.get(l["id"])]

    import_pairs = [tuple(e) for e in graph["edges"]] + [tuple(e) for e in graph.get("pyedges", [])]
    edges = rollup(import_pairs, layer_of)
    route_files = [f for f in files if f.startswith("app/api/") and f.endswith("/route.ts")]
    http, http_misses = http_edges(graph.get("api_calls", {}), layer_of, route_files)
    rpc, rpc_misses = rpc_edges(graph.get("rpcs", {}), graph.get("sqlfns", {}), layer_of)
    manual = manual_edges(spec)
    edges += http + rpc + manual
    fedges, fedge_drops = file_level_edges(
        import_pairs, graph.get("api_calls", {}), route_files, graph.get("rpcs", {}),
        graph.get("sqlfns", {}), layer_of, files)

    # file importer counts, for per-layer top_fan_in
    importers = collections.defaultdict(set)
    for a, b in import_pairs:
        if a != b:
            importers[b].add(a)

    layer_ids = [l["id"] for l in layers]
    adj = adjacency(edges, layer_ids)
    radj = {i: set() for i in layer_ids}
    for a, outs in adj.items():
        for b in outs:
            radj[b].add(a)
    cycle = find_cycle(adj)

    nodes, idx = [], 1
    for l in layers:
        lfiles = sorted(f for f in files if layer_of.get(f) == l["id"])
        nodes.append(layer_node(l, idx, lfiles, texts))
        idx += 1
    for f in files:
        lid = layer_of.get(f)
        desc = extract_desc(texts[f], f)
        nodes.append({
            "idx": str(idx), "id": f, "kind": "file", "layer": lid,
            "label": os.path.basename(f), "desc": desc, "path": f,
            "lines": texts[f].count("\n"),
            "tokens": tokens_of(os.path.basename(f), desc, f),
        })
        idx += 1

    layers_out = {}
    for l in layers:
        lid = l["id"]
        lfiles = sorted(f for f in files if layer_of.get(f) == lid)
        layers_out[lid] = {
            "files": lfiles,
            "upstream": reachable(adj, lid),
            "downstream": reachable(radj, lid),
            "top_fan_in": [f for f, _ in sorted(
                ((f, len(importers.get(f, ()))) for f in lfiles),
                key=lambda kv: (-kv[1], kv[0]))[:5] if importers.get(f)],
        }

    doc = {
        "meta": {
            "repo": spec.get("repo", os.path.basename(os.path.abspath(repo))),
            "ref": ref, "commit": commit,
            "built_at": datetime.datetime.now(datetime.timezone.utc).replace(
                microsecond=0).isoformat().replace("+00:00", "Z"),
            "counts": {"layers": len(layers), "files": len(files), "edges": len(edges),
                       "file_edges": len(fedges)},
        },
        "nodes": nodes,
        "edges": edges,
        "file_edges": fedges,
        "layers": layers_out,
    }

    # Validate a private candidate; never publish failing maps over a valid one.
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    fd, candidate = tempfile.mkstemp(prefix='.map-', dir=os.path.dirname(os.path.abspath(out_path)))
    try:
        with os.fdopen(fd, "w") as fh:
            json.dump(doc, fh, indent=1)
            fh.write("\n")
        report = check(doc, candidate, graph, unmapped, double, empty, cycle, layer_ids, spec,
                       http_misses, rpc_misses, fedge_drops)
        if all(ok for ok, _, _ in report):
            os.replace(candidate, out_path)
    finally:
        if os.path.exists(candidate):
            os.unlink(candidate)
    # Diagnostics are returned even when the candidate is rejected.
    doc['diagnostics'] = {'unresolved': graph.get('unresolved', []),
                          'unsupported': graph.get('unsupported', []),
                          'unmapped': unmapped, 'duplicate_assignments': double,
                          'empty_layers': empty, 'layer_cycle': cycle,
                          'non_source_connections': list(fedge_drops),
                          'unresolved_http': http_misses, 'unresolved_rpc': rpc_misses}
    return doc, report, extract_log


# ----------------------------------------------------------------------- checks

def check(doc, out_path, graph, unmapped, double, empty, cycle, layer_ids, spec,
          http_misses, rpc_misses, fedge_drops=()):
    results = []

    def add(ok, name, detail=""):
        results.append((ok, name, detail))

    unres = graph.get("unresolved", [])
    add(not unres, f"unresolved imports == 0 (got {len(unres)})",
        "\n".join(f"    {a} -> {b}" for a, b in unres[:10]))
    add(not unmapped, f"unmapped files == 0 (got {len(unmapped)})",
        "\n".join(f"    UNMAPPED {f}" for f in unmapped[:20]))
    add(not double, f"double-mapped files == 0 (got {len(double)})",
        "\n".join(f"    DOUBLE {f} {o}" for f, o in list(double.items())[:20]))
    add(not empty, f"empty layers == 0 (got {len(empty)})",
        "    " + ", ".join(empty) if empty else "")
    add(cycle is None, "no layer cycles (realtime ignored)",
        "    cycle: " + " -> ".join(cycle) if cycle else "")

    bad_manual = [e for e in spec.get("manual_edges", [])
                  if e["from"] not in layer_ids or e["to"] not in layer_ids]
    add(not bad_manual, f"manual edges reference known layers ({len(spec.get('manual_edges', []))} edges)",
        "\n".join(f"    BAD {e['from']} -> {e['to']}" for e in bad_manual))

    try:
        reloaded = load_json(out_path)
        ids = {n["id"] for n in reloaded["nodes"]}
        dangling = [e for e in reloaded["edges"] if e["from"] not in ids or e["to"] not in ids]
        dup_idx = len({n["idx"] for n in reloaded["nodes"]}) != len(reloaded["nodes"])
        dup_ids = len(ids) != len(reloaded['nodes'])
        ok = not dangling and not dup_idx and not dup_ids
        add(ok, "map.json round-trips, every edge endpoint is a known id",
            ("\n".join(f"    DANGLING {e['from']} -> {e['to']}" for e in dangling[:10])
             + ("\n    DUPLICATE idx values" if dup_idx else "")
             + ("\n    DUPLICATE node IDs" if dup_ids else "")).rstrip())

        file_ids = {n["id"] for n in reloaded["nodes"] if n.get("kind") == "file"}
        fdangling = [e for e in reloaded["file_edges"]
                     if e["from"] not in file_ids or e["to"] not in file_ids]
        add(not fdangling,
            f"every file_edge endpoint is a known file node ({len(reloaded['file_edges'])} edges)",
            "\n".join(f"    DANGLING {e['from']} -> {e['to']} ({e['type']})"
                      for e in fdangling[:10]))
    except Exception as exc:  # noqa: BLE001 - surfaced in the report
        add(False, "map.json round-trips", f"    {exc!r}")

    if fedge_drops:
        add(True, f"note: {len(fedge_drops)} file edge(s) dropped, endpoint is not a file node",
            "\n".join(f"    {a} -> {b} ({t})" for a, b, t in list(fedge_drops)[:10]))
    if http_misses:
        add(True, f"note: {len(http_misses)} fetch path(s) with no route handler",
            "\n".join(f"    {a} -> {b}" for a, b in http_misses[:10]))
    if rpc_misses:
        add(True, f"note: {len(rpc_misses)} .rpc() call(s) with no SQL definition",
            "\n".join(f"    {a} -> {b}()" for a, b in rpc_misses[:10]))
    return results


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--layers", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tops", nargs="+", default=DEFAULT_TOPS)
    a = ap.parse_args(argv)

    doc, report, extract_log = build(a.repo, a.ref, a.layers, a.out, a.tops)
    m = doc["meta"]
    by_type = collections.Counter(e["type"] for e in doc["edges"])

    print(f"build_map: {m['repo']} {m['ref']} @ {m['commit']}")
    print(f"extract:   {extract_log}")
    print(f"nodes:     {m['counts']['layers']} layers + {m['counts']['files']} files "
          f"= {len(doc['nodes'])}")
    print(f"edges:     {m['counts']['edges']} (" + ", ".join(
        f"{t} {n}" for t, n in sorted(by_type.items())) + ")")
    fby_type = collections.Counter(e["type"] for e in doc["file_edges"])
    cross = sum(1 for e in doc["file_edges"] if e["cross_layer"])
    print(f"file edges:{m['counts']['file_edges']} (" + ", ".join(
        f"{t} {n}" for t, n in sorted(fby_type.items())) + f"; cross-layer {cross})")
    print(f"output:    {a.out} (promoted only if every check passes)")
    print("checks:")
    failed = 0
    for ok, name, detail in report:
        print(f"  {'PASS' if ok else 'FAIL'} {name}")
        if detail:
            print(detail)
        failed += not ok
    print(f"{len(report) - failed}/{len(report)} checks passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
