#!/usr/bin/env python3
"""Extract a module graph from a TS/JS + Python repo snapshot.

Usage: import_graph.py <src_dir> <out.json> [top-level dirs/files ...]
Default tops: app components lib src pages proxy.ts middleware.ts scripts browser-runtime
Output: nodes{path:{lines,client}}, edges, pyedges, ext, api_calls, rpcs, sqlfns, cycles, unresolved, fan_in, fan_out.
"""
import os, re, sys, json, glob, collections, ast
from build_map import included
from python_static import static_paths
from python_symbols import extract_symbols, extract_search_text

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

def jsonc(text):
    """Remove JSONC comments/trailing commas without touching quoted strings."""
    tokens = r'"(?:\\.|[^"\\])*"|/\*[\s\S]*?\*/|//[^\r\n]*'
    text = re.sub(tokens, lambda m: m[0] if m[0].startswith('"') else
                  re.sub(r'[^\r\n]', ' ', m[0]), text)
    return json.loads(re.sub(r'"(?:\\.|[^"\\])*"|,\s*(?=[}\]])',
                             lambda m: m[0] if m[0].startswith('"') else '', text))


config_issues = []
repo_root = os.path.realpath('.')


def local_path(path):
    """Never inspect config or targets outside the pinned repository."""
    return os.path.commonpath([repo_root, os.path.realpath(path)]) == repo_root


def load_tsconfig(path, chain=()):
    path = os.path.normpath(path)
    if not local_path(path) or path in chain or len(chain) >= 64:
        config_issues.append([path, 'TypeScript config unsupported', 'outside repository, cycle or depth limit'])
        return {}
    try:
        with open(path, encoding='utf-8-sig') as handle:
            data = jsonc(handle.read())
        if not isinstance(data, dict):
            raise ValueError('config must be an object')
        options = data.get('compilerOptions', {})
        if not isinstance(options, dict):
            raise ValueError('compilerOptions must be an object')
    except (OSError, ValueError) as exc:
        config_issues.append([path, 'TypeScript config unreadable', str(exc)])
        return {}
    result = {}
    parents = data.get('extends', [])
    parents = [parents] if isinstance(parents, str) else parents
    if not isinstance(parents, list):
        parents = []
        config_issues.append([path, 'TypeScript config unsupported', 'invalid extends'])
    for parent in parents:
        if not isinstance(parent, str) or not parent.startswith(('./', '../')):
            config_issues.append([path, 'TypeScript config unsupported', 'non-relative extends'])
            continue
        target = os.path.normpath(os.path.join(os.path.dirname(path), parent))
        if not os.path.isfile(target) and not target.endswith('.json'):
            target += '.json'
        result.update(load_tsconfig(target, chain + (path,)))
    if isinstance(options.get('baseUrl'), str):
        result['baseUrl'] = os.path.normpath(os.path.join(os.path.dirname(path), options['baseUrl']))
    if isinstance(options.get('paths'), dict):
        # paths replaces, rather than merges, the inherited table. With no baseUrl,
        # its relative targets belong to the config that declared that table.
        result['paths'] = options['paths']
        result['pathsOrigin'] = os.path.dirname(path)
    return result


tsconfig = next((p for p in ('tsconfig.json', 'jsconfig.json') if os.path.isfile(p)), None)
tsoptions = load_tsconfig(tsconfig) if tsconfig else {}


def resolve_candidate(base):
    base = os.path.normpath(base)
    for c in [base] + [base + e for e in EXTS] + [os.path.join(base, "index" + e) for e in EXTS]:
        if local_path(c) and os.path.isfile(c):
            return c


def resolve(f, spec):
    if spec.startswith('.'):
        return resolve_candidate(os.path.join(os.path.dirname(f), spec)) or "UNRESOLVED:" + spec
    paths = tsoptions.get('paths', {})
    matches = []
    for pattern, targets in paths.items():
        if pattern == spec:
            matches.append((True, len(pattern), pattern, '', targets))
        elif pattern.count('*') == 1:
            prefix, suffix = pattern.split('*')
            if spec.startswith(prefix) and spec.endswith(suffix) and len(spec) >= len(prefix) + len(suffix):
                matches.append((False, len(prefix), pattern, spec[len(prefix):len(spec) - len(suffix) if suffix else None], targets))
    if matches:
        # Stable ties retain declaration order, as TypeScript does.
        _, _, pattern, star, targets = max(matches, key=lambda m: m[:2])
        origin = tsoptions.get('baseUrl', tsoptions.get('pathsOrigin', ''))
        for target in targets if isinstance(targets, list) else []:
            if isinstance(target, str) and target.count('*') <= 1:
                found = resolve_candidate(os.path.join(origin, target.replace('*', star)))
                if found:
                    return found
        return "UNRESOLVED:" + spec
    if 'baseUrl' in tsoptions and not os.path.isabs(spec):
        found = resolve_candidate(os.path.join(tsoptions['baseUrl'], spec))
        if found:
            return found
    if not spec.startswith('@/'):
        return None
    found = resolve_candidate(spec[2:])
    if found:
        return found
    return "UNRESOLVED:" + spec

imp = re.compile(r"""\b(?:import|export)\s[^'";]*?from\s*['"]([^'"]+)['"]|\bimport\s*\(\s*['"]([^'"]+)['"]\s*\)|\bimport\s+['"]([^'"]+)['"]""", re.M)
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


def code_matches(pattern, text, mask):
    """Keep normal non-overlapping matches; retry masked starts without consuming code."""
    pos = 0
    while (match := pattern.search(text, pos)) is not None:
        if mask[match.start()]:
            yield match
            pos = match.end()
        else:
            pos = match.start() + 1
            while pos < len(mask) and not mask[pos]:
                pos += 1


require_re = re.compile(r"""\brequire\s*\(\s*['"]([^'"]+)['"]\s*\)""")
unsupported = list(config_issues)
nodes, edges, ext, api, rpcs = {}, [], {}, {}, {}
for f in sorted(files):
    t = open(f, encoding="utf-8", errors="ignore").read()
    nodes[f] = {"lines": t.count("\n"), "client": "use client" in t[:200]}
    mask = code_mask(t)
    specs = [m.group(1) or m.group(2) or m.group(3) for m in code_matches(imp, t, mask)] + [m.group(1) for m in code_matches(require_re, t, mask)]
    for m in code_matches(re.compile(r"\b(require|import)\s*\(\s*([^)]*)\)"), t, mask):
        if not re.fullmatch(r"[\'\"][^\'\"]+[\'\"]", m.group(2).strip()):
            unsupported.append([f, "nonliteral " + m.group(1), m.group(2).strip()[:160]])
    for spec in specs:
        r = resolve(f, spec)
        if r is None:
            ext.setdefault(f, set()).add(spec if spec.startswith('/') else "/".join(spec.split("/")[:2]) if spec.startswith("@") else spec.split("/")[0])
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
mods = collections.defaultdict(list)
for p in py:
    name = p[:-3].replace('/', '.')
    name = name.removesuffix('.__init__')
    mods[name].append(p)
# Namespace packages have no source node. Their concrete submodules still resolve.
namespaces = {'.'.join(p.split('/')[:i]) for p in py for i in range(1, len(p.split('/')))}
pyedges = set()
static_loader_edges = set()
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
    path_insertions, loader_paths = static_paths(tree, p)

    def link(name, skip_self=False):
        hits = mods.get(name, [])
        if len(hits) > 1:
            pyunresolved.append([p, 'UNRESOLVED:ambiguous Python ' + name])
            return True  # Known local, but never select an arbitrary target.
        if hits:
            if not skip_self or hits[0] != p:
                pyedges.add((p, hits[0]))
            return True
        return name in namespaces

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            loader = loader_paths.get(node)
            if loader is not None and loader in py:
                if loader != p:
                    pyedges.add((p, loader))
                    static_loader_edges.add((p, loader))
            elif (isinstance(fn, ast.Name) and fn.id in ('__import__', 'spec_from_file_location')) or (isinstance(fn, ast.Attribute) and fn.attr in ('import_module', 'spec_from_file_location')):
                unsupported.append([p, 'dynamic Python import', ast.unparse(node)[:160]])
            if ast.unparse(fn) in ('sys.path.insert', 'sys.path.append', 'sys.path.extend') and not any(line == node.lineno for line, directory in path_insertions):
                unsupported.append([p, 'Python search path not modeled', ast.unparse(node)[:160]])
        if not isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        relative = isinstance(node, ast.ImportFrom) and node.level > 0
        if relative:
            parts = package.split('.') if package else []
            if node.level > len(parts):
                pyunresolved.append([p, 'UNRESOLVED:relative Python beyond package ' + ast.unparse(node)])
                continue
            prefix = '.'.join(parts[:len(parts) - node.level + 1])
            names = [prefix + ('.' + node.module if node.module else '')]
        else:
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
        for name in names:
            chosen = name
            if not relative:
                for line, directory in reversed(path_insertions):
                    candidate = (directory.replace('/', '.') + '.' + name).lstrip('.')
                    if line < node.lineno and (candidate in mods or candidate in namespaces):
                        chosen = candidate
                        break
            # Repo-root module first, then documented same-directory script mode.
            if not relative and chosen == name and name not in mods and name not in namespaces and package:
                local = package + '.' + name
                if local in mods or local in namespaces:
                    chosen = local
            known = link(chosen, skip_self=relative and node.module is None)
            if isinstance(node, ast.ImportFrom) and known:
                for alias in node.names:
                    if alias.name != '*':
                        child = chosen + '.' + alias.name
                        found = link(child)  # A symbol without a real module never invents an edge.
                        if not found and chosen in namespaces and chosen not in mods:
                            pyunresolved.append([p, 'UNRESOLVED:missing namespace submodule ' + child])
            if not known:
                if relative or name.split('.')[0] in namespaces or name.split('.')[0] in mods:
                    pyunresolved.append([p, 'UNRESOLVED:missing local Python ' + chosen])
                else:
                    suffixes = sorted(k for k in mods if k.endswith('.' + name))
                    if len(suffixes) > 1:
                        pyunresolved.append([p, 'UNRESOLVED:ambiguous Python ' + name])
                    elif suffixes:
                        unsupported.append([p, 'Python search path not modeled', name + ' could refer to ' + suffixes[0] + '; no suffix guessing'])
                    ext.setdefault(p, set()).add(name.split('.')[0])

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
result = {"nodes": nodes, "edges": edges, "pyedges": sorted(pyedges), "static_loader_edges": sorted(static_loader_edges), "ext": {k: sorted(v) for k, v in ext.items()},
          "api_calls": api, "rpcs": rpcs, "sqlfns": sqlfns, "cycles": cycles,
          "unresolved": sorted([e for e in edges if e[1].startswith("UNRESOLVED")] + pyunresolved),
          "unsupported": sorted(unsupported),
          "fan_in": indeg.most_common(15), "fan_out": sorted(((len(v), k) for k, v in adj.items()), reverse=True)[:10]}
python_sources = {p: open(p, encoding='utf-8', errors='replace').read() for p in py}
result['symbol_graph'] = extract_symbols(python_sources, pyedges)
# Leave the existing 16 MiB sidecar bound intact, including all JSON overhead.
remaining = 16 * 1024 * 1024 - len(json.dumps(result, separators=(',', ':')).encode('utf-8')) - 256
if remaining >= 128:
    result['search_text'] = extract_search_text(nodes, python_sources, result['symbol_graph']['nodes'],
                                               budget=min(1024 * 1024, remaining))
# The bounded extractor sidecar is machine-read; whitespace need not consume its budget.
json.dump(result, open(out, "w"), separators=(',', ':'))
print(f"{len(nodes)} nodes, {len(edges)} js edges, {len(pyedges)} py edges, {len(cycles)} cycles, {len(result['unresolved'])} unresolved")
print("fan-in:", result["fan_in"][:8])
print("fan-out:", result["fan_out"][:5])
