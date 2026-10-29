"""Outcome-blind multi-project selection and bounded-memory ancestry checks."""
import importlib.util
from pathlib import Path


def load(name, monkeypatch):
    folder=Path(__file__).resolve().parents[2]/'scripts'
    monkeypatch.syspath_prepend(str(folder))
    spec=importlib.util.spec_from_file_location(name,folder/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_larger_selection_keeps_earliest_build_and_fixed_split(monkeypatch):
    choose=load('prepare_d091_cohorts',monkeypatch).choose
    rows=[{'project':'hive','pr_base_branch':'master','build_head_sha':str(i),
           'pr_name':str(i),'build_id':'1','build_timestamp':str(i),'stage_id':'single'} for i in range(23)]
    rows.append({**rows[0],'build_id':'9','build_timestamp':'999'})
    first,total=choose(rows,'hive','master',maximum=21)
    reverse,_=choose(list(reversed(rows)),'hive','master',maximum=21)
    assert first==reverse and total==23
    assert [sum(b['split']==s for b in first) for s in ['train','audit','evaluation']]==[12,4,5]
    assert first[0]['excluded_later_rerun_rows']==1
    assert first[0]['jobs'][0]['build_id']=='1'


def test_ancestry_does_not_confuse_siblings_or_include_self(monkeypatch):
    prior=load('audit_d091_ancestry',monkeypatch).prior_heads
    graph={'a':[], 'b':['a'], 'c':['a'], 'd':['b','c']}
    assert prior(graph,'b',{'a','b','c'})=={'a'}
    assert prior(graph,'d',{'a','b','c','d'})=={'a','b','c'}
