#!/usr/bin/env python3
"""Freeze source-checked targets without invoking either query implementation."""
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SEED = 'dag-variation-v1-20261013'
SYNONYMS = [['db', 'database'], ['config', 'configuration', 'settings'], ['msg', 'message'],
            ['auth', 'authentication'], ['repo', 'repository'], ['env', 'environment']]


def freeze():
    result = {'seed': SEED, 'design': 'phrase x target-form baseline plus one-axis-at-a-time canonical-target perturbations',
              'synonyms': SYNONYMS, 'repos': {}}
    for repo in ['honcho', 'salesroom']:
        snapshot = json.loads((ROOT / f'artifacts/question-parser/{repo}/snapshot.json').read_text())
        pin = snapshot['source']['commit']
        caches = list((ROOT / 'artifacts/question-parser/workspace/git-cache').glob(f'*-{pin}/repo.git'))
        assert len(caches) == 1
        def git(*args):
            return subprocess.check_output(['git', '--git-dir', str(caches[0]), *args])
        paths = set(git('ls-tree', '-r', '--name-only', pin).decode().splitlines())
        def rank(n):
            return hashlib.sha256((SEED + n['id']).encode()).hexdigest()
        nodes = snapshot['map']['nodes']
        symbols = snapshot['map'].get('symbol_graph', {}).get('nodes', [])
        chosen = []
        for kind, count in [('file', 30), ('layer', 15 if repo == 'honcho' else 10), ('symbol', 30 if repo == 'honcho' else 0)]:
            pool = [n for n in nodes + symbols if n['kind'] == kind and n.get('label') != '(root)']
            chosen.extend(sorted(pool, key=rank)[:count])
            assert len([n for n in chosen if n['kind'] == kind]) >= count
        # Include applicable synonym targets rather than depending on random coverage.
        for n in nodes:
            text = n.get('path', n['label'])
            stem = Path(text).stem
            if any(stem in group for group in SYNONYMS) and n not in chosen:
                chosen.append(n)
        targets = []
        for n in chosen:
            t = {k: n[k] for k in ['id', 'kind', 'label', 'path', 'name', 'qualname', 'symbolKind', 'start', 'end'] if k in n}
            if n['kind'] == 'layer':
                assert any(p.startswith(n['label'] + '/') for p in paths)
                t['sourceCheck'] = 'git tree contains folder descendants'
            else:
                assert n['path'] in paths
                content = git('show', pin + ':' + n['path'])
                t['sourceSha256'] = hashlib.sha256(content).hexdigest()
                if n['kind'] == 'symbol':
                    parsed = ast.parse(content)
                    assert any(isinstance(a, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and
                               a.name == n['name'] and a.lineno == n['start'] for a in ast.walk(parsed))
                    t['sourceCheck'] = 'AST definition name and start line at pinned commit'
                else:
                    t['sourceCheck'] = 'git blob at pinned commit'
            targets.append(t)
        known = {n['id']: n for n in nodes + symbols}
        pairs = []
        for graph, op in [(snapshot['map'], 'PATH'),
                          ({'edges': snapshot['map'].get('file_edges', [])}, 'PATH'),
                          (snapshot['map'].get('symbol_graph', {}), 'FLOW')]:
            edges = [e for e in graph.get('edges', []) if e['from'] != e['to'] and
                     known[e['from']]['kind'] == known[e['to']]['kind'] and e.get('type') != 'realtime']
            edges.sort(key=lambda e: rank({'id': e['from'] + '->' + e['to']}))
            for e in edges[:10]:
                a, b = known[e['from']], known[e['to']]
                pairs.append({'from': a['id'], 'to': b['id'], 'a': a.get('path', a['label']) if op == 'PATH' else a['id'],
                              'b': b.get('path', b['label']) if op == 'PATH' else b['id'], 'operation': op,
                              'evidence': 'observed directed graph edge'})
                for n in [a, b]:
                    if n.get('path'):
                        assert n['path'] in paths
        result['repos'][repo] = {'pin': pin, 'snapshotSha256': hashlib.sha256((ROOT / f'artifacts/question-parser/{repo}/snapshot.json').read_bytes()).hexdigest(),
                                  'targets': targets, 'pairs': pairs}
    return result


if __name__ == '__main__':
    out = ROOT / 'eval/variation_templates.json'
    if sys.argv[1:] == ['--extend-file-pairs']:
        stored = json.loads(out.read_text())
        actual = freeze()
        for repo, spec in stored['repos'].items():
            fresh = actual['repos'][repo]
            assert spec['targets'] == fresh['targets']
            assert spec['pin'] == fresh['pin'] and spec['snapshotSha256'] == fresh['snapshotSha256']
            assert all(pair in fresh['pairs'] for pair in spec['pairs'])
            spec['pairs'] = fresh['pairs']
        out.write_text(json.dumps(stored, indent=2) + '\n')
        print('Extended only source-checked file PATH pairs; targets, seed and pins unchanged')
        raise SystemExit(0)
    if sys.argv[1:] == ['--check']:
        actual = freeze()
        stored = json.loads(out.read_text())
        assert actual['repos'] == stored['repos'], 'Frozen source selection changed'
        assert actual['seed'] == stored['seed']
        print('Frozen source targets, pairs and snapshot hashes verified')
        raise SystemExit(0)
    if out.exists():
        raise SystemExit('Refusing to overwrite frozen targets; use a new version explicitly.')
    out.write_text(json.dumps(freeze(), indent=2) + '\n')
    print(out)
