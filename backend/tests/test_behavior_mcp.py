"""The optional witness tool cannot bypass repository consent or the test brake."""
from pathlib import Path

import pytest

from codedna.agent.mcp_server import BrakeServer


def call(server,name,arguments=None):
    return server.handle({'jsonrpc':'2.0','id':1,'method':'tools/call',
        'params':{'name':name,'arguments':arguments or {}}})


def names(server):
    return [tool['name'] for tool in server.handle({'jsonrpc':'2.0','id':1,'method':'tools/list'})['result']['tools']]


def project(repo):
    repo.write('pom.xml','<project/>')
    repo.write('src/main/java/example/Fee.java',
        'package example; public class Fee { public static int fee(int x) { return x+1; } }')
    repo.write('src/test/java/example/FeeTest.java',
        'package example; import org.junit.jupiter.api.Test; class FeeTest { @Test void check() {} }')
    base=repo.commit('base')
    repo.write('src/main/java/example/Fee.java',
        'package example; public class Fee { public static int fee(int x) { return x+2; } }')
    return base,repo.commit('head')


def test_default_tools_stay_unchanged_and_opt_in_needs_build_consent(repo):
    project(repo)
    normal=BrakeServer(repo=repo.path)
    builds=BrakeServer(repo=repo.path,allow_build=True)
    assert names(normal)==['codedna_plan_tests','codedna_impact']
    assert names(builds)==['codedna_plan_tests','codedna_impact','codedna_check']
    assert 'error' in call(builds,'codedna_find_witness')
    with pytest.raises(ValueError,match='allow-build'):
        BrakeServer(repo=repo.path,moonshot=True)
    with pytest.raises(ValueError,match='needs --repo'):
        BrakeServer(allow_build=True,moonshot=True)
    enabled=BrakeServer(repo=repo.path,allow_build=True,moonshot=True)
    assert names(enabled)==names(builds)+['codedna_find_witness']


@pytest.mark.parametrize('arguments',[{}, {'file':'Fee.java'},
    {'file':'Fee.java','symbol':'Fee#fee(int)','output_dir':''},
    {'file':'Fee.java','symbol':'Fee#fee(int)','output_dir':'new','surprise':True}])
def test_required_arguments_are_validated_before_execution(repo,arguments,monkeypatch):
    import codedna.behavior as behavior
    project(repo)
    def forbidden(*args,**kwargs):raise AssertionError('invalid tool arguments cannot execute')
    monkeypatch.setattr(behavior,'find_difference',forbidden)
    server=BrakeServer(repo=repo.path,allow_build=True,moonshot=True)
    result=call(server,'codedna_find_witness',arguments)
    assert 'error' in result or result['result']['isError'] is True


def test_repository_bound_witness_cannot_execute_another_repository(repo,tmp_path,monkeypatch):
    import codedna.behavior as behavior
    project(repo)
    def forbidden(*args,**kwargs):raise AssertionError('cross-repository execution must be refused')
    monkeypatch.setattr(behavior,'find_difference',forbidden)
    server=BrakeServer(repo=repo.path,allow_build=True,moonshot=True)
    result=call(server,'codedna_find_witness',{'repo':str(tmp_path),'file':'Fee.java',
        'symbol':'Fee#fee(int)','output_dir':str(tmp_path/'out')})
    assert result['result']['isError'] is True


@pytest.mark.parametrize('status',['difference','no_difference_observed','unsupported','inconclusive','cancelled'])
def test_witness_result_does_not_change_required_tests_or_validation(repo,tmp_path,monkeypatch,status):
    import codedna.behavior as behavior
    base,head=project(repo)
    server=BrakeServer(repo=repo.path,allow_build=True,moonshot=True)
    comparison={'base':base,'head':head}
    before=call(server,'codedna_plan_tests',comparison)['result']['structuredContent']
    assert before['must_run']==['example.FeeTest'] and before['risk']['status']=='unvalidated'
    monkeypatch.setattr(behavior,'find_difference',lambda *a,**kw:dict(status=status,
        regression_established=False,required_tests_removed=False))
    result=call(server,'codedna_find_witness',{**comparison,'file':'src/main/java/example/Fee.java',
        'symbol':'example.Fee#fee(int)','output_dir':str(tmp_path/'out')})['result']
    assert result['isError']==(status in ('unsupported','inconclusive','cancelled'))
    after=call(server,'codedna_plan_tests',comparison)['result']['structuredContent']
    for planned in [before,after]:planned['risk'].pop('analysis_seconds',None)
    assert after==before


@pytest.mark.maven
def test_optional_mcp_executes_real_witness_and_profiles_project_execution(repo,tmp_path):
    base,head=project(repo)
    server=BrakeServer(repo=repo.path,allow_build=True,moonshot=True)
    result=call(server,'codedna_find_witness',{'base':base,'head':head,
        'file':'src/main/java/example/Fee.java','symbol':'example.Fee#fee(int)',
        'output_dir':str(tmp_path/'out'),'max_inputs':1,'reduce_budget':0,'timeout':120,'profile':True})['result']
    assert result['isError'] is False,result
    data=result['structuredContent']
    assert data['status']=='difference' and data['regression_established'] is False
    assert data['operation_timings']['scope']=='includes_project_execution'
    assert data['operation_timings']['stages']['behavior.comparison']['calls']==1
