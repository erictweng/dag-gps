#!/usr/bin/env python3
"""Propose deterministic folder ownership from an immutable Git snapshot, never approve it."""
import argparse
import json
from pathlib import Path
import tempfile

from build_map import build, git, source_files
from build_project import repo_identity
from onboarding import DRAFT_SCHEMA, group_files


def draft_layers(repo, ref, tops=None):
    repo = str(Path(repo).resolve())
    commit = git(repo, 'rev-parse', '--verify', ref + '^{commit}').strip()
    files = source_files(repo, commit)
    scope = tops if tops is not None else files
    layers = group_files(files)
    if not layers:
        raise ValueError('No supported source files in pinned inventory')
    with tempfile.TemporaryDirectory(prefix='draft-layers-') as tmp:
        spec = Path(tmp) / 'layers.json'
        spec.write_text(json.dumps({'repo': repo_identity(repo), 'layers': layers}))
        # Same archive/extractor/coverage pipeline. Rejected candidate returns evidence;
        # no draft map is published, and real file cycles/links are never removed.
        doc, checks, _ = build(repo, commit, str(spec), str(Path(tmp) / 'map.json'), scope)
    return {'schema': DRAFT_SCHEMA, 'repo': repo_identity(repo), 'commit': commit,
            'tops': scope, 'source_files': files, 'layers': layers,
            'file_edges': doc['file_edges'], 'diagnostics': doc['diagnostics'],
            'trust': doc['trust'], 'checks': [{'ok': ok, 'name': n, 'detail': d} for ok, n, d in checks],
            'reviewed': False, 'reference_warnings': [],
            'limitations': ['Folder proposals are not architectural truth. Human semantic review required.',
                             'Only supported static links; unknown runtime behavior and coverage.',
                             'Changing/removing layer IDs requires manual alias/tour review; no automatic migration.']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--repo', required=True)
    p.add_argument('--ref', required=True)
    p.add_argument('--tops', nargs='+')
    p.add_argument('--out', required=True)
    a = p.parse_args()
    draft = draft_layers(a.repo, a.ref, a.tops)
    target = Path(a.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(draft, indent=2, sort_keys=True) + '\n')
    print(f"Draft only: {draft['repo']} @ {draft['commit']}: {len(draft['source_files'])} files / {len(draft['layers'])} folder proposals")
    print('Findings:', json.dumps(draft['diagnostics']))


if __name__ == '__main__':
    main()
