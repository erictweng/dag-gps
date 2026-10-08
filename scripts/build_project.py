#!/usr/bin/env python3
"""Build a pinned repository + reviewed layers into safely refreshed offline artifacts."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from build_map import build, git, load_json, source_files
from render import check_map, render, DEFAULT_TEMPLATE


class BuildFailure(ValueError):
    pass


def repo_identity(repo):
    """Origin-derived identity, never a layer spec's hardcoded repository name."""
    try:
        remote = subprocess.check_output(['git', '-C', repo, 'remote', 'get-url', 'origin'], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'local:' + str(Path(repo).resolve())
    # Normalize common SSH/HTTPS spellings to the same host/path namespace.
    ssh = re.fullmatch(r'(?:[^@/]+@)?([^:/]+):(.+)', remote) if '://' not in remote else None
    if ssh:
        host, path = ssh.groups()
    elif '://' in remote:
        from urllib.parse import urlsplit
        parsed = urlsplit(remote)
        host, path = parsed.hostname, parsed.path.lstrip('/')
        if not host:
            return 'local:' + str(Path(repo).resolve())
    else:
        return 'local:' + str(Path(repo).resolve())
    path = path.removesuffix('.git').rstrip('/')
    return path if host.lower() == 'github.com' else host.lower() + '/' + path


def snapshot_diff(previous, current):
    """Deterministic semantic diff; build timestamps/indices do not create noise."""
    if previous and previous['meta']['repo'] != current['meta']['repo']:
        raise BuildFailure('Previous map belongs to another repository')
    old = {n['id']: n for n in (previous or {}).get('nodes', [])}
    new = {n['id']: n for n in current['nodes']}
    def connections(doc):
        return {(scope, e['from'], e['to'], e['type'])
                for scope in ('edges', 'file_edges') for e in (doc or {}).get(scope, [])}
    def encoded(edges):
        return [dict(scope=s, **{'from': a, 'to': b, 'type': t}) for s, a, b, t in sorted(edges)]
    oe, ne = connections(previous), connections(current)
    shared = sorted(old.keys() & new.keys())
    assignments = [{'id': i, 'from': old[i].get('layer'), 'to': new[i].get('layer')}
                   for i in shared if old[i].get('layer') != new[i].get('layer')]
    changes = []
    for i in shared:
        fields = sorted((old[i].keys() | new[i].keys()) - {'idx'})
        changed = {k: {'from': old[i].get(k), 'to': new[i].get(k)}
                   for k in fields if old[i].get(k) != new[i].get(k)}
        if changed:
            changes.append({'id': i, 'fields': changed})
    def provenance(doc):
        if not doc:
            return None
        m = doc['meta']
        return {'commit': m.get('snapshot_commit', m['commit']), 'ref': m.get('ref')}
    result = {'version': 1, 'repo': current['meta']['repo'],
              'baseline': provenance(previous), 'snapshot': provenance(current),
              'initial_build': previous is None,
              'added_files': sorted(i for i in new.keys() - old.keys() if new[i]['kind'] == 'file'),
              'deleted_files': sorted(i for i in old.keys() - new.keys() if old[i]['kind'] == 'file'),
              'added_layers': sorted(i for i in new.keys() - old.keys() if new[i]['kind'] == 'layer'),
              'deleted_layers': sorted(i for i in old.keys() - new.keys() if old[i]['kind'] == 'layer'),
              'added_connections': encoded(ne - oe), 'removed_connections': encoded(oe - ne),
              'assignment_changes': assignments, 'node_changes': changes}
    result['summary'] = {k: len(result[k]) for k in ('added_files', 'deleted_files', 'added_layers',
                         'deleted_layers', 'added_connections', 'removed_connections',
                         'assignment_changes', 'node_changes')}
    return result


def publish(stage, output, names):
    """Same-filesystem atomic per-file replace, rollback on caught promotion errors.

    Not a cross-file transaction for concurrent readers or power/process loss.
    Keep one writer and open the HTML after this command succeeds.
    """
    output = Path(output)
    prior = {name: (output / name).read_bytes() if (output / name).exists() else None for name in names}
    promoted = []
    try:
        for name in names:
            os.replace(Path(stage) / name, output / name)
            promoted.append(name)
    except BaseException as exc:
        rollback_errors = []
        for name in reversed(promoted):
            target = output / name
            try:
                if prior[name] is None:
                    target.unlink()
                else:
                    restore = Path(stage) / ('rollback-' + name)
                    restore.write_bytes(prior[name])
                    os.replace(restore, target)
            except OSError as restore_error:
                rollback_errors.append(name + ': ' + str(restore_error))
        if rollback_errors:
            raise RuntimeError('Promotion failed and rollback incomplete; inspect output before use: ' +
                               '; '.join(rollback_errors)) from exc
        raise


def build_project(repo, ref, layers, out_dir, previous_map=None, tops=None, tours=None):
    repo = str(Path(repo).resolve())
    pinned = git(repo, 'rev-parse', '--verify', ref + '^{commit}').strip()
    tip = git(repo, 'rev-parse', '--verify', 'HEAD^{commit}').strip()
    output = Path(out_dir).resolve()
    if previous_map is None and (output / 'map.json').exists():
        previous_map = output / 'map.json'
    previous = load_json(previous_map) if previous_map else None
    if previous and check_map(previous):
        raise BuildFailure('Previous map is invalid: ' + '; '.join(check_map(previous)))
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.refresh-', dir=output) as stage:
        # Explicit discovery avoids quest-coder defaults and never extracts mutable worktrees.
        discovered = tops if tops is not None else source_files(repo, pinned)
        doc, checks, log = build(repo, pinned, layers, str(Path(stage) / 'candidate.json'), discovered)
        doc['meta'].update(repo=repo_identity(repo), ref=ref, snapshot_commit=pinned,
                           source_tip_at_build=tip, source_tip_ref='HEAD',
                           freshness='Snapshot only; build-time local HEAD verified, not live remote freshness.',
                           extraction_scope=discovered)
        diff = snapshot_diff(previous, doc)
        report = {'version': 1, 'meta': doc['meta'], 'extract': log,
                  'checks': [{'ok': ok, 'name': name, 'detail': detail} for ok, name, detail in checks],
                  'diagnostics': doc['diagnostics'], 'diff_summary': diff['summary'],
                  'limitations': ['JS imports use a lexical extractor, not a full parser; regex literals and template interpolation are not modeled.',
                                  'Only relative and @/ JS specs are local-resolved; other configured aliases and bare package resolution are not interpreted.',
                                  'Nonliteral require/import, relative Python imports, and dynamic Python imports are unsupported and not guessed.',
                                  'Bare Python names without a unique local match are external/unknown, not proof of installed dependencies.',
                                  'HTTP/RPC extraction is literal pattern-based; non-source targets remain explicit diagnostic findings.']}
        if not all(ok for ok, _, _ in checks):
            raise BuildFailure(json.dumps(report, indent=2))
        problems = check_map(doc)
        if problems:
            raise BuildFailure('; '.join(problems))
        doc['refresh'] = diff
        for name, data in [('map.json', doc), ('diff.json', diff), ('report.json', report)]:
            (Path(stage) / name).write_text(json.dumps(data, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        from tours import compile_tours
        compiled = compile_tours(load_json(tours), doc, repo) if tours else None
        html = render(Path(DEFAULT_TEMPLATE).read_text(encoding='utf-8'), doc, compiled)
        (Path(stage) / 'index.html').write_text(html, encoding='utf-8')
        # Exercise serialized artifacts before touching any previous valid output.
        if check_map(load_json(Path(stage) / 'map.json')) or load_json(Path(stage) / 'diff.json') != diff:
            raise BuildFailure('Staged artifacts failed validation')
        publish(stage, output, ['map.json', 'diff.json', 'report.json', 'index.html'])
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    for arg in ('repo', 'ref', 'layers', 'out-dir'):
        ap.add_argument('--' + arg, required=True)
    ap.add_argument('--previous-map')
    ap.add_argument('--tours', help='Reviewed tours JSON pinned to the same repository and commit')
    ap.add_argument('--tops', nargs='+', help='Explicit extractor scope; all source files must still be assigned')
    a = ap.parse_args(argv)
    try:
        report = build_project(a.repo, a.ref, a.layers, a.out_dir, a.previous_map, a.tops, a.tours)
    except (BuildFailure, OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Refresh failed; candidates are validated before promotion (caught promotion errors trigger rollback).\n' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
