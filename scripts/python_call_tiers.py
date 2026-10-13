"""Additional, explicitly uncertain Python call evidence; no runtime evaluation.

Keep the legacy lexical resolver separate so certain-only queries remain reproducible.
Bindings must be single-assignment direct statements, never captured by nested code.
"""
import ast
from collections import Counter

TIERS = ('resolved', 'instance-local', 'typed', 'through-decorator')


def weakest(tiers):
    return max(tiers, key=TIERS.index)


def decorator_metadata(tree):
    names = [ast.unparse(d)[:512] for d in tree.decorator_list]
    # Registration is metadata, not an implicit invocation of the handler.
    registration = {'get', 'post', 'put', 'patch', 'delete', 'route', 'websocket',
                    'task', 'shared_task', 'job', 'scheduled_job', 'on_event', 'command'}
    entry = []
    for d, text in zip(tree.decorator_list, names):
        fn = d.func if isinstance(d, ast.Call) else d
        name = ast.unparse(fn)
        if name.split('.')[-1] in registration or name.startswith(('app.', 'router.', 'scheduler.')):
            entry.append(text)
    return names, entry


class CallTiers:
    def __init__(self, trees, scopes, definitions, resolve, lookup, mutated):
        self.scopes, self.resolve, self.lookup, self.mutated = scopes, resolve, lookup, mutated
        self.by_id = {n['id']: n for n in definitions.values()}
        self.syntax, self.paths = {}, {}
        self.parents = {}
        for path, tree in trees.items():
            for item in ast.walk(tree):
                for child in ast.iter_child_nodes(item):
                    self.parents[id(child)] = item
                if id(item) in definitions:
                    ident = definitions[id(item)]['id']
                    self.syntax[ident], self.paths[ident] = item, path
        self.mro_cache = {}
        self.method_writes = {}
        self.bindings, self.attributes = {}, {}
        for ident, tree in self.syntax.items():
            if isinstance(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.bindings[ident] = self.local_bindings(tree, scopes[id(tree)], self.paths[ident])
        for ident, tree in self.syntax.items():
            if isinstance(tree, ast.ClassDef):
                self.attributes[ident] = self.init_attributes(tree, self.paths[ident])
                self.method_writes[ident] = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                                            and isinstance(n.ctx, (ast.Store, ast.Del))}
        for path, tree in trees.items():
            for item in ast.walk(tree):
                if isinstance(item, ast.Attribute) and isinstance(item.ctx, (ast.Store, ast.Del)):
                    parent = item
                    while id(parent) not in scopes:
                        parent = self.parents[id(parent)]
                    cls = self.class_target(item.value, scopes[id(parent)], path)
                    if cls:
                        self.method_writes[cls].add(item.attr)

    def class_target(self, expr, scope, path, before=None):
        if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
            try:
                expr = ast.parse(expr.value, mode='eval').body
            except (SyntaxError, ValueError):
                return None
        ident = self.resolve(scope, expr, path, before=before)
        node = self.by_id.get(ident)
        return ident if node and node['symbolKind'] == 'class' else None

    def candidate(self, stmt, scope, path):
        value = getattr(stmt, 'value', None)
        if isinstance(value, ast.Call):
            cls = self.class_target(value.func, scope, path)
            if cls:
                return cls, 'instance-local'
        if isinstance(stmt, ast.AnnAssign):
            cls = self.class_target(stmt.annotation, scope, path)
            if cls:
                return cls, 'typed'
        return None

    def local_bindings(self, tree, scope, path):
        found = {}
        # Existing collector counts all writes (including branches, loops, del,
        # walrus, except, global/nonlocal). A second binding invalidates the name.
        captured = set()
        for item in ast.walk(tree):
            if item is not tree and isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.GeneratorExp)):
                captured.update(n.id for n in ast.walk(item) if isinstance(n, ast.Name))
        def unique(name):
            return name not in captured and not scope['wildcard'] and len(scope['names'].get(name, [])) == 1
        for arg in tree.args.posonlyargs + tree.args.args + tree.args.kwonlyargs:
            if arg.annotation is not None and unique(arg.arg):
                # Annotations belong to the definition's enclosing namespace,
                # including an immediate class namespace, not function locals.
                outer = scope['parent']
                # A class body is sequential: a later binding is not available to
                # this method's annotation. Strings/postponed annotations use the
                # same conservative guard; we do not emulate their evaluation.
                before = tree.lineno if outer['class'] == outer['owner'] and outer['owner'] else None
                cls = self.class_target(arg.annotation, outer, path, before=before)
                if cls:
                    found[arg.arg] = (cls, 'typed', tree.lineno)
        for stmt in tree.body:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target] if isinstance(stmt, ast.AnnAssign) else []
            if len(targets) != 1 or not isinstance(targets[0], ast.Name) or not unique(targets[0].id):
                continue
            value = self.candidate(stmt, scope, path)
            if value:
                found[targets[0].id] = (*value, stmt.end_lineno)
        return found

    def init_attributes(self, tree, path):
        writes = Counter(n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                         and isinstance(n.ctx, (ast.Store, ast.Del)))
        result = {}
        initializers = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == '__init__']
        if len(initializers) != 1 or initializers[0].decorator_list:
            return result
        init = initializers[0]
        scope = self.scopes[id(init)]
        value = self.lookup(scope, 'self')
        if not value or value[0] != 'self':
            return result
        for stmt in init.body:
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target] if isinstance(stmt, ast.AnnAssign) else []
            if len(targets) != 1:
                continue
            dest = targets[0]
            if not (isinstance(dest, ast.Attribute) and isinstance(dest.value, ast.Name) and dest.value.id == 'self' and writes[dest.attr] == 1):
                continue
            if isinstance(getattr(stmt, 'value', None), ast.Call):
                cls = self.class_target(stmt.value.func, scope, path)
                if cls:
                    result[dest.attr] = (cls, stmt.end_lineno)
        return result

    def mro(self, cls, active=()):
        if cls in self.mro_cache:
            return self.mro_cache[cls]
        if cls in active:
            return None
        tree, path = self.syntax[cls], self.paths[cls]
        scope = self.scopes[id(tree)]['parent']
        bases = []
        for expr in tree.bases:
            if isinstance(expr, ast.Name) and expr.id == 'object' and self.lookup(scope, 'object') is None:
                continue
            base = self.class_target(expr, scope, path)
            if not base:
                return None
            bases.append(base)
        seqs = []
        for base in bases:
            order = self.mro(base, active + (cls,))
            if order is None:
                return None
            seqs.append(list(order))
        seqs.append(bases[:])
        result = [cls]
        while any(seqs):
            seqs = [s for s in seqs if s]
            head = next((s[0] for s in seqs if all(s[0] not in other[1:] for other in seqs)), None)
            if head is None:
                return None
            result.append(head)
            for seq in seqs:
                if seq[0] == head:
                    seq.pop(0)
        self.mro_cache[cls] = result
        return result

    def method(self, cls, name):
        # Raw AST private names do not describe the runtime mangled attribute.
        # Keep protocol dunders, but abstain until caller-class mangling is modeled.
        if name.startswith('__') and not name.endswith('__'):
            return None
        # Own methods are knowable even with an external base. Inherited lookup
        # requires a complete C3 MRO; unknown/ambiguous bases never get skipped.
        own = self.scopes[id(self.syntax[cls])]['names'].get(name)
        if name in self.method_writes.get(cls, set()):
            return None
        order = [cls] if own else self.mro(cls)
        for parent in order or []:
            if name in self.method_writes.get(parent, set()):
                return None
            values = self.scopes[id(self.syntax[parent])]['names'].get(name)
            if values:
                if len(values) != 1 or values[0] is None or values[0][0] != 'def':
                    return None
                node = values[0][1]
                return node['id'] if node['symbolKind'] != 'class' else None
        return None

    def infer(self, call, scope, path):
        fn = call.func
        if ast.unparse(fn) in self.mutated[path]:
            return None
        direct = self.resolve(scope, fn, path, decorated=True)
        if direct:
            return direct, 'through-decorator'
        if not isinstance(fn, ast.Attribute):
            return None
        receiver, cls, tier = fn.value, None, None
        if isinstance(receiver, ast.Name):
            binding = self.bindings.get(scope['owner'], {}).get(receiver.id)
            # Do not reuse the enclosing function's inference in a comprehension.
            owner_tree = self.syntax.get(scope['owner'])
            if binding and owner_tree and scope is self.scopes[id(owner_tree)] and call.lineno > binding[2]:
                cls, tier = binding[:2]
        elif isinstance(receiver, ast.Attribute) and isinstance(receiver.value, ast.Name) and receiver.value.id == 'self':
            value = self.lookup(scope, 'self')
            if value and value[0] == 'self' and scope['parent'] is value[1]:
                held = self.attributes.get(scope['class'], {}).get(receiver.attr)
                if held:
                    owner = self.syntax[scope['owner']]
                    if owner.name != '__init__' or call.lineno > held[1]:
                        cls, tier = held[0], 'instance-local'
        dest = self.method(cls, fn.attr) if cls else None
        if dest:
            return dest, weakest([tier, 'through-decorator']) if self.by_id[dest]['decorated'] else tier
        return None
