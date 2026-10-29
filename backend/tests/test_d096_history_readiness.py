"""Readiness bounds are optimistic screens, never fabricated training outcomes."""
import importlib
from pathlib import Path
import pytest


@pytest.fixture
def readiness(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]/'scripts'))
    return importlib.import_module('screen_d096_history_readiness').readiness


@pytest.mark.parametrize('count,possible',[(0,False),(8,False),(60,True)])
def test_readiness_uses_real_gate_bound(repo,readiness,count,possible):
    builds=[{'number':i,'commit':str(i),'finished':1} for i in range(count)]
    target={'started':10,'commit':'head','parent':'base'}
    result=readiness(target,builds,set(range(count)))
    assert result['optimistic_prior_unique_commits']==count
    assert result['can_meet_either_gate_even_optimistically'] is possible


def test_future_missing_duplicate_and_current_commit_do_not_inflate_history(repo,readiness):
    builds=[{'number':1,'commit':'base','finished':1},{'number':2,'commit':'base','finished':2},
            {'number':3,'commit':'future','finished':20},{'number':4,'commit':'missing','finished':1},
            {'number':5,'commit':'head','finished':1}]
    result=readiness({'started':10,'commit':'head','parent':'base'},builds,{1,2,3,5})
    assert result['optimistic_prior_unique_commits']==1
    assert result['base_has_available_completed_root_report']
