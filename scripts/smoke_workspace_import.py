#!/usr/bin/env python3
"""Real pinned public import smoke; imported source remains unexecuted data."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.repositories import acquire_repository
from app.snapshots import build_workspace_snapshot


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-url', required=True)
    parser.add_argument('--expected-commit', required=True)
    parser.add_argument('--cache-root', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--receipt', required=True)
    args = parser.parse_args(argv)

    audit = {'subprocesses': [], 'pythonNetworkEvents': []}

    def audit_hook(event, values):
        if event == 'subprocess.Popen':
            executable, command = values[0], values[1]
            audit['subprocesses'].append({'executable': str(executable),
                                           'argv': [str(value) for value in command]})
        elif event.startswith('socket.connect'):
            audit['pythonNetworkEvents'].append(event)

    sys.addaudithook(audit_hook)
    acquisition_events = []
    acquisition = acquire_repository(args.repo_url, args.cache_root, args.expected_commit,
                                     progress=acquisition_events.append)
    if acquisition['commit'] != args.expected_commit:
        raise RuntimeError('Acquisition returned a different commit')
    first_events = []
    first = build_workspace_snapshot(acquisition, args.output, progress=first_events.append)
    second_events = []
    second = build_workspace_snapshot(acquisition, args.output, progress=second_events.append)
    inventory = json.loads(Path(first['inventory_path']).read_text(encoding='utf-8'))
    preview = json.loads(Path(first['preview_path']).read_text(encoding='utf-8'))
    publication_receipt = json.loads(Path(first['receipt_path']).read_text(encoding='utf-8'))
    if not first_events or first_events[0]['stage'] != 'inventory-ready':
        raise RuntimeError('Inventory was not observable before dependency extraction')
    if not second['cache_hit'] or first['snapshot_id'] != second['snapshot_id']:
        raise RuntimeError('Second build did not reuse the exact source/options identity')
    allowed = {'/usr/bin/git', sys.executable}
    unexpected = [item for item in audit['subprocesses'] if item['executable'] not in allowed]
    imported_commands = [item for item in audit['subprocesses']
                         if item['executable'] == sys.executable
                         and (len(item['argv']) < 2 or not item['argv'][1].endswith('/scripts/import_graph.py'))]
    if unexpected or imported_commands:
        raise RuntimeError('Observed an unexpected subprocess during import')
    result = {
        'schema': 'dag-gps-real-import-smoke/v1',
        'source': inventory['source'],
        'acquisition': {'cacheHit': acquisition['cache_hit'], 'events': acquisition_events},
        'inventoryBeforeExtraction': True,
        'firstEvents': first_events,
        'secondEvents': second_events,
        'secondBuildCacheHit': second['cache_hit'],
        'inventoryCounts': inventory['counts'],
        'preview': {
            'state': preview['state'],
            'grouping': preview['grouping'],
            'publicationBlocked': preview['publicationBlocked'],
            'mapCounts': preview['map']['meta']['counts'],
            'diagnosticCounts': preview['diagnostics']['counts'],
        },
        'outputs': first['output_sha256'],
        'producer': publication_receipt['producer'],
        'paths': {key: first[key] for key in ('inventory_path', 'preview_path', 'html_path', 'receipt_path')},
        'audit': {
            'subprocessCount': len(audit['subprocesses']),
            'executables': sorted(set(item['executable'] for item in audit['subprocesses'])),
            'trustedExtractorInvocations': sum(item['executable'] == sys.executable for item in audit['subprocesses']),
            'unexpectedSubprocesses': unexpected,
            'importedSourceCommands': imported_commands,
            'pythonNetworkEvents': audit['pythonNetworkEvents'],
            'modelOrProviderSubprocessObserved': any(
                any(token in ' '.join(item['argv']).lower() for token in ('anthropic', 'openai', 'claude', 'model'))
                for item in audit['subprocesses']),
            'boundary': 'Python audit hook covers subprocess launches in this process; Git performs the approved GitHub transport in its child process.',
        },
    }
    receipt = Path(args.receipt)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
