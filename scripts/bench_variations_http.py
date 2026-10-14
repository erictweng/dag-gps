#!/usr/bin/env python3
"""Real loopback server + worker; no mock transport, no imported-source execution."""
import hashlib
import http.client
import json
import os
from pathlib import Path
import statistics
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
CODE = Path(sys.argv[1]).resolve()
REPO, VERSION = sys.argv[2:4]
sys.path.insert(0, str(CODE))
from app.server import WorkspaceServer
from app.contracts import validate_snapshot

OUT = ROOT / 'artifacts/variation-benchmark'
workspace = OUT / ('http-' + REPO + '-' + VERSION)
workspace.mkdir(parents=True, exist_ok=True)
snapshot = json.loads((ROOT / f'artifacts/question-parser/{REPO}/snapshot.json').read_text())
# Same graph/inventory on both versions; bind honest query-code provenance.
snapshot['queryCode'] = {p: hashlib.sha256((CODE / p).read_bytes()).hexdigest()
                         for p in ['web/scorer.js', 'web/router.js', 'web/query-service.js']}
snapshot['scorerSha256'] = snapshot['queryCode']['web/scorer.js']
validate_snapshot(snapshot)
snapshot_path = workspace / 'snapshot.json'
snapshot_path.write_text(json.dumps(snapshot))
server = WorkspaceServer(workspace, port=0)
server.store.project_dir(snapshot['projectId']).mkdir(parents=True, exist_ok=True)
server.store.record(snapshot, snapshot_path)
threading.Thread(target=server.serve_forever, daemon=True).start()
rows = json.loads((OUT / f'{REPO}-{VERSION}-http-input.json').read_text())


def stats(values):
    ordered = sorted(values)
    import math
    return {'n': len(values), **{k: ordered[math.ceil(len(values) * p) - 1]
            for k, p in [('p50', .5), ('p95', .95), ('p99', .99), ('max', 1)]},
            'mean': statistics.mean(values), 'stddev': statistics.pstdev(values)}


try:
    result = {'loadBefore': os.getloadavg(), 'warmups': 20, 'repeats': 2, 'samples': []}
    for repeat in range(-1, 2):
        for row in rows[:20] if repeat == -1 else rows:
            body = json.dumps({'requestId': row['id'], 'query': row['question'], 'snapshotId': snapshot['snapshotId']})
            start = time.perf_counter()
            connection = http.client.HTTPConnection('127.0.0.1', server.port, timeout=60)
            connection.request('POST', f"/api/projects/{snapshot['projectId']}/query", body,
                               {'Content-Type': 'application/json', 'X-DAG-GPS-Session': server.session_token})
            response = connection.getresponse()
            data = response.read()
            elapsed = (time.perf_counter() - start) * 1000
            connection.close()
            assert response.status == 200, (response.status, data[:400])
            packet = json.loads(data)
            assert packet['requestId'] == row['id']
            if repeat >= 0:
                result['samples'].append({'id': row['id'], 'operation': row['operation'], 'status': packet['status'],
                                          'ms': elapsed, 'bytes': len(data), 'directMs': row['directMs']})
                if len(result['samples']) % 100 == 0:
                    print(REPO, VERSION, 'HTTP samples', len(result['samples']), 'last ms', elapsed, flush=True)
    result['loadAfter'] = os.getloadavg()
    samples = result.pop('samples')
    result['latency'] = stats([r['ms'] for r in samples])
    result['pairedDirect'] = stats([statistics.median(r['directMs']) for r in samples])
    result['pairedDifference'] = stats([r['ms'] - statistics.median(r['directMs']) for r in samples])
    result['repeatLatency'] = [stats([r['ms'] for r in samples[i * len(rows):(i + 1) * len(rows)]]) for i in range(2)]
    (OUT / f'{REPO}-{VERSION}-http-raw.json').write_text(json.dumps(samples))
    (OUT / f'{REPO}-{VERSION}-http.json').write_text(json.dumps(result, indent=2) + '\n')
    print(REPO, VERSION, 'HTTP', result['latency'])
finally:
    server.shutdown()
