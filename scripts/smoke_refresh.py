#!/usr/bin/env python3
"""Generate two real committed synthetic snapshots for refresh/browser regression."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build_project import build_project


def main():
    root = ROOT / 'artifacts' / 'refresh-fixture'
    if root.exists():
        shutil.rmtree(root)
    repo = root / 'repo'
    repo.mkdir(parents=True)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True).strip()
    git('init', '-q')
    git('config', 'user.name', 'Synthetic fixture')
    git('config', 'user.email', 'fixture@example.invalid')
    (repo / 'a.cjs').write_text("const b=require('./b');\nmodule.exports=b;\n")
    (repo / 'b.js').write_text('exports.b = 1;\n')
    (repo / 'gone.py').write_text('x = 1\n')
    git('add', '.')
    git('commit', '-qm', 'synthetic baseline')
    first = git('rev-parse', 'HEAD')
    layers1 = root / 'layers-before.json'
    layers2 = root / 'layers-after.json'
    spec = {'layers': [{'id': 'consumer', 'label': 'Consumer', 'globs': ['a.cjs', 'gone.py']},
                       {'id': 'dependency', 'label': 'Dependency', 'globs': ['b.js']}], 'manual_edges': []}
    layers1.write_text(json.dumps(spec))
    out = ROOT / 'dist' / 'refresh-fixture'
    if out.exists():
        shutil.rmtree(out)
    build_project(str(repo), first, str(layers1), str(out))
    shutil.copyfile(out / 'map.json', root / 'before-map.json')
    (repo / 'gone.py').unlink()
    (repo / 'a.cjs').write_text('module.exports = 1;\n')
    (repo / 'new.cjs').write_text("const b=require('./b');\nmodule.exports=b;\n")
    git('add', '.')
    git('commit', '-qm', 'synthetic add delete and reassign')
    second = git('rev-parse', 'HEAD')
    spec['layers'][0]['globs'] = ['new.cjs']
    spec['layers'][1]['globs'].append('a.cjs')
    layers2.write_text(json.dumps(spec))
    manifest = {'synthetic': True, 'repo': str(repo), 'before_commit': first,
                'after_commit': second, 'layers': str(layers2), 'out_dir': str(out)}
    (ROOT / 'artifacts' / 'refresh-fixture.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
