"""Repository-bound live risk recommendation; all-suite fallback without evidence.

The operational predictor uses 15 change/test/history features available for new
commits, not graph/co-failure features needing historical structural replay.
Its own chronological audit is separate from the retrospective 19-feature study.
No serialized Python models are loaded or repository code executed here.
"""
from collections import defaultdict
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from codedna.git_analysis import extract_changes
from codedna.git_analysis.git import resolve_repository, run_git
from codedna.selection import select_tests
from codedna.models.rankers import order_by_baseline
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import (
    CHANGE_FEATURES, TEST_FEATURES, HISTORY_FEATURES, Dataset, Row, NEVER, _is_file_of, _is_test_path)

LIVE_FEATURES = CHANGE_FEATURES + TEST_FEATURES + [f for f in HISTORY_FEATURES if f != 'co_failures']


def fit_audited(dataset,risk_target=.05):
    from codedna.selection.live import fit_audited as fit_shared
    return fit_shared(dataset,LIVE_FEATURES,risk_target)


def prediction_rows(dataset, changes, test_ids):
    """Labels/durations in returned rows are placeholders, never observed outcomes."""
    observed = defaultdict(list)
    groups = dataset.rows_by_commit()
    for i, commit in enumerate(dataset.commits):
        for r in groups[commit]:
            observed[r.test_id].append((i, r))
    files = changes.changed_files
    common = dict(zip(CHANGE_FEATURES, [len(files), sum(f.is_java for f in files),
        sum(not f.is_java for f in files), sum(_is_test_path(f.path) for f in files),
        sum(b-a+1 for f in files for a,b in f.changed_lines),
        sum(b-a+1 for f in files for a,b in f.removed_lines)]))
    rows = []
    for test in test_ids:
        history = observed[test]
        failures = [(i,r) for i,r in history if r.label]
        features = {**common, 'test_file_changed':float(any(_is_file_of(test,f.path) for f in files)),
            'past_runs':len(history), 'past_failures':len(failures),
            'failure_rate':len(failures)/len(history) if history else 0.,
            'recent_failures':sum(r.label for _,r in history[-5:]),
            'failed_last_run':history[-1][1].label if history else 0.,
            'commits_since_failure':len(dataset.commits)-failures[-1][0] if failures else NEVER,
            'mean_duration':sum(r.duration for _,r in history)/len(history) if history else 0.,
            'last_duration':history[-1][1].duration if history else 0.}
        rows.append(Row(changes.head_commit,len(dataset.commits),test,0,0.,features))
    return rows


METHODS = ('b10', 'crc')


def recommend(repo_path, base, head, *, history_csv=None, risk_target=.05, must_run=None,
              method='b10'):
    """``method``: ``b10`` = stop at estimated skip risk ``risk_target`` behind the D-041 gate;
    ``crc`` = B12f, the stop is chosen by conformal risk control so that at most
    ``risk_target`` of failing audit commits miss a failure (D-063, D-068)."""
    import math
    if not math.isfinite(risk_target) or not 0 < risk_target < 1:
        raise ValueError('Risk target must lie strictly between zero and one')
    if method not in METHODS:
        raise ValueError(f'Unknown risk method {method!r}; choose from {METHODS}')
    started = perf_counter()
    repo = resolve_repository(repo_path)
    # Discover the full candidate universe, including changed classes and warnings.
    result = select_tests(repo, base, head, 'all', must_run=must_run).to_dict()
    result['strategy'] = 'risk'
    # Must-run tests (D-050) are never skipped; their reasons survive every path.
    pinned = set(result['policy']['pinned'])
    pin_reasons = {item['test']:[r for r in item['reasons'] if r != 'retest-all']
                   for item in result['selected'] if item['test'] in pinned}
    risk = {'status':'unvalidated', 'method':method, 'target':risk_target, 'estimated_skip_risk':None,
            'proposed_skip_risk':None, 'validation':None, 'reasons':[],
            'note':'Historical validation is not a guarantee; full-suite audits must refresh evidence.'}
    result['risk'] = risk
    def fallback(reason):
        risk['reasons'].append(reason)
        for item in result['selected']:
            item['reasons'] = ['risk unvalidated: run the full suite']+pin_reasons.get(item['test'],[])
        risk['analysis_seconds'] = round(perf_counter()-started,4)
        return result
    path = Path(history_csv) if history_csv else repo/'.codedna/history.csv'
    if not path.is_file():
        return fallback('No target-project test history is available.')
    try:
        dataset = Dataset.from_csv(path)
        if not dataset.commits or len(set(dataset.commits)) != len(dataset.commits):
            return fallback('History is empty or has duplicate commits.')
        if len({(r.commit,r.test_id) for r in dataset.rows}) != len(dataset.rows):
            return fallback('History contains duplicate commit/test rows.')
        import math
        if any(r.label not in (0,1) or not math.isfinite(r.duration) or r.duration < 0 or
               any(not math.isfinite(v) for v in r.features.values()) for r in dataset.rows):
            return fallback('History contains invalid labels, durations or feature values.')
        ancestry = run_git(repo,'rev-list','--first-parent','--reverse',result['base_commit']).splitlines()
        positions = {c:i for i,c in enumerate(ancestry)}
        if any(c not in positions for c in dataset.commits):
            return fallback('History includes another repository, branch or future commits.')
        if [positions[c] for c in dataset.commits] != sorted(positions[c] for c in dataset.commits):
            return fallback('History is not chronological on the target branch.')
        if dataset.commits[-1] != result['base_commit'] or result['head_commit'] in dataset.commits:
            return fallback('History is stale at BASE or includes the requested target outcome.')
        # Only the next first-parent change is within the operational validation domain.
        parent = run_git(repo,'rev-parse',result['head_commit']+'^1').strip()
        if parent != result['base_commit']:
            return fallback('Risk validation applies only to the next first-parent change.')
        changes = extract_changes(repo,base,head)
        if any(not f.is_java for f in changes.changed_files):
            return fallback('This change includes unsupported non-Java files.')
        ids = [item['test'] for item in result['selected']]
        latest = {r.test_id for r in dataset.rows_by_commit()[dataset.commits[-1]]}
        if not set(ids).issubset(latest):
            return fallback('Current tests lack recorded outcomes at BASE; a full-suite audit is needed.')
        audit_shas = dataset.commits[int(len(dataset.commits)*.75):]
        groups = dataset.rows_by_commit()
        if any(not set(ids).issubset({r.test_id for r in groups[c]}) for c in audit_shas):
            return fallback('Prior audit omits current test classes; complete full-suite outcomes are required.')
        model, calibrator, evidence, provenance = fit_audited(dataset,risk_target)
        risk['validation'] = evidence.to_dict()
        risk['provenance'] = {**provenance,'history_sha256':sha256(path.read_bytes()).hexdigest()}
        rows = prediction_rows(dataset,changes,ids)
        probabilities = calibrator.transform(model.predict_proba(rows))
        stop = risk_target
        if method == 'crc':
            from codedna.selection import conformal
            audit = [groups[c] for c in provenance['audit_commits']]
            stop, crc = conformal.failing_commit_threshold(audit,model,calibrator,risk_target)
            risk['conformal'] = {**crc,'note':'Bound on missed failures among failing commits; '
                                 'it assumes past and future failing commits are exchangeable.'}
            if stop is conformal.FULL:
                return fallback('Conformal stop needs the full suite: '+crc['reason']+'.')
        decision = decide(rows,probabilities,RiskPolicy(budget=None,risk_target=stop),
                          order=order_by_baseline('recent_failures',rows),always=pinned)
        risk['proposed_skip_risk'] = decision.estimated_skip_risk
        if method == 'b10' and not evidence.accepted:
            return fallback('Prior target audit failed: '+ '; '.join(evidence.reasons))
        risk.update(status='validated_history',estimated_skip_risk=decision.estimated_skip_risk,
                    analysis_seconds=round(perf_counter()-started,4))
        score = {r.test_id:p for r,p in zip(rows,probabilities)}
        rule = ('recent-failure order, conformal stop at estimated risk '+f'{stop:g}'
                if method == 'crc' else 'recent-failure order with calibrated risk stopping')
        result['selected'] = [{'test':t,'reasons':pin_reasons.get(t) or [rule],
                               'estimated_failure_probability':score[t]} for t in decision.selected]
        by_id = {r.test_id:r for r in rows}
        for item in result['selected']:
            features = by_id[item['test']].features
            item['reasons'] += [f"{features['recent_failures']:.0f} failures in the last five recorded runs",
                                f"estimated failure probability {score[item['test']]:.2%}"]
            if features['test_file_changed']:
                item['reasons'].append('changed test class always selected')
        result['skipped'] = decision.skipped
        result['selected_count'] = len(decision.selected)
        result['selection_ratio'] = len(decision.selected)/len(rows) if rows else 0.
        costs = {r.test_id:r.features['mean_duration'] for r in rows}
        total = sum(costs.values()); chosen=sum(costs[t] for t in decision.selected)
        result['estimated_time'] = {'selected_seconds':chosen,'all_seconds':total,
                                   'saved_ratio':1-chosen/total if total else 0.}
        return result
    except (ValueError,KeyError,StopIteration,RuntimeError,ImportError) as exc:
        return fallback('Risk evidence cannot be used: '+str(exc))
