#!/usr/bin/env python3
"""Export retained questions as frozen-set-shaped review drafts, never gold labels."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.query_log import read_entries


def export(path, project_id=None, commit=None):
    entries = [q for q in reversed(read_entries(Path(path)))
               if (project_id is None or q['projectId'] == project_id)
               and (commit is None or q['commit'] == commit)]
    identities = {(q['projectId'], q['commit']) for q in entries}
    if len(identities) > 1:
        raise ValueError('Select one project and commit with --project-id and --commit')
    return {'schema': 'dag-gps-question-parser-eval/v1', 'seed': None,
            'pin': entries[0]['commit'] if entries else commit,
            'provenance': 'local question log; review draft, NOT frozen ground truth',
            'reviewRequired': True,
            'rows': [{'id': q['entryId'], 'question': q['query'], 'autoLabel': q['label'],
                      'verdict': q['verdict'], 'verdictAt': q['verdictAt'],
                      'projectId': q['projectId'], 'snapshotId': q['snapshotId'], 'commit': q['commit'],
                      'operation': q['operation'], 'expected': None, 'targets': [],
                      'observedTargets': q['selectedNodeIds'], 'sourceEvidence': [],
                      'split': None, 'rationale': 'Needs independent target/operation review and split assignment.'}
                     for q in entries]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path, help='query-log.jsonl; includes retained .1 generation')
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--project-id')
    parser.add_argument('--commit')
    args = parser.parse_args()
    if not args.log.is_file():
        parser.error('Log does not exist')
    try:
        result = export(args.log, args.project_id, args.commit)
        # Never silently replace a frozen set or any other user file.
        with args.out.open('x', encoding='utf-8') as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    except (ValueError, OSError) as error:
        parser.error(str(error))
    print('Exported %d review drafts; no frozen set modified.' % len(result['rows']))


if __name__ == '__main__':
    main()
