#!/usr/bin/env python3
"""Pinned-source call-site/target audit and legacy packet parity, no target execution.

Produces a source excerpt for EVERY new call link, plus a focused review sheet for
all new links displayed in the eleven questions. Structural corroboration is not
runtime semantic proof: decorator wrappers/mocks and annotation truth remain unknown.
"""
import ast
import hashlib
import json
import subprocess
import sys
from unittest.mock import patch
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
from app.context import git_dir_for
from app.contracts import validate_evidence_packet


def main():
    out = Path(sys.argv[1]).resolve()
    snapshot = json.loads((out / 'snapshot.json').read_text())
    graph = snapshot['map']['symbol_graph']
    git_dir = git_dir_for(out / 'workspace/git-cache', snapshot)
    pin = snapshot['source']['commit']
    sources, trees = {}, {}
    inventory = {f['path']: f for f in snapshot['inventory']}
    nodes = {n['id']: n for n in graph['nodes']}
    v3 = out.name == 'honcho-v3'
    overloads = {(n['path'], n['qualname']) for n in graph['nodes'] if n.get('overloadDeclaration')}
    def source(path):
        if path not in sources:
            raw = subprocess.check_output(['git', '--git-dir=' + str(git_dir), 'show', pin + ':' + path])
            assert hashlib.sha256(raw).hexdigest() == inventory[path]['sha256']
            sources[path] = raw.decode()
            trees[path] = ast.parse(sources[path])
        return sources[path].splitlines()
    def excerpt(path, start, end):
        lines = source(path)
        return '\n'.join('%d: %s' % (i + 1, lines[i]) for i in range(max(0, start - 3), min(len(lines), end + 2)))
    displayed = set()
    question_count = len(json.loads((out / 'questions.json').read_text()))
    for index in range(1, question_count + 1):
        packet = json.loads((out / ('packet-%d.json' % index)).read_text())
        displayed.update((e['from'], e['to']) for e in packet['selectedEdges'])
        validate_evidence_packet(packet, snapshot)
        validate_evidence_packet(json.loads((out / ('certain-%d.json' % index)).read_text()), snapshot)
    rows = []
    for edge in graph['edges']:
        inferred = [s for s in edge['sites'] if s.get('confidence', 'resolved') != 'resolved'
                    or (v3 and (s.get('reexports') or (nodes[edge['to']]['path'], nodes[edge['to']]['qualname']) in overloads))]
        if not inferred:
            continue
        target = nodes[edge['to']]
        target_lines = source(target['path'])
        definition = next(n for n in ast.walk(trees[target['path']]) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.lineno == target['start'])
        assert definition.name == target['name']
        decorators = [ast.unparse(d)[:512] for d in definition.decorator_list]
        if edge['confidence'] == 'through-decorator':
            assert decorators and decorators == edge['decorators']
        sites = []
        for site in inferred:
            source(site['path'])
            calls = [n for n in ast.walk(trees[site['path']]) if isinstance(n, ast.Call) and n.lineno == site['start'] and n.end_lineno == site['end'] and ast.unparse(n.func)[:256] == site['expression']]
            assert calls, site
            for hop in site.get('reexports', []):
                source(hop['path'])
                stmt = next(n for n in trees[hop['path']].body if isinstance(n, ast.ImportFrom) and n.lineno == hop['start'])
                assert stmt.end_lineno == hop['end']
                assert any((a.asname or a.name) == hop['name'] and a.name == hop['targetName'] for a in stmt.names)
                assert (hop['path'], hop['targetPath']) in [(e['from'], e['to']) for e in snapshot['map']['file_edges'] if e['type'] == 'import']
            caller = nodes[edge['from']]
            assert caller['path'] == site['path'] and caller['start'] <= site['start'] <= caller['end']
            sites.append(dict(site, excerpt=excerpt(site['path'], site['start'], site['end'])))
        rows.append({'from': edge['from'], 'to': edge['to'], 'confidence': edge['confidence'],
                     'displayed': (edge['from'], edge['to']) in displayed,
                     'decorators': decorators, 'sites': sites,
                     'definition': excerpt(target['path'], min([d.lineno for d in definition.decorator_list] + [definition.lineno]), definition.lineno + 1)})
    (out / 'all-new-links.json').write_text(json.dumps(rows, indent=2))
    shown = [r for r in rows if r['displayed']]
    report = []
    for r in shown:
        report.append(r['confidence'] + ' ' + r['from'] + ' -> ' + r['to'])
        report.append(r['definition'])
        report.extend(s['excerpt'] for s in r['sites'])
        report.append('')
    (out / 'displayed-new-links.txt').write_text('\n'.join(report))
    # Use the baseline extractor on exactly the same full pinned Python inputs.
    paths = [f['path'] for f in snapshot['inventory'] if f['path'].endswith('.py') and any(n.get('path') == f['path'] for n in snapshot['map']['nodes'])]
    all_sources = {p: subprocess.check_output(['git', '--git-dir=' + str(git_dir), 'show', pin + ':' + p]).decode() for p in paths}
    imports = [(e['from'], e['to']) for e in snapshot['map']['file_edges'] if e['type'] == 'import']
    namespace = {}
    exec(compile(subprocess.check_output(['git', 'show', '62010f6:scripts/python_symbols.py'], cwd=ROOT, text=True), '<baseline>', 'exec'), namespace)
    baseline = dict(snapshot, map=dict(snapshot['map'], symbol_graph=namespace['extract_symbols'](all_sources, imports)))
    if v3:
        # Static re-exports/overload implementations intentionally expand resolved.
        # Prove certain-only parity against an independently extracted graph with
        # inference disabled, through the unchanged legacy query implementation.
        from python_symbols import extract_symbols
        from python_call_tiers import CallTiers
        with patch.object(CallTiers, 'infer', return_value=None):
            baseline['map']['symbol_graph'] = extract_symbols(all_sources, imports)
    assert baseline['map']['symbol_graph']['counts']['resolved'] == graph['counts']['resolved']
    (out / 'baseline-snapshot.json').write_text(json.dumps(baseline))
    code = r"""
const fs=require('fs'),cp=require('child_process'),vm=require('vm'),path=require('path');
const out=process.argv[1],s=JSON.parse(fs.readFileSync(path.join(out,'baseline-snapshot.json')));
const box={module:{exports:{}},TextEncoder,require:n=>require(path.resolve('web',n))};
vm.runInNewContext(cp.execFileSync('git',['show','62010f6:web/query-service.js'],{encoding:'utf8'}),box);
const service=box.module.exports.createQueryService(s);
const count=JSON.parse(fs.readFileSync(path.join(out,'questions.json'))).length;
for(let i=1;i<=count;i++) {
 const p=JSON.parse(fs.readFileSync(path.join(out,'certain-'+i+'.json')));
 const old=service.query({requestId:p.requestId,query:p.query}); delete p.certainOnly;
 require('assert').deepStrictEqual(JSON.parse(JSON.stringify(old)),p,'question '+i);
}
console.log(count+' complete packets equal baseline except explicit certainOnly marker');
"""
    parity = subprocess.run(['node', '-e', code, str(out)], cwd=ROOT, text=True, capture_output=True)
    (out / 'certain-parity.log').write_text(parity.stdout + parity.stderr)
    assert parity.returncode == 0, parity.stderr
    summary = {'allNewEdges': len(rows), 'allNewSites': sum(len(r['sites']) for r in rows),
               'displayedNewEdges': len(shown), 'displayedNewSites': sum(len(r['sites']) for r in shown),
               'sourceFilesHashVerified': len(sources), 'certainParityPackets': question_count,
               'note': 'All source sites/definition ranges/decorators corroborated structurally. Semantic spot checks are recorded separately; no runtime accuracy claim.'}
    (out / 'tier-audit.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
