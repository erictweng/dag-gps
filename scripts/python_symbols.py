"""Conservative Python AST definitions and call sites. Never imports target code.

A resolved edge is static lexical/import evidence, not runtime dispatch. Additional
receiver/decorator evidence has explicit weaker tiers; unknown bindings remain unknown.
"""
import ast
import json
import re
from collections import defaultdict
from python_call_tiers import CallTiers, TIERS, decorator_metadata, weakest

DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def extract_search_text(paths, sources, symbols, budget=1024 * 1024):
    """Bounded metadata only; no comments, imports or execution of target code.

    Python AST first docstring paragraphs; other languages use names/paths only.
    Budget is encoded JSON bytes, including IDs/keys, not just text characters.
    """
    def token_text(value, cap):
        value = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', value)
        return ' '.join(re.findall(r'[a-z0-9]+', value.lower()))[:cap]

    def paragraph(node):
        value = ast.get_docstring(node) or ''
        paragraph = ' '.join(re.split(r'\n\s*\n', value, maxsplit=1)[0].split())
        return ''.join(c for c in paragraph if ord(c) >= 32)[:300]

    docs = {}
    for path, source in sources.items():
        try:
            tree = ast.parse(source, filename=path)
        except (SyntaxError, ValueError):
            continue
        docs[(path, 0)] = paragraph(tree)
        for node in ast.walk(tree):
            if isinstance(node, DEFS):
                docs[(path, node.lineno)] = paragraph(node)
    candidates = [(path, path.rsplit('/', 1)[-1], path, 0) for path in sorted(paths)]
    candidates += [(n['id'], n['qualname'], n['path'], n['start']) for n in symbols]
    result = {'schema': 'dag-gps-search-text/v1', 'nodes': {}, 'omitted': 0}
    used = 128
    for ident, name, path, line in candidates:
        value = {'name': token_text(name, 80), 'path': token_text(path, 120),
                 'docstring': docs.get((path, line), '')}
        size = len(json.dumps({ident: value}, separators=(',', ':')).encode('utf-8')) + 1
        if used + size > max(128, budget):
            result['omitted'] += 1
            continue
        used += size
        result['nodes'][ident] = value
    return result


def extract_symbols(sources, import_edges):
    observed = set(tuple(e) for e in import_edges)
    nodes, calls, diagnostics = [], [], []
    trees, scopes, definitions, mutated_attributes = {}, {}, {}, {}
    import_sites, top_level, export_dynamic, static_imports = {}, {}, set(), set()
    static_definitions = set()
    modules = defaultdict(list)
    for path in sorted(sources):
        module = path[:-3].replace('/', '.')
        if module.endswith('.__init__'):
            module = module[:-9]
        modules[module].append(path)
        try:
            trees[path] = ast.parse(sources[path], filename=path)
            top_level[path] = {id(n) for n in trees[path].body}
            def collect_static(body):
                for stmt in body:
                    if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                        static_imports.add(id(stmt))
                    elif isinstance(stmt, DEFS):
                        static_definitions.add(id(stmt))
                        collect_static(stmt.body)
            collect_static(trees[path].body)
            # A literal __all__ declaration does not change explicit named imports.
            # Do not interpret dynamic construction/mutation or star exports.
            literal_all = {id(n.targets[0]) for n in trees[path].body
                           if isinstance(n, ast.Assign) and len(n.targets) == 1
                           and isinstance(n.targets[0], ast.Name) and n.targets[0].id == '__all__'
                           and isinstance(n.value, (ast.List, ast.Tuple))
                           and all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in n.value.elts)}
            if any(isinstance(n, ast.Name) and n.id == '__all__' and id(n) not in literal_all for n in ast.walk(trees[path])):
                export_dynamic.add(path)
            mutated_attributes[path] = {ast.unparse(n) for n in ast.walk(trees[path])
                                        if isinstance(n, ast.Attribute) and isinstance(n.ctx, (ast.Store, ast.Del))}
        except (SyntaxError, ValueError) as error:
            diagnostics.append({'path': path, 'start': getattr(error, 'lineno', None),
                                'reason': 'Python parse error: ' + str(error)})

    def new_scope(parent, owner=None, cls=None):
        return {'parent': parent, 'owner': owner, 'class': cls, 'names': defaultdict(list),
                'wildcard': False, 'invocable': True, 'binding_ends': defaultdict(list)}

    def bind(scope, name, value, end=0):
        scope['names'][name].append(value)
        scope['binding_ends'][name].append(end)

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
                bind(scope, child.name, ('def', node), child.end_lineno)
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
                    if module == 'typing' and not modules.get('typing') and not value and id(child) in static_imports:
                        if isinstance(child, ast.ImportFrom) and attr == 'overload':
                            value = ('typing-overload',)
                        elif isinstance(child, ast.Import):
                            value = ('typing-module',)
                    if value and value[0] == 'import':
                        # Tuple identity distinguishes identical imports at different sites.
                        import_sites[id(value)] = (path, child, local)
                    bind(scope, local, value, child.end_lineno)
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

    def lookup(scope, name, before=None):
        while scope is not None:
            if scope['wildcard']:
                return None
            if name in scope['names']:
                # Abstain rather than reconstruct a partially executed namespace.
                # This also protects imported names bound after an annotation.
                if before is not None and any(end >= before for end in scope['binding_ends'][name]):
                    return None
                values = scope['names'][name]
                return values[0] if len(values) == 1 else None
            parent = scope['parent']
            # A method does not lexically inherit the class namespace.
            if parent and parent['class'] == parent['owner'] and parent['owner']:
                parent = parent['parent']
            scope = parent
        return None

    # A known write through ANY imported typing module alias invalidates markers
    # in that file, including from-import aliases. Do not execute target code.
    for path, tree in trees.items():
        typing_aliases = {a.asname or a.name for item in ast.walk(tree)
                          if isinstance(item, ast.Import) for a in item.names if a.name == 'typing'}
        mutated_marker = any(alias + '.overload' in mutated_attributes[path] for alias in typing_aliases)
        groups = defaultdict(list)
        for item in ast.walk(tree):
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            outer = scopes[id(item)]['parent']
            groups[(id(outer), item.name)].append(item)
            for decorator in item.decorator_list:
                value = lookup(outer, decorator.id, decorator.lineno) if isinstance(decorator, ast.Name) else None
                module = lookup(outer, decorator.value.id, decorator.lineno) if isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Name) else None
                if not mutated_marker and (value == ('typing-overload',) or (module == ('typing-module',) and isinstance(decorator, ast.Attribute) and decorator.attr == 'overload')):
                    definitions[id(item)]['overloadDeclaration'] = True
                    break
        for items in groups.values():
            declarations = [item for item in items if definitions[id(item)].get('overloadDeclaration')]
            if not declarations:
                continue
            implementations = [item for item in items if item not in declarations]
            outer = scopes[id(items[0])]['parent']
            values = outer['names'][items[0].name]
            supported = (len(implementations) == 1 and len(values) == len(items)
                         and all(id(item) in static_definitions for item in items)
                         and all(item.end_lineno < implementations[0].lineno for item in declarations))
            # Only coalesce an unconditional group with one FOLLOWING implementation.
            # Invalid groups retain an unknown binding; declaration-only names must
            # not accidentally become through-decorator call targets either.
            for item in declarations:
                values.remove(('def', definitions[id(item)]))
            if not supported:
                values.append(None)

    def exported(path, name, active=()):
        """Return a concrete definition and static initializer-import witnesses."""
        if path not in trees or (path, name) in active or len(active) >= 64:
            return None, []
        scope = scopes[id(trees[path])]
        value = lookup(scope, name)
        if value and value[0] == 'import':
            witness = import_sites[id(value)]
            _, stmt, local = witness
            if (not path.endswith('/__init__.py') or path in export_dynamic
                    or id(stmt) not in top_level[path] or not isinstance(stmt, ast.ImportFrom)
                    or not value[3] or not value[2]):
                return None, []
            result, hops = exported(value[1], value[2], active + ((path, name),))
            if result:
                return result, [{'path': path, 'start': stmt.lineno, 'end': stmt.end_lineno,
                                 'name': local, 'targetPath': value[1], 'targetName': value[2]}] + hops
            return None, []
        if active and value and value[0] == 'def':
            # Re-export endpoints must also be unconditional top-level definitions.
            if not any(id(n) in top_level[path] and definitions.get(id(n)) is value[1] for n in trees[path].body):
                return None, []
        return value, []

    def target(scope, fn, path, decorated=False, reexports=None, before=None):
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
        value = lookup(scope, fn.id, before)
        if value is None:
            return None
        if value[0] == 'self' and len(attrs) == 1:
            entries = value[1]['names'].get(attrs[0], [])
            value = entries[0] if len(entries) == 1 else None
            attrs = []
        elif value[0] == 'import':
            import_stmt = import_sites[id(value)][1]
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
            value, hops = exported(path, names[0])
            if hops and id(import_stmt) not in static_imports:
                return None
            if reexports is not None:
                reexports.extend(hops)
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
            hops = []
            destination = target(scope, tree.func, path, reexports=hops) if scope['owner'] and scope['invocable'] else None
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
            if destination and hops:
                calls[-1]['reexports'] = hops
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
            if call.get('reexports'):
                site['reexports'] = call['reexports']
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
