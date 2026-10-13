#!/usr/bin/env python3
"""Validate real saved packets, bridge parity, and retrieve pinned source evidence."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.contracts import validate_evidence_packet
from app.context import build_context, git_dir_for, read_source

OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / 'artifacts/function-layer/honcho'
snapshot = json.loads((OUT / 'snapshot.json').read_text())
queries = json.loads((OUT / 'questions.json').read_text())
git_dir = git_dir_for(OUT / 'workspace/git-cache', snapshot)
packets = []
for i, query in enumerate(queries, 1):
    packet = json.loads((OUT / ('packet-%d.json' % i)).read_text())
    assert packet['query'] == query
    validate_evidence_packet(packet, snapshot)
    packets.append(packet)
context = build_context(git_dir, snapshot, packets[0])
assert context['files'][0]['start'] == packets[0]['sourceRefs'][0]['start']
(OUT / 'context.json').write_text(json.dumps(context, indent=2))
bridge = []
for tool, symbol, packet_index in [('find_symbols', 'create_messages_for_session', 0),
                                  ('get_callees', 'src/crud/message.py:create_messages', 1),
                                  ('get_callers', 'process_representation_tasks_batch', 2)]:
    request = {'tool': tool, 'projectId': snapshot['projectId'], 'snapshotId': snapshot['snapshotId'], 'args': {'symbol': symbol}}
    p = subprocess.run([sys.executable, str(ROOT / 'scripts/workspace_cli.py'), '--workspace', str(OUT / 'workspace')],
                       input=json.dumps(request), text=True, capture_output=True, timeout=60, check=True)
    response = json.loads(p.stdout)
    assert response['ok'], response
    assert response['result']['selectedNodeIds'] == packets[packet_index]['selectedNodeIds']
    validate_evidence_packet(response['result'], snapshot)
    bridge.append({'tool': tool, 'ok': True, 'selectedNodeIds': response['result']['selectedNodeIds']})
    if OUT.name in ('honcho-v2', 'honcho-v3'):
        request['args']['certainOnly'] = True
        certain = subprocess.run([sys.executable, str(ROOT / 'scripts/workspace_cli.py'), '--workspace', str(OUT / 'workspace')],
                                 input=json.dumps(request), text=True, capture_output=True, timeout=60, check=True)
        result = json.loads(certain.stdout)
        assert result['ok'], result
        expected = json.loads((OUT / ('certain-%d.json' % (packet_index + 1))).read_text())
        assert result['result']['selectedNodeIds'] == expected['selectedNodeIds']
        assert result['result']['selectedEdges'] == expected['selectedEdges']
        validate_evidence_packet(result['result'], snapshot)
        bridge[-1]['certainOnlyVerified'] = True
paths = {'src/routers/messages.py', 'src/crud/message.py', 'src/deriver/consumer.py',
         'src/deriver/deriver.py', 'src/routers/peers.py', 'src/dialectic/chat.py', 'src/dialectic/core.py'}
if OUT.name in ('honcho-v2', 'honcho-v3'):
    paths.update({'src/llm/__init__.py', 'src/llm/api.py', 'src/llm/executor.py', 'src/llm/backends/openai.py', 'src/llm/registry.py', 'src/llm/request_builder.py', 'src/llm/tool_loop.py',
                  'src/telemetry/logging.py', 'src/utils/representation.py', 'tests/bench/runner_common.py',
                  'src/telemetry/metrics_collector.py'})
source_dir = OUT / 'source'
source_dir.mkdir(exist_ok=True)
for path in sorted(paths):
    source = read_source(git_dir, snapshot, path, max_lines=3000)
    assert not source['truncated']
    (source_dir / path.replace('/', '__')).write_text('\n'.join(source['lines']) + '\n')
report = {'packetsValidated': len(packets), 'bridge': bridge, 'contextDefinitionStart': context['files'][0]['start'],
          'files': len(snapshot['inventory']), 'mappedFiles': snapshot['map']['meta']['counts']['files'],
          'counts': snapshot['map']['symbol_graph']['counts'], 'sourceFilesRetrieved': sorted(paths)}
(OUT / 'audit.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
