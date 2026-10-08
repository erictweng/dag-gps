"""V1 onboarding contract. Legacy glob specs remain explicitly compatible."""
import re
import subprocess
from pathlib import Path


def repo_identity(repo):
    """Origin-derived identity, never a layer spec's hardcoded repository name."""
    try:
        remote = subprocess.check_output(['git', '-C', repo, 'remote', 'get-url', 'origin'], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'local:' + str(Path(repo).resolve())
    ssh = re.fullmatch(r'(?:[^@/]+@)?([^:/]+):(.+)', remote) if '://' not in remote else None
    if ssh:
        host, path = ssh.groups()
    elif '://' in remote:
        from urllib.parse import urlsplit
        parsed = urlsplit(remote)
        host, path = parsed.hostname, parsed.path.lstrip('/')
        if not host:
            return 'local:' + str(Path(repo).resolve())
    else:
        return 'local:' + str(Path(repo).resolve())
    path = path.removesuffix('.git').rstrip('/')
    return path if host.lower() == 'github.com' else host.lower() + '/' + path

DRAFT_SCHEMA = 'dag-gps-layer-draft/v1'
SPEC_SCHEMA = 'dag-gps-reviewed-layers/v1'
MAX_BYTES = 8 * 1024 * 1024


def validate_spec(spec, files, repo, commit, tops):
    """Validate authoring metadata and exact ownership before extraction/publication."""
    if not isinstance(spec, dict) or not isinstance(spec.get('layers'), list) or not spec['layers']:
        raise ValueError('Layer specification must contain nonempty layers')
    ids = set()
    for layer in spec['layers']:
        if not isinstance(layer, dict) or not isinstance(layer.get('id'), str) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,100}', layer['id']):
            raise ValueError('Invalid layer ID')
        if layer['id'] in ids or layer['id'] in files:
            raise ValueError('Duplicate/conflicting layer ID')
        ids.add(layer['id'])
        if not isinstance(layer.get('label'), str) or not layer['label'].strip() or len(layer['label']) > 500:
            raise ValueError('Invalid layer label')
        for key in ('desc', 'reason'):
            if key in layer and (not isinstance(layer[key], str) or len(layer[key]) > 5000):
                raise ValueError('Invalid layer ' + key)
        key = 'files' if 'files' in layer else 'globs'
        if not isinstance(layer.get(key), list) or not layer[key] or any(not isinstance(x, str) or not x for x in layer[key]):
            raise ValueError('Layer requires nonempty files or globs')
        if key == 'files' and (len(layer[key]) != len(set(layer[key])) or set(layer[key]) - set(files)):
            raise ValueError('Duplicate or unknown exact file ownership')
        if 'files' in layer and 'globs' in layer:
            raise ValueError('Use files OR globs, not both')
    if 'schema' not in spec and 'onboarding' not in spec:
        return  # Existing reviewed hand-authored glob specs predate the marker.
    if spec.get('schema') != SPEC_SCHEMA:
        raise ValueError('Draft is not publishable: review in layer editor and export reviewed layers')
    meta = spec.get('onboarding')
    if not isinstance(meta, dict) or meta.get('reviewed') is not True:
        raise ValueError('Explicit human review confirmation required')
    if spec.get('repo') != repo or meta.get('repo') != repo or meta.get('commit') != commit:
        raise ValueError('Onboarding repository/commit mismatch; regenerate draft')
    if meta.get('source_files') != files or meta.get('tops') != tops:
        raise ValueError('Onboarding inventory/extraction scope mismatch; use exported --tops or regenerate draft')
    if any('files' not in l for l in spec['layers']):
        raise ValueError('Reviewed onboarding requires exact per-file ownership')
    if not isinstance(meta.get('reference_warnings'), list) or any(not isinstance(x, str) for x in meta['reference_warnings']):
        raise ValueError('Reference migration warnings must remain visible')
    if spec.get('manual_edges'):
        raise ValueError('Onboarding v1 does not author manual edges')


def group_files(files):
    """Path-only proposals: parent folders, explicit root and helper naming, no inference."""
    import hashlib
    groups = {}
    for path in sorted(files):
        parent = path.rsplit('/', 1)[0] if '/' in path else '(root)'
        groups.setdefault(parent, []).append(path)
    out = []
    for folder, paths in sorted(groups.items()):
        helpers = folder.split('/')[-1].lower() in {'lib', 'utils', 'util', 'helpers', 'shared', 'common'}
        reason = ('Flat root source files; review entrypoint/helper ownership.' if folder == '(root)' else
                  'Helper-named folder; sharing is not inferred from its name.' if helpers else
                  'Same parent folder; not a claim of architectural responsibility.')
        out.append({'id': 'folder-' + hashlib.sha256(folder.encode()).hexdigest()[:16],
                    'label': folder, 'desc': reason, 'files': paths, 'reason': reason})
    return out
