"""Validate curated source walkthroughs and compile only cited immutable excerpts."""
import copy
import re
import subprocess
from pathlib import PurePosixPath


def compile_tours(spec, map_data, repo):
    if not isinstance(spec, dict) or type(spec.get('version')) is not int or spec.get('version') != 1:
        raise ValueError('Tours require schema version 1')
    sha = spec.get('commit', '')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Tours require exact audited commit SHA')
    if spec.get('repo') != map_data['meta']['repo']:
        raise ValueError('Tours repository mismatch')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True)
    pinned = git('rev-parse', '--verify', sha + '^{commit}').strip()
    mapped = git('rev-parse', '--verify', map_data['meta'].get('snapshot_commit', map_data['meta']['commit']) + '^{commit}').strip()
    if pinned != sha or mapped != sha:
        raise ValueError('Stale tours: map and audited commit must match exactly')
    nodes = {n['id']: n for n in map_data['nodes']}
    files = {n.get('path'): n['id'] for n in map_data['nodes'] if n['kind'] == 'file'}
    result = copy.deepcopy(spec)
    cache = {}
    def text(value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError('Missing tour narration or symbol')
    def ids(values):
        if not isinstance(values, list) or not values or any(not isinstance(v, str) for v in values) or len(set(values)) != len(values) or any(v not in nodes for v in values):
            raise ValueError('Unknown or duplicate tour node IDs')
    def evidence(entries):
        if not isinstance(entries, list) or not entries:
            raise ValueError('Missing source evidence')
        for e in entries:
            if not isinstance(e, dict):
                raise ValueError('Evidence must be an object')
            path = e.get('path', '')
            if not isinstance(path, str) or path not in files or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
                raise ValueError('Evidence must reference a mapped source file')
            text(e.get('symbol'))
            if path not in cache:
                cache[path] = git('show', sha + ':' + path).splitlines()
            lines = cache[path]
            start, end = e.get('start'), e.get('end')
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines) or end - start > 49:
                raise ValueError('Invalid evidence line bounds (maximum 50 lines)')
            excerpt = '\n'.join(lines[start - 1:end])
            if 'excerpt' in e and e['excerpt'] != excerpt:
                raise ValueError('Evidence excerpt does not match audited source')
            e['excerpt'] = excerpt
            e['nodeId'] = files[path]
    tours = result.get('tours')
    if not isinstance(tours, list):
        raise ValueError('Missing tours array')
    seen = set()
    for tour in tours:
        if not isinstance(tour, dict):
            raise ValueError('Tour must be an object')
        text(tour.get('id')); text(tour.get('title')); text(tour.get('overview'))
        if tour['id'] in seen:
            raise ValueError('Duplicate tour ID')
        seen.add(tour['id'])
        queries = tour.get('queries')
        if not isinstance(queries, list) or not queries:
            raise ValueError('Missing explicit tour queries')
        for q in queries: text(q)
        steps = tour.get('steps')
        if not isinstance(steps, list) or not steps:
            raise ValueError('Missing ordered steps')
        involved = set()
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError('Step must be an object')
            ids(step.get('nodeIds'))
            involved.update(step['nodeIds'])
            for field in ('title', 'does', 'receives', 'passes', 'explanation'):
                text(step.get(field))
            evidence(step.get('evidence'))
            if any(e['nodeId'] not in step['nodeIds'] for e in step['evidence']):
                raise ValueError('Step evidence not attached to its node')
        links = tour.get('links')
        if not isinstance(links, list):
            raise ValueError('Missing typed links')
        for link in links:
            if not isinstance(link, dict) or not isinstance(link.get('from'), str) or not isinstance(link.get('to'), str):
                raise ValueError('Link requires string endpoints')
            if link.get('from') not in involved or link.get('to') not in involved:
                raise ValueError('Unknown tour link endpoint')
            if link.get('type') not in ('import', 'http', 'message', 'spawn', 'data') or link.get('direction') != 'from-to' or link.get('status') not in ('source-supported', 'inferred', 'unverified'):
                raise ValueError('Invalid typed/directed tour link')
            text(link.get('label')); evidence(link.get('evidence'))
            if link['type'] == 'import' and not any(e['from'] == link['from'] and e['to'] == link['to'] and e['type'] == 'import' for e in map_data['file_edges']):
                raise ValueError('Import link absent from import graph')
    queries = [q.strip().lower() for t in tours for q in t['queries']]
    if len(queries) != len(set(queries)):
        raise ValueError('Ambiguous tour queries')
    return result
