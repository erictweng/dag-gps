#!/usr/bin/env python3
"""Late-requested supplement; baseline uses pristine main, not current parser."""
import hashlib
import json
from pathlib import Path
import random
import subprocess

base = Path('artifacts/question-parser')
snapshot = json.loads((base / 'salesroom/snapshot.json').read_text())
pin = '5de5c0b4b64ca6579c5c5527fe09108fcf03a0ce'
assert snapshot['source']['commit'] == pin
repo = next(p for p in (base / 'workspace/git-cache').glob('*/repo.git') if pin in str(p))
nodes = {n['id']: n for n in snapshot['map']['nodes']}
rows = []


def add(questions, expected, targets, rationale='Pinned file/name exists; first lines source-checked.'):
    evidence = []
    for target in targets:
        n = nodes[target]
        path = n.get('path') or next(n['path'] for n in nodes.values() if n.get('layer') == target)
        data = subprocess.check_output(['git', '--git-dir=' + str(repo), 'show', pin + ':' + path])
        evidence.append({'nodeId': target, 'path': path, 'start': 1, 'sha256': hashlib.sha256(data).hexdigest()})
    for q in questions:
        rows.append({'id': 'sr-%03d' % (len(rows) + 1), 'question': q, 'expected': expected,
                     'targets': targets, 'operation': 'LOCATE', 'sourceEvidence': evidence, 'rationale': rationale})


add(['youtube', 'where is the youtube', 'where is the YOUTUBE', "where's youtube", 'wheres the youtube',
     'where is youtube located', 'where is the youtube file', 'where is youtube logic', 'where is youtube code',
     'where is the youtube module', 'find src/lib/youtube.ts', 'where is SRC/LIB/YOUTUBE.TS'], 'match', ['src/lib/youtube.ts'])
add(['db', 'where is the db', "where's the db", 'where is the DB', 'where is the db layer',
     'where is the database', 'where is the db module', 'where is the db file'], 'match', ['src/lib/db.ts'])
add(['src', 'where is the src', 'where is the src folder', 'where is the SRC directory'], 'choose',
    ['folder-91be6cfb7c9129b9', 'folder-e19e62e010f8b565', 'folder-3e95fbd4b5d32d26'],
    'No src parent node in the preview: offer real descendant folders rather than invent src.')
add(['where is repo', 'where is the repo file', 'where is repository'], 'match', ['src/lib/repo.ts'])
add(['where is env', 'where is environment', 'where is the ENV file'], 'match', ['src/lib/env.ts'])
add(['where is the config'], 'choose', ['next.config.mjs', 'postcss.config.mjs', 'tailwind.config.ts', 'vitest.config.ts'])
add(['where do we play videos', 'where is video playback'], 'choose', ['src/components/content/VideoPlayer.tsx'],
    'VideoPlayer.tsx renders an embedded YouTube player; TS BM25 names/paths may lack these concept words.')
add(['where do we persist room data'], 'choose', ['src/lib/db.ts', 'src/lib/repo.ts'], 'SQLite persistence documented at top of each file.')
add(['where is youtube.test.ts'], 'match', ['src/lib/__tests__/youtube.test.ts'])
add(['where is quantum banana teleporter', 'where is the lunar payroll processor',
     'where is the dinosaur genome assembler', 'where is the nonexistent_zyx_987',
     'where are embeddings created', 'where is the deriver queue', 'where is the llm',
     'where is the submarine sonar driver'], 'no-match', [], 'Absent responsibility or fabricated name in this sales-room application.')
rng = random.Random(3922)
order = list(range(len(rows)))
rng.shuffle(order)
holdout = set(order[:(len(rows) + 3) // 4])
for i, r in enumerate(rows):
    r['split'] = 'holdout' if i in holdout else 'dev'
with Path('eval/question_parser_salesroom.json').open('x') as f:
    json.dump({'schema': 'dag-gps-question-parser-eval/v1', 'pin': pin, 'seed': 3922,
               'provenance': 'Late operator supplement frozen after Honcho rules; baseline from pristine 7db31cd before salesroom tuning.',
               'rows': rows}, f, indent=2)
    f.write('\n')
legacy = base / 'main-code'
legacy.mkdir(exist_ok=True)
for name in ['scorer.js', 'query-service.js', 'router.js']:
    (legacy / name).write_bytes(subprocess.check_output(['git', 'show', '7db31cd:web/' + name]))
print({'cases': len(rows), 'holdout': len(holdout)})
