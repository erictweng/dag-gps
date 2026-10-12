#!/usr/bin/env python3
"""Source-check every v3-added link against the pinned v2 baseline, no target execution.

This corroborates static imports, declarations, call syntax and local receiver evidence;
it does not certify runtime dispatch, mocking or alias escape behavior.
"""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from app.context import git_dir_for


def main():
    out = Path(sys.argv[1]).resolve()
    snapshot = json.loads((out / 'snapshot.json').read_text())
    graph = snapshot['map']['symbol_graph']
    git_dir = git_dir_for(out / 'workspace/git-cache', snapshot)
    pin = snapshot['source']['commit']
    inventory = {f['path']: f for f in snapshot['inventory']}
    paths = {n['path'] for n in snapshot['map']['nodes'] if n.get('path', '').endswith('.py')}
    sources, trees = {}, {}
    for path in sorted(paths):
        raw = subprocess.check_output(['git', '--git-dir=' + str(git_dir), 'show', pin + ':' + path])
        assert hashlib.sha256(raw).hexdigest() == inventory[path]['sha256']
        sources[path] = raw.decode()
        try:
            trees[path] = ast.parse(sources[path])
        except SyntaxError:
            pass
    imports = [(e['from'], e['to']) for e in snapshot['map']['file_edges'] if e['type'] == 'import']
    # Execute only the previous extractor, never any Honcho source.
    old_tiers = types.ModuleType('python_call_tiers')
    exec(compile(subprocess.check_output(['git', 'show', 'b97d6d6:scripts/python_call_tiers.py'], cwd=ROOT), '<v2-tiers>', 'exec'), old_tiers.__dict__)
    old_symbols = {}
    with patch.dict(sys.modules, {'python_call_tiers': old_tiers}):
        exec(compile(subprocess.check_output(['git', 'show', 'b97d6d6:scripts/python_symbols.py'], cwd=ROOT), '<v2-symbols>', 'exec'), old_symbols)
    before = old_symbols['extract_symbols'](sources, imports)
    def key(edge, site):
        return (edge['from'], edge['to'], site['path'], site['start'], site['end'], site['expression'], site.get('confidence', 'resolved'))
    old = Counter(key(e, s) for e in before['edges'] for s in e['sites'])
    new = Counter(key(e, s) for e in graph['edges'] for s in e['sites'])
    remaining = new - old
    removed = list((old - new).elements())
    assert not removed, removed
    nodes = {n['id']: n for n in graph['nodes']}
    displayed = set()
    for i in range(1, 14):
        p = json.loads((out / ('packet-%d.json' % i)).read_text())
        displayed.update((e['from'], e['to']) for e in p['selectedEdges'])

    def excerpt(path, start, end):
        lines = sources[path].splitlines()
        return '\n'.join('%d: %s' % (i + 1, lines[i]) for i in range(max(0, start - 2), min(len(lines), end + 1)))

    def module_path(module, path):
        candidates = [module.replace('.', '/') + '.py', module.replace('.', '/') + '/__init__.py']
        return [p for p in candidates if p in sources and (path, p) in imports]

    def import_module(path, stmt):
        if stmt.level:
            package = path.split('/')[:-1]
            assert stmt.level <= len(package)
            module = '.'.join(package[:len(package) - stmt.level + 1] + ([stmt.module] if stmt.module else []))
        else:
            module = stmt.module or ''
        return module

    def import_target(path, stmt, alias):
        return module_path(import_module(path, stmt), path)

    def caller_import(path, call, expected_path, expected_name):
        fn, attrs = call.func, []
        while isinstance(fn, ast.Attribute):
            attrs.insert(0, fn.attr)
            fn = fn.value
        assert isinstance(fn, ast.Name)
        parents = {id(c): n for n in ast.walk(trees[path]) for c in ast.iter_child_nodes(n)}
        def owners(n):
            result = []
            while id(n) in parents:
                n = parents[id(n)]
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    result.append(id(n))
            return result
        call_owners = owners(call)
        for stmt in ast.walk(trees[path]):
            if not isinstance(stmt, (ast.Import, ast.ImportFrom)) or any(o not in call_owners for o in owners(stmt)):
                continue
            for alias in stmt.names:
                local = alias.asname or (alias.name if isinstance(stmt, ast.ImportFrom) else alias.name.split('.')[0])
                if local != fn.id:
                    continue
                if isinstance(stmt, ast.ImportFrom):
                    base = import_module(path, stmt)
                    candidates = [(base, [alias.name] + attrs), (base + '.' + alias.name, attrs)]
                else:
                    prefix = [] if alias.asname else alias.name.split('.')[1:]
                    candidates = [(alias.name, attrs[len(prefix):])] if attrs[:len(prefix)] == prefix else []
                if any(names == [expected_name] and module_path(module, path) == [expected_path] for module, names in candidates):
                    return excerpt(path, stmt.lineno, stmt.end_lineno)
        # The overload implementation may call itself directly in the same module.
        assert path == expected_path and not attrs and fn.id == expected_name, (path, call.lineno, expected_path, expected_name)
        return 'Same-module overload implementation: ' + expected_name

    rows, checked_hops = [], set()
    for edge in graph['edges']:
        sites = []
        target = nodes[edge['to']]
        definition = next(n for n in ast.walk(trees[target['path']]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.lineno == target['start'])
        for site in edge['sites']:
            ident = key(edge, site)
            if not remaining[ident]:
                continue
            remaining[ident] -= 1
            call = next(n for n in ast.walk(trees[site['path']]) if isinstance(n, ast.Call) and n.lineno == site['start'] and n.end_lineno == site['end'] and ast.unparse(n.func)[:256] == site['expression'])
            assert definition.name == target['name'] and not target.get('overloadDeclaration')
            hop_text = []
            for hop in site.get('reexports', []):
                stmt = next(n for n in trees[hop['path']].body if isinstance(n, ast.ImportFrom) and n.lineno == hop['start'])
                alias = next(a for a in stmt.names if (a.asname or a.name) == hop['name'])
                assert alias.name == hop['targetName']
                assert import_target(hop['path'], stmt, alias) == [hop['targetPath']]
                checked_hops.add((hop['path'], hop['start'], hop['name'], hop['targetPath'], hop['targetName']))
                hop_text.append(excerpt(hop['path'], hop['start'], hop['end']))
            tier = site.get('confidence', 'resolved')
            if site.get('reexports') or tier == 'resolved':
                first = site.get('reexports', [{}])[0]
                hop_text.insert(0, caller_import(site['path'], call, first.get('path', target['path']), first.get('name', target['name'])))
            if not site.get('reexports') and tier == 'resolved':
                # New direct links (without export hops) must be overload recovery.
                declarations = [n for n in graph['nodes'] if n.get('overloadDeclaration') and n['path'] == target['path'] and n['qualname'] == target['qualname']]
                assert declarations, ident
                hop_text.extend(excerpt(n['path'], n['start'] - 1, n['end']) for n in declarations)
            elif not site.get('reexports'):
                # Only the three newly inferable receiver edges at this pin.
                assert isinstance(call.func, ast.Attribute)
                assert isinstance(call.func.value, ast.Name)
                caller = nodes[edge['from']]
                owner = next(n for n in ast.walk(trees[caller['path']]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.lineno == caller['start'])
                receiver = call.func.value.id
                binding = [n for n in owner.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == receiver for t in n.targets)]
                annotations = [a for a in owner.args.args if a.arg == receiver and a.annotation is not None]
                assert binding or annotations, ident
                hop_text.extend(excerpt(caller['path'], n.lineno, n.end_lineno) for n in binding + annotations)
            sites.append(dict(site, excerpt=excerpt(site['path'], site['start'], site['end']), bindingEvidence=hop_text))
        if sites:
            rows.append({'from': edge['from'], 'to': edge['to'], 'confidence': edge['confidence'],
                         'displayed': (edge['from'], edge['to']) in displayed, 'sites': sites,
                         'definition': excerpt(target['path'], min([d.lineno for d in definition.decorator_list] + [definition.lineno]), definition.lineno + 1)})
    assert not +remaining
    report = {'before': before['counts'], 'after': graph['counts'],
              'delta': {k: graph['counts'][k] - before['counts'][k] for k in graph['counts']},
              'addedEdges': len(rows), 'addedSites': sum(len(r['sites']) for r in rows),
              'displayedAddedEdges': sum(r['displayed'] for r in rows),
              'displayedAddedSites': sum(len(r['sites']) for r in rows if r['displayed']),
              'removedSites': removed, 'sourceFilesHashVerified': len(sources),
              'distinctStaticExportBindingsChecked': len(checked_hops),
              'note': 'Every added edge/site source-corroborated; not runtime execution or repository-wide semantic accuracy.'}
    (out / 'reexport-delta.json').write_text(json.dumps(report, indent=2))
    (out / 'reexport-source-checks.json').write_text(json.dumps(rows, indent=2))
    focused = [r for r in rows if any(not s.get('reexports') and s.get('confidence', 'resolved') != 'resolved' for s in r['sites'])]
    (out / 'new-receiver-review.txt').write_text('\n\n'.join(r['from'] + ' -> ' + r['to'] + '\n' + r['definition'] + '\n' + '\n'.join(s['excerpt'] + '\n' + '\n'.join(s['bindingEvidence']) for s in r['sites']) for r in focused))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
