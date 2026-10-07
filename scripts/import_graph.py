#!/usr/bin/env python3
"""Extract a module graph from a TS/JS + Python repo snapshot.

Usage: import_graph.py <src_dir> <out.json> [top-level dirs/files ...]
Default tops: app components lib src pages proxy.ts middleware.ts scripts browser-runtime
Output: nodes{path:{lines,client}}, edges, pyedges, ext, api_calls, rpcs, sqlfns, cycles, unresolved, fan_in, fan_out.
"""
import os, re, sys, json, glob, collections

src, out = sys.argv[1], os.path.abspath(sys.argv[2])
tops = sys.argv[3:] or ["app", "components", "lib", "src", "pages", "proxy.ts", "middleware.ts", "scripts", "browser-runtime"]
os.chdir(src)
EXTS = [".ts", ".tsx", ".mjs", ".js", ".jsx"]
files = set()
for top in tops:
    if os.path.isfile(top):
        files.add(top)
    for p in glob.glob(f"{top}/**/*", recursive=True):
        if os.path.splitext(p)[1] in EXTS and "node_modules" not in p:
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
nodes, edges, ext, api, rpcs = {}, [], {}, {}, {}
for f in sorted(files):
    t = open(f, encoding="utf-8", errors="ignore").read()
    nodes[f] = {"lines": t.count("\n"), "client": "use client" in t[:200]}
    for m in imp.finditer(t):
        spec = m.group(1) or m.group(2) or m.group(3)
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
for p in sorted(glob.glob("**/migrations/*.sql", recursive=True)):
    t = open(p).read()
    nodes[p] = {"lines": t.count("\n")}
    for m in re.finditer(r"create\s+(?:or\s+replace\s+)?function\s+(?:\w+\.)?([a-z0-9_]+)", t, re.I):
        sqlfns.setdefault(m.group(1), []).append(p)

py = sorted(p for p in glob.glob("**/*.py", recursive=True) if "node_modules" not in p and ".venv" not in p)
mods = {p[:-3].replace("/", ".").replace(".__init__", ""): p for p in py}
pyedges = set()
for p in py:
    t = open(p, errors="ignore").read()
    nodes[p] = {"lines": t.count("\n")}
    for m in re.finditer(r"^\s*(?:from\s+([\w\.]+)\s+import\s+([\w, ]+)|import\s+([\w\.]+))", t, re.M):
        mod = m.group(1) or m.group(3)
        names = [mod] + ([f"{mod}.{n.strip()}" for n in m.group(2).split(",")] if m.group(2) else [])
        for n in names:
            cands = [n] + [k for k in mods if k.endswith("." + n)]
            hit = next((mods[c] for c in cands if c in mods and mods[c] != p), None)
            if hit:
                pyedges.add((p, hit)); break

adj = collections.defaultdict(set)
for a, b in edges + list(pyedges):
    adj[a].add(b)
cycles, color = [], {}
sys.setrecursionlimit(10000)
def dfs(u, stack):
    color[u] = 1; stack.append(u)
    for v in adj[u]:
        if color.get(v) == 1: cycles.append(stack[stack.index(v):] + [v])
        elif not color.get(v): dfs(v, stack)
    stack.pop(); color[u] = 2
for n in list(adj):
    if not color.get(n): dfs(n, [])

indeg = collections.Counter(b for a, b in edges)
result = {"nodes": nodes, "edges": edges, "pyedges": sorted(pyedges), "ext": {k: sorted(v) for k, v in ext.items()},
          "api_calls": api, "rpcs": rpcs, "sqlfns": sqlfns, "cycles": cycles,
          "unresolved": [e for e in edges if e[1].startswith("UNRESOLVED")],
          "fan_in": indeg.most_common(15), "fan_out": sorted(((len(v), k) for k, v in adj.items()), reverse=True)[:10]}
json.dump(result, open(out, "w"), indent=1)
print(f"{len(nodes)} nodes, {len(edges)} js edges, {len(pyedges)} py edges, {len(cycles)} cycles, {len(result['unresolved'])} unresolved")
print("fan-in:", result["fan_in"][:8])
print("fan-out:", result["fan_out"][:5])
