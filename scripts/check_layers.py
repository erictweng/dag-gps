#!/usr/bin/env python3
"""Draft check for a hand-drawn layer map: glob coverage + layer rollup of the import graph.

Usage: check_layers.py <layers.json> <repo_dir> <git_ref> <import_graph.json> [out.mmd]
Prints unmapped / double-mapped files, files per layer, rolled-up layer edges, 2-cycles.
Writes a Mermaid flowchart of the rolled-up DAG (import edges solid, manual edges dashed).
"""
import collections, fnmatch, json, subprocess, sys

layers_path, repo, ref, graph_path = sys.argv[1:5]
mmd_path = sys.argv[5] if len(sys.argv) > 5 else None
spec = json.load(open(layers_path))
layers = spec["layers"]
files = [
    f for f in subprocess.check_output(["git", "-C", repo, "ls-tree", "-r", "--name-only", ref], text=True).split()
    if f.rsplit(".", 1)[-1] in ("ts", "tsx", "js", "mjs", "py", "sql")
]


def match(f, g):
    if g.endswith("/**"):
        return f.startswith(g[:-2])
    return fnmatch.fnmatchcase(f, g) and f.count("/") == g.count("/")


owner = {f: [l["id"] for l in layers if any(match(f, g) for g in l["globs"])] for f in files}
unmapped = [f for f, o in owner.items() if not o]
double = {f: o for f, o in owner.items() if len(o) > 1}
counts = collections.Counter(o[0] for o in owner.values() if o)
print(f"files {len(files)} unmapped {len(unmapped)} double {len(double)}")
for f in unmapped:
    print("  UNMAPPED", f)
for f, o in double.items():
    print("  DOUBLE", f, o)
print("per layer:", dict(counts))
print("empty layers:", [l["id"] for l in layers if l["id"] not in counts])

layer_of = {f: o[0] for f, o in owner.items() if o}
edges = collections.Counter()
for a, b in json.load(open(graph_path))["edges"]:
    la, lb = layer_of.get(a), layer_of.get(b)
    if la and lb and la != lb:
        edges[(la, lb)] += 1
for (a, b), n in sorted(edges.items()):
    print(f"  {a} -> {b}: {n}")
cycles = sorted({tuple(sorted(k)) for k in edges if (k[1], k[0]) in edges})
print("2-cycles:", cycles)

if mmd_path:
    out = ["flowchart TD"]
    for l in layers:
        out.append(f'  {l["id"].replace("-", "_")}["{l["label"]}<br/>{counts.get(l["id"], 0)} files"]')
    for (a, b), n in sorted(edges.items()):
        out.append(f'  {a.replace("-", "_")} -->|{n}| {b.replace("-", "_")}')
    for e in spec.get("manual_edges", []):
        out.append(f'  {e["from"].replace("-", "_")} -.->|{e["type"]}| {e["to"].replace("-", "_")}')
    open(mmd_path, "w").write("\n".join(out) + "\n")
    print("wrote", mmd_path)
