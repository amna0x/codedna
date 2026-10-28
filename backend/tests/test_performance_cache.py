"""Timing isolation and fitted-model identity, using offline temporary repos."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import replace

import pytest

from codedna import performance
from codedna.models import fit_cache
from codedna.test_history.features import Dataset, Row


@pytest.fixture(autouse=True)
def isolated(repo):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    fit_cache.clear_fitted_models()
    yield
    fit_cache.clear_fitted_models()


def data():
    return Dataset([Row('a', 0, 'A', 1, 2., {'x': 3.})], ['x'], ['a'])


def test_nested_timings_account_for_child_work_and_failures(monkeypatch):
    ticks = iter([0., 1., 2., 4., 6., 8.])
    monkeypatch.setattr(performance, 'perf_counter', lambda: next(ticks))
    with performance.capture_timings() as report:
        with performance.stage('outer'):
            with pytest.raises(ValueError), performance.stage('inner'):
                raise ValueError('fixture')
    result = report.to_dict()
    assert result['total_seconds'] == 8.
    assert result['stages']['outer'] == {'calls': 1, 'seconds': 5., 'self_seconds': 3.}
    assert result['stages']['inner'] == {'calls': 1, 'seconds': 2., 'self_seconds': 2.}


def test_timing_context_does_not_leak_to_threads_or_after_exit():
    @performance.timed('work')
    def work(): return 7
    with performance.capture_timings() as report:
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(copy_context().run, work).result() == 7
        assert not report.stages
        assert work() == 7
        with performance.capture_timings(False): work()
    work()
    assert report.to_dict()['stages']['work']['calls'] == 1


def test_profile_bounds_and_no_input_capture():
    with performance.capture_timings() as report:
        for i in range(100):
            with performance.stage(f's{i}'): pass
            performance.count(f'c{i}')
    result = report.to_dict()
    assert len(result['stages']) == len(result['counters']) == 64
    assert set(result) == {'schema_version', 'total_seconds', 'stages', 'counters'}


def use(dataset, compute, *, features=('x',), target=.05, implementation=('fixture-v1',)):
    return fit_cache.fitted_models(dataset, features, target, implementation, compute)


def test_scoped_reuse_is_defensive_and_unscoped_calls_remain_fresh():
    calls = []
    def compute(): calls.append(1); return ({'weights': [4.]}, {'calibration': [5.]})
    d = data()
    with performance.capture_timings() as report, fit_cache.fitted_model_scope(('repo', 'base', 'history')):
        first = use(d, compute); first[0]['weights'][0] = 999
        second = use(d, compute); second[1]['calibration'][0] = 999
        third = use(d, compute)
    assert third == ({'weights': [4.]}, {'calibration': [5.]})
    assert len(calls) == 1 and report.counters['fit_cache.hit'] == 2
    use(d, compute); assert len(calls) == 2


@pytest.mark.parametrize('change', ['label', 'feature', 'duration', 'row_order', 'commits', 'namespace', 'features', 'target', 'implementation'])
def test_any_relevant_input_change_invalidates_models(change):
    d = data(); d.rows.append(Row('b', 1, 'B', 0, 1., {'x': 2.})); d.commits.append('b')
    calls = []
    def compute(): calls.append(1); return ({}, {})
    with fit_cache.fitted_model_scope(('repo',)):
        use(d, compute)
    kwargs = {}; namespace = ('repo',)
    if change == 'label': d.rows[0] = replace(d.rows[0], label=0)
    elif change == 'feature': d.rows[0].features['x'] = 8.
    elif change == 'duration': d.rows[0] = replace(d.rows[0], duration=9.)
    elif change == 'row_order': d.rows.reverse()
    elif change == 'commits': d.commits.reverse()
    elif change == 'namespace': namespace = ('other repo',)
    elif change == 'features': kwargs['features'] = ('other',)
    elif change == 'target': kwargs['target'] = .1
    elif change == 'implementation': kwargs['implementation'] = ('fixture-v2',)
    with fit_cache.fitted_model_scope(namespace): use(d, compute, **kwargs)
    assert len(calls) == 2


def test_failed_fit_is_not_cached_and_exception_restores_scope():
    calls = []
    def fail(): calls.append(1); raise ValueError('no fit')
    for _ in range(2):
        with pytest.raises(ValueError), fit_cache.fitted_model_scope(('repo',)):
            use(data(), fail)
    assert len(calls) == 2 and fit_cache._SCOPE.get() is None


def test_expiry_and_lru_bound(monkeypatch):
    clock = [0.]; monkeypatch.setattr(fit_cache, 'monotonic', lambda: clock[0])
    calls = []
    def compute(): calls.append(1); return ({}, {})
    for repo in ('a', 'b', 'c'):
        with fit_cache.fitted_model_scope((repo,)): use(data(), compute)
    assert len(fit_cache._CACHE) == 2
    with fit_cache.fitted_model_scope(('a',)): use(data(), compute)
    clock[0] = 301.
    with fit_cache.fitted_model_scope(('a',)): use(data(), compute)
    assert len(calls) == 5 and len(fit_cache._CACHE) == 1


def test_inherited_thread_context_cannot_reuse_parent_scope():
    calls = []
    def compute(): calls.append(1); return ({}, {})
    with fit_cache.fitted_model_scope(('repo',)):
        use(data(), compute)
        with ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(copy_context().run, use, data(), compute).result()
    assert len(calls) == 2
