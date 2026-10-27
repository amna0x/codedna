"""The optional job API retains loopback/token and explicit-build boundaries."""
import sys
import time

import pytest
from fastapi.testclient import TestClient

from codedna.api.app import create_app

TOKEN = 't' * 32
AUTH = {'X-CodeDNA-Token': TOKEN}


def await_result(client, key):
    end = time.monotonic() + 90
    while time.monotonic() < end:
        response = client.get('/api/analysis-jobs/' + key, headers=AUTH)
        assert response.status_code == 200
        value = response.json()
        if value['state'] in {'completed', 'failed', 'cancelled'}:
            return value
        time.sleep(.02)
    raise AssertionError(value)


def test_job_routes_require_token_loopback_host_and_typed_inputs(repo):
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    app = create_app(TOKEN)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        assert client.post('/api/analysis-jobs/tests', json={'repo': str(repo.path)}).status_code == 401
        assert client.get('/api/analysis-jobs/not-owned').status_code == 401
        assert client.post('/api/analysis-jobs/not-owned/cancel').status_code == 401
        assert client.post('/api/analysis-jobs/tests', headers={**AUTH, 'Host': 'evil.example'},
                           json={'repo': str(repo.path)}).status_code == 403
        for operation, body in [('tests', {}), ('analyze', {'repo': 'x'}),
                                ('impact', {'repo': 'x', 'base': 'a', 'head': 'b', 'max_depth': -1}),
                                ('select', {'repo': 'x', 'base': 'a', 'head': 'b', 'strategy': 'shell'}),
                                ('risk-select', {'repo': 'x', 'base': 'a', 'head': 'b', 'risk_target': 0})]:
            assert client.post('/api/analysis-jobs/' + operation, headers=AUTH, json=body).status_code == 422
        assert app.state.analysis_jobs._thread is None
        assert client.post('/api/analysis-jobs/run-tests', headers=AUTH, json={}).status_code == 405
        assert client.get('/api/analysis-jobs/not-owned', headers=AUTH).status_code == 404
        assert client.post('/api/analysis-jobs/not-owned/cancel', headers=AUTH).status_code == 404
        capabilities = client.get('/api/capabilities', headers=AUTH).json()
        assert capabilities['analysis_jobs']['version'] == 1
        assert capabilities['allow_build'] is False


@pytest.mark.parametrize('operation', ['tests', 'analyze', 'impact', 'select', 'risk-select'])
def test_job_results_equal_synchronous_routes_without_executing_project_code(repo, operation):
    repo.write('src/main/java/A.java', 'class A { int value() { return 1; } }')
    repo.write('src/test/java/ATest.java', 'import org.junit.jupiter.api.Test; class ATest { @Test void check() {} }')
    base = repo.commit('initial')
    repo.write('src/main/java/A.java', 'class A { int value() { return 2; } }'); head = repo.commit('change')
    body = {'repo': str(repo.path), 'base': base, 'head': head}
    if operation == 'tests': body = {'repo': str(repo.path), 'rev': head}
    if operation == 'select': body['strategy'] = 'dependency'
    with TestClient(create_app(TOKEN), base_url='http://127.0.0.1') as client:
        expected = client.post('/api/' + operation, headers=AUTH, json=body)
        assert expected.status_code == 200
        submitted = client.post('/api/analysis-jobs/' + operation, headers=AUTH, json=body)
        assert submitted.status_code == 202
        key = submitted.json()['id']
        completed = await_result(client, key)
        assert completed['state'] == 'completed', completed
        result, synchronous = completed['result'], expected.json()
        if operation == 'risk-select':
            # Independently measured execution time is not a decision field.
            for report in (result, synchronous):
                seconds = report['risk'].pop('analysis_seconds')
                assert isinstance(seconds, (int, float)) and 0 <= seconds < 90
        assert result == synchronous
        assert not (repo.path / '.codedna').exists()


def test_queue_limit_and_shutdown_cleanup_are_visible_at_api_boundary(repo, tmp_path, monkeypatch):
    from codedna.api import analysis_jobs
    repo.write('A.java', 'class A {}'); repo.commit('fixture')
    helper = tmp_path / 'trusted_waiter.py'
    helper.write_text("import sys,time; sys.stdin.readline(); time.sleep(120)")
    monkeypatch.setattr(analysis_jobs, 'worker_command', lambda: [sys.executable, str(helper)])
    app = create_app(TOKEN)
    with TestClient(app, base_url='http://127.0.0.1') as client:
        first = client.post('/api/analysis-jobs/tests', headers=AUTH, json={'repo': str(repo.path)}).json()['id']
        end = time.monotonic() + 10
        while app.state.analysis_jobs.get(first)['state'] == 'queued' and time.monotonic() < end:
            time.sleep(.01)
        second = client.post('/api/analysis-jobs/tests', headers=AUTH, json={'repo': str(repo.path)}).json()['id']
        third = client.post('/api/analysis-jobs/tests', headers=AUTH, json={'repo': str(repo.path)}).json()['id']
        assert client.post('/api/analysis-jobs/tests', headers=AUTH, json={'repo': str(repo.path)}).status_code == 429
        assert client.post('/api/analysis-jobs/' + second + '/cancel', headers=AUTH).json()['state'] == 'cancelled'
        # Another API session cannot inspect or cancel this session's worker.
        with TestClient(create_app('u' * 32), base_url='http://127.0.0.1') as other:
            assert other.get('/api/analysis-jobs/' + first, headers={'X-CodeDNA-Token': 'u' * 32}).status_code == 404
    assert app.state.analysis_jobs.get(first)['state'] == 'cancelled'
    assert app.state.analysis_jobs.get(third)['state'] == 'cancelled'
    assert not app.state.analysis_jobs._thread.is_alive()
