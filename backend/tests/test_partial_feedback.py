from dataclasses import replace
from types import MappingProxyType

import pytest

from codedna.models.partial_feedback import (
    AuditedPolicy, DecisionTest, DecisionView, FullPolicy, Observation, ObservedTest,
    Proposal, ReplayConfig, StructuralPlan, StructuralPolicy, complete_dataset, run_replay,
)
from codedna.test_history.features import CHANGE_FEATURES, TEST_FEATURES, HISTORY_FEATURES, Dataset, Row


@pytest.fixture
def sample(repo):
    commits=[]; rows=[]
    for i in range(5):
        repo.write('A.java', f'class A {{ int value() {{ return {i}; }} }}')
        commit=repo.commit(f'change {i}')
        commits.append(commit)
        for test in ['a','b']:
            features={name:0. for name in CHANGE_FEATURES+TEST_FEATURES+HISTORY_FEATURES}
            features.update(files_changed=1.,java_files_changed=1.,mean_duration=9999.,past_failures=9999.)
            rows.append(Row(commit,i,test,int(test=='b'),1. if test=='a' else 2.,features))
    return Dataset(rows,list(rows[0].features),commits)


def plans(data, *, required=('a',), pinned=(), available=True):
    return {c:StructuralPlan(frozenset(required),frozenset(pinned),available) for c in data.commits}


class OnlyA:
    structural=False
    def decide(self,view,history): return Proposal(frozenset({'a'}),'fixed')


def signatures(output):
    return [(r['selected'],r['proposed'],r['input_digest'],r['status']) for r in output['trace']]


def test_hidden_labels_do_not_change_decisions_until_audit_reveals_them(sample):
    class ReactToObservedFailure:
        structural=False
        def decide(self,view,history):
            b=next(t for t in view.tests if t.test_id=='b')
            return Proposal(frozenset({'b' if b.features['past_failures'] else 'a'}),'observed_only')
    mutated=replace(sample,rows=[replace(r,label=0) if r.test_id=='b' else r for r in sample.rows])
    config=ReplayConfig(warmup=0,audit_every=3)
    first=run_replay(sample,plans(sample),config,{'p':ReactToObservedFailure})['p']
    second=run_replay(mutated,plans(mutated),config,{'p':ReactToObservedFailure})['p']
    assert signatures(first)[:3]==signatures(second)[:3]
    assert first['trace'][3]['selected']!=second['trace'][3]['selected']


def test_hidden_durations_and_original_history_features_cannot_drive_choices(sample):
    class ReactToObservedDuration:
        structural=False
        def decide(self,view,history):
            b=next(t for t in view.tests if t.test_id=='b')
            return Proposal(frozenset({'b' if b.features['mean_duration']>10 else 'a'}),'observed_only')
    changed=replace(sample,rows=[replace(r,duration=999.) if r.test_id=='b' else r for r in sample.rows])
    config=ReplayConfig(warmup=0,audit_every=3)
    one=run_replay(sample,plans(sample),config,{'p':ReactToObservedDuration})['p']
    two=run_replay(changed,plans(changed),config,{'p':ReactToObservedDuration})['p']
    assert signatures(one)[:3]==signatures(two)[:3]
    assert one['trace'][3]['selected']!=two['trace'][3]['selected']
    forged=replace(sample,rows=[replace(r,features={**r.features,**{key:1e9 for key in HISTORY_FEATURES}}) for r in sample.rows])
    other=run_replay(forged,plans(forged),config,{'p':ReactToObservedDuration})['p']
    assert signatures(one)==signatures(other)


def test_history_only_contains_executed_results_and_freezes_pre_reveal_features(sample):
    seen=[]
    class Capture(OnlyA):
        def decide(self,view,history):
            seen.append((view,history))
            assert not hasattr(view.tests[0],'label') and not hasattr(view.tests[0],'duration')
            with pytest.raises(TypeError): view.tests[0].features['past_runs']=123
            return super().decide(view,history)
    run_replay(sample,plans(sample),ReplayConfig(warmup=0,audit_every=3),{'p':Capture},
               changed_paths={c:('A.java',) for c in sample.commits})
    view,history=seen[2]  # index3, after the scheduled full audit at index2
    assert view.index==3
    assert [t.test_id for t in history[0].tests]==['a']
    assert history[0].complete is False and history[2].complete is True
    b=next(t for t in history[2].tests if t.test_id=='b')
    assert b.label==1 and b.features['past_failures']==0 and b.features['past_runs']==0
    current=next(t for t in view.tests if t.test_id=='b')
    assert current.features['past_failures']==1 and current.features['co_failures']==1
    assert current.features['commits_since_failure']==1
    complete=complete_dataset(history,['past_runs'])
    assert complete.commits==[sample.commits[2]]


def test_policies_have_isolated_observed_state_and_fresh_instances(sample):
    result=run_replay(sample,plans(sample),ReplayConfig(warmup=0,audit_every=99),
                      {'reduced':OnlyA,'full':FullPolicy})
    assert result['reduced']['trace'][2]['input_digest']!=result['full']['trace'][2]['input_digest']
    instance=OnlyA()
    with pytest.raises(ValueError,match='fresh isolated'):
        run_replay(sample,plans(sample),ReplayConfig(warmup=0),{'x':lambda:instance,'y':lambda:instance})


def test_safety_escape_and_recall_have_distinct_denominators(sample):
    data=replace(sample,commits=sample.commits[:1],rows=[replace(r,label=1) for r in sample.rows[:2]])
    class NoneSelected:
        structural=False
        def decide(self,view,history): return Proposal(frozenset(),'none')
    result=run_replay(data,plans(data),ReplayConfig(warmup=0,audit_every=99),
                      {'one':OnlyA,'none':NoneSelected,'full':FullPolicy})
    one=result['one']['metrics']; none=result['none']['metrics']; full=result['full']['metrics']
    assert one['zero_omission_safety']==0 and one['build_escape_rate']==0
    assert one['missed_class_fraction']==.5 and one['failing_class_recall']==.5
    assert none['build_escape_rate']==1 and full['zero_omission_safety']==1
    assert one['first_failure_classes']==2 and one['missed_first_failure_classes']==1


def test_no_failing_commits_does_not_produce_fake_safety(sample):
    data=replace(sample,rows=[replace(r,label=0) for r in sample.rows])
    result=run_replay(data,plans(data),ReplayConfig(warmup=0),{'full':FullPolicy})['full']['metrics']
    assert result['failing_commits']==0
    assert result['zero_omission_safety'] is None and result['build_escape_rate'] is None
    assert result['failing_class_recall'] is None


def test_audits_pins_structural_floor_and_warmup_are_charged_without_duplicate_runs(sample):
    class Combined(OnlyA): structural=True
    result=run_replay(sample,plans(sample,required=('b',),pinned=('b',)),
                      ReplayConfig(warmup=1,audit_every=2),{'p':Combined})['p']
    assert all(r['selected']==['a','b'] for r in result['trace'])
    assert result['trace'][0]['status']=='warmup_full'
    assert result['trace'][2]['status']=='scheduled_audit'
    assert result['trace'][1]['proposed']==['a']
    assert result['metrics']['recorded_test_seconds_including_warmup']==15
    assert result['metrics']['simulated_additional_repeated_executions']==0


def test_unavailable_structure_falls_back_to_full_and_unknown_ids_fail(sample):
    result=run_replay(sample,plans(sample,required=(),available=False),
                      ReplayConfig(warmup=0),{'s':StructuralPolicy})['s']
    assert all(row['selected']==['a','b'] for row in result['trace'])
    with pytest.raises(ValueError,match='unknown reference'):
        run_replay(sample,plans(sample,required=('missing',)),ReplayConfig(),{'s':StructuralPolicy})


def test_insufficient_audit_preserves_full_suite_without_invented_risk(sample):
    config=ReplayConfig(warmup=0)
    features=CHANGE_FEATURES+TEST_FEATURES+[f for f in HISTORY_FEATURES if f!='co_failures']
    result=run_replay(sample,plans(sample),config,{'h':lambda:AuditedPolicy(features,config)})['h']
    assert all(row['selected']==['a','b'] for row in result['trace'])
    assert result['trace'][0]['status']=='unvalidated_full'
    assert 'fewer than 40' in result['trace'][0]['evidence']['reason']


def test_audited_model_sees_only_complete_past_data_and_prediction_placeholders(sample,monkeypatch):
    import codedna.selection.live as live
    captured=[]
    features={**sample.rows[0].features,'mean_duration':1.,'past_runs':40.,'past_failures':0.}
    history=tuple(Observation(f'old{i}',i,i%2==0,
        (ObservedTest('a',i%2,1.,MappingProxyType(features)),)) for i in range(80))
    class Ranker:
        def predict_proba(self,rows):
            assert all(r.label==0 and r.duration==0 for r in rows)
            return [0. for _ in rows]
    class Calibrator:
        def transform(self,scores): return scores
    class Evidence:
        accepted=True; reasons=[]
        def to_dict(self): return {'accepted':True}
    def fit(data,names,target):
        captured.append(data)
        return Ranker(),Calibrator(),Evidence(),{}
    monkeypatch.setattr(live,'fit_audited',fit)
    view=DecisionView('current',80,(DecisionTest('a',MappingProxyType(features)),),StructuralPlan(frozenset()))
    policy=AuditedPolicy(list(features),ReplayConfig(warmup=0))
    policy.decide(view,history)
    assert captured[0].commits==[f'old{i}' for i in range(0,80,2)]
    assert len(captured[0].rows)==40 and all(r.label==0 for r in captured[0].rows)
    # Off-cadence branch change invalidates an otherwise accepted cached fit.
    decision=policy.decide(replace(view,index=81),history[1:])
    assert decision.status=='unvalidated_full' and policy.model is None


def test_invalid_truth_is_rejected_before_any_decision(sample):
    class Forbidden:
        def __init__(self): pytest.fail('policy should not be constructed')
    data=replace(sample,rows=[replace(r,duration=-1) for r in sample.rows])
    with pytest.raises(ValueError,match='invalid reference truth'):
        run_replay(data,plans(data),ReplayConfig(),{'x':Forbidden})


def test_foreign_branch_observations_do_not_enter_current_features(sample):
    changed=replace(sample,rows=[replace(r,label=1,duration=999.) if r.commit==sample.commits[1] else r for r in sample.rows])
    eligibility={commit:frozenset(c for c in sample.commits[:i] if c!=sample.commits[1])
                 for i,commit in enumerate(sample.commits)}
    config=ReplayConfig(warmup=0,audit_every=99)
    one=run_replay(sample,plans(sample),config,{'p':OnlyA},eligible_history=eligibility)['p']
    two=run_replay(changed,plans(changed),config,{'p':OnlyA},eligible_history=eligibility)['p']
    assert signatures(one)==signatures(two)
    assert one['trace'][2]['eligible_prior_commits']==1
