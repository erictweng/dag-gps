"""Persistent trusted Node query worker with a bounded JSON-lines protocol.

One child process per snapshot answers requests serially. Every reply must echo
the request ID and pass the frozen evidence contract against the snapshot this
manager was constructed with, so a worker cannot substitute another
project/revision. Timeouts kill the process group and restart on next use.
No shell; the default command runs only the installed DAG GPS worker script.
"""
from __future__ import annotations

import collections
import json
import os
import queue
import shutil
import signal
import subprocess
import threading
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from app.contracts import ContractError, validate_evidence_packet

ROOT = Path(__file__).resolve().parents[1]
WORKER_SCRIPT = ROOT / 'scripts' / 'query_worker.cjs'
MAX_REPLY_BYTES = 2 * 1024 * 1024
MAX_STDERR_BYTES = 16 * 1024
DEFAULT_TIMEOUT = 10.0
MAX_WAITING = 8


class QueryWorkerError(RuntimeError):
    pass


class QueryTimeout(QueryWorkerError):
    pass


class QueryBusy(QueryWorkerError):
    pass


class QueryWorker:
    def __init__(self, snapshot_path: Any, snapshot: Mapping[str, Any], *,
                 command: Optional[Sequence[str]] = None, timeout: float = DEFAULT_TIMEOUT,
                 max_waiting: int = MAX_WAITING) -> None:
        self.snapshot_path = Path(snapshot_path)
        self.snapshot = snapshot
        node = shutil.which('node')
        if command is None and node is None:
            raise QueryWorkerError('Node.js is required for the query worker')
        self.command = list(command) if command else [node, str(WORKER_SCRIPT), str(self.snapshot_path)]
        self.timeout = float(timeout)
        self._lock = threading.Lock()
        self._waiting = threading.BoundedSemaphore(max_waiting)
        self._process: Optional[subprocess.Popen] = None
        self._lines: 'queue.Queue[Any]' = queue.Queue()
        self._stderr: 'collections.deque[str]' = collections.deque()
        self._stderr_size = 0

    # -- lifecycle -----------------------------------------------------------
    @property
    def pid(self) -> Optional[int]:
        return self._process.pid if self._process else None

    def __enter__(self) -> 'QueryWorker':
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()

    def _start(self) -> None:
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'NODE_OPTIONS': ''}
        self._lines = queue.Queue()
        self._process = subprocess.Popen(
            self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(ROOT), env=env, start_new_session=True)
        threading.Thread(target=self._read_stdout, args=(self._process, self._lines), daemon=True).start()
        threading.Thread(target=self._read_stderr, args=(self._process,), daemon=True).start()

    def _read_stdout(self, process: subprocess.Popen, lines: 'queue.Queue[Any]') -> None:
        stream = process.stdout
        while True:
            line = stream.readline(MAX_REPLY_BYTES + 1)
            if not line:
                lines.put(EOFError())
                return
            if len(line) > MAX_REPLY_BYTES or not line.endswith(b'\n'):
                lines.put(QueryWorkerError('Worker reply too large'))
                return
            lines.put(line)

    def _read_stderr(self, process: subprocess.Popen) -> None:
        for raw in iter(lambda: process.stderr.read(4096), b''):
            text = raw.decode('utf-8', 'replace')
            self._stderr.append(text)
            self._stderr_size += len(text)
            while self._stderr_size > MAX_STDERR_BYTES and self._stderr:
                dropped = self._stderr.popleft()
                self._stderr_size -= len(dropped)

    def stderr_tail(self) -> str:
        return ''.join(self._stderr)[-MAX_STDERR_BYTES:]

    def _kill(self) -> None:
        process, self._process = self._process, None
        if process is None:
            return
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        for stream in (process.stdin, process.stdout, process.stderr):
            try:
                stream.close()
            except Exception:
                pass

    def close(self) -> None:
        with self._lock:
            self._kill()

    # -- protocol ------------------------------------------------------------
    def query(self, request: Mapping[str, Any]) -> dict[str, Any]:
        request_id = request.get('requestId')
        if type(request_id) is not str or not request_id:
            raise QueryWorkerError('requestId is required')
        if not self._waiting.acquire(blocking=False):
            raise QueryBusy('Query queue is full; retry shortly')
        try:
            if not self._lock.acquire(timeout=self.timeout):
                raise QueryBusy('Query worker is busy; retry shortly')
            try:
                return self._query_locked(request, request_id)
            finally:
                self._lock.release()
        finally:
            self._waiting.release()

    def _query_locked(self, request: Mapping[str, Any], request_id: str) -> dict[str, Any]:
        if self._process is None or self._process.poll() is not None:
            self._kill()
            self._start()
        line = (json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8')
        try:
            self._process.stdin.write(line)
            self._process.stdin.flush()
        except (BrokenPipeError, OSError):
            self._exited()
        try:
            item = self._lines.get(timeout=self.timeout)
        except queue.Empty:
            self._kill()
            raise QueryTimeout('Query exceeded %.1f s; worker restarted' % self.timeout)
        if isinstance(item, EOFError):
            self._exited()
        if isinstance(item, Exception):
            self._kill()
            raise item
        try:
            reply = json.loads(item.decode('utf-8'))
        except ValueError:
            self._kill()
            raise QueryWorkerError('Worker reply was not JSON')
        if type(reply) is not dict or type(reply.get('ok')) is not bool:
            raise QueryWorkerError('Malformed worker reply')
        if not reply['ok']:
            if reply.get('requestId') not in (request_id, None):
                self._kill()
                raise QueryWorkerError('Worker reply has a mismatched request ID')
            raise QueryWorkerError(str(reply.get('error') or 'Query failed')[:500])
        packet = reply.get('packet')
        if type(packet) is not dict or packet.get('requestId') != request_id:
            self._kill()
            raise QueryWorkerError('Worker reply has a mismatched request ID')
        try:
            validate_evidence_packet(packet, self.snapshot)
        except ContractError as error:
            self._kill()
            raise QueryWorkerError('Worker packet failed the evidence contract: %s' % error)
        return packet

    def _exited(self) -> None:
        process = self._process
        code = process.wait(timeout=5) if process else None
        detail = self.stderr_tail().strip().splitlines()[-1:] or ['']
        self._kill()
        raise QueryWorkerError('Query worker exited (%s): %s' % (code, detail[0][:300]))


class WorkerPool:
    """At most ``size`` live workers, keyed by snapshot ID (least recently used evicted)."""

    def __init__(self, size: int = 4, **options: Any) -> None:
        self.size = size
        self.options = options
        self._workers: 'collections.OrderedDict[str, QueryWorker]' = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, snapshot_path: Path, snapshot: Mapping[str, Any]) -> QueryWorker:
        key = snapshot['snapshotId']
        with self._lock:
            worker = self._workers.pop(key, None)
            if worker is None:
                worker = QueryWorker(snapshot_path, snapshot, **self.options)
            self._workers[key] = worker
            while len(self._workers) > self.size:
                _, old = self._workers.popitem(last=False)
                old.close()
            return worker

    def close(self) -> None:
        with self._lock:
            for worker in self._workers.values():
                worker.close()
            self._workers.clear()
