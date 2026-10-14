#!/usr/bin/env python3
"""Real HTTP benchmark; run each version in a separate process, same input rows.

Instrumentation wraps real stage functions, never replaces their work. Artifacts
contain packet hashes, not capability headers. Cold request precedes 20 warmups.
"""
import argparse
import hashlib
import http.client
import json
import math
import os
from pathlib import Path
import resource
import statistics
import subprocess
import sys
import threading
import time


def stats(values):
    ordered = sorted(values)
    return dict(n=len(values), mean=statistics.mean(values), **{
        key: ordered[math.ceil(len(values) * quantile) - 1]
        for key, quantile in [('p50', .5), ('p95', .95), ('p99', .99), ('max', 1)]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--code', required=True)
    parser.add_argument('--snapshot', required=True)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    code, out = Path(args.code).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(code))
    import app.server as server_module
    import app.query_worker as worker_module
    snapshot = json.loads(Path(args.snapshot).read_text())
    snapshot['queryCode'] = {p: hashlib.sha256((code / p).read_bytes()).hexdigest()
                             for p in ['web/scorer.js', 'web/router.js', 'web/query-service.js']}
    snapshot['scorerSha256'] = snapshot['queryCode']['web/scorer.js']
    workspace = out / 'workspace'
    workspace.mkdir(exist_ok=True)
    path = workspace / 'snapshot.json'
    path.write_text(json.dumps(snapshot))
    server = server_module.WorkspaceServer(workspace, port=0)
    server.store.project_dir(snapshot['projectId']).mkdir(parents=True, exist_ok=True)
    server.store.record(snapshot, path)
    stages = {}

    def instrument(owner, name, stage):
        original = getattr(owner, name)
        def measured(*a, **kw):
            start = time.perf_counter()
            try:
                return original(*a, **kw)
            finally:
                stages[stage] = stages.get(stage, 0) + (time.perf_counter() - start) * 1000
        setattr(owner, name, measured)

    instrument(server_module.WorkspaceStore, 'snapshot', 'read_parse_cache')
    instrument(worker_module.QueryWorker, 'query', 'worker_including_validation')
    validator = ('validate_evidence_packet_against' if hasattr(worker_module, 'validate_evidence_packet_against')
                 else 'validate_evidence_packet')
    instrument(worker_module, validator, 'validation')
    # _json includes socket writing; separate JSON encode by wrapping the handler.
    def measured_json(self, status, value):
        start = time.perf_counter()
        data = json.dumps(value, ensure_ascii=False).encode('utf-8')
        stages['serialization'] = (time.perf_counter() - start) * 1000
        self._send(status, data, 'application/json; charset=utf-8')
    server_module._Handler._json = measured_json
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    rows = json.loads(Path(args.inputs).read_text())
    assert len(rows) >= 240
    samples = []
    cold = {}
    try:
        for repeat in [-2, -1, 0, 1]:
            selected = rows[:1] if repeat == -2 else rows[:20] if repeat == -1 else rows
            for row in selected:
                stages.clear()
                body = json.dumps(dict(requestId=row['id'], query=row['question'], snapshotId=snapshot['snapshotId']))
                start = time.perf_counter()
                connection = http.client.HTTPConnection('127.0.0.1', server.port, timeout=60)
                connection.request('POST', '/api/projects/' + snapshot['projectId'] + '/query', body,
                                   {'Content-Type': 'application/json', 'X-DAG-GPS-Session': server.session_token})
                response = connection.getresponse()
                data = response.read()
                elapsed = (time.perf_counter() - start) * 1000
                connection.close()
                assert response.status == 200, (response.status, data[:400])
                packet = json.loads(data)
                assert packet['requestId'] == row['id']
                timing = dict(stages)
                timing['worker'] = timing['worker_including_validation'] - timing['validation']
                sample = dict(id=row['id'], repeat=repeat, ms=elapsed, stages=timing,
                              status=packet['status'], packetSha256=hashlib.sha256(data).hexdigest())
                if repeat == -2:
                    cold = sample
                if repeat >= 0:
                    samples.append(sample)
                    if len(samples) % 100 == 0:
                        print(out.name, len(samples), round(elapsed, 3), flush=True)
        rss = int(subprocess.check_output(['ps', '-p', str(os.getpid()), '-o', 'rss=']).strip())
        workers = [w.pid for w in server.workers._workers.values() if w.pid]
        worker_rss = {str(pid): int(subprocess.check_output(['ps', '-p', str(pid), '-o', 'rss=']).strip()) for pid in workers}
        report = dict(code=str(code), head=subprocess.check_output(['git', '-C', str(code), 'rev-parse', 'HEAD'], text=True).strip(),
                      snapshotSha256=hashlib.sha256(Path(args.snapshot).read_bytes()).hexdigest(),
                      inputsSha256=hashlib.sha256(Path(args.inputs).read_bytes()).hexdigest(),
                      latency=stats([s['ms'] for s in samples]), cold=cold,
                      stages={key: stats([s['stages'][key] for s in samples]) for key in cold['stages']},
                      pythonRssKiB=rss, workerRssKiB=worker_rss, maxRss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        (out / 'raw.json').write_text(json.dumps(samples))
        (out / 'summary.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2), flush=True)
    finally:
        server.shutdown()
        thread.join()


if __name__ == '__main__':
    main()
