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



def recommend(repo_path,base,head,*,history_csv=None,risk_target=.05,language='java',must_run=None,
              method='b10'):
    """Dispatch supported risk methods; unsupported/mixed languages run all tests.

    ``language=None`` discovers the test language instead of assuming Java.
    This is the brake's default; explicit callers retain their language choice.
    """
    import math
    from codedna.git_analysis.git import resolve_commit, resolve_repository
    from codedna.plugins import load_plugins
    from codedna.plugins.languages import commit_tests, require

    if not math.isfinite(risk_target) or not 0 < risk_target < 1:
        raise ValueError('Risk target must lie strictly between zero and one')
    if method not in ('b10', 'crc'):
        raise ValueError(f'Unknown risk method {method!r}; choose b10 or crc')
    registry=load_plugins()
    if language is None:
        repo_path=resolve_repository(repo_path)
        base=resolve_commit(repo_path,base)
        head=resolve_commit(repo_path,head)
        discovery=commit_tests(repo_path,head,registry=registry)
        active=[name for name,report in discovery.reports.items()
                if any(t.runs_by_default for t in report.tests)]
        if len(active)!=1:
            reason=('Multiple test languages have no joint validated risk selector: '
                    +', '.join(sorted(active))+'.' if active else
                    'No default-running tests were discovered for a risk selector.')
            return _unvalidated_all(repo_path,base,head,risk_target,must_run,method,reason)
        language=active[0]
    plugin=require(language,registry)
    select=getattr(plugin,'risk_select',None)
    if select is None:
        return _unvalidated_all(repo_path,base,head,risk_target,must_run,method,
            f'Language plugin {language!r} does not provide validated risk selection; '
            'run the full suite.')
    options={} if method=='b10' else {'method':method}
    return select(repo_path,base,head,history_csv=history_csv,risk_target=risk_target,
                  must_run=must_run,**options)


def _unvalidated_all(repo,base,head,target,must_run,method,reason):
    """Use the existing all-language universe and policy; invent no probability."""
    from time import perf_counter
    from codedna.selection import select_tests

    started=perf_counter()
    result=select_tests(repo,base,head,'all',must_run=must_run).to_dict()
    result['strategy']='risk'
    for item in result['selected']:
        item['reasons']=['risk unvalidated: run the full suite']+[
            r for r in item['reasons'] if r!='retest-all']
    result['risk']={'status':'unvalidated','method':method,'target':target,
        'estimated_skip_risk':None,'proposed_skip_risk':None,'validation':None,
        'reasons':[reason],
        'note':'No validated risk estimate is available; all discovered tests are required.',
        'analysis_seconds':round(perf_counter()-started,4)}
    return result
