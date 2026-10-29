"""CI completion/order invariants on temporary repositories; no network."""
from dataclasses import replace
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]/'scripts'))
    return importlib.import_module('d092_prequential'),importlib.import_module('run_d092_main_ci')


def builds(repo,module):
    times=[(0,10),(5,12),(11,13),(13,20)];result=[];parent=None
    for index,(start,end) in enumerate(times,1):
        repo.write('A.java',f'class A {{ int x={index}; }}')
        commit=repo.commit(str(index))
        result.append(module.Build(index,commit,parent,start,end,True));parent=commit
    return result


def test_decision_is_persisted_before_truth_and_overlap_waits(repo,modules):
    module,_=modules;sequence=builds(repo,module);persisted=set();visible=[]
    def decide(build,history):
        visible.append([x.build.number for x in history]);return {'action':'all'}
    def persist(build,decision,history):persisted.add(build.number)
    def truth(build):
        assert build.number in persisted
        return module.Outcome({'Test'},set(),True)
    module.replay(sequence,decide,truth,persist)
    assert visible==[[],[],[1],[1,2,3]]


def test_future_mutation_cannot_affect_decision_until_completion(repo,modules):
    module,_=modules;sequence=builds(repo,module)
    def run(changed):
        def decide(build,history):return {'failures':sum(bool(x.outcome.failed) for x in history)}
        def truth(build):return module.Outcome({'Test'},{'Test'} if changed and build.number==2 else set(),True)
        return module.replay(sequence,decide,truth,lambda *args:None)
    before,after=run(False),run(True)
    assert [r['decision'] for r in before[:3]]==[r['decision'] for r in after[:3]]
    assert before[3]['decision']!=after[3]['decision']


def test_passing_repeat_cannot_erase_failure_or_inflate_commit_count(modules):
    module,_=modules
    one=module.Build(1,'sha','parent',0,1,True);two=replace(one,number=2,started=2,finished=3)
    history=[module.Completed(one,module.Outcome({'Test'},{'Test'},True)),
             module.Completed(two,module.Outcome({'Test'},set(),True))]
    usable,unstable=module.eligible_history(history,{'sha'},4)
    assert not usable and unstable=={'sha'}
    assert history[0].outcome.failed==frozenset({'Test'})


def test_report_unknown_status_is_not_a_pass_and_failure_is_kept(modules):
    _,runner=modules
    report={'passCount':1,'failCount':1,'skipCount':0,'suites':[{'cases':[
        {'className':'Test','status':'FAILED'}, {'className':'Other','status':'UNKNOWN'}]}]}
    result=runner.parse_report(report)
    assert not result.complete_as_published and result.failed==frozenset({'Test'})


def test_duplicate_build_identity_is_rejected_before_truth(repo,modules):
    module,_=modules;sequence=builds(repo,module)
    with pytest.raises(ValueError,match='Duplicate'):
        module.replay([sequence[0],sequence[0]],None,None,None)


def test_maven_aggregate_requires_matching_child_counts(modules):
    _,runner=modules
    child={'passCount':1,'failCount':1,'skipCount':0,'suites':[{'cases':[
        {'className':'Pass','status':'PASSED'},{'className':'Fail','status':'FAILED'}]}]}
    data={'failCount':1,'skipCount':0,'childReports':[{'result':child}]}
    outcome=runner.parse_report(data)
    assert outcome.complete_as_published and outcome.failed==frozenset({'Fail'})
    data['failCount']=0
    assert not runner.parse_report(data).complete_as_published


def test_missing_child_count_is_not_assumed_zero(modules):
    _,runner=modules
    data={'failCount':0,'skipCount':0,'childReports':[{'result':{
        'suites':[{'cases':[{'className':'Test','status':'PASSED'}]}]}}]}
    assert not runner.parse_report(data).complete_as_published
