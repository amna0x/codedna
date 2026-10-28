"""Reuse fitting, never audit acceptance; compare batched inference to reference."""
from dataclasses import replace

from codedna.models.fit_cache import clear_fitted_models, fitted_model_scope
from codedna.performance import capture_timings
from codedna.selection import live
from codedna.selection.risk import RiskPolicy, decide
from codedna.models.rankers import order_by_baseline
from codedna.models.experiment import _outcomes
from codedna.selection.validation import validate_outcomes
from codedna.test_history.features import Dataset, Row


def data(repo):
    repo.write('A.java','class A {}'); repo.commit('fixture')
    rows=[]; commits=[str(i) for i in range(80)]
    for i,commit in enumerate(commits):
        for j in range(3):
            rows.append(Row(commit,i,str(j),int(j==0),float(j+1),
                            {'recent_failures':float(j==0),'mean_duration':float(j+1)}))
    return Dataset(rows,['recent_failures','mean_duration'],commits)


def test_fit_reused_but_audit_recomputed_and_matches_unbatched_reference(repo,monkeypatch):
    dataset=data(repo); clear_fitted_models(); fits=[]; audits=[]; predictions=[]
    original_fit=live.MLRanker.fit; original_audit=live.validate_outcomes
    original_predict=live.MLRanker.predict_proba
    def fit(self,rows): fits.append(1); return original_fit(self,rows)
    def audit(*args,**kwargs): audits.append(1); return original_audit(*args,**kwargs)
    def predict(self,rows): predictions.append(len(rows)); return original_predict(self,rows)
    monkeypatch.setattr(live.MLRanker,'fit',fit)
    monkeypatch.setattr(live.MLRanker,'predict_proba',predict)
    monkeypatch.setattr(live,'validate_outcomes',audit)
    with capture_timings() as timing, fitted_model_scope((str(repo.path),'base','history')):
        first=live.fit_audited(dataset,dataset.feature_names)
        second=live.fit_audited(dataset,dataset.feature_names)
    assert len(fits)==1 and len(audits)==2
    assert timing.counters['fit_cache.hit']==1
    # One calibration prediction on miss, one batched audit per call.
    assert predictions==[60,60,60]
    model,calibrator,evidence,provenance=second
    groups=dataset.rows_by_commit(); audit_rows=[groups[c] for c in provenance['audit_commits']]
    def reference(rows):
        d=decide(rows,calibrator.transform(model.predict_proba(rows)),
                 RiskPolicy(budget=None,risk_target=.05),order=order_by_baseline('recent_failures',rows))
        return d.selected,d
    expected=validate_outcomes(_outcomes(audit_rows,reference),.05)
    assert evidence.to_dict()==expected.to_dict()==first[2].to_dict()
    assert first[3]==provenance
    # Changing audit labels changes the fresh evidence, not fitted predictions.
    altered=Dataset([replace(r,label=1-r.label) if r.seq>=60 else r for r in dataset.rows],
                    dataset.feature_names,dataset.commits)
    with fitted_model_scope((str(repo.path),'base','history')):
        third=live.fit_audited(altered,altered.feature_names)
    assert len(fits)==2 and len(audits)==3  # full data fingerprint also invalidates reuse
    assert third[1].transform(third[0].predict_proba(dataset.rows[-3:]))==calibrator.transform(model.predict_proba(dataset.rows[-3:]))
    assert third[2].to_dict()!=evidence.to_dict()
    first[0].feature_names.append('caller-only')
    first[3]['features'].append('caller-only')
    assert 'caller-only' not in dataset.feature_names and 'caller-only' not in second[0].feature_names
    clear_fitted_models()


def test_csv_snapshot_has_same_parser_and_preserves_exact_loaded_data(repo,tmp_path):
    d=data(repo); path=tmp_path/'history.csv';d.to_csv(path)
    raw=path.read_bytes(); snapshot=Dataset.from_csv_bytes(raw,source=path)
    assert snapshot==Dataset.from_csv(path)
    path.write_text('replaced after snapshot',encoding='utf-8')
    assert snapshot==Dataset.from_csv_bytes(raw,source=path)
