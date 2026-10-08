#!/usr/bin/env python3
"""Extract a module graph from a TS/JS + Python repo snapshot.

Usage: import_graph.py <src_dir> <out.json> [top-level dirs/files ...]
Default tops: app components lib src pages proxy.ts middleware.ts scripts browser-runtime
Output: nodes{path:{lines,client}}, edges, pyedges, ext, api_calls, rpcs, sqlfns, cycles, unresolved, fan_in, fan_out.
"""
import os, re, sys, json, glob, collections, ast
from build_map import included

src, out = sys.argv[1], os.path.abspath(sys.argv[2])
tops = sys.argv[3:] or ["app", "components", "lib", "src", "pages", "proxy.ts", "middleware.ts", "scripts", "browser-runtime"]
os.chdir(src)
EXTS = [".ts", ".tsx", ".mjs", ".js", ".jsx", ".cjs"]
files = set()
for top in tops:
    if os.path.isfile(top) and included(top) and os.path.splitext(top)[1] in EXTS:
        files.add(top)
    for p in glob.glob(f"{top}/**/*", recursive=True):
        if os.path.splitext(p)[1] in EXTS and included(p):
            files.add(p)

def resolve(f, spec):
    if spec.startswith("@/"):
        base = spec[2:]
    elif spec.startswith("."):
        base = os.path.normpath(os.path.join(os.path.dirname(f), spec))
    else:
        return None
    for c in [base] + [base + e for e in EXTS] + [os.path.join(base, "index" + e) for e in EXTS]:
        if os.path.isfile(c):
            return c
    return "UNRESOLVED:" + spec

imp = re.compile(r"""(?:import|export)\s[^'"]*?from\s*['"]([^'"]+)['"]|import\(\s*['"]([^'"]+)['"]\s*\)|^import\s+['"]([^'"]+)['"]""", re.M)
fetch_re = re.compile(r"""['"`](/api/[a-zA-Z0-9_\-/\[\]]+)""")
rpc_re = re.compile(r"""\.rpc\(\s*['"]([a-z0-9_]+)['"]""")
def code_mask(text):
    """Mask comments/string bodies so literal fixtures cannot invent imports.

    Lightweight lexical guard, not a JS parser; template interpolation is unsupported.
    """
    mask = [True] * len(text)
    rx = re.compile(r"/\*[\s\S]*?\*/|//[^\n]*|'(?:\\.|[^'\\])*'|\"(?:\\.|[^\"\\])*\"|`(?:\\.|[^`\\])*`")
    for m in rx.finditer(text):
        for i in range(m.start(), m.end()):
            mask[i] = False
    return mask


require_re = re.compile(r"""\brequire\(\s*['"]([^'"]+)['"]\s*\)""")
unsupported = []
nodes, edges, ext, api, rpcs = {}, [], {}, {}, {}
for f in sorted(files):
    t = open(f, encoding="utf-8", errors="ignore").read()
    nodes[f] = {"lines": t.count("\n"), "client": "use client" in t[:200]}
    mask = code_mask(t)
    specs = [m.group(1) or m.group(2) or m.group(3) for m in imp.finditer(t) if mask[m.start()]] + [m.group(1) for m in require_re.finditer(t) if mask[m.start()]]
    for m in re.finditer(r"\b(require|import)\(\s*([^)]*)\)", t):
        if mask[m.start()] and not re.fullmatch(r"[\'\"][^\'\"]+[\'\"]", m.group(2).strip()):
            unsupported.append([f, "nonliteral " + m.group(1), m.group(2).strip()[:160]])
    for spec in specs:
        r = resolve(f, spec)
        if r is None:
            ext.setdefault(f, set()).add("/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0])
        else:
            edges.append([f, r])
    calls = sorted(set(fetch_re.findall(t)))
    if calls and "/api/" not in f:
        api[f] = calls
    r = sorted(set(rpc_re.findall(t)))
    if r:
        rpcs[f] = r

sqlfns = {}
for p in sorted(p for p in glob.glob("**/migrations/*.sql", recursive=True) if included(p)):
    t = open(p).read()
    nodes[p] = {"lines": t.count("\n")}
    for m in re.finditer(r"create\s+(?:or\s+replace\s+)?function\s+(?:\w+\.)?([a-z0-9_]+)", t, re.I):
        sqlfns.setdefault(m.group(1), []).append(p)

py = sorted(p for p in glob.glob("**/*.py", recursive=True) if included(p))
mods = {p[:-3].replace("/", ".").replace(".__init__", ""): p for p in py}
pyedges = set()
pyunresolved = []
for p in py:
    t = open(p, errors="ignore").read()
    nodes[p] = {"lines": t.count("\n")}
    try:
        tree = ast.parse(t, filename=p)
    except SyntaxError as exc:
        unsupported.append([p, 'Python parse error', str(exc)])
        pyunresolved.append([p, 'UNRESOLVED:Python syntax'])
        continue
    package = os.path.dirname(p).replace('/', '.')
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == '__import__':
            unsupported.append([p, 'dynamic Python import', ast.unparse(node)[:160]])
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Import):
            groups = [[alias.name] for alias in node.names]
        else:
            if node.level:
                unsupported.append([p, 'relative Python import', ast.unparse(node)[:160]])
                continue
            mod = node.module or ''
            groups = [[mod] + [mod + '.' + alias.name for alias in node.names]]
        for names in groups:
            hit = None
            for n in names:
                # Exact or same-directory script imports first. A unique suffix
                # covers sys.path-added script folders; ambiguities are reported.
                cands = [n, package + '.' + n]
                hits = [mods[c] for c in cands if c in mods and mods[c] != p]
                if not hits:
                    hits = sorted(set(v for k, v in mods.items() if k.endswith('.' + n) and v != p))
                if len(set(hits)) == 1:
                    hit = hits[0]
                    break
                if len(set(hits)) > 1:
                    pyunresolved.append([p, 'UNRESOLVED:ambiguous Python ' + n])
                    break
            if hit:
                pyedges.add((p, hit))
            # Bare unresolvable names may be stdlib/third-party. Record separately.
            else:
                ext.setdefault(p, set()).add(names[0].split('.')[0])

adj = collections.defaultdict(set)
for a, b in edges + list(pyedges):
    adj[a].add(b)
cycles, color = [], {}
sys.setrecursionlimit(10000)
def dfs(u, stack):
    color[u] = 1; stack.append(u)
    for v in sorted(adj[u]):
        if color.get(v) == 1: cycles.append(stack[stack.index(v):] + [v])
        elif not color.get(v): dfs(v, stack)
    stack.pop(); color[u] = 2
for n in sorted(adj):
    if not color.get(n): dfs(n, [])

indeg = collections.Counter(b for a, b in edges)
result = {"nodes": nodes, "edges": edges, "pyedges": sorted(pyedges), "ext": {k: sorted(v) for k, v in ext.items()},
          "api_calls": api, "rpcs": rpcs, "sqlfns": sqlfns, "cycles": cycles,
          "unresolved": sorted([e for e in edges if e[1].startswith("UNRESOLVED")] + pyunresolved),
          "unsupported": sorted(unsupported),
          "fan_in": indeg.most_common(15), "fan_out": sorted(((len(v), k) for k, v in adj.items()), reverse=True)[:10]}
json.dump(result, open(out, "w"), indent=1)
print(f"{len(nodes)} nodes, {len(edges)} js edges, {len(pyedges)} py edges, {len(cycles)} cycles, {len(result['unresolved'])} unresolved")
print("fan-in:", result["fan_in"][:8])
print("fan-out:", result["fan_out"][:5])
