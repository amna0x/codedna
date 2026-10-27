"""Bounded, session-owned read-only analysis jobs; no arbitrary command API."""
from __future__ import annotations

from collections import deque
from copy import deepcopy
import json
from pathlib import Path
import sys
from threading import Condition, Thread, Timer
from time import monotonic
from uuid import uuid4

from codedna.api.owned_process import OwnedProcess

MAX_MESSAGE = 8 * 1024 * 1024
TERMINAL = frozenset({'completed', 'failed', 'cancelled'})
OPERATIONS = frozenset({'tests', 'analyze', 'impact', 'select', 'risk-select'})


class JobCapacityError(RuntimeError):
    pass


def worker_command():
    if getattr(sys, 'frozen', False):
        return [sys.executable, '--codedna-analysis-worker']
    return [sys.executable, '-m', 'codedna.api.analysis_worker']


class AnalysisJobs:
    """One active worker, two queued jobs and bounded retained results.

    IDs, input, state and process ownership stay in this API session. Every job
    gets a fresh contained worker; no audit/model acceptance is reused here.
    """
    def __init__(self, *, deadline=300., ttl=600., max_records=8, queue_size=2):
        self._condition = Condition()
        self._records = {}
        self._queue = deque()
        self._deadline = deadline
        self._ttl = ttl
        self._max_records = max_records
        self._queue_size = queue_size
        self._closed = False
        self._thread = None
        self._plugins = None
        if getattr(sys, 'frozen', False):
            from codedna.plugins import desktop_store
            self._plugins = desktop_store.worker_snapshot()

    def _prune(self):
        now = monotonic()
        for key, record in list(self._records.items()):
            if record['state'] in TERMINAL and now - record['finished'] >= self._ttl:
                del self._records[key]
        # Reclaim oldest completed records when reaching the retention bound.
        for key in list(self._records):
            if len(self._records) < self._max_records:
                break
            if self._records[key]['state'] in TERMINAL:
                del self._records[key]

    def submit(self, operation, payload):
        if operation not in OPERATIONS:
            raise ValueError('unsupported analysis operation')
        # Freeze caller input; do not retain mutable request objects.
        request = json.dumps({'operation': operation, 'payload': payload,
                              'plugins': self._plugins}, allow_nan=False).encode() + b'\n'
        if len(request) > MAX_MESSAGE:
            raise ValueError('analysis request exceeds the worker message limit')
        with self._condition:
            self._prune()
            if self._closed:
                raise JobCapacityError('analysis session is closing')
            if len(self._queue) >= self._queue_size or len(self._records) >= self._max_records:
                raise JobCapacityError('analysis queue is full; wait or cancel a queued operation')
            key = uuid4().hex
            self._records[key] = dict(id=key, operation=operation, state='queued',
                stage='queued', created=monotonic(), finished=None, request=request,
                owner=None, cancel_requested=False, result=None, error=None)
            self._queue.append(key)
            if self._thread is None:
                self._thread = Thread(target=self._loop, name='codedna-analysis-jobs', daemon=True)
                self._thread.start()
            self._condition.notify_all()
            return self._view(self._records[key])

    def _view(self, record):
        end = record['finished'] or monotonic()
        view = {key: record[key] for key in ('id', 'operation', 'state', 'stage')}
        view['elapsed_seconds'] = round(max(0., end - record['created']), 3)
        if record['state'] == 'completed':
            view['result'] = deepcopy(record['result'])
        if record['state'] == 'failed':
            view['error'] = record['error']
        return view

    def get(self, key):
        with self._condition:
            record = self._records.get(key)
            if record is None or (record['state'] in TERMINAL and
                monotonic() - record['finished'] >= self._ttl):
                raise KeyError('analysis operation not found or expired')
            return self._view(record)

    def cancel(self, key):
        with self._condition:
            record = self._records.get(key)
            if record is None:
                raise KeyError('analysis operation not found or expired')
            if record['state'] in TERMINAL:
                return self._view(record)
            record['cancel_requested'] = True
            record['stage'] = 'cancelling'
            owner = record['owner']
            if key in self._queue:
                self._queue.remove(key)
            # If startup is in progress, _perform will contain and close its
            # worker before any project input is sent. Wait for that handshake.
            if owner is None and record['state'] == 'running':
                self._condition.wait_for(lambda: record['owner'] is not None or
                    record['state'] in TERMINAL, timeout=15)
                owner = record['owner']
        error = None
        if owner is not None:
            try:
                owner.close()
            except Exception:
                error = 'analysis worker cleanup could not be confirmed'
        with self._condition:
            if owner is None and record['state'] == 'running':
                error = 'analysis worker startup cleanup could not be confirmed'
            self._finish(record, 'failed' if error else 'cancelled', error=error, force=True)
            return self._view(record)

    def _finish(self, record, state, *, result=None, error=None, force=False):
        if record['state'] in TERMINAL or (record['cancel_requested'] and not force):
            return
        record.update(state=state, stage=state, result=result, error=error,
                      finished=monotonic(), request=None)
        self._condition.notify_all()

    def _loop(self):
        while True:
            with self._condition:
                self._condition.wait_for(lambda: self._queue or self._closed)
                if self._closed:
                    return
                key = self._queue.popleft()
                record = self._records[key]
                record.update(state='running', stage='starting contained worker')
            self._perform(record)

    def _perform(self, record):
        owner = None
        timer = None
        drain = None
        result = None
        error = None
        success = False
        cleanup_failed = False
        try:
            owner = OwnedProcess(worker_command(), cwd=Path(__file__).resolve().parent)
            with self._condition:
                record['owner'] = owner
                self._condition.notify_all()
                cancelled = record['cancel_requested'] or self._closed
                request = record['request']
            if cancelled:
                return

            def expire():
                with self._condition:
                    if record['state'] in TERMINAL or record['cancel_requested']:
                        return
                    self._finish(record, 'failed', error='analysis deadline exceeded')
                try:
                    owner.close()
                except Exception:
                    with self._condition:
                        self._closed = True
                        record['error'] = 'analysis deadline exceeded; worker cleanup could not be confirmed'
                        for key in self._queue:
                            self._finish(self._records[key], 'failed',
                                error='analysis session stopped after worker cleanup failure', force=True)
                        self._queue.clear()
                        self._condition.notify_all()

            timer = Timer(self._deadline, expire); timer.daemon = True; timer.start()
            # Drain diagnostics without retaining source, logs or unbounded text.
            def discard_stderr():
                while owner.process.stderr.read(4096):
                    pass
            drain = Thread(target=discard_stderr, daemon=True); drain.start()
            owner.process.stdin.write(request); owner.process.stdin.close()
            got_result = False
            events = 0
            while True:
                line = owner.process.stdout.readline(MAX_MESSAGE + 1)
                if not line:
                    break
                events += 1
                if len(line) > MAX_MESSAGE or events > 32:
                    raise ValueError('analysis worker exceeded protocol limits')
                event = json.loads(line)
                if event.get('kind') == 'stage' and not got_result:
                    stage = event['value']
                    if not isinstance(stage, str) or len(stage) > 100:
                        raise ValueError('invalid analysis progress event')
                    with self._condition:
                        if record['state'] not in TERMINAL and not record['cancel_requested']:
                            record['stage'] = stage
                elif event.get('kind') == 'result' and not got_result:
                    result = event['value']; got_result = True
                    if not isinstance(result, dict):
                        raise ValueError('invalid analysis result')
                elif event.get('kind') == 'error' and isinstance(event.get('value'), str):
                    error = event['value'][:1000]
                else:
                    raise ValueError('invalid analysis worker event')
            code = owner.process.wait(timeout=10)
            success = code == 0 and got_result and error is None
            if not success:
                error = error or 'analysis worker exited without a result'
        except Exception as exc:
            error = str(exc)[:1000] or 'analysis worker failed'
        finally:
            if timer:
                timer.cancel()
            if owner:
                try:
                    owner.close()
                except Exception:
                    success = False
                    cleanup_failed = True
                    error = 'analysis worker cleanup could not be confirmed'
                if drain:
                    drain.join(timeout=10)
                for stream in (owner.process.stdin, owner.process.stdout, owner.process.stderr):
                    stream.close()
            with self._condition:
                if cleanup_failed:
                    # Stop dispatching if ownership cleanup cannot be proved.
                    # Do not report a cancelled worker and start another one.
                    self._closed = True
                    self._finish(record, 'failed', error=error, force=True)
                    for key in self._queue:
                        self._finish(self._records[key], 'failed',
                                     error='analysis session stopped after worker cleanup failure', force=True)
                    self._queue.clear()
                elif record['cancel_requested'] and record['state'] not in TERMINAL:
                    self._finish(record, 'cancelled', force=True)
                elif record['state'] not in TERMINAL:
                    self._finish(record, 'completed' if success else 'failed',
                                 result=result if success else None, error=error)
                record['owner'] = None
                self._condition.notify_all()

    def close(self):
        with self._condition:
            self._closed = True
            pending = [key for key, record in self._records.items() if record['state'] not in TERMINAL]
            owners = [record['owner'] for record in self._records.values() if record['owner'] is not None]
            self._condition.notify_all()
        for key in pending:
            self.cancel(key)
        errors = []
        for owner in owners:
            try:
                owner.close()
            except Exception as exc:
                errors.append(exc)
        if self._thread:
            self._thread.join(timeout=20)
        if errors:
            raise RuntimeError('analysis shutdown could not confirm worker cleanup') from errors[0]
