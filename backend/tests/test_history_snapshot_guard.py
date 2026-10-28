"""Live provenance and fresh eligibility when fitted models are reusable."""
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace

from codedna.models.fit_cache import clear_fitted_models
from codedna.performance import capture_timings
from codedna.selection.live import recommend
from codedna.test_history.features import Dataset, Row
from codedna_java import live


def test_live_provenance_hashes_the_parsed_snapshot_even_if_file_changes(repo,tmp_path,monkeypatch):
    repo.write('pom.xml','<project/>')
    repo.write('src/main/java/a/Core.java','package a; class Core { int n = 1; }')
    for name in ['CoreTest','OtherTest']:
        repo.write(f'src/test/java/a/{name}.java',f'package a; import org.junit.jupiter.api.Test; class {name} {{ @Test void check() {{}} }}')
    base=repo.commit('fixture');repo.write('src/main/java/a/Core.java','package a; class Core { int n = 2; }');head=repo.commit('change')
    features={name:0. for name in live.LIVE_FEATURES};features.update(mean_duration=1.)
    dataset=Dataset([Row(base,0,name,0,1.,dict(features)) for name in ['a.CoreTest','a.OtherTest']],list(live.LIVE_FEATURES),[base])
    history=tmp_path/'history.csv';dataset.to_csv(history);snapshot=history.read_bytes()
    reader=Dataset.from_csv_bytes.__func__
    def replaced(cls,raw,*,source):
        parsed=reader(cls,raw,source=source)
        Path(source).write_bytes(b'changed after the read')
        return parsed
    monkeypatch.setattr(Dataset,'from_csv_bytes',classmethod(replaced))
    # Deliberately mocked acceptance solely to reach provenance construction;
    # this tiny fixture is not empirical validation of a stopping rule.
    model=SimpleNamespace(predict_proba=lambda rows:[.9 if row.test_id=='a.CoreTest' else .001 for row in rows])
    cal=SimpleNamespace(transform=lambda values:values)
    evidence=SimpleNamespace(accepted=True,reasons=[],to_dict=lambda:{'accepted':True})
    monkeypatch.setattr(live,'fit_audited',lambda *args:(model,cal,evidence,{'audit_commits':[base]}))
    result=recommend(repo.path,base,head,history_csv=history)
    assert history.read_bytes()==b'changed after the read'
    assert result['risk']['provenance']['history_sha256']==sha256(snapshot).hexdigest()


def test_cached_models_never_reuse_selected_sets_or_override_eligibility(repo,tmp_path):
    from test_live_risk import validated_change
    base,head,history=validated_change(repo,tmp_path);clear_fitted_models()
    try:
        first=recommend(repo.path,base,head,history_csv=history)
        assert first['risk']['status']=='validated_history' and first['skipped']==['a.OtherTest']
        with capture_timings() as timing:
            pinned=recommend(repo.path,base,head,history_csv=history,must_run=['a.OtherTest'])
        assert timing.counters['fit_cache.hit']==1 and timing.stages['risk.audit']['calls']==1
        assert pinned['skipped']==[] and len(pinned['selected'])==2
        # New WORKTREE has the unobserved HEAD as parent, not the audited base.
        repo.write('src/main/java/a/Core.java','package a; class Core { int n = 3; }')
        with capture_timings() as invalid:
            stale=recommend(repo.path,base,'WORKTREE',history_csv=history)
        assert stale['risk']['status']=='unvalidated' and stale['skipped']==[]
        assert 'fit_cache.hit' not in invalid.counters and 'risk.audit' not in invalid.stages
    finally:clear_fitted_models()


def test_history_read_failure_returns_full_suite_instead_of_an_error(repo,tmp_path,monkeypatch):
    repo.write('pom.xml','<project/>');repo.write('src/main/java/A.java','class A {}')
    repo.write('src/test/java/ATest.java','import org.junit.jupiter.api.Test; class ATest { @Test void check() {} }')
    base=repo.commit('fixture');repo.write('src/main/java/A.java','class A { int n; }');head=repo.commit('change')
    history=tmp_path/'history.csv';history.write_text('fixture',encoding='utf-8')
    reader=Path.read_bytes
    def fail(path):
        if path==history:raise PermissionError('fixture history unavailable')
        return reader(path)
    monkeypatch.setattr(Path,'read_bytes',fail)
    result=recommend(repo.path,base,head,history_csv=history)
    assert result['risk']['status']=='unvalidated' and result['skipped']==[]
    assert len(result['selected'])==1 and any('history unavailable' in text for text in result['risk']['reasons'])
