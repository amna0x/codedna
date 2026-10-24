"""Selection execution cannot silently run the whole suite or unknown filters."""
import json,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from codedna.api.app import create_app
from codedna.test_mapping.maven import run_maven_tests,BuildError
FAKE=[sys.executable,str(Path(__file__).with_name('fake_mvn.py'))]

@pytest.fixture
def project(repo,tmp_path,monkeypatch):
    repo.write('pom.xml','<project/>')
    for name in ['ATest','BTest']:
        repo.write('src/test/java/a/'+name+'.java',
            'package a; import org.junit.jupiter.api.Test; class '+name+' { @Test void x() {} }')
    base=repo.commit('tests')
    spec=tmp_path/'spec.json';spec.write_text(json.dumps({'tests':{
        'a.ATest':{'status':'passed','time':1.,'cases':['x']},
        'a.BTest':{'status':'failed','time':2.,'cases':['x']}}}))
    monkeypatch.setenv('CODEDNA_FAKE_MVN_SPEC',str(spec))
    return repo,base


def test_run_one_selected_class(project,tmp_path):
    repo,head=project
    result,_=run_maven_tests(repo.path,head,tmp_path/'one',allow_build=True,
        selected_tests=['a.ATest'],maven_command=FAKE)
    assert set(result.tests)=={'a.ATest'}
    assert '-Dtest=a.ATest,a.ATest$*' in result.commands[0]
    assert not result.failing_tests


def test_empty_selection_never_invokes_maven(project,tmp_path):
    repo,head=project
    result,_=run_maven_tests(repo.path,head,tmp_path/'none',allow_build=True,
        selected_tests=[],maven_command=['nonexistent-command'])
    assert result.commands==[] and result.tests=={}


@pytest.mark.parametrize('tests',[['a.ATest','a.ATest'],['UnknownTest'],['*'],['a.ATest,-DskipTests']])
def test_invalid_test_filter_rejected_before_export(project,tmp_path,tests):
    repo,head=project
    with pytest.raises(BuildError,match='distinct discovered'):
        run_maven_tests(repo.path,head,tmp_path/'invalid',allow_build=True,
            selected_tests=tests,maven_command=FAKE)
    assert not (tmp_path/'invalid').exists()


def test_api_recomputes_full_fallback_and_requires_consent(project):
    repo,head=project
    api=TestClient(create_app('t'*32,allow_build=True,maven_command=FAKE),base_url='http://127.0.0.1')
    auth={'X-CodeDNA-Token':'t'*32};body={'repo':str(repo.path),'base':head,'head':head,'strategy':'risk'}
    assert api.post('/api/run-selection',headers=auth,json=body).status_code==400
    r=api.post('/api/run-selection',headers=auth,json={**body,'allow_build':True})
    assert r.status_code==200,r.text
    assert r.json()['selection']['risk']['status']=='unvalidated'
    assert len(r.json()['results']['tests'])==2
