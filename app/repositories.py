"""Safe, token-free acquisition of immutable public GitHub commits.

This module never checks out or executes imported source.  The public acquisition
entry point accepts only canonical GitHub repository roots.  A private local
transport adapter exists solely for synthetic mechanical tests.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import time
from typing import Any, Callable, Mapping, Optional
from urllib.parse import urlsplit


_COMMIT = re.compile(r'[0-9a-f]{40}\Z')
_SEGMENT = re.compile(r'[A-Za-z0-9_.-]+\Z')
_CACHE_MARKER = '.dag-gps-repository-cache-v1'
_WRITER_LOCK = '.writer.lock'
_METADATA_VERSION = 1
_TRUSTED_GIT_CANDIDATES = ('/usr/bin/git',)
_DEFAULT_LIMITS = {
    'timeout_seconds': 60.0,
    'max_cache_bytes': 1024 * 1024 * 1024,
    'max_entries': 32,
    'max_git_output_bytes': 1024 * 1024,
}


class RepositoryAcquisitionError(RuntimeError):
    """A repository could not be safely acquired or validated."""


class RepositoryTimeout(RepositoryAcquisitionError):
    pass


class RepositoryCancelled(RepositoryAcquisitionError):
    pass


def parse_github_repository(value: str) -> dict[str, str]:
    """Parse an exact canonical ``https://github.com/owner/repository`` root.

    The canonical policy rejects a trailing slash and ``.git`` clone suffix.
    Input is never stripped, decoded, lowercased, or otherwise repaired.
    """
    if type(value) is not str or not value or len(value) > 2048:
        raise ValueError('Use https://github.com/owner/repository')
    if any(ord(char) <= 32 or ord(char) == 127 for char in value) or '%' in value:
        raise ValueError('GitHub repository URL contains ambiguous characters')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or parsed.netloc != 'github.com' or
            parsed.username is not None or parsed.password is not None or
            parsed.port is not None or parsed.query or parsed.fragment):
        raise ValueError('Use https://github.com/owner/repository')
    if not parsed.path.startswith('/') or parsed.path.endswith('/'):
        raise ValueError('Use a canonical repository root without a trailing slash')
    parts = parsed.path[1:].split('/')
    if (len(parts) != 2 or any(not part or part in {'.', '..'} or
                               not _SEGMENT.fullmatch(part) for part in parts)):
        raise ValueError('Expected a repository root, not a file or branch URL')
    owner, repo = parts
    if repo.endswith('.git'):
        raise ValueError('Use the browser repository root without a .git suffix')
    return {'owner': owner, 'repo': repo}


def _cancelled(cancel: Any) -> bool:
    if cancel is None:
        return False
    if callable(cancel):
        return bool(cancel())
    checker = getattr(cancel, 'is_set', None)
    return bool(checker()) if callable(checker) else bool(cancel)


def _safe_git_environment() -> dict[str, str]:
    keep = ('TMPDIR', 'LANG', 'LC_ALL', 'LC_CTYPE', 'SYSTEMROOT')
    env = {key: os.environ[key] for key in keep if key in os.environ}
    env.update({
        'GIT_TERMINAL_PROMPT': '0',
        'GIT_CONFIG_NOSYSTEM': '1',
        'GIT_CONFIG_GLOBAL': '/dev/null',
        'GIT_OPTIONAL_LOCKS': '0',
        'GIT_NO_REPLACE_OBJECTS': '1',
        'GIT_ASKPASS': '/usr/bin/false',
        'GIT_SSH_COMMAND': '/usr/bin/false',
    })
    return env


def _validated_git_executable(executable: Optional[str]) -> str:
    """Return an absolute, regular executable without consulting PATH."""
    candidates = (executable,) if executable is not None else _TRUSTED_GIT_CANDIDATES
    for candidate in candidates:
        if type(candidate) is not str or not os.path.isabs(candidate):
            continue
        try:
            mode = os.lstat(candidate).st_mode
        except OSError:
            continue
        if stat.S_ISREG(mode) and not stat.S_ISLNK(mode) and os.access(candidate, os.X_OK):
            return candidate
    if executable is None:
        raise RepositoryAcquisitionError('No trusted absolute Git executable is available')
    raise ValueError('Git executable must be an absolute executable regular file')


def _terminate_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    else:
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
    # Reap and close subprocess pipes after group termination.
    process.communicate()


def _tree_bytes_during_write(path: Optional[Path]) -> int:
    if path is None or not path.exists():
        return 0
    total = 0
    for base, _, files in os.walk(path, followlinks=False):
        for name in files:
            item = Path(base) / name
            if not item.is_symlink():
                try:
                    total += item.stat().st_size
                except FileNotFoundError:
                    pass
    return total


def _run_git(
    args: list[str], *, cwd: Optional[Path] = None, input_data: Any = None,
    text: bool = True, timeout: float = 60.0, cancel: Any = None,
    allow_file_protocol: bool = False, executable: Optional[str] = None,
    check: bool = True,
    max_output_bytes: int = 1024 * 1024, watch_path: Optional[Path] = None,
    max_disk_bytes: Optional[int] = None,
) -> subprocess.CompletedProcess:
    """Run fixed Git argv with isolated config, bounded lifetime, and group cleanup.

    ``input_data`` and text/binary output are retained for later read-only object
    helpers.  No shell is used.  File transport is private synthetic-test only.
    """
    protocol = 'always' if allow_file_protocol else 'never'
    command = [
        _validated_git_executable(executable),
        '-c', 'protocol.allow=never',
        '-c', 'protocol.https.allow=always',
        '-c', 'protocol.file.allow=' + protocol,
        '-c', 'http.followRedirects=false',
        '-c', 'credential.helper=',
        '-c', 'core.hooksPath=/dev/null',
        '-c', 'core.fsmonitor=false',
        '-c', 'fetch.recurseSubmodules=false',
        *args,
    ]
    process = subprocess.Popen(
        command, cwd=str(cwd) if cwd else None, env=_safe_git_environment(),
        stdin=subprocess.PIPE if input_data is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
        start_new_session=True, shell=False,
    )
    started = time.monotonic()
    pending_input = input_data
    while True:
        if _cancelled(cancel):
            _terminate_group(process)
            raise RepositoryCancelled('Repository acquisition cancelled')
        remaining = timeout - (time.monotonic() - started)
        if remaining <= 0:
            _terminate_group(process)
            raise RepositoryTimeout('Git operation exceeded its deadline')
        try:
            stdout, stderr = process.communicate(input=pending_input, timeout=min(0.05, remaining))
            break
        except subprocess.TimeoutExpired as error:
            pending_input = None
            observed = 0
            for output in (error.output, error.stderr):
                if output is not None:
                    observed += len(output.encode('utf-8') if isinstance(output, str) else output)
            if observed > max_output_bytes:
                _terminate_group(process)
                raise RepositoryAcquisitionError('Git output exceeded its safety limit')
            if max_disk_bytes is not None and _tree_bytes_during_write(watch_path) > max_disk_bytes:
                _terminate_group(process)
                raise RepositoryAcquisitionError('Repository exceeds the configured cache quota')
    output_size = sum(
        len(output.encode('utf-8') if isinstance(output, str) else output)
        for output in (stdout, stderr) if output is not None
    )
    if output_size > max_output_bytes:
        raise RepositoryAcquisitionError('Git output exceeded its safety limit')
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if check and result.returncode:
        detail = stderr if isinstance(stderr, str) else stderr.decode('utf-8', 'replace')
        detail = detail.strip().replace('\n', ' ')[:500]
        raise RepositoryAcquisitionError('Git operation failed' + (': ' + detail if detail else ''))
    return result


def _limits(value: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    result = dict(_DEFAULT_LIMITS)
    if value is not None:
        if type(value) is not dict or set(value) - set(result):
            raise ValueError('Unknown repository acquisition limit')
        result.update(value)
    timeout = result['timeout_seconds']
    if type(timeout) not in (int, float) or isinstance(timeout, bool) or timeout <= 0 or timeout > 600:
        raise ValueError('timeout_seconds must be between 0 and 600')
    for name in ('max_cache_bytes', 'max_entries', 'max_git_output_bytes'):
        if type(result[name]) is not int or result[name] < 1:
            raise ValueError(name + ' must be a positive integer')
    return result


def _notify(progress: Optional[Callable[[dict[str, Any]], None]], stage: str, **values: Any) -> None:
    if progress is not None:
        progress({'stage': stage, **values})


def _preflight_tree(path: Path) -> None:
    """Reject links and special files without following them.

    This is a fail-closed preflight, not protection against a hostile same-user
    process racing filesystem changes after validation.
    """
    try:
        root_mode = os.lstat(path).st_mode
    except OSError as error:
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid path') from error
    if stat.S_ISLNK(root_mode):
        raise RepositoryAcquisitionError('Repository cache contains a symbolic link')
    if not stat.S_ISDIR(root_mode):
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid path')
    pending = [path]
    while pending:
        directory = pending.pop()
        try:
            children = list(os.scandir(directory))
        except OSError as error:
            raise RepositoryAcquisitionError('Repository cache entry is poisoned: unreadable path') from error
        for child in children:
            try:
                mode = child.stat(follow_symlinks=False).st_mode
            except OSError as error:
                raise RepositoryAcquisitionError('Repository cache entry is poisoned: unreadable path') from error
            if stat.S_ISLNK(mode):
                raise RepositoryAcquisitionError('Repository cache contains a symbolic link')
            if stat.S_ISDIR(mode):
                pending.append(Path(child.path))
            elif not stat.S_ISREG(mode):
                raise RepositoryAcquisitionError('Repository cache entry contains a special file')


def _prepare_cache_root(cache_root: Any) -> Path:
    if isinstance(cache_root, bytes):
        raise ValueError('cache_root must be a filesystem path')
    root = Path(cache_root).expanduser()
    if root.exists() and root.is_symlink():
        raise RepositoryAcquisitionError('Cache root may not be a symbolic link')
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve()
    marker = root / _CACHE_MARKER
    if not marker.exists():
        if any(root.iterdir()):
            raise RepositoryAcquisitionError('Refusing to use a directory that is not an owned cache')
        marker.write_text('1\n', encoding='ascii')
    elif marker.is_symlink() or marker.read_text(encoding='ascii') != '1\n':
        raise RepositoryAcquisitionError('Invalid repository cache ownership marker')
    return root


def _entry_path(root: Path, repo_id: str, commit: str) -> Path:
    repo_key = hashlib.sha256(repo_id.encode('utf-8')).hexdigest()[:24]
    entry = root / ('repo-' + repo_key + '-' + commit)
    if entry.parent.resolve() != root:
        raise RepositoryAcquisitionError('Cache path escaped its root')
    return entry


def _metadata(entry: Path) -> dict[str, Any]:
    try:
        value = json.loads((entry / 'metadata.json').read_text(encoding='utf-8'))
    except (OSError, ValueError, UnicodeError) as error:
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid metadata') from error
    if type(value) is not dict:
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid metadata')
    return value


def _reject_git_object_indirection(git_dir: Path) -> None:
    forbidden = (
        git_dir / 'refs' / 'replace',
        git_dir / 'info' / 'grafts',
        git_dir / 'objects' / 'info' / 'alternates',
        git_dir / 'objects' / 'info' / 'http-alternates',
    )
    if any(path.exists() for path in forbidden):
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: object indirection')
    packed_refs = git_dir / 'packed-refs'
    if packed_refs.exists():
        try:
            packed = packed_refs.read_text(encoding='ascii')
        except (OSError, UnicodeError) as error:
            raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid refs') from error
        if any(' refs/replace/' in line for line in packed.splitlines()):
            raise RepositoryAcquisitionError('Repository cache entry is poisoned: replacement ref')


def _validate_entry(
    entry: Path, *, repo_id: str, url: str, commit: str, timeout: float,
    cancel: Any, allow_file_protocol: bool, max_output_bytes: int,
) -> Path:
    if entry.is_symlink() or not entry.is_dir():
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: invalid path')
    _preflight_tree(entry)
    expected = {'version': _METADATA_VERSION, 'repo_id': repo_id, 'url': url, 'commit': commit}
    if _metadata(entry) != expected:
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: identity mismatch')
    git_dir = entry / 'repo.git'
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: missing Git directory')
    _reject_git_object_indirection(git_dir)
    config_path = git_dir / 'config'
    try:
        configs = _run_git(
            ['config', '--file', str(config_path), '--no-includes', '--name-only', '--list'],
            cwd=entry.parent, timeout=timeout, cancel=cancel,
            allow_file_protocol=allow_file_protocol, max_output_bytes=max_output_bytes,
        ).stdout.splitlines()
    except RepositoryAcquisitionError as error:
        raise RepositoryAcquisitionError(
            'Repository cache entry is poisoned: unsafe config'
        ) from error
    allowed_config = {
        'core.repositoryformatversion', 'core.filemode', 'core.bare',
        'core.ignorecase', 'core.precomposeunicode',
    }
    lowered = [name.lower() for name in configs]
    if (len(lowered) != len(set(lowered)) or not set(lowered).issubset(allowed_config)
            or 'core.repositoryformatversion' not in lowered or 'core.bare' not in lowered):
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: unsafe config')
    bare = _run_git(
        ['--git-dir', str(git_dir), 'rev-parse', '--is-bare-repository'], timeout=timeout,
        cancel=cancel, allow_file_protocol=allow_file_protocol, max_output_bytes=max_output_bytes,
    ).stdout.strip()
    if bare != 'true':
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: not bare')
    kind = _run_git(
        ['--git-dir', str(git_dir), 'cat-file', '-t', commit], timeout=timeout,
        cancel=cancel, allow_file_protocol=allow_file_protocol, check=False,
        max_output_bytes=max_output_bytes,
    )
    if kind.returncode or kind.stdout.strip() != 'commit':
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: missing commit object')
    integrity = _run_git(
        ['--git-dir', str(git_dir), 'fsck', '--full', '--no-dangling', commit],
        timeout=timeout, cancel=cancel, allow_file_protocol=allow_file_protocol, check=False,
        max_output_bytes=max_output_bytes,
    )
    if integrity.returncode:
        raise RepositoryAcquisitionError('Repository cache entry is poisoned: object integrity failure')
    return git_dir


def _directory_bytes(path: Path) -> int:
    _preflight_tree(path)
    total = 0
    for base, _, files in os.walk(path, followlinks=False):
        for name in files:
            total += (Path(base) / name).stat().st_size
    return total


def _owned_entries(root: Path) -> list[Path]:
    entries = []
    for item in root.iterdir():
        if item.name in {_CACHE_MARKER, _WRITER_LOCK}:
            continue
        if item.name.startswith('.staging-'):
            raise RepositoryAcquisitionError('Repository cache contains stale staging data')
        if item.is_symlink() or not item.is_dir() or not item.name.startswith('repo-'):
            raise RepositoryAcquisitionError('Repository cache contains unowned data; refusing eviction')
        _preflight_tree(item)
        _metadata(item)
        entries.append(item)
    return entries


def _enforce_quota(root: Path, target: Path, limits: Mapping[str, Any]) -> None:
    entries = _owned_entries(root)
    sizes = {item: _directory_bytes(item) for item in entries}
    if sizes[target] > limits['max_cache_bytes']:
        raise RepositoryAcquisitionError('Repository exceeds the configured cache quota')
    entries.sort(key=lambda item: (item.stat().st_mtime_ns, item.name))
    while (len(entries) > limits['max_entries'] or
           sum(sizes[item] for item in entries) > limits['max_cache_bytes']):
        victim = next((item for item in entries if item != target), None)
        if victim is None:
            raise RepositoryAcquisitionError('Repository exceeds the configured cache quota')
        shutil.rmtree(victim)
        entries.remove(victim)
        del sizes[victim]


def _acquire(
    url: str, cache_root: Any, commit: Optional[str], *, limits: Optional[Mapping[str, Any]],
    progress: Optional[Callable[[dict[str, Any]], None]], cancel: Any,
    transport_url: str, allow_file_protocol: bool,
) -> dict[str, Any]:
    parsed = parse_github_repository(url)
    repo_id = parsed['owner'] + '/' + parsed['repo']
    if commit is not None and (type(commit) is not str or not _COMMIT.fullmatch(commit)):
        raise ValueError('commit must be a full lowercase 40-hex SHA')
    bounds = _limits(limits)
    timeout = float(bounds['timeout_seconds'])
    max_output_bytes = bounds['max_git_output_bytes']
    root = _prepare_cache_root(cache_root)
    lock = root / _WRITER_LOCK
    try:
        lock.mkdir()
    except FileExistsError as error:
        raise RepositoryAcquisitionError('Another repository cache writer is active') from error
    staging: Optional[Path] = None
    try:
        # Under the single-writer lock, reject every unexpected root entry,
        # including crash-leftover staging, before any Git or eviction read.
        _owned_entries(root)
        if _cancelled(cancel):
            raise RepositoryCancelled('Repository acquisition cancelled')
        resolved = commit
        if resolved is None:
            _notify(progress, 'resolving', repo_id=repo_id)
            result = _run_git(
                ['ls-remote', '--exit-code', transport_url, 'HEAD'], timeout=timeout,
                cancel=cancel, allow_file_protocol=allow_file_protocol, check=False,
                max_output_bytes=max_output_bytes,
            )
            fields = result.stdout.strip().split()
            if result.returncode or len(fields) != 2 or fields[1] != 'HEAD' or not _COMMIT.fullmatch(fields[0]):
                raise RepositoryAcquisitionError('Repository is unavailable, private, empty, or has no resolvable HEAD')
            resolved = fields[0]
        target = _entry_path(root, repo_id, resolved)
        if target.exists():
            git_dir = _validate_entry(
                target, repo_id=repo_id, url=url, commit=resolved, timeout=timeout,
                cancel=cancel, allow_file_protocol=allow_file_protocol,
                max_output_bytes=max_output_bytes,
            )
            _enforce_quota(root, target, bounds)
            os.utime(target, None)
            _notify(progress, 'ready', repo_id=repo_id, commit=resolved, cache_hit=True)
            return {
                'url': url, 'repo_id': repo_id, 'commit': resolved,
                'git_dir': str(git_dir.resolve()), 'cache_hit': True,
            }

        staging = root / ('.staging-' + str(os.getpid()) + '-' + resolved)
        if staging.exists():
            raise RepositoryAcquisitionError('Repository cache staging collision')
        staging.mkdir()
        git_dir = staging / 'repo.git'
        _run_git(
            ['init', '--bare', '--quiet', str(git_dir)], timeout=timeout, cancel=cancel,
            max_output_bytes=max_output_bytes,
        )
        _notify(progress, 'fetching', repo_id=repo_id, commit=resolved)
        _run_git(
            ['--git-dir', str(git_dir), 'fetch', '--quiet', '--no-tags', '--no-write-fetch-head',
             transport_url, resolved],
            timeout=timeout, cancel=cancel, allow_file_protocol=allow_file_protocol,
            max_output_bytes=max_output_bytes, watch_path=staging,
            max_disk_bytes=bounds['max_cache_bytes'],
        )
        kind = _run_git(
            ['--git-dir', str(git_dir), 'cat-file', '-t', resolved], timeout=timeout,
            cancel=cancel, allow_file_protocol=allow_file_protocol,
            max_output_bytes=max_output_bytes,
        ).stdout.strip()
        if kind != 'commit':
            raise RepositoryAcquisitionError('Fetched object is not a commit')
        metadata = {'version': _METADATA_VERSION, 'repo_id': repo_id, 'url': url, 'commit': resolved}
        (staging / 'metadata.json').write_text(
            json.dumps(metadata, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8'
        )
        _validate_entry(
            staging, repo_id=repo_id, url=url, commit=resolved, timeout=timeout,
            cancel=cancel, allow_file_protocol=allow_file_protocol,
            max_output_bytes=max_output_bytes,
        )
        if _directory_bytes(staging) > bounds['max_cache_bytes']:
            raise RepositoryAcquisitionError('Repository exceeds the configured cache quota')
        staging.rename(target)
        staging = None
        git_dir = target / 'repo.git'
        _enforce_quota(root, target, bounds)
        _notify(progress, 'ready', repo_id=repo_id, commit=resolved, cache_hit=False)
        return {
            'url': url, 'repo_id': repo_id, 'commit': resolved,
            'git_dir': str(git_dir.resolve()), 'cache_hit': False,
        }
    finally:
        if staging is not None and staging.exists():
            shutil.rmtree(staging)
        try:
            lock.rmdir()
        except FileNotFoundError:
            pass


def acquire_repository(
    url: str, cache_root: Any, commit: Optional[str] = None, *,
    limits: Optional[Mapping[str, Any]] = None,
    progress: Optional[Callable[[dict[str, Any]], None]] = None,
    cancel: Any = None,
) -> dict[str, Any]:
    """Acquire one immutable commit from a canonical public GitHub repository."""
    parse_github_repository(url)
    return _acquire(
        url, cache_root, commit, limits=limits, progress=progress, cancel=cancel,
        transport_url=url, allow_file_protocol=False,
    )


def _acquire_repository_for_test(
    url: str, cache_root: Any, transport_url: str, commit: Optional[str] = None, *,
    limits: Optional[Mapping[str, Any]] = None,
    progress: Optional[Callable[[dict[str, Any]], None]] = None,
    cancel: Any = None,
) -> dict[str, Any]:
    """Synthetic local-Git adapter; intentionally not accepted by the public API."""
    if type(transport_url) is not str or '://' in transport_url:
        raise ValueError('Synthetic transport must be a local test path')
    return _acquire(
        url, cache_root, commit, limits=limits, progress=progress, cancel=cancel,
        transport_url=transport_url, allow_file_protocol=True,
    )
