"""Narrow, non-evaluating __file__-relative path syntax used by pinned demos.

Not arbitrary Python execution or importlib resolution. Only unconditional top-level
assignments/sys.path.insert(0, ...) and explicit loader file paths are recognized.
"""
import ast
import os


def static_paths(tree, source):
    values = {'__file__': os.path.abspath(source)}
    insertions = []

    def path(node):
        if isinstance(node, ast.Name):
            return values.get(node.id)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
            a, b = path(node.left), path(node.right)
            return os.path.join(a, b) if a is not None and b is not None else None
        if isinstance(node, ast.Attribute) and node.attr == 'parent':
            a = path(node.value)
            return os.path.dirname(a) if a is not None else None
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == 'parents' and isinstance(node.slice, ast.Constant) and type(node.slice.value) is int and 0 <= node.slice.value <= 8:
            a = path(node.value.value)
            if a is not None:
                for _ in range(node.slice.value + 1):
                    a = os.path.dirname(a)
                return a
        if isinstance(node, ast.Call) and not node.keywords:
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'resolve' and not node.args:
                a = path(node.func.value)
                return os.path.abspath(a) if a is not None else None
            fn = ast.unparse(node.func)
            args = [path(a) for a in node.args]
            if any(a is None for a in args):
                return None
            if fn in ('pathlib.Path', 'Path', 'os.path.abspath') and len(args) == 1:
                return os.path.abspath(args[0])
            if fn == 'str' and len(args) == 1:
                return args[0]
            if fn == 'os.path.dirname' and len(args) == 1:
                return os.path.dirname(args[0])
            if fn == 'os.path.join' and args:
                return os.path.join(*args)
        return None

    def relative(value):
        if value is None or not os.path.isabs(value):
            return None
        rel = os.path.relpath(value)
        return rel if rel != '..' and not rel.startswith('../') else None

    loaders = {}
    for node in tree.body:
        if isinstance(node, (ast.Expr, ast.Assign)) and isinstance(node.value, ast.Call):
            call = node.value
            if ast.unparse(call.func) in ('importlib.util.spec_from_file_location', 'spec_from_file_location') and len(call.args) >= 2:
                loaders[call] = relative(path(call.args[1]))
        if isinstance(node, ast.Assign):
            result = path(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    values.pop(target.id, None)
                    if result is not None:
                        values[target.id] = result
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            call = node.value
            if ast.unparse(call.func) == 'sys.path.insert' and len(call.args) == 2 and isinstance(call.args[0], ast.Constant) and call.args[0].value == 0:
                result = path(call.args[1])
                if result is not None and os.path.isabs(result):
                    insertions.append((node.lineno, result))
    # Bound recognition to repository-local concrete files/dirs; never import code.
    return [(line, relative(value)) for line, value in insertions if relative(value) is not None], loaders
