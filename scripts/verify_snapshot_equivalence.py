#!/usr/bin/env python3
"""Compare all existing Python packet fixtures with the frozen pre-cache oracle.

Also accepts real snapshot/input pairs for a distributed set of real packets.
Runs repository tests without altering them; every imported packet-validator alias
is wrapped to compare acceptance, exception type name and exact message.
"""
import argparse

import json
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from app import contracts
from app.query_worker import QueryWorker
from app.workspace_snapshot import query_code_digests


def outcome(call):
    try:
        call()
        return ('accepted', '')
    except Exception as error:
        return (type(error).__name__, str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='6928324bc47f7bd3db0fd6a12070a9531aa8b24d')
    parser.add_argument('--fixtures', help='parser worktree containing pinned artifacts')
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    oracle = types.ModuleType('frozen_contracts')
    source = subprocess.check_output(['git', 'show', args.base + ':app/contracts.py'], cwd=ROOT, text=True)
    exec(compile(source, '<frozen-contracts>', 'exec'), oracle.__dict__)
    current = contracts.validate_evidence_packet
    counts = dict(packetChecks=0, accepted=0, rejected=0, indexedChecks=0, realPackets=0)
    mismatches = []

    def compare(packet, snapshot):
        before = outcome(lambda: oracle.validate_evidence_packet(packet, snapshot))
        after = outcome(lambda: current(packet, snapshot))
        if before != after:
            mismatches.append((before, after))
        assert before == after, (before, after)
        counts['packetChecks'] += 1
        counts['accepted' if before[0] == 'accepted' else 'rejected'] += 1
        try:
            index = contracts.validate_snapshot(snapshot)
        except Exception:
            index = None
        if index is not None:
            indexed = outcome(lambda: contracts.validate_evidence_packet_against(packet, index))
            if before != indexed:
                mismatches.append((before, indexed))
            assert before == indexed, (before, indexed)
            counts['indexedChecks'] += 1
        return current(packet, snapshot)

    suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
    # Fixtures import aliases at module scope. Replace only this exact function,
    # leaving snapshot validation, request generation and assertions untouched.
    for module in list(sys.modules.values()):
        if module is not None and getattr(module, 'validate_evidence_packet', None) is current:
            setattr(module, 'validate_evidence_packet', compare)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful(), 'fixture suite failed'
    if args.fixtures:
        fixtures = Path(args.fixtures)
        for repo in ['honcho', 'salesroom']:
            path = fixtures / ('artifacts/question-parser/' + repo + '/snapshot.json')
            snapshot = json.loads(path.read_text())
            # Same rebinding as HTTP benchmark: inventory/map stay fixed while
            # queryCode truthfully names the parser used to generate packets.
            snapshot['queryCode'] = query_code_digests()
            snapshot['scorerSha256'] = snapshot['queryCode']['web/scorer.js']
            path = Path(args.out).parent / ('oracle-' + repo + '-snapshot.json')
            path.write_text(json.dumps(snapshot))
            inputs = json.loads((fixtures / ('artifacts/variation-benchmark/' + repo + '-parser-http-input.json')).read_text())
            with QueryWorker(path, snapshot) as worker:
                for row in inputs[::10]:
                    packet = worker.query(dict(requestId=row['id'], query=row['question']))
                    compare(packet, snapshot)
                    counts['realPackets'] += 1
                if repo == 'honcho':
                    for certain in [False, True]:
                        for query in ['trace from backfill', 'what calls backfill', 'what does backfill call']:
                            packet = worker.query(dict(requestId='function', query=query, certainOnly=certain))
                            compare(packet, snapshot)
                            counts['realPackets'] += 1
    assert not mismatches, mismatches
    report = dict(base=args.base, testsRun=result.testsRun, skipped=len(result.skipped), mismatches=mismatches, **counts)
    Path(args.out).write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
