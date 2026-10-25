"""Offline live-risk domain and evidence checks using temporary repositories."""
from dataclasses import replace
import json
import pytest
from fastapi.testclient import TestClient
from codedna.api.app import create_app
from codedna.selection.live import recommend
from codedna.plugins.java_live import prediction_rows, fit_audited, LIVE_FEATURES
from codedna.selection.validation import validate_outcomes
from codedna.test_history.features import Dataset,Row
from codedna.models.dante_history import historical_scores,order_history

JAVA='package a; public class Core { int value() { return 1; } }'
TEST='package a; import org.junit.jupiter.api.Test; class CoreTest { @Test void test() {} }'

@pytest.fixture
def change(repo):
    repo.write('src/main/java/a/Core.java',JAVA)
    repo.write('src/test/java/a/CoreTest.java',TEST)
    repo.write('pom.xml','<project/>')
    base=repo.commit('base')
    repo.write('src/main/java/a/Core.java',JAVA.replace('return 1','return 2'))
    head=repo.commit('change')
    return repo,base,head


def dataset(commits):
    rows=[]
    for i,sha in enumerate(commits):
        for j in range(2):
            features={k:0. for k in LIVE_FEATURES}
            features.update(mean_duration=1.,past_runs=float(i),failure_rate=float(j==0),
                failed_last_run=float(j==0),recent_failures=5.*(j==0))
            rows.append(Row(sha,i,'a.CoreTest' if j==0 else 'a.OtherTest',int(j==0),1.,features))
    return Dataset(rows,list(LIVE_FEATURES),commits)


def test_no_history_returns_full_suite_with_no_invented_risk(change):
    repo,base,head=change
    r=recommend(repo.path,base,head)
    assert r['risk']['status']=='unvalidated'
    assert r['risk']['estimated_skip_risk'] is None
    assert r['skipped']==[] and r['selected'][0]['test']=='a.CoreTest'


@pytest.mark.parametrize('kind',['future','foreign','stale'])
def test_history_is_bound_to_target_ancestry_and_base(change,tmp_path,kind):
    repo,base,head=change
    shas=[head] if kind=='future' else ['f'*40] if kind=='foreign' else []
    if kind=='stale':
        earlier=repo.git('rev-list','--max-parents=0',base)
        repo.write('src/main/java/a/Core.java',JAVA.replace('return 1','return 3'))
        head=repo.commit('third')
        base=repo.git('rev-parse','HEAD^1')
        shas=[earlier]
    path=tmp_path/'history.csv';dataset(shas).to_csv(path)
    r=recommend(repo.path,base,head,history_csv=path)
    assert r['risk']['status']=='unvalidated' and not r['skipped']
    assert r['risk']['validation'] is None


def test_prediction_uses_prior_outcomes_and_costs_only(change):
    repo,base,head=change
    from codedna.git_analysis import extract_changes
    d=dataset([base]);d.rows[0].duration=7.
    rows=prediction_rows(d,extract_changes(repo.path,base,head),['a.CoreTest'])
    assert rows[0].label==0 and rows[0].duration==0
    assert rows[0].features['past_failures']==1
    assert rows[0].features['mean_duration']==7.


def test_audit_needs_failures_recall_and_an_upper_bound(repo):
    assert not validate_outcomes([(0.,0,0)]*1000).accepted
    assert not validate_outcomes([(0.,1,1)]*100).accepted
    assert not validate_outcomes([(1.,1,0)]*10).accepted
    good=validate_outcomes([(.5,1,0)]*100)
    assert good.accepted and good.miss_upper_bound < .05
    assert good.failure_recall==1


def test_model_calibration_and_audit_are_separate(repo):
    d=dataset([str(i) for i in range(400)])
    model,cal,evidence,p=fit_audited(d)
    assert evidence.accepted
    assert len(p['training_commits'])==200
    assert len(p['calibration_commits'])==len(p['audit_commits'])==100
    assert not set(p['training_commits'])&set(p['audit_commits'])
    # Changing audit labels must not alter model or calibrator predictions.
    changed=Dataset([replace(r,label=1-r.label) if r.seq>=300 else r for r in d.rows],
                     d.feature_names,d.commits)
    m2,c2,e2,_=fit_audited(changed)
    assert cal.transform(model.predict_proba(d.rows[-4:]))==c2.transform(m2.predict_proba(d.rows[-4:]))
    assert not e2.accepted


def test_history_ranker_does_not_read_current_or_future_labels(repo):
    d=dataset(['a','b','c','d'])
    before=historical_scores(d)
    changed=Dataset([replace(r,label=1-r.label) if r.seq>=2 else r for r in d.rows],d.feature_names,d.commits)
    after=historical_scores(changed)
    assert all(before[(c,r.test_id)]==after[(c,r.test_id)] for c in ['a','b','c'] for r in d.rows[:2])
    assert set(order_history(d.rows[:2],before))=={'a.CoreTest','a.OtherTest'}


def test_api_gate_and_execution_permission(change):
    repo,base,head=change
    api=TestClient(create_app('t'*32),base_url='http://127.0.0.1')
    body={'repo':str(repo.path),'base':base,'head':head}
    assert api.post('/api/risk-select',json=body).status_code==401
    auth={'X-CodeDNA-Token':'t'*32}
    r=api.post('/api/risk-select',json=body,headers=auth)
    assert r.status_code==200 and r.json()['risk']['status']=='unvalidated'
    assert api.post('/api/run-selection',headers=auth,json={**body,'allow_build':True}).status_code==403


def test_cli_risk_select(change,capsys):
    from codedna.cli import main
    repo,base,head=change
    assert main(['risk-select','--repo',str(repo.path),'--base',base,'--head',head])==0
    assert json.loads(capsys.readouterr().out)['risk']['status']=='unvalidated'


def test_validation_rejects_partial_audit_history(change,tmp_path,monkeypatch):
    import codedna.plugins.java_live as live
    repo,base,head=change
    # All SHAs are real target ancestors, but the audit omits the current class.
    rows=[Row(base,0,'a.OtherTest',0,1.,{k:0. for k in LIVE_FEATURES})]
    path=tmp_path/'partial.csv';Dataset(rows,list(LIVE_FEATURES),[base]).to_csv(path)
    # Missing current class is rejected before any model is fitted.
    def forbidden(*args,**kwargs): raise AssertionError('must not fit partial history')
    monkeypatch.setattr(live,'fit_audited',forbidden)
    r=live.recommend(repo.path,base,head,history_csv=path)
    assert r['risk']['status']=='unvalidated'
    assert not r['skipped']


def validated_change(repo,tmp_path,policy_text=None):
    """240 recorded target commits, then one unobserved change of Core."""
    from codedna.git_analysis.git import run_git_bytes
    repo.write('pom.xml','<project/>')
    repo.write('src/main/java/a/Core.java',JAVA)
    repo.write('src/test/java/a/CoreTest.java',TEST)
    repo.write('src/test/java/a/OtherTest.java',TEST.replace('CoreTest','OtherTest'))
    if policy_text:
        repo.write('.codedna/policy.toml',policy_text)
    initial=repo.commit('initial')
    branch=repo.git('symbolic-ref','--short','HEAD')
    commands=[]
    for i in range(1,241):
        parent=initial if i==1 else ':'+str(i-1)
        commands.append(f'commit refs/heads/{branch}\nmark :{i}\ncommitter Test <test@example.invalid> {1700000000+i} +0000\ndata 7\nhistory\nfrom {parent}\n\n')
    run_git_bytes(repo.path,'fast-import','--quiet',stdin=''.join(commands).encode())
    shas=repo.git('rev-list','--first-parent','--reverse','HEAD').splitlines()
    base=shas[-1]
    path=tmp_path/'history.csv';dataset(shas).to_csv(path)
    repo.write('src/main/java/a/Core.java',JAVA.replace('return 1','return 2'))
    head=repo.commit('unobserved change')
    return base,head,path


def test_live_acceptance_uses_only_real_prior_target_ancestors(repo,tmp_path):
    base,head,path=validated_change(repo,tmp_path)
    result=recommend(repo.path,base,head,history_csv=path)
    assert result['risk']['status']=='validated_history',result['risk']
    assert result['risk']['validation']['accepted']
    assert [t['test'] for t in result['selected']]==['a.CoreTest']
    assert result['skipped']==['a.OtherTest']
    assert head not in result['risk']['provenance']['audit_commits']
    assert result['risk']['estimated_skip_risk']==0.


def test_validated_selection_never_skips_must_run_tests(repo,tmp_path):
    policy='[[must_run]]\ntests = ["a.OtherTest"]\nreason = "smoke suite"\n'
    base,head,path=validated_change(repo,tmp_path,policy)
    result=recommend(repo.path,base,head,history_csv=path)
    assert result['risk']['status']=='validated_history',result['risk']
    assert [t['test'] for t in result['selected']]==['a.CoreTest','a.OtherTest']
    assert result['skipped']==[] and result['policy']['pinned']==['a.OtherTest']
    other=result['selected'][1]
    assert other['reasons'][0]=='must-run: smoke suite'
    # Request patterns add to the project policy.
    both=recommend(repo.path,base,head,history_csv=path,must_run=['a.Core*'])
    assert both['policy']['pinned']==['a.CoreTest','a.OtherTest']


def test_fallback_keeps_must_run_reasons(change):
    repo,base,head=change
    r=recommend(repo.path,base,head,must_run=['a.CoreTest'])
    assert r['risk']['status']=='unvalidated'
    assert r['selected'][0]['reasons']==['risk unvalidated: run the full suite',
                                         'must-run: pinned by request']


@pytest.mark.parametrize('value',[0.,1.,float('nan'),float('inf')])
def test_invalid_risk_target_rejected_even_without_history(change,value):
    repo,base,head=change
    with pytest.raises(ValueError,match='strictly between'):
        recommend(repo.path,base,head,risk_target=value)


def test_dante_history_adapter_isolates_test_windows_and_matches_fixed_score(repo):
    d=dataset([str(i) for i in range(22)])
    values=historical_scores(d)
    # Twenty prior conditioning events enable all ten fixed lag windows.
    expected=(1+sum(1/n for n in range(1,11)))*21
    assert values[('21','a.CoreTest')]==pytest.approx(expected)
    assert values[('21','a.OtherTest')]==0.
    assert values[('21','a.CoreTest')]>1.  # ranking score, never a probability
