"""Reuse immutable parses across nested planning; never retain operation state."""
from contextvars import copy_context
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
import pytest

from codedna.dependency_graph import cache as module
from codedna.agent import brake
from codedna.performance import capture_timings


def seed(repo):
    repo.write('src/main/java/A.java','class A { int n() { return 1; } }')
    for name in ['ATest','BTest']:
        repo.write(f'src/test/java/{name}.java',f'import org.junit.jupiter.api.Test; class {name} {{ A a; @Test void check() {{}} }}')
    base=repo.commit('fixture');repo.write('src/main/java/A.java','class A { int n() { return 2; } }')
    return base


def test_brake_reuses_parses_without_changing_its_plan(repo,monkeypatch):
    base=seed(repo)
    with capture_timings() as reused:
        first=brake.plan(repo.path,base=base)
    import codedna.selection.baselines as baselines
    monkeypatch.setattr(baselines,'operation_parse_cache',lambda *args: module.BoundedParseCache())
    with capture_timings() as separate:
        second=brake.plan(repo.path,base=base)
    first['risk'].pop('analysis_seconds',None);second['risk'].pop('analysis_seconds',None)
    assert first==second
    assert reused.stages['parse.java']['calls']<separate.stages['parse.java']['calls']
    assert reused.counters['parse_cache.get']>0
    assert module._OPERATION.get() is None


def test_scope_partition_changes_and_threads_do_not_inherit_cache(repo):
    seed(repo)
    class Plugin:
        version='1';api_version='1.1'
        def parse(self,source): return source
    registry=SimpleNamespace(plugins={'fixture':Plugin()})
    with module.parse_cache_scope():
        first=module.operation_parse_cache(repo.path,registry);first['blob']='value'
        assert module.operation_parse_cache(repo.path,registry) is first
        with module.parse_cache_scope(): assert module.operation_parse_cache(repo.path,registry) is first
        registry.plugins['fixture'].version='2'
        changed=module.operation_parse_cache(repo.path,registry)
        assert changed is not first and 'blob' not in changed
        with ThreadPoolExecutor(max_workers=1) as pool:
            other=pool.submit(copy_context().run,module.operation_parse_cache,repo.path,registry).result()
        assert other is not changed
    with module.parse_cache_scope():
        assert module.operation_parse_cache(repo.path,registry) is not changed
    with pytest.raises(ValueError), module.parse_cache_scope(): raise ValueError('fixture')
    assert module._OPERATION.get() is None
