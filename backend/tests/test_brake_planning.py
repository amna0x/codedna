"""Structural planning and conservative Python/mixed brake behavior on real temp repos."""
import json
import sys
from pathlib import Path

import pytest

from codedna.agent import brake
from codedna.agent.mcp_server import BrakeServer
from codedna.selection import select_tests
from codedna.selection.live import recommend


@pytest.fixture
def java_project(repo):
    repo.write('pom.xml', '<project/>')
    for name in ['Core', 'Other']:
        repo.write(f'src/main/java/a/{name}.java',
                   f'package a; public class {name} {{ int value() {{ return 1; }} }}')
        repo.write(f'src/test/java/a/{name}Test.java',
                   f'package a; import org.junit.jupiter.api.Test; class {name}Test {{ '
                   f'@Test void check() {{ new {name}().value(); }} }}')
    repo.commit('base')
    repo.write('src/main/java/a/Core.java',
               'package a; public class Core { int value() { return 2; } }')
    return repo


@pytest.fixture
def python_project(repo):
    repo.write('pyproject.toml', '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    repo.write('tests/test_sample.py', 'def test_ok():\n    assert True\n')
    repo.commit('python base')
    repo.write('README.md', 'An agent edit.\n')
    return repo


def test_structural_plan_is_exact_dependency_selection(java_project):
    repo = java_project
    planned = brake.plan(repo.path)
    raw = select_tests(repo.path, planned['base_commit'], planned['head_commit'], 'dependency')
    structural = dict(planned['structural_plan'])
    assert structural.pop('note') == 'structural only, no probability'
    assert structural == raw.to_dict()
    assert [item['test'] for item in structural['selected']] == ['a.CoreTest']
    assert planned['must_run'] == ['a.CoreTest', 'a.OtherTest']
    assert planned['skipped'] == [] and planned['risk']['status'] == 'unvalidated'


def test_requested_pins_do_not_relabel_structural_only_plan(java_project):
    planned = brake.plan(java_project.path, must_run=['a.OtherTest'])
    assert [item['test'] for item in planned['structural_plan']['selected']] == ['a.CoreTest']
    assert set(planned['must_run']) == {'a.CoreTest', 'a.OtherTest'}
    assert 'a.OtherTest' in planned['pinned_by_policy']


def test_validated_risk_plan_cannot_omit_structural_tests(java_project, monkeypatch):
    import codedna.selection.live as live
    repo = java_project
    result = recommend(repo.path, 'HEAD', 'WORKTREE')
    result['selected'] = [item for item in result['selected'] if item['test'] == 'a.OtherTest']
    result['skipped'] = ['a.CoreTest']
    result['risk'] = {**result['risk'], 'status': 'validated_history',
                      'estimated_skip_risk': .01, 'reasons': []}
    monkeypatch.setattr(live, 'recommend', lambda *a, **k: result)
    planned = brake.plan(repo.path)
    assert set(planned['must_run']) == {'a.CoreTest', 'a.OtherTest'}
    assert planned['skipped'] == []
    assert planned['risk']['estimated_skip_risk'] == 0.0
    assert planned['summary'].startswith('Run 2 of 2')


def test_structural_plan_uses_same_immutable_snapshot(java_project, monkeypatch):
    import codedna.selection.live as live
    repo = java_project
    original = live.recommend
    captured = {}
    def edit_after_recommend(*args, **kwargs):
        result = original(*args, **kwargs)
        captured['head'] = result['head_commit']
        repo.write('src/main/java/a/Other.java',
                   'package a; public class Other { int value() { return 9; } }')
        return result
    monkeypatch.setattr(live, 'recommend', edit_after_recommend)
    planned = brake.plan(repo.path)
    assert planned['head_commit'] == captured['head']
    assert planned['structural_plan']['head_commit'] == captured['head']
    assert [item['test'] for item in planned['structural_plan']['selected']] == ['a.CoreTest']


def test_partial_broadening_labels_original_estimate_conservatively(java_project, monkeypatch):
    import codedna.selection.live as live
    repo = java_project
    repo.write('src/main/java/a/Third.java',
               'package a; public class Third { int value() { return 1; } }')
    repo.write('src/test/java/a/ThirdTest.java',
               'package a; import org.junit.jupiter.api.Test; class ThirdTest { '
               '@Test void check() { new Third().value(); } }')
    repo.commit('three independent test groups')
    repo.write('src/main/java/a/Core.java',
               'package a; public class Core { int value() { return 3; } }')
    result = recommend(repo.path, 'HEAD', 'WORKTREE')
    result['selected'] = [item for item in result['selected'] if item['test'] == 'a.OtherTest']
    result['skipped'] = ['a.CoreTest', 'a.ThirdTest']
    result['risk'] = {**result['risk'], 'status': 'validated_history',
                      'estimated_skip_risk': .01, 'reasons': []}
    monkeypatch.setattr(live, 'recommend', lambda *a, **k: result)
    planned = brake.plan(repo.path)
    assert set(planned['must_run']) == {'a.CoreTest', 'a.OtherTest'}
    assert planned['skipped'] == ['a.ThirdTest']
    assert planned['risk']['estimated_skip_risk'] == .01
    assert planned['risk']['estimate_is_conservative'] is True
    assert 'Conservative bound on the model' in planned['summary']
    assert any('conservative bound' in reason for reason in planned['risk']['reasons'])
    assert planned['summary'].startswith('Run 2 of 3')


@pytest.mark.parametrize('method', ['b10', 'crc'])
@pytest.mark.parametrize('language', [None, 'python'])
def test_python_plan_has_explicit_full_suite_fallback(python_project, method, language):
    planned = brake.plan(python_project.path, method=method, language=language)
    assert planned['must_run'] == ['py:tests.test_sample']
    assert planned['risk']['status'] == 'unvalidated'
    assert planned['risk']['estimated_skip_risk'] is None
    assert any('python' in reason and 'does not provide' in reason
               for reason in planned['risk']['reasons'])
    assert planned['skipped'] == []


def test_python_fallback_keeps_policy_pins(python_project):
    result = recommend(python_project.path, 'HEAD', 'WORKTREE', language='python',
                       must_run=['py:tests.test_sample'])
    assert 'py:tests.test_sample' in result['policy']['pinned']
    assert 'must-run: pinned by request' in result['selected'][0]['reasons']


@pytest.mark.parametrize('passing', [True, False])
def test_python_check_executes_pytest_and_reports_actual_verdict(python_project, passing):
    repo = python_project
    repo.write('tests/test_sample.py', f'def test_ok():\n    assert {passing}\n')
    before = repo.git('status', '--porcelain')
    result = brake.check(repo.path, allow_build=True, python_command=[sys.executable])
    assert result['verdict'] == ('passed' if passing else 'blocked')
    assert result['plan']['must_run'] == ['py:tests.test_sample']
    assert result['results']['tool'] == 'pytest'
    assert result['recording']['recorded'] is False
    assert repo.git('status', '--porcelain') == before


def test_python_check_still_requires_consent(python_project):
    with pytest.raises(ValueError, match='allow_build'):
        brake.check(python_project.path, python_command=['must-not-run'])


def test_mcp_python_plan_is_not_an_error(python_project):
    server = BrakeServer(repo=python_project.path)
    answer = server.handle({'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call',
                            'params': {'name': 'codedna_plan_tests', 'arguments': {}}})['result']
    assert not answer['isError']
    assert answer['structuredContent']['must_run'] == ['py:tests.test_sample']
    assert answer['structuredContent']['structural_plan']['note'] == 'structural only, no probability'


def test_mixed_repo_falls_back_and_runs_both_plugins(java_project, tmp_path, monkeypatch):
    repo = java_project
    repo.write('pyproject.toml', '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n')
    repo.write('tests/test_sample.py', 'def test_ok():\n    assert True\n')
    spec = tmp_path/'maven-spec.json'
    spec.write_text(json.dumps({'exit_code': 0, 'tests': {
        'a.CoreTest': {'status':'passed','time':1.0,'cases':['check']},
        'a.OtherTest': {'status':'passed','time':1.0,'cases':['check']}}}))
    monkeypatch.setenv('CODEDNA_FAKE_MVN_SPEC', str(spec))
    planned = brake.plan(repo.path)
    assert set(planned['must_run']) == {'a.CoreTest','a.OtherTest','py:tests.test_sample'}
    assert planned['risk']['status'] == 'unvalidated'
    assert 'Multiple test languages' in planned['risk']['reasons'][0]
    fake = Path(__file__).with_name('fake_mvn.py')
    result = brake.check(repo.path, allow_build=True, maven_command=[sys.executable,str(fake)],
                         python_command=[sys.executable])
    assert result['verdict'] == 'passed'
    assert {t['id'] for t in result['results']['tests']} == set(planned['must_run'])
    assert result['results']['tool'] == 'maven+pytest'


@pytest.mark.parametrize('target', [0.0, 1.0, float('nan')])
def test_unsupported_language_does_not_bypass_target_validation(python_project, target):
    with pytest.raises(ValueError, match='Risk target'):
        recommend(python_project.path, 'HEAD', 'WORKTREE', language='python', risk_target=target)


def test_unsupported_language_does_not_accept_unknown_method(python_project):
    with pytest.raises(ValueError, match='Unknown risk method'):
        recommend(python_project.path, 'HEAD', 'WORKTREE', language='python', method='unknown')
