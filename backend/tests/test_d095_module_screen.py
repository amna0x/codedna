"""Module screening uses identities/completeness, never favorable failures."""
import importlib
import json
from pathlib import Path

import pytest


@pytest.mark.parametrize('failed,reported,expected_candidates',[(False,'TTest',[0]),(True,'TTest',[0]),(False,'OtherTest',[])])
def test_module_screen_keeps_all_children_without_outcome_selection(repo,monkeypatch,failed,reported,expected_candidates):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]/'scripts'))
    module=importlib.import_module('screen_d095_ci_modules')
    root=repo.path
    monkeypatch.setattr(module,'__file__',str(root/'scripts/screen.py'))
    results=root/'experiments/results';results.mkdir(parents=True)
    (results/'source-universe-d093-2026-10-29.json').write_text(json.dumps({'commit':'a'*40,'parent':'b'*40}))
    cache=results/'rolling-main-ci-d092-corrected-2026-10-29';cache.mkdir()
    case={'className':'p.'+reported,'status':'FAILED' if failed else 'PASSED','name':'test'}
    report={'passCount':0 if failed else 1,'failCount':1 if failed else 0,'skipCount':0,'suites':[{'cases':[case]}]}
    (cache/'report-3012.json').write_text(json.dumps({'childReports':[{'result':report}]}))
    monkeypatch.setattr(module,'run_git',lambda *args:'m/src/test/java/p/TTest.java\nm/src/test/java/p/OtherTest.java\n')
    class Selection:
        def to_dict(self):return {'selected':[{'test':'p.TTest'}]}
    monkeypatch.setattr(module,'select_tests',lambda *args:Selection())
    module.main()
    output=json.loads((results/'module-compatibility-d095-2026-10-30.json').read_text())
    assert output['candidate_children']==expected_candidates
    assert len(output['children'])==1
    assert 'failed' not in output['children'][0]
