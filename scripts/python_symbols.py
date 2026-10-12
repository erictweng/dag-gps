"""Conservative Python AST definitions and call sites. Never imports target code.

A resolved edge is legacy lexical evidence, not runtime dispatch. Additional
receiver/decorator evidence has explicit weaker tiers; unknown bindings remain unknown.
"""
import ast
from collections import defaultdict
from python_call_tiers import CallTiers, TIERS, decorator_metadata, weakest

DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def extract_symbols(sources, import_edges):
    observed = set(tuple(e) for e in import_edges)
    nodes, calls, diagnostics = [], [], []
    trees, scopes, definitions, mutated_attributes = {}, {}, {}, {}
    modules = defaultdict(list)
    for path in sorted(sources):
        module = path[:-3].replace('/', '.')
        if module.endswith('.__init__'):
            module = module[:-9]
        modules[module].append(path)
        try:
            trees[path] = ast.parse(sources[path], filename=path)
            mutated_attributes[path] = {ast.unparse(n) for n in ast.walk(trees[path])
                                        if isinstance(n, ast.Attribute) and isinstance(n.ctx, (ast.Store, ast.Del))}
        except (SyntaxError, ValueError) as error:
            diagnostics.append({'path': path, 'start': getattr(error, 'lineno', None),
                                'reason': 'Python parse error: ' + str(error)})

    def new_scope(parent, owner=None, cls=None):
        return {'parent': parent, 'owner': owner, 'class': cls, 'names': defaultdict(list),
                'wildcard': False, 'invocable': True}

    def bind(scope, name, value):
        scope['names'][name].append(value)

    def collect(tree, path, scope, prefix=''):
        for child in tree if isinstance(tree, list) else ast.iter_child_nodes(tree):
            if isinstance(child, DEFS):
                qualname = prefix + child.name
                ident = path + '#' + qualname + '@' + str(child.lineno)
                node = {'id': ident, 'kind': 'symbol', 'symbolKind': 'class' if isinstance(child, ast.ClassDef) else
                        'async-function' if isinstance(child, ast.AsyncFunctionDef) else 'function',
                        'name': child.name, 'qualname': qualname, 'label': qualname,
                        'path': path, 'start': child.lineno, 'end': child.end_lineno,
                        'parentId': scope['owner'], 'decorated': bool(child.decorator_list)}
                nodes.append(node)
                decorators, entry = decorator_metadata(child)
                if decorators:
                    node['decorators'] = decorators
                if entry:
                    node['entryPoint'] = entry
                definitions[id(child)] = node
                bind(scope, child.name, ('def', node))
                is_class = isinstance(child, ast.ClassDef)
                nested = new_scope(scope, ident, ident if is_class else scope['class'])
                nested['invocable'] = not is_class
                scopes[id(child)] = nested
                if not is_class:
                    args = child.args
                    for arg in args.posonlyargs + args.args + args.kwonlyargs:
                        bind(nested, arg.arg, None)
                    for arg in (args.vararg, args.kwarg):
                        if arg:
                            bind(nested, arg.arg, None)
                    # Only a literal first self parameter of an undecorated method.
                    positional = args.posonlyargs + args.args
                    if scope['class'] == scope['owner'] and positional and positional[0].arg == 'self' and not child.decorator_list:
                        nested['names']['self'] = [('self', scope)]
                # Defaults, decorators, bases and annotations bind in the defining
                # scope. Only the body and parameters belong to the new scope.
                for field, value in ast.iter_fields(child):
                    items = value if isinstance(value, list) else [value]
                    items = [item for item in items if isinstance(item, ast.AST)]
                    collect(items, path,
                            nested if field == 'body' else scope,
                            qualname + ('.' if is_class else '.<locals>.') if field == 'body' else prefix)
            elif isinstance(child, (ast.Import, ast.ImportFrom)):
                package = path.rpartition('/')[0].replace('/', '.')
                if isinstance(child, ast.ImportFrom):
                    if child.level:
                        parts = package.split('.') if package else []
                        base = '.'.join(parts[:len(parts) - child.level + 1]) if child.level <= len(parts) else ''
                        base += ('.' if base and child.module else '') + (child.module or '')
                    else:
                        base = child.module or ''
                    entries = [(a.asname or a.name, base, a.name) for a in child.names]
                else:
                    entries = [(a.asname or a.name.split('.')[0], a.name,
                                '' if a.asname else a.name.partition('.')[2]) for a in child.names]
                for local, module, attr in entries:
                    if local == '*':
                        scope['wildcard'] = True
                        continue
                    candidates = []
                    submodule = None
                    for candidate in (module, (package + '.' + module).strip('.')):
                        child_hits = modules.get(candidate + '.' + attr, []) if isinstance(child, ast.ImportFrom) else []
                        if len(child_hits) == 1 and (path, child_hits[0]) in observed:
                            submodule = child_hits[0]
                            break
                        hits = modules.get(candidate, [])
                        if len(hits) == 1 and (path, hits[0]) in observed:
                            candidates.append(hits[0])
                            break
                    value = ('import', candidates[0], attr, isinstance(child, ast.ImportFrom)) if candidates else None
                    if submodule:
                        value = ('import', submodule, '', False)
                    bind(scope, local, value)
            else:
                if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                    bind(scope, child.id, None)
                if isinstance(child, (ast.Global, ast.Nonlocal)):
                    for name in child.names:
                        bind(scope, name, None)
                if isinstance(child, ast.ExceptHandler) and child.name:
                    bind(scope, child.name, None)
                collect(child, path, scope, prefix)

    for path, tree in trees.items():
        scope = new_scope(None)
        scopes[id(tree)] = scope
        collect(tree, path, scope)

    def lookup(scope, name):
        while scope is not None:
            if scope['wildcard']:
                return None
            if name in scope['names']:
                values = scope['names'][name]
                return values[0] if len(values) == 1 else None
            parent = scope['parent']
            # A method does not lexically inherit the class namespace.
            if parent and parent['class'] == parent['owner'] and parent['owner']:
                parent = parent['parent']
            scope = parent
        return None

    def target(scope, fn, path, decorated=False):
        # File-wide invalidation is intentionally conservative: do not pretend an
        # assigned callback is still the class/module definition of that name.
        if ast.unparse(fn) in mutated_attributes[path]:
            return None
        attrs = []
        while isinstance(fn, ast.Attribute):
            attrs.insert(0, fn.attr)
            fn = fn.value
        if not isinstance(fn, ast.Name):
            return None
        value = lookup(scope, fn.id)
        if value is None:
            return None
        if value[0] == 'self' and len(attrs) == 1:
            entries = value[1]['names'].get(attrs[0], [])
            value = entries[0] if len(entries) == 1 else None
            attrs = []
        elif value[0] == 'import':
            _, path, attr, from_import = value
            if from_import:
                names = [attr] + attrs
            else:
                prefix = attr.split('.') if attr else []
                if attrs[:len(prefix)] != prefix:
                    return None
                names = attrs[len(prefix):]
            if len(names) != 1 or path not in trees:
                return None
            value = lookup(scopes[id(trees[path])], names[0])
            attrs = []
        if value and value[0] == 'def' and not attrs and (decorated or not value[1]['decorated']):
            return value[1]['id']
        return None

    tiers = CallTiers(trees, scopes, definitions, target, lookup, mutated_attributes)

    def walk(tree, path, scope):
        if isinstance(tree, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            outer = scope
            scope = new_scope(outer, outer['owner'], outer['class'])
            scope['invocable'] = outer['invocable'] and not isinstance(tree, (ast.Lambda, ast.GeneratorExp))
            for item in ast.walk(tree):
                if isinstance(item, ast.arg):
                    bind(scope, item.arg, None)
                elif isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                    bind(scope, item.id, None)
        if isinstance(tree, DEFS):
            # Decorators/defaults/bases run in the outer scope, not the body.
            for field, value in ast.iter_fields(tree):
                if field == 'body':
                    for item in value:
                        walk(item, path, scopes[id(tree)])
                elif isinstance(value, ast.AST):
                    walk(value, path, scope)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, ast.AST):
                            walk(item, path, scope)
            return
        if isinstance(tree, ast.Call):
            destination = target(scope, tree.func, path) if scope['owner'] and scope['invocable'] else None
            confidence = 'resolved' if destination else 'unresolved'
            if destination is None and scope['owner'] and scope['invocable']:
                inferred = tiers.infer(tree, scope, path)
                if inferred:
                    destination, confidence = inferred
            calls.append({'from': scope['owner'], 'to': destination,
                          'confidence': confidence,
                          'path': path, 'start': tree.lineno, 'end': tree.end_lineno,
                          'expression': ast.unparse(tree.func)[:256],
                          'reason': 'Lexically bound definition' if destination else 'No unique supported lexical target; runtime dispatch not inferred'})
        for child in ast.iter_child_nodes(tree):
            walk(child, path, scope)

    for path, tree in trees.items():
        walk(tree, path, scopes[id(tree)])
    edges = {}
    legacy_unknown = 0
    additions = []
    for call in calls:
        if call['confidence'] != 'resolved':
            if call['to']:
                additions.append((legacy_unknown, call))
            else:
                legacy_unknown += 1
        if call['to']:
            key = (call['from'], call['to'])
            edge = edges.setdefault(key, {'from': key[0], 'to': key[1], 'type': 'call',
                                         'confidence': 'resolved', 'sites': []})
            site = {k: call[k] for k in ('path', 'start', 'end', 'expression')}
            if call['confidence'] != 'resolved':
                site['confidence'] = call['confidence']
            edge['sites'].append(site)
            edge['confidence'] = weakest([edge['confidence'], call['confidence']])
            if tiers.by_id[call['to']].get('decorators'):
                edge['decorators'] = tiers.by_id[call['to']]['decorators']
    unresolved = [c for c in calls if not c['to']]
    ordered_edges = [edges[key] for key in sorted(edges)]
    edge_indices = {key: index for index, key in enumerate(sorted(edges))}
    site_indices = defaultdict(int)
    compact_additions = []
    # Reference existing site evidence instead of copying large unresolved records.
    for before, call in additions:
        key = (call['from'], call['to'])
        sites = edges[key]['sites']
        index = site_indices[key]
        while sites[index].get('confidence', 'resolved') == 'resolved':
            index += 1
        compact_additions.append([before, edge_indices[key], index])
        site_indices[key] = index + 1
    return {'schema': 'dag-gps-symbols/v1', 'nodes': nodes,
            'edges': ordered_edges, 'unresolved': unresolved,
            'diagnostics': diagnostics, 'certainAdditions': compact_additions,
            'counts': dict({'symbols': len(nodes), 'unresolved': len(unresolved),
                            'entryPoints': sum(bool(n.get('entryPoint')) for n in nodes)},
                           **{tier: sum(c['confidence'] == tier for c in calls) for tier in TIERS})}
