"""Loopback-only DAG GPS workspace service (local prototype, not a hosted server).

Boundary: binds 127.0.0.1/::1 only; rejects unexpected Host (DNS rebinding) and
cross-origin requests; every /api route needs the per-run session capability
header; bodies are bounded JSON; only explicit routes are served (no directory
serving, no CORS). Paths use opaque validated IDs, never request-supplied
filesystem paths. Python's http.server is documented as unsuitable for
production; this is a single-user local tool.

Runtime makes no model calls and never executes imported repository code.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import re
import secrets
import shutil
import sys
import threading
import time
import traceback
from collections import OrderedDict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.query_worker import QueryBusy, QueryTimeout, QueryWorkerError, WorkerPool  # noqa: E402
from app.repositories import RepositoryAcquisitionError, acquire_repository, parse_github_repository  # noqa: E402
from app.snapshots import SnapshotError, build_workspace_snapshot  # noqa: E402
from app.workspace_snapshot import canonical_json, load_publication, write_snapshot  # noqa: E402

MAX_BODY_BYTES = 64 * 1024
MAX_JOBS = 100
MAX_QUEUED_IMPORTS = 4
SESSION_HEADER = 'X-DAG-GPS-Session'
PROJECT_ID = re.compile(r'p-[0-9a-f]{20}\Z')
SNAPSHOT_ID = re.compile(r'[0-9a-f]{64}\Z')
JOB_ID = re.compile(r'j-[0-9a-f]{24}\Z')
COMMIT = re.compile(r'[0-9a-f]{40}\Z')
QUERY_FIELDS = {'snapshotId', 'requestId', 'query', 'continuation', 'chosenNodeId'}
STATIC = {
    '/': ('web/workspace.html', 'text/html; charset=utf-8'),
    '/workspace.js': ('web/workspace.js', 'text/javascript; charset=utf-8'),
    '/workspace.css': ('web/workspace.css', 'text/css; charset=utf-8'),
}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; "
       "img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


class ApiError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def project_id_for(repo: str) -> str:
    return 'p-' + hashlib.sha256(repo.lower().encode('utf-8')).hexdigest()[:20]


class WorkspaceStore:
    """Per-project immutable revisions under one private root."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        (self.root / 'projects').mkdir(parents=True, exist_ok=True)
        (self.root / 'git-cache').mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def project_dir(self, project_id: str) -> Path:
        if not PROJECT_ID.fullmatch(project_id):
            raise ApiError(404, 'Unknown project')
        return self.root / 'projects' / project_id

    def _index(self, project_id: str) -> Optional[dict[str, Any]]:
        path = self.project_dir(project_id) / 'project.json'
        if not path.is_file():
            return None
        return json.loads(path.read_text('utf-8'))

    def projects(self) -> list[dict[str, Any]]:
        out = []
        for entry in sorted((self.root / 'projects').iterdir()):
            if PROJECT_ID.fullmatch(entry.name):
                index = self._index(entry.name)
                if index:
                    out.append(index)
        return out

    def record(self, snapshot: dict[str, Any], snapshot_path: Path) -> dict[str, Any]:
        source = snapshot['source']
        pid = snapshot['projectId']
        with self._lock:
            index = self._index(pid) or {'projectId': pid, 'repo': source['repo'], 'url': source.get('url'),
                                         'snapshots': {}}
            entry = {'snapshotId': snapshot['snapshotId'], 'commit': source['commit'],
                     'path': str(snapshot_path.relative_to(self.root)), 'importedAt': int(time.time()),
                     'extractionState': snapshot.get('extractionState'),
                     'counts': snapshot['map'].get('meta', {}).get('counts')}
            index['snapshots'][snapshot['snapshotId']] = entry
            index['current'] = entry
            path = self.project_dir(pid) / 'project.json'
            tmp = path.with_suffix('.tmp')
            tmp.write_bytes(canonical_json(index))
            tmp.replace(path)
            return index

    def snapshot(self, project_id: str, snapshot_id: str) -> tuple[Path, dict[str, Any]]:
        if not SNAPSHOT_ID.fullmatch(snapshot_id or ''):
            raise ApiError(404, 'Unknown snapshot')
        index = self._index(project_id)
        entry = index and index['snapshots'].get(snapshot_id)
        if not entry:
            raise ApiError(404, 'Unknown snapshot for this project')
        path = (self.root / entry['path']).resolve()
        if self.root.resolve() not in path.parents:
            raise ApiError(404, 'Unknown snapshot')
        snapshot = json.loads(path.read_text('utf-8'))
        if snapshot.get('snapshotId') != snapshot_id or snapshot.get('projectId') != project_id:
            raise ApiError(409, 'Stored snapshot identity mismatch')
        return path, snapshot


class ImportManager:
    """Serialized background imports; job state is in memory for this run."""

    def __init__(self, store: WorkspaceStore, acquire: Callable[..., dict[str, Any]]) -> None:
        self.store = store
        self.acquire = acquire
        self.jobs: 'OrderedDict[str, dict[str, Any]]' = OrderedDict()
        self._lock = threading.Lock()
        self._run_lock = threading.Lock()
        self._queued = 0

    def submit(self, url: str, commit: Optional[str]) -> dict[str, Any]:
        repo = parse_github_repository(url)  # raises ValueError before any job/network
        with self._lock:
            if self._queued >= MAX_QUEUED_IMPORTS:
                raise ApiError(429, 'Too many imports queued; wait for one to finish')
            self._queued += 1
            job_id = 'j-' + secrets.token_hex(12)
            job = {'jobId': job_id, 'state': 'queued', 'url': url, 'repo': repo['owner'] + '/' + repo['repo'],
                   'commit': commit, 'events': [], 'error': None, 'projectId': None, 'snapshotId': None,
                   'createdAt': int(time.time())}
            self.jobs[job_id] = job
            while len(self.jobs) > MAX_JOBS:
                self.jobs.popitem(last=False)
        threading.Thread(target=self._run, args=(job,), daemon=True).start()
        return self.view(job_id)

    def view(self, job_id: str) -> dict[str, Any]:
        if not JOB_ID.fullmatch(job_id or ''):
            raise ApiError(404, 'Unknown import job')
        with self._lock:
            job = self.jobs.get(job_id)
            if job is None:
                raise ApiError(404, 'Unknown import job')
            return json.loads(json.dumps(job))

    def _event(self, job: dict[str, Any], stage: str, **extra: Any) -> None:
        safe = {k: v for k, v in extra.items() if isinstance(v, (str, int, float, bool)) or v is None}
        with self._lock:
            job['state'] = stage if stage in ('failed', 'ready') else 'running'
            job['events'].append(dict(safe, stage=stage, at=round(time.time(), 3)))

    def _run(self, job: dict[str, Any]) -> None:
        with self._run_lock:
            try:
                self._event(job, 'acquiring')
                acquisition = self.acquire(
                    job['url'], self.store.root / 'git-cache', job['commit'],
                    progress=lambda e: self._event(job, 'acquire:' + str(e.get('stage', 'progress'))))
                commit = acquisition['commit']
                pid = project_id_for(job['repo'])
                base = self.store.project_dir(pid) / 'commits' / commit
                base.mkdir(parents=True, exist_ok=True)

                def progress(event: dict[str, Any]) -> None:
                    stage = str(event.get('stage', 'progress'))
                    self._event(job, stage, files=event.get('files'))

                build_workspace_snapshot(acquisition, base / 'publication', progress=progress)
                snapshot = load_publication(base / 'publication', project_id=pid)
                snapshot_path = base / ('snapshot-%s.json' % snapshot['snapshotId'][:16])
                write_snapshot(snapshot, snapshot_path)
                self.store.record(snapshot, snapshot_path)
                with self._lock:
                    job.update(projectId=pid, snapshotId=snapshot['snapshotId'], commit=commit)
                self._event(job, 'ready')
            except (RepositoryAcquisitionError, SnapshotError, ValueError) as error:
                with self._lock:
                    job['error'] = str(error)[:500]
                self._event(job, 'failed')
            except Exception:  # pragma: no cover - unexpected internal failure
                traceback.print_exc()
                with self._lock:
                    job['error'] = 'Import failed (internal error; see server log)'
                self._event(job, 'failed')
            finally:
                with self._lock:
                    self._queued -= 1


class _Handler(BaseHTTPRequestHandler):
    server_version = 'DAG-GPS-Workspace'
    sys_version = ''
    protocol_version = 'HTTP/1.1'

    # -- plumbing --------------------------------------------------------------
    def log_message(self, fmt: str, *args: Any) -> None:  # no request logging (no tokens/paths in logs)
        return

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        self.send_header('Content-Security-Policy', CSP)
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)

    def _json(self, status: int, value: Any) -> None:
        self._send(status, json.dumps(value, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')

    def _check_boundary(self) -> None:
        app = self.server.app
        allowed = {'127.0.0.1:%d' % app.port, 'localhost:%d' % app.port, '[::1]:%d' % app.port}
        if self.headers.get('Host') not in allowed:
            raise ApiError(403, 'Unexpected Host header')
        origin = self.headers.get('Origin')
        if origin is not None and origin not in {'http://' + h for h in allowed}:
            raise ApiError(403, 'Cross-origin requests are not allowed')
        if self.headers.get('Sec-Fetch-Site') not in (None, 'same-origin', 'none'):
            raise ApiError(403, 'Cross-site requests are not allowed')

    def _check_session(self) -> None:
        supplied = self.headers.get(SESSION_HEADER) or ''
        if not hmac.compare_digest(supplied.encode('utf-8'), self.server.app.session_token.encode('utf-8')):
            raise ApiError(401, 'Missing or invalid session capability')

    def _body(self) -> dict[str, Any]:
        if (self.headers.get('Content-Type') or '').split(';')[0].strip() != 'application/json':
            raise ApiError(415, 'Expected application/json')
        try:
            length = int(self.headers.get('Content-Length') or '')
        except ValueError:
            raise ApiError(411, 'Content-Length required')
        if length < 0 or length > MAX_BODY_BYTES:
            self.close_connection = True
            raise ApiError(413, 'Request body too large')
        try:
            value = json.loads(self.rfile.read(length).decode('utf-8'))
        except (UnicodeDecodeError, ValueError):
            raise ApiError(400, 'Body must be JSON')
        if type(value) is not dict:
            raise ApiError(400, 'Body must be a JSON object')
        return value

    def _dispatch(self) -> None:
        try:
            self._check_boundary()
            path = self.path
            if '?' in path or '#' in path or '..' in path or '//' in path:
                raise ApiError(404, 'Not found')
            if self.command in ('GET', 'HEAD') and path in STATIC:
                name, kind = STATIC[path]
                self._send(200, (ROOT / name).read_bytes(), kind)
                return
            if not path.startswith('/api/'):
                raise ApiError(404, 'Not found')
            self._check_session()
            self._api(self.command, path.split('/')[2:])
        except ApiError as error:
            self._json(error.status, {'error': error.message})
        except Exception:  # pragma: no cover
            traceback.print_exc()
            self._json(500, {'error': 'Internal error'})

    do_GET = do_POST = do_HEAD = _dispatch

    def do_PUT(self) -> None:
        self._json(405, {'error': 'Method not allowed'})

    do_DELETE = do_PATCH = do_OPTIONS = do_PUT

    # -- API routes -------------------------------------------------------------
    def _api(self, method: str, parts: list[str]) -> None:
        app = self.server.app
        if method == 'GET' and parts == ['projects']:
            self._json(200, {'projects': app.store.projects()})
        elif method == 'POST' and parts == ['imports']:
            body = self._body()
            url, commit = body.get('url'), body.get('commit')
            if set(body) - {'url', 'commit'} or type(url) is not str:
                raise ApiError(400, 'Expected {"url": "https://github.com/owner/repo", "commit"?: sha}')
            if commit is not None and (type(commit) is not str or not COMMIT.fullmatch(commit)):
                raise ApiError(400, 'commit must be a full 40-character lowercase SHA')
            try:
                job = app.imports.submit(url.strip(), commit)
            except ValueError as error:
                raise ApiError(400, str(error))
            self._json(202, job)
        elif method == 'GET' and len(parts) == 2 and parts[0] == 'imports':
            self._json(200, app.imports.view(parts[1]))
        elif method == 'GET' and len(parts) == 4 and parts[0] == 'projects' and parts[2] == 'snapshots':
            _, snapshot = app.store.snapshot(parts[1], parts[3])
            self._json(200, snapshot)
        elif method == 'POST' and len(parts) == 3 and parts[0] == 'projects' and parts[2] == 'query':
            self._query(parts[1], self._body())
        else:
            raise ApiError(404, 'Not found')

    def _query(self, project_id: str, body: dict[str, Any]) -> None:
        app = self.server.app
        if set(body) - QUERY_FIELDS:
            raise ApiError(400, 'Unexpected query fields')
        for field in ('requestId', 'query'):
            if type(body.get(field)) is not str or not body[field] or len(body[field]) > 2048:
                raise ApiError(400, field + ' must be a nonempty bounded string')
        continuation = body.get('continuation')
        if continuation is not None and (type(continuation) is not str or not re.fullmatch(r'offset:\d{1,9}', continuation)):
            raise ApiError(400, 'Invalid continuation')
        chosen = body.get('chosenNodeId')
        if chosen is not None and (type(chosen) is not str or len(chosen) > 4096):
            raise ApiError(400, 'Invalid chosenNodeId')
        path, snapshot = app.store.snapshot(project_id, body.get('snapshotId') or '')
        if chosen is not None and chosen not in {n['id'] for n in snapshot['map']['nodes']}:
            raise ApiError(400, 'chosenNodeId is not a node in this snapshot')
        try:
            packet = app.workers.get(path, snapshot).query(body)
        except QueryBusy as error:
            raise ApiError(429, str(error))
        except QueryTimeout as error:
            raise ApiError(504, str(error))
        except QueryWorkerError as error:
            raise ApiError(422, str(error))
        self._json(200, packet)


class WorkspaceServer:
    def __init__(self, root: Any, *, host: str = '127.0.0.1', port: int = 8765,
                 acquire: Callable[..., dict[str, Any]] = acquire_repository,
                 worker_timeout: float = 10.0) -> None:
        if host not in ('127.0.0.1', '::1', 'localhost'):
            raise ValueError('The workspace service binds to loopback only')
        self.store = WorkspaceStore(Path(root))
        self.imports = ImportManager(self.store, acquire)
        self.workers = WorkerPool(timeout=worker_timeout)
        self.session_token = secrets.token_urlsafe(32)
        self.httpd = ThreadingHTTPServer(('127.0.0.1' if host == 'localhost' else host, port), _Handler)
        self.httpd.daemon_threads = True
        self.httpd.app = self
        self.port = self.httpd.server_address[1]

    @property
    def url(self) -> str:
        return 'http://127.0.0.1:%d/#session=%s' % (self.port, self.session_token)

    def serve_forever(self) -> None:
        self.httpd.serve_forever(poll_interval=0.2)

    def shutdown(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.workers.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Local DAG GPS workspace (loopback only).')
    parser.add_argument('--root', default=str(ROOT / 'artifacts' / 'workspace'),
                        help='private workspace directory (cache, snapshots)')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args(argv)
    if shutil.which('node') is None:
        print('Node.js is required for queries', file=sys.stderr)
        return 2
    server = WorkspaceServer(args.root, port=args.port)
    print('DAG GPS workspace running. Open this private link (it contains your session key):')
    print('  ' + server.url, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
