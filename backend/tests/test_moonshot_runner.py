"""Pilot cannot execute before consent and a frozen tracked implementation."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[2]


def runner():
    spec=importlib.util.spec_from_file_location('moonshot_runner',ROOT/'scripts/run_moonshot_pilot.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_pilot_requires_explicit_execution_consent_before_creating_fixtures(repo,tmp_path):
    module=runner();module.ROOT=repo.path
    with pytest.raises(SystemExit) as error:module.main(['--out',str(tmp_path/'out')])
    assert error.value.code==2 and not (tmp_path/'out').exists()
    assert not (repo.path/'build').exists()


@pytest.mark.parametrize('guard',['dirty','untracked','escaping_case','duplicate_case'])
def test_unfrozen_or_escaping_pilot_is_rejected_before_any_execution(repo,tmp_path,monkeypatch,guard):
    module=runner();module.ROOT=repo.path
    cases={'cases':[{'id':'safe_case'}]}
    repo.write('experiments/moonshot-engineering-cases.json',json.dumps(cases))
    repo.write('source.py','original');repo.commit('baseline')
    module.PINNED=['source.py']
    monkeypatch.setattr(module,'fingerprints',lambda:{'source.py':'fixed'})
    if guard=='dirty':repo.write('source.py','changed')
    elif guard=='untracked':
        repo.write('other.py','untracked');module.PINNED=['other.py']
    elif guard=='escaping_case':
        cases['cases'][0]['id']='../../elsewhere'
        repo.write('experiments/moonshot-engineering-cases.json',json.dumps(cases))
    else:
        cases['cases'].append({'id':'safe_case'})
        repo.write('experiments/moonshot-engineering-cases.json',json.dumps(cases))
    def forbidden(*args,**kwargs):raise AssertionError('guard failed before execution')
    monkeypatch.setattr(module,'find_difference',forbidden)
    with pytest.raises(SystemExit) as error:
        module.main(['--out',str(tmp_path/'out'),'--allow-build'])
    assert error.value.code==2
    assert not (tmp_path/'out').exists() and not (repo.path/'build').exists()
