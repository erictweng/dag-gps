#!/usr/bin/env python3
"""Run the project's real release gates; retain logs and fail closed."""
import argparse
import datetime
import hashlib
import json
import os
import shlex
import signal
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def run(commands, output, timeout=600):
    output.mkdir(parents=True, exist_ok=True)
    results = []
    for name, command in commands.items():
        if command is None:
            continue
        start = time.perf_counter()
        with (output / (name + '.stdout.log')).open('w') as stdout, (output / (name + '.stderr.log')).open('w') as stderr:
            process = subprocess.Popen(command, shell=True, cwd=ROOT, stdout=stdout, stderr=stderr,
                                       start_new_session=True)
            try:
                returncode = process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                stderr.write('Gate process group timed out; release blocked.\n')
                returncode = 124
            result = subprocess.CompletedProcess(command, returncode)
        results.append(dict(name=name, command=command, returncode=result.returncode,
                            seconds=time.perf_counter() - start))
        print(name, result.returncode, flush=True)
        if result.returncode:
            break
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quest-repo', default=os.environ.get('DAG_GPS_QUEST_REPO', '/Users/aibert/projects/quest-coder'))
    parser.add_argument('--output', default='artifacts/release-check')
    parser.add_argument('--legacy-only', action='store_true', help='Bootstrap audit: not a complete release gate')
    args = parser.parse_args()
    config = json.loads((ROOT / '.verify.json').read_text())
    missing = [p for p in config['required_files'] if not (ROOT / p).is_file()]
    if missing:
        print('Missing required input: ' + ', '.join(missing), file=sys.stderr)
        return 1
    quest_repo = str(Path(args.quest_repo).resolve())
    pin = '749d8b5de490cc2e6a0c98c713fab3ab856da799'
    probe = subprocess.run(['git', '-C', quest_repo, 'cat-file', '-e', pin + '^{commit}'], capture_output=True)
    if probe.returncode:
        print('Missing pinned quest Git source: ' + quest_repo + ' @ ' + pin, file=sys.stderr)
        return 1
    os.environ['DAG_GPS_QUEST_REPO'] = quest_repo
    commands = {k: v.replace('/Users/aibert/projects/quest-coder', shlex.quote(quest_repo)) if v else v
                for k, v in config['commands'].items()}
    # Separate from the legacy recipes to avoid recursive release invocation.
    if not args.legacy_only:
        commands.update(config.get('release_commands', {}))
        if not config.get('release_commands'):
            print('Missing release acceptance commands', file=sys.stderr)
            return 1
    output = ROOT / args.output
    input_files = set(config['required_files']) | {'.verify.json', 'README.md', 'docs/V1_ACCEPTANCE.md'}
    input_files.update(str(p.relative_to(ROOT)) for directory in ['web', 'scripts']
                       for p in (ROOT / directory).glob('*') if p.is_file()
                       and p.suffix in ['.py', '.js', '.cjs', '.mjs', '.html'])
    inputs = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in sorted(input_files)}
    results = run(commands, output, config["timeout_seconds"])
    changed = [p for p, digest in inputs.items() if hashlib.sha256((ROOT / p).read_bytes()).hexdigest() != digest]
    if changed:
        results.append(dict(name='input_integrity', command='verify immutable gate inputs', returncode=1,
                            changed=changed, seconds=0))
    environment = {}
    for name, command in {'python': ['python3', '--version'], 'node': ['node', '--version'],
                          'git': ['git', '--version'], 'os': ['uname', '-a'],
                          'hardware': ['sysctl', '-n', 'machdep.cpu.brand_string', 'hw.memsize']}.items():
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
        environment[name] = dict(returncode=result.returncode, output=result.stdout.strip())
    report = dict(environment=environment, timestamp=datetime.datetime.now().astimezone().isoformat(),
                  build_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                  legacy_only=args.legacy_only, results=results,
                  human_acceptance='pending; this runner cannot approve semantics or unaided use',
                  inputs=inputs)
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    if not results or any(r['returncode'] != 0 for r in results):
        return 1
    if not args.legacy_only:
        result = subprocess.run([sys.executable, 'scripts/package_release.py', '--verification',
                                 str(output / 'verification.json')], cwd=ROOT, text=True, capture_output=True)
        (output / 'package.stdout.log').write_text(result.stdout)
        (output / 'package.stderr.log').write_text(result.stderr)
        (output / 'package-result.json').write_text(json.dumps(dict(returncode=result.returncode,
            stdout='package.stdout.log', stderr='package.stderr.log'), indent=2) + '\n')
        print(result.stdout, end='')
        print(result.stderr, end='', file=sys.stderr)
        return result.returncode
    return 0


if __name__ == '__main__':
    sys.exit(main())
