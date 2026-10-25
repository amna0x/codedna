"""Shared target audit and dispatch through the installed language plugin."""
from codedna.calibration.calibrators import Calibrator
from codedna.models.experiment import _outcomes
from codedna.models.rankers import MLRanker, order_by_baseline
from codedna.selection.risk import RiskPolicy, decide
from codedna.selection.validation import validate_outcomes


def fit_audited(dataset, feature_names, risk_target=.05):
    """50/25/25 fit/calibrate/audit; do not refit after inspecting the audit."""
    n = len(dataset.commits)
    a, b = int(n*.5), int(n*.75)
    groups = dataset.rows_by_commit()
    train = [r for c in dataset.commits[:a] for r in groups[c]]
    cal = [r for c in dataset.commits[a:b] for r in groups[c]]
    audit = [groups[c] for c in dataset.commits[b:]]
    ranker = MLRanker('gradient_boosting', feature_names, seed=0)
    ranker.fit(train)
    calibrator = Calibrator('isotonic').fit(ranker.predict_proba(cal), [r.label for r in cal])
    def choose(rows):
        d = decide(rows, calibrator.transform(ranker.predict_proba(rows)),
                   RiskPolicy(budget=None, risk_target=risk_target),
                   order=order_by_baseline('recent_failures', rows))
        return d.selected, d
    evidence = validate_outcomes(_outcomes(audit, choose), risk_target)
    return ranker, calibrator, evidence, {
        'training_commits': dataset.commits[:a], 'calibration_commits': dataset.commits[a:b],
        'audit_commits': dataset.commits[b:], 'features': feature_names,
        'model': 'gradient_boosting', 'calibration': 'isotonic', 'seed': 0}



def recommend(repo_path,base,head,*,history_csv=None,risk_target=.05,language='java',must_run=None):
    from codedna.plugins.languages import require
    from codedna.selection import SelectionError
    plugin=require(language)
    select=getattr(plugin,'risk_select',None)
    if select is None:
        raise SelectionError(f'Language plugin {language!r} does not provide risk selection')
    return select(repo_path,base,head,history_csv=history_csv,risk_target=risk_target,
                  must_run=must_run)
