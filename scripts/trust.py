"""Versioned extraction provenance, not a runtime-completeness measurement."""
from collections import Counter

VERSION = 2
CATEGORIES = ('resolved_source', 'non_source_target', 'unresolved_local_reference',
              'unsupported_dynamic_construct', 'external_dependency')
LIMITATIONS = [
    'Static source links are not runtime execution, coverage or guaranteed impact.',
    'JS uses lexical imports, not a full parser; regex literals and template interpolation are not modeled.',
    'Only relative and root @/ JS specs resolve locally; configured aliases/package exports are not interpreted.',
    'Python resolves exact modules, relative package names and same-directory scripts; sys.path changes and dynamic loading are not executed.',
    'HTTP/RPC links are inferred from literal patterns, not verified runtime calls.',
    'Diagnostics are observed findings, not an exhaustive list of blind spots. Missing edges do not prove absence of consumers.'
]


def validate_trust(doc):
    t = doc.get('trust')
    if t is None:
        return []  # Legacy maps use an explicit unavailable-provenance UI fallback.

    def require(condition):
        if not condition:
            raise ValueError('invalid trust')

    try:
        require(t['version'] == VERSION and t['extractor'] == 'dag-gps-static-v2')
        require(t['snapshot_commit'] == doc['meta']['snapshot_commit'])
        require(t['categories'] == list(CATEGORIES))
        files = {n['id'] for n in doc['nodes'] if n['kind'] == 'file'}
        s = t['scope']
        extracted, missing = set(s['extracted_paths']), set(s['unscanned_paths'])
        require(extracted.isdisjoint(missing) and extracted | missing == files)
        require(len(extracted) == len(s['extracted_paths']) == s['extracted_files'])
        require(len(missing) == len(s['unscanned_paths']) and s['inventory_files'] == len(files))
        counts = Counter()
        for f in t['findings']:
            require(f['category'] in CATEGORIES)
            require(all(isinstance(f[k], str) and f[k] for k in ('path', 'target', 'reason', 'evidence')))
            counts[f['category']] += 1
        require(t['counts'] == {c: counts[c] for c in CATEGORIES})
        require(isinstance(t['limitations'], list) and bool(t['limitations']))
        require(isinstance(t['file_cycles'], list))
    except (ValueError, KeyError, TypeError):
        return ['invalid versioned trust provenance/counts/scope']
    return []


def build_trust(graph, files, file_edges, drops, http_misses, rpc_misses, scope, snapshot):
    findings = []
    def add(category, path, target, reason, evidence):
        findings.append(dict(category=category, path=path, target=target, reason=reason, evidence=evidence))
    for e in file_edges:
        lexical = e['type'] == 'import'
        loader = lexical and [e['from'], e['to']] in graph.get('static_loader_edges', [])
        add('resolved_source', e['from'], e['to'],
            'Explicit static Python loader file path resolved; consumer → dependency, no loader code executed or runtime verified.' if loader else
            'Resolved static import; consumer → dependency, not execution order.' if lexical else
            'Literal ' + e['type'].upper() + ' pattern matched a source target; runtime behavior unverified.',
            'resolved_static_loader' if loader else 'resolved_lexical_import' if lexical else 'inferred_unverified')
    for a, b, typ in drops:
        if not b.startswith('UNRESOLVED:'):
            add('non_source_target', a, b, 'Resolved ' + typ + ' target has no source node in the assignment inventory; omitted from graph.', 'static_resolution')
    for a, b in graph.get('unresolved', []):
        add('unresolved_local_reference', a, b, 'Local resolution failed: ' + b, 'unresolved')
    for a, why, detail in graph.get('unsupported', []):
        add('unsupported_dynamic_construct', a, detail, why + ': ' + detail + '; not evaluated or guessed.', 'unsupported')
    for path, packages in sorted(graph.get('ext', {}).items()):
        for package in packages:
            add('external_dependency', path, package, 'Bare/external dependency; installed package and configured alias resolution not verified. Not an unresolved local error.', 'external_unverified')
    for kind, misses in [('HTTP route', http_misses), ('RPC function', rpc_misses)]:
        for a, b in misses:
            add('unresolved_local_reference', a, b, 'Literal ' + kind + ' reference has no mapped source target; not proof the endpoint is absent at runtime.', 'inferred_unverified')
    findings = sorted({tuple(sorted(f.items())) for f in findings})
    findings = [dict(f) for f in findings]
    counts = Counter(f['category'] for f in findings)
    extracted = sorted(set(graph['nodes']) & set(files))
    return {'version': VERSION, 'extractor': 'dag-gps-static-v2', 'snapshot_commit': snapshot,
            'categories': list(CATEGORIES), 'counts': {c: counts[c] for c in CATEGORIES},
            'scope': {'js_inputs': list(scope), 'python': 'repository-wide included .py files',
                      'sql': 'repository-wide included migrations/*.sql function scan',
                      'inventory_files': len(files), 'extracted_files': len(extracted),
                      'extracted_paths': extracted, 'unscanned_paths': sorted(set(files) - set(extracted))},
            'file_cycles': graph.get('cycles', []), 'findings': findings,
            'limitations': list(LIMITATIONS)}
