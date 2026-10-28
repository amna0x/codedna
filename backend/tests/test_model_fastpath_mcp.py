from codedna.agent.mcp_server import BrakeServer
from codedna.selection.live import recommend
from codedna.performance import capture_timings


def project(repo):
    repo.write('pom.xml','<project/>')
    repo.write('src/main/java/A.java','class A { int n = 1; }')
    repo.write('src/test/java/ATest.java','import org.junit.jupiter.api.Test; class ATest { @Test void check() {} }')
    base=repo.commit('fixture');repo.write('src/main/java/A.java','class A { int n = 2; }');head=repo.commit('change')
    return base,head


def test_all_mandatory_fastpath_never_reads_history_or_fits_model(repo,tmp_path,monkeypatch):
    base,head=project(repo)
    from codedna_java import live
    def forbidden(*args,**kwargs): raise AssertionError('model cannot reduce a fully pinned suite')
    monkeypatch.setattr(live,'fit_audited',forbidden)
    history=tmp_path/'history.csv';history.write_bytes(b'not valid history')
    with capture_timings() as timings:
        result=recommend(repo.path,base,head,history_csv=history,must_run=['*'])
    assert result['skipped']==[] and result['policy']['pinned']==['ATest']
    assert result['risk']['status']=='unvalidated' and result['risk']['estimated_skip_risk'] is None
    assert timings.counters['fallback.all_tests_required']==1
    assert 'risk.history_load' not in timings.stages and 'risk.training' not in timings.stages


def test_mcp_profile_is_optional_and_not_a_build_permission(repo):
    project(repo);server=BrakeServer(repo=repo.path)
    def request(arguments):
        return server.handle({'jsonrpc':'2.0','id':1,'method':'tools/call',
            'params':{'name':'codedna_plan_tests','arguments':arguments}})
    plain=request({})['result']['structuredContent'];assert 'operation_timings' not in plain
    measured=request({'profile':True})['result']['structuredContent']
    metrics=measured.pop('operation_timings')
    assert metrics['scope']=='analysis_only' and metrics['total_seconds']>0
    assert metrics['stages']['git']['calls']>0
    assert str(repo.path) not in str(metrics)
    plain['risk'].pop('analysis_seconds',None);measured['risk'].pop('analysis_seconds',None)
    assert plain==measured
    assert 'error' in request({'profile':'yes'})
    denied=server.handle({'jsonrpc':'2.0','id':2,'method':'tools/call',
        'params':{'name':'codedna_check','arguments':{'profile':True}}})
    assert 'error' in denied
