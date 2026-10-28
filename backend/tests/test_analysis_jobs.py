"""Bounded worker lifecycle and exact core output using temporary repositories."""
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
import sys
from threading import Event
import time

import pytest

from codedna.api import analysis_jobs as module
from codedna.api.analysis_jobs import AnalysisJobs, JobCapacityError
from codedna.api.analysis_worker import execute


def await_state(jobs, key, states, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = jobs.get(key)
        if value['state'] in states:
            return value
        time.sleep(.02)
    raise AssertionError(f'job did not reach {states}: {jobs.get(key)}')


@contextmanager
def fixture_jobs(repo, tmp_path, monkeypatch, **options):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    helper = tmp_path / 'trusted_worker.py'
    helper.write_text('''import json, sys, time
request = json.loads(sys.stdin.readline())
body = request['payload']
def emit(kind, value):
    print(json.dumps({'kind': kind, 'value': value}), flush=True)
emit('stage', 'fixture ready')
if body.get('mode') == 'crash':
    sys.exit(7)
if body.get('mode') == 'malformed':
    print('bad protocol', flush=True); sys.exit(0)
if body.get('mode') == 'flood':
    for _ in range(40): emit('stage', 'fixture flood')
    sys.exit(0)
time.sleep(body.get('sleep', 0))
emit('result', {'value': body.get('value', 1)})
''')
    monkeypatch.setattr(module, 'worker_command', lambda: [sys.executable, str(helper)])
    jobs = AnalysisJobs(**options)
    try:
        yield jobs
    finally:
        jobs.close()


def ready(jobs, key):
    end = time.monotonic() + 20
    while time.monotonic() < end:
        value = jobs.get(key)
        if value['stage'] == 'fixture ready':
            return value
        time.sleep(.02)
    raise AssertionError(jobs.get(key))


def test_queue_bound_cancelled_work_never_runs_and_later_work_succeeds(repo, tmp_path, monkeypatch):
    with fixture_jobs(repo, tmp_path, monkeypatch) as jobs:
        first = jobs.submit('tests', {'sleep': 120})['id']; ready(jobs, first)
        second = jobs.submit('tests', {'value': 2})['id']
        third = jobs.submit('tests', {'value': 3})['id']
        with pytest.raises(JobCapacityError):
            jobs.submit('tests', {})
        assert jobs.cancel(second)['state'] == 'cancelled'
        assert jobs.cancel(first)['state'] == 'cancelled'
        assert jobs.cancel(first)['state'] == 'cancelled'
        assert await_state(jobs, third, {'completed'})['result'] == {'value': 3}
        assert jobs.get(first)['state'] == jobs.get(second)['state'] == 'cancelled'
        assert not (repo.path / '.codedna').exists()


@pytest.mark.parametrize('mode', ['crash', 'malformed', 'flood'])
def test_bad_worker_fails_but_queue_recovers(repo, tmp_path, monkeypatch, mode):
    with fixture_jobs(repo, tmp_path, monkeypatch) as jobs:
        bad = jobs.submit('tests', {'mode': mode})['id']
        failed = await_state(jobs, bad, {'failed'})
        assert failed['error'] and 'result' not in failed
        good = jobs.submit('tests', {})['id']
        assert await_state(jobs, good, {'completed'})['result'] == {'value': 1}


def test_deadline_stops_owned_worker_and_does_not_complete_later(repo, tmp_path, monkeypatch):
    with fixture_jobs(repo, tmp_path, monkeypatch, deadline=1.) as jobs:
        key = jobs.submit('tests', {'sleep': 120})['id']
        value = await_state(jobs, key, {'failed'})
        assert value['error'] == 'analysis deadline exceeded'
        time.sleep(.1)
        assert jobs.get(key)['state'] == 'failed'


def test_retention_is_bounded_and_results_cannot_be_mutated(repo, tmp_path, monkeypatch):
    with fixture_jobs(repo, tmp_path, monkeypatch, max_records=2, ttl=60) as jobs:
        first = jobs.submit('tests', {})['id']
        value = await_state(jobs, first, {'completed'})
        value['result']['value'] = 999
        assert jobs.get(first)['result'] == {'value': 1}
        second = jobs.submit('tests', {})['id']; await_state(jobs, second, {'completed'})
        third = jobs.submit('tests', {})['id']; await_state(jobs, third, {'completed'})
        with pytest.raises(KeyError): jobs.get(first)
        assert len(jobs._records) == 2


def test_close_cancels_active_and_queued_jobs_and_rejects_more(repo, tmp_path, monkeypatch):
    with fixture_jobs(repo, tmp_path, monkeypatch) as jobs:
        first = jobs.submit('tests', {'sleep': 120})['id']; ready(jobs, first)
        second = jobs.submit('tests', {})['id']
        jobs.close(); jobs.close()
        assert jobs.get(first)['state'] == jobs.get(second)['state'] == 'cancelled'
        assert not jobs._thread.is_alive()
        with pytest.raises(JobCapacityError): jobs.submit('tests', {})


def test_unknown_ids_and_unsupported_operations_are_rejected(repo):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    jobs = AnalysisJobs()
    try:
        with pytest.raises(ValueError): jobs.submit('run-tests', {})
        with pytest.raises(KeyError): jobs.get('123')
        with pytest.raises(KeyError): jobs.cancel('123')
        assert jobs._thread is None
    finally:
        jobs.close()


def test_cancellation_during_worker_startup_never_sends_project_input(repo, tmp_path, monkeypatch):
    entered, release = Event(), Event()
    original = module.OwnedProcess
    def slow_start(*args, **kwargs):
        entered.set()
        assert release.wait(15)
        return original(*args, **kwargs)
    with fixture_jobs(repo, tmp_path, monkeypatch) as jobs:
        monkeypatch.setattr(module, 'OwnedProcess', slow_start)
        key = jobs.submit('tests', {'sleep': 120})['id']
        assert entered.wait(15)
        with ThreadPoolExecutor(max_workers=1) as executor:
            cancelled = executor.submit(jobs.cancel, key)
            try:
                time.sleep(.05)
                assert not cancelled.done()  # no false cleanup confirmation
            finally:
                release.set()
            assert cancelled.result(timeout=20)['state'] == 'cancelled'
        assert jobs.get(key)['state'] == 'cancelled'


def test_expired_results_are_unavailable_and_new_work_still_runs(repo, tmp_path, monkeypatch):
    with fixture_jobs(repo, tmp_path, monkeypatch, ttl=.1) as jobs:
        key = jobs.submit('tests', {})['id']
        await_state(jobs, key, {'completed'})
        time.sleep(.15)
        with pytest.raises(KeyError): jobs.get(key)
        later = jobs.submit('tests', {})['id']
        assert await_state(jobs, later, {'completed'})['result'] == {'value': 1}


def test_unconfirmed_cleanup_stops_dispatch_instead_of_claiming_success(repo, tmp_path, monkeypatch):
    original = module.OwnedProcess
    class UnconfirmedCleanup(original):
        def close(self):
            super().close()
            raise OSError('fixture could not confirm cleanup')
    with fixture_jobs(repo, tmp_path, monkeypatch) as jobs:
        monkeypatch.setattr(module, 'OwnedProcess', UnconfirmedCleanup)
        key = jobs.submit('tests', {})['id']
        failed = await_state(jobs, key, {'failed'})
        assert 'cleanup could not be confirmed' in failed['error']
        with pytest.raises(JobCapacityError): jobs.submit('tests', {})


def test_deadline_cleanup_failure_is_reported_and_stops_queued_work(repo, tmp_path, monkeypatch):
    original = module.OwnedProcess
    class UnconfirmedOnce(original):
        unconfirmed = True
        def close(self):
            super().close()
            if self.unconfirmed:
                self.unconfirmed = False
                raise OSError('fixture first cleanup confirmation failed')
    with fixture_jobs(repo, tmp_path, monkeypatch, deadline=1.) as jobs:
        monkeypatch.setattr(module, 'OwnedProcess', UnconfirmedOnce)
        key = jobs.submit('tests', {'sleep': 120})['id']
        ready(jobs, key)
        queued = jobs.submit('tests', {})['id']
        await_state(jobs, key, {'failed'})
        end = time.monotonic() + 10
        while not jobs._closed and time.monotonic() < end:
            time.sleep(.01)
        assert jobs._closed
        assert 'cleanup could not be confirmed' in jobs.get(key)['error']
        assert jobs.get(queued)['state'] == 'failed'
        with pytest.raises(JobCapacityError): jobs.submit('tests', {})


@pytest.mark.parametrize('operation,payload', [
    ('tests', {'rev': 'HEAD'}),
    ('analyze', {'base': 'HEAD~1', 'head': 'HEAD', 'level': 'file'}),
    ('select', {'base': 'HEAD~1', 'head': 'HEAD', 'strategy': 'all'}),
])
def test_real_worker_matches_sync_core_and_does_not_record_history(repo, operation, payload):
    repo.write('src/main/java/A.java', 'class A { int value() { return 1; } }')
    repo.write('src/test/java/ATest.java', 'import org.junit.jupiter.api.Test; class ATest { @Test void check() {} }')
    repo.commit('initial')
    repo.write('src/main/java/A.java', 'class A { int value() { return 2; } }'); repo.commit('change')
    payload = dict(repo=str(repo.path), **payload)
    expected = execute(operation, payload)
    jobs = AnalysisJobs(deadline=90.)
    try:
        key = jobs.submit(operation, payload)['id']
        completed = await_state(jobs, key, {'completed', 'failed'}, timeout=100)
        assert completed['state'] == 'completed', completed
        assert completed['result'] == expected
        assert not (repo.path / '.codedna').exists()
    finally:
        jobs.close()
