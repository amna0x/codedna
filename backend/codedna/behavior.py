"""Experimental behavioral evidence; does not alter any test-selection gate."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import sys
from subprocess import SubprocessError
from threading import Event, Thread
from time import monotonic, sleep

from codedna.api.owned_process import OwnedProcess
from codedna.performance import timed
from codedna.git_analysis.git import resolve_commit, resolve_repository, reuse_git_validation

MAX_MESSAGE = 1024 * 1024
_BLOCKED_REASON = None


def _exchange(owner, request, deadline):
    """Bound private stdout/stderr and stop the owned tree on every exit."""
    global _BLOCKED_REASON
    data = json.dumps(request, allow_nan=False).encode('utf-8') + b'\n'
    if len(data) > 64 * 1024:
        raise ValueError('behavioral request exceeds its message limit')
    buffers = [bytearray(), bytearray()]
    overflow, io_error = Event(), Event()

    def read(stream, buffer, limit):
        try:
            while chunk := stream.read1(4096):
                if len(buffer) + len(chunk) > limit:
                    overflow.set()
                    return
                buffer.extend(chunk)
        except (OSError, ValueError):
            io_error.set()

    def write():
        try:
            owner.process.stdin.write(data)
            owner.process.stdin.close()
        except (OSError, ValueError):
            io_error.set()

    readers = [Thread(target=read, args=(owner.process.stdout, buffers[0], MAX_MESSAGE), daemon=True),
               Thread(target=read, args=(owner.process.stderr, buffers[1], 64 * 1024), daemon=True)]
    writer = Thread(target=write, daemon=True)
    for thread in [*readers, writer]:
        thread.start()
    try:
        while owner.process.poll() is None:
            if overflow.is_set():
                raise RuntimeError('behavioral worker exceeded its output limit')
            if monotonic() >= deadline:
                raise TimeoutError('behavioral operation exceeded its time budget')
            sleep(.025)
        if monotonic() >= deadline:
            raise TimeoutError('behavioral result arrived after its time budget')
    finally:
        # Includes descendants holding inherited pipes after the leader exits.
        cleanup_error = None
        try:
            owner.close()
        except Exception as exc:
            cleanup_error = exc
            _BLOCKED_REASON = 'Project cleanup could not be confirmed; restart the CodeDNA worker/server before further witness execution'
        cleanup_deadline = monotonic()+2
        for thread in [*readers, writer]:
            thread.join(timeout=max(0., cleanup_deadline-monotonic()))
        if any(thread.is_alive() for thread in [*readers, writer]):
            _BLOCKED_REASON = _BLOCKED_REASON or 'Worker I/O cleanup could not be confirmed; restart CodeDNA before further witness execution'
            cleanup_error = cleanup_error or RuntimeError(_BLOCKED_REASON)
        else:
            # Never wait for a buffered-stream lock held by an unfinished reader.
            for stream in (owner.process.stdin, owner.process.stdout, owner.process.stderr):
                stream.close()
        if cleanup_error is not None:
            raise RuntimeError(_BLOCKED_REASON) from cleanup_error
    if any(thread.is_alive() for thread in [*readers, writer]) or io_error.is_set():
        raise RuntimeError('behavioral worker I/O did not finish cleanly')
    if overflow.is_set():
        raise RuntimeError('behavioral worker exceeded its output limit')
    if owner.process.returncode != 0:
        raise RuntimeError('behavioral worker failed; no confirmed result is available')
    result = json.loads(buffers[0])
    if not isinstance(result, dict) or result.get('status') not in {
        'difference', 'no_difference_observed', 'unsupported', 'inconclusive'}:
        raise ValueError('invalid behavioral worker result')
    return result


@timed('behavior.comparison')
@reuse_git_validation
def find_difference(repo_path, base, head, *, file, symbol, output_dir,
                    language='java', allow_build=False, max_inputs=16, seed=0,
                    timeout=30, reduce_budget=8, generation='guided'):
    """Execute an optional plugin capability with explicit consent and ownership.

    A difference is an observation, not a regression classification. Nothing
    returned here validates skip risk or removes a required test.
    """
    if allow_build is not True:
        raise ValueError('behavioral comparison executes project code; pass --allow-build to confirm')
    if _BLOCKED_REASON:
        raise RuntimeError(_BLOCKED_REASON)
    started = monotonic()
    for name, value, low, high in [('max_inputs', max_inputs, 1, 64),
                                  ('seed', seed, 0, 2**32-1),
                                  ('timeout', timeout, 1, 120),
                                  ('reduce_budget', reduce_budget, 0, 16)]:
        if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
            raise ValueError(f'{name} must be an integer between {low} and {high}')
    if generation not in ('guided', 'simple'):
        raise ValueError('generation must be guided or simple')
    if not isinstance(language, str) or not language or len(language) > 64:
        raise ValueError('language must be a bounded installed-plugin name')
    if not isinstance(output_dir, (str, Path)) or not str(output_dir) or len(str(output_dir)) > 4096:
        raise ValueError('output_dir must name a bounded new export folder')
    if not isinstance(symbol, str) or not symbol or len(symbol) > 256:
        raise ValueError('symbol must be a non-empty bounded plugin symbol ID')
    if not isinstance(file, str) or not file or len(file) > 1024:
        raise ValueError('file must be a bounded repository-relative path')
    relative = PurePosixPath(file.replace('\\', '/'))
    if not relative.parts or relative.is_absolute() or any(p in ('..', '') or ':' in p for p in relative.parts):
        raise ValueError('file must stay within the repository')
    repo = resolve_repository(repo_path)
    base_sha, head_sha = resolve_commit(repo, base), resolve_commit(repo, head)
    output = Path(output_dir).resolve()
    if output.is_relative_to(repo):
        raise ValueError('choose an export folder outside the analysed repository')
    if output.exists():
        raise ValueError('export folder must not already exist')
    from codedna.plugins import load_plugins
    from codedna.plugins.languages import require
    plugin = require(language, load_plugins())
    if not callable(getattr(plugin, 'find_witness', None)):
        raise ValueError(f'language plugin {language!r} has no experimental behavioral witness capability')
    deadline = started + timeout
    output.mkdir(parents=True, exist_ok=False)
    common = {'schema_version': 1, 'kind': 'codedna-behavioral-evidence', 'experimental': True,
              'repository': str(repo), 'base_commit': base_sha, 'head_commit': head_sha,
              'language': language, 'file': relative.as_posix(), 'symbol': symbol,
              'regression_established': False, 'required_tests_removed': False,
              'plugin_version': plugin.version, 'plugin_api_version': plugin.api_version,
              'export_disclosure': 'A confirmed export includes the entire selected base/head source file; compiler diagnostics may quote source. Review before sharing.',
              'interpretation': 'A stable observed difference needs an applicable expectation to be called a regression. '
                                'No witness within a finite budget does not establish equivalence or validate skip risk.'}
    request = {**common, 'allow_build': True, 'output_dir': str(output), 'deadline': deadline,
               'options': {'max_inputs': max_inputs, 'seed': seed, 'reduce_budget': reduce_budget,
                           'generation': generation}, 'plugins': None}
    if getattr(sys, 'frozen', False):
        from codedna.plugins import desktop_store
        request['plugins'] = desktop_store.worker_snapshot()
        command = [sys.executable, '--codedna-behavior-worker']
    else:
        command = [sys.executable, '-m', 'codedna.behavior_worker']
    try:
        if monotonic() >= deadline:
            raise TimeoutError('time budget exhausted before project execution')
        with OwnedProcess(command, cwd=Path(__file__).resolve().parent) as owner:
            result = _exchange(owner, request, deadline)
    except KeyboardInterrupt:
        result = {'status': 'cancelled', 'reason': 'operation cancelled; no confirmed result was accepted'}
    except (OSError, ValueError, RuntimeError, SubprocessError) as exc:
        result = {'status': 'inconclusive', 'reason': str(exc)[:1000]}
    if _BLOCKED_REASON:
        result = {'status': 'inconclusive', 'reason': _BLOCKED_REASON}
    # The controller owns interpretation and identity fields, even for plugins.
    report = {**result, **common, 'further_execution_blocked': bool(_BLOCKED_REASON),
              'elapsed_seconds': round(monotonic()-started, 6)}
    with (output/'report.json').open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(report, indent=2, allow_nan=False)+'\n')
    return report
