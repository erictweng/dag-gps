#!/usr/bin/env python3
"""One-time, source-checked question freeze; refuses to overwrite the frozen set."""
import hashlib
import json
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = '3922af856d78ec41133916deec4d821fa9c5a92e'
BASE = ROOT / 'artifacts/question-parser'
workspace = BASE / 'workspace'
repo = next(workspace.glob('git-cache/*/repo.git'))
snapshot = json.loads(next(workspace.glob('projects/*/commits/*/snapshot-*.json')).read_text())
assert snapshot['source']['commit'] == PIN
nodes = snapshot['map']['nodes'] + snapshot['map']['symbol_graph']['nodes']
by_id = {n['id']: n for n in nodes}
rows = []


def symbol(path, name):
    found = [n['id'] for n in nodes if n.get('path') == path and n.get('qualname') == name]
    assert len(found) == 1, (path, name, found)
    return found[0]


def add(questions, outcome, targets=(), operation='LOCATE', note='Literal name/path in pinned inventory and source.'):
    citations = []
    for ident in targets:
        n = by_id[ident]
        path = n.get('path')
        if n['kind'] == 'layer':
            owned = [f for f in snapshot['map']['nodes'] if f.get('layer') == ident]
            assert owned
            path = owned[0]['path']
        data = subprocess.check_output(['git', '--git-dir=' + str(repo), 'show', PIN + ':' + path])
        start = n.get('start', 1)
        if n['kind'] == 'symbol':
            assert n['name'] in data.decode().splitlines()[start - 1]
        citations.append({'nodeId': ident, 'path': path, 'start': start, 'sha256': hashlib.sha256(data).hexdigest()})
    for question in questions:
        rows.append({'id': 'qp-%03d' % (len(rows) + 1), 'question': question,
                     'expected': outcome, 'targets': list(targets), 'operation': operation,
                     'sourceEvidence': citations, 'rationale': note})


add(['where is the db', 'where is the DB', "where's the db", 'wheres the db',
     'WHERE IS THE DB?!', 'where is db located', 'where is the db file',
     'find the db module', 'where is db logic', 'where is db code',
     'where is db stuff', 'where is the db part', 'what is db', "what's db", 'whats db',
     'where is src/db.py', 'where is SRC/DB.PY', 'locate src/db', 'where is the db script'], 'match', ['src/db.py'])
add(['where is the src', 'where is the src folder', 'where is the src directory',
     'locate src dir', 'find src package', "where's the src folder"], 'match', ['folder-25a6634263c1b1f6'])
add(['where is the database layer', 'where is database', 'where is the database folder'], 'match', ['folder-3549b0028b75d981'])
add(['where is config', 'where is CONFIG', "where's config", 'where is the config file',
     'where is the configuration file', 'where is the settings file'], 'choose',
    ['src/config.py', 'honcho-cli/src/honcho_cli/config.py', 'harness-plugin-core/src/config.ts', 'mcp/src/config.ts'])
add(['where is src/config.py', 'where is src/config', 'where is src/config.py located'], 'match', ['src/config.py'])
add(['where is msg', 'where is message', 'where is the msg file'], 'choose',
    ['src/crud/message.py', 'sdks/python/src/honcho/message.py', 'honcho-cli/src/honcho_cli/commands/message.py'])
add(['where is llm', 'where is the llm folder', 'where is the LLM directory'], 'choose',
    ['folder-2204ae27992d53cf', 'folder-d164207056a18ac3'])
for name, path, qual in [
    ('get_pool_stats', 'src/db.py', 'get_pool_stats'),
    ('EmbeddingClient', 'src/embedding_client.py', 'EmbeddingClient'),
    ('QueueManager', 'src/deriver/queue_manager.py', 'QueueManager'),
    ('deliver_webhook', 'src/webhooks/webhook_delivery.py', 'deliver_webhook'),
    ('EmbeddingClient.embed', 'src/embedding_client.py', 'EmbeddingClient.embed')]:
    target = symbol(path, qual)
    kind = 'method' if '.' in qual else 'class' if name[0].isupper() else 'function'
    add([f'where is {name} defined', f'find {kind} {name}', f'where is the {kind} {name}',
         f'WHERE IS {name.upper()} DEFINED', f"where's {name}"], 'match', [target])
auth = symbol('src/security.py', 'auth')
add(['where is auth', 'where is the auth function', 'where is authentication'], 'match', [auth],
    note='src/security.py auth authenticates JWT; require_auth wraps it as a dependency.')
for questions, targets, note in [
    (['where do we store messages', 'where are messages stored'], ['src/crud/message.py', symbol('src/crud/message.py', 'create_messages')], 'create_messages persists session messages in the database at lines 385 onward.'),
    (['where are embeddings created', 'where do we embed text'], ['src/embedding_client.py', symbol('src/embedding_client.py', 'EmbeddingClient.embed'), symbol('src/embedding_client.py', '_EmbeddingClient.embed')], 'Embedding client owns provider embedding calls.'),
    (['what handles webhooks', 'where do we deliver webhook events'], ['src/webhooks/webhook_delivery.py', symbol('src/webhooks/webhook_delivery.py', 'deliver_webhook'), 'folder-4710e5ed8b11c0a2'], 'deliver_webhook delivers an event to configured endpoints.'),
    (['where is the deriver queue'], ['src/deriver/queue_manager.py', symbol('src/deriver/queue_manager.py', 'QueueManager')], 'QueueManager claims/processes deriver queue items.'),
    (['where do we verify JWT tokens'], ['src/security.py', symbol('src/security.py', 'verify_jwt')], 'verify_jwt verifies and decodes JWT parameters.'),
    (['where do we split text into chunks'], [symbol('src/embedding_client.py', '_chunk_text_with_tokens'), 'src/embedding_client.py'], 'Docstring explicitly says split text into chunks within token limits.'),
    (['where do we load TOML configuration'], [symbol('src/config.py', 'load_toml_config'), 'src/config.py'], 'Docstring: load configuration from TOML file if it exists.'),
    (['where is semantic message search'], [symbol('src/crud/message.py', '_semantic_search_messages'), symbol('src/crud/message.py', 'search_messages'), 'src/crud/message.py'], 'Source implements semantic similarity search.')]:
    add(questions, 'choose', targets, note=note)
for q in ['who invokes get_pool_stats', 'where is get_pool_stats called from', 'what calls get_pool_stats']:
    add([q], 'match', [symbol('src/db.py', 'get_pool_stats')], operation='CALLERS')
add(['what does src/db.py depend on', 'dependencies of src/db.py'], 'match', ['src/db.py'], operation='UPSTREAM')
add(['quantum banana teleporter', 'where is the lunar payroll processor', 'where is the unicorn stables',
     'where is nonexistent_zyx_987', 'find nonexistent_zyx_987.py', 'where is nonexistent/phantom.py',
     'where is the cryptocurrency mining rig', 'where is the pizza oven controller',
     'where is the submarine sonar driver', 'where is the dinosaur genome assembler',
     'where is the interstellar autopilot', 'where is the chess grandmaster engine',
     'where is the volcano eruption predictor', 'where is the watercolor rasterizer',
     'where is the dental xray classifier', 'where is the fax modem firmware',
     'where is the penguin migration simulator', 'where is the orbital rocket thruster',
     'where is the waffle batter dispenser', 'where is the holographic dragon renderer'], 'no-match',
    note='Absent requested responsibility: no corresponding path/definition in the pinned inventory; arbitrary shared words are not evidence of this concept.')
assert len(rows) >= 80
assert len({r['question'] for r in rows}) == len(rows)
rng = random.Random(3922)
order = list(range(len(rows)))
rng.shuffle(order)
holdout = set(order[:(len(rows) + 3) // 4])
for i, row in enumerate(rows):
    row['split'] = 'holdout' if i in holdout else 'dev'
out = ROOT / 'eval/question_parser.json'
with out.open('x') as f:
    json.dump({'schema': 'dag-gps-question-parser-eval/v1', 'seed': 3922, 'pin': PIN,
               'provenance': 'source-checked worker draft; not user accuracy; freeze before implementation',
               'rows': rows}, f, indent=2)
    f.write('\n')
(BASE / 'baseline-snapshot.json').write_text(json.dumps(snapshot))
print(json.dumps({'cases': len(rows), 'holdout': len(holdout), 'no-match': sum(r['expected'] == 'no-match' for r in rows)}))
