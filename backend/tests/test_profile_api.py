"""Real optional profile reporting without changing core decisions or defaults."""
import time
from fastapi.testclient import TestClient
from codedna.api.app import create_app

AUTH={'X-CodeDNA-Token':'t'*32}

def done(client,key):
    end=time.monotonic()+60
    while time.monotonic()<end:
        result=client.get('/api/analysis-jobs/'+key,headers=AUTH).json()
        if result['state'] in {'completed','failed','cancelled'}:return result
        time.sleep(.02)
    raise AssertionError(result)


def test_profile_is_optional_and_contains_measured_stages_without_source(repo):
    repo.write('src/test/java/ATest.java','import org.junit.jupiter.api.Test; class ATest { @Test void works() {} }')
    repo.commit('fixture')
    with TestClient(create_app('t'*32),base_url='http://127.0.0.1') as client:
        body={'repo':str(repo.path)}
        first=client.post('/api/analysis-jobs/tests',headers=AUTH,json=body)
        plain=done(client,first.json()['id']);assert plain['state']=='completed',plain
        assert 'metrics' not in plain
        second=client.post('/api/analysis-jobs/tests?profile=true',headers=AUTH,json=body)
        profiled=done(client,second.json()['id']);assert profiled['state']=='completed',profiled
        assert profiled['result']==plain['result']
        metrics=profiled['metrics']
        assert metrics['total_seconds']>0 and metrics['worker_startup_seconds']>0
        assert metrics['stages']['git']['calls']>0
        assert metrics['stages']['parse.java']['calls']>0
        assert str(repo.path) not in str(metrics) and 'source' not in metrics


def test_profile_explains_cold_history_fallback_and_invalid_profile_is_rejected(repo):
    repo.write('pom.xml','<project/>')
    repo.write('src/main/java/A.java','class A {}')
    repo.write('src/test/java/ATest.java','import org.junit.jupiter.api.Test; class ATest { @Test void works() {} }')
    base=repo.commit('fixture');repo.write('src/main/java/A.java','class A { int n; }');head=repo.commit('change')
    with TestClient(create_app('t'*32),base_url='http://127.0.0.1') as client:
        body={'repo':str(repo.path),'base':base,'head':head}
        submitted=client.post('/api/analysis-jobs/risk-select?profile=true',headers=AUTH,json=body)
        result=done(client,submitted.json()['id']);assert result['state']=='completed',result
        assert result['result']['risk']['status']=='unvalidated' and not result['result']['skipped']
        assert result['metrics']['counters']['fallback.history_missing']==1
        assert 'risk.training' not in result['metrics']['stages']
        assert client.post('/api/analysis-jobs/tests?profile=garbage',headers=AUTH,json={'repo':str(repo.path)}).status_code==422


def test_failed_analysis_keeps_measured_diagnostics_but_no_result(repo):
    repo.write('A.java','class A {}');repo.commit('fixture')
    with TestClient(create_app('t'*32),base_url='http://127.0.0.1') as client:
        submitted=client.post('/api/analysis-jobs/tests?profile=true',headers=AUTH,
                              json={'repo':str(repo.path/'missing')})
        result=done(client,submitted.json()['id'])
        assert result['state']=='failed' and 'result' not in result
        assert result['metrics']['total_seconds']>0
