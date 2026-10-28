"""Optional bounded, synchronous stage timings. Contains no paths or source."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
import os
from threading import get_ident
from time import perf_counter

_ACTIVE = ContextVar('codedna_performance', default=None)
_LIMIT = 64


def _owner():
    return os.getpid(), get_ident()


class TimingReport:
    def __init__(self):
        self.owner = _owner()
        self.started = perf_counter()
        self.finished = None
        self.stack = []
        self.stages = {}
        self.counters = {}

    def to_dict(self):
        end = self.finished if self.finished is not None else perf_counter()
        return {'schema_version': 1, 'total_seconds': round(max(0., end-self.started), 6),
                'stages': {name: {key: round(value, 6) if key != 'calls' else value
                                 for key, value in record.items()}
                           for name, record in self.stages.items()},
                'counters': dict(self.counters)}


def _current():
    report = _ACTIVE.get()
    return report if report is not None and report.owner == _owner() else None


@contextmanager
def capture_timings(enabled=True):
    report = TimingReport() if enabled else None
    token = _ACTIVE.set(report)
    try:
        yield report
    finally:
        if report is not None:
            report.finished = perf_counter()
        _ACTIVE.reset(token)


@contextmanager
def stage(name):
    report = _current()
    if report is None:
        yield
        return
    if not isinstance(name, str) or len(name) > 64:
        raise ValueError('timing stage needs a bounded static name')
    if name not in report.stages and len(report.stages) >= _LIMIT:
        yield
        return
    record = report.stages.setdefault(name, {'calls': 0, 'seconds': 0., 'self_seconds': 0.})
    frame = [perf_counter(), 0.]
    report.stack.append(frame)
    try:
        yield
    finally:
        elapsed = max(0., perf_counter()-frame[0])
        report.stack.pop()
        record['calls'] += 1
        record['seconds'] += elapsed
        record['self_seconds'] += max(0., elapsed-frame[1])
        if report.stack:
            report.stack[-1][1] += elapsed


def count(name, amount=1):
    report = _current()
    if report is None:
        return
    if not isinstance(name, str) or len(name) > 64 or not isinstance(amount, int) or amount < 0:
        raise ValueError('timing counter needs a bounded static name and nonnegative integer')
    if name in report.counters or len(report.counters) < _LIMIT:
        report.counters[name] = report.counters.get(name, 0) + amount


def timed(name):
    def decorate(function):
        @wraps(function)
        def measured(*args, **kwargs):
            if _current() is None:
                return function(*args, **kwargs)
            with stage(name):
                return function(*args, **kwargs)
        return measured
    return decorate
