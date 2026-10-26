"""B10 against a Predictive Test Selection baseline; rules fixed in docs/PTS_BASELINE_PROTOCOL.md."""
import argparse
import hashlib
import importlib.util
import json
import platform
import random
from importlib.metadata import version
from pathlib import Path

from codedna.models.experiment import _outcomes
from codedna.models.rankers import order_by_baseline
from codedna.models.uncertainty import match_budget, metrics
from codedna_java.live import LIVE_FEATURES
from codedna.selection import pts
from codedna.selection.live import fit_audited
from codedna.selection.risk import RiskPolicy, _skip_risk, decide
from codedna.test_history.features import Dataset

RISK = .05
CODE = ['scripts/run_pts_check.py', 'docs/PTS_BASELINE_PROTOCOL.md',
        'backend/codedna/selection/pts.py', 'scripts/run_rolling_evidence.py',
        'backend/codedna/selection/live.py', 'backend/codedna/selection/risk.py',
        'plugins/codedna-java/codedna_java/live.py', 'backend/codedna/models/rankers.py',
        'backend/codedna/models/uncertainty.py', 'backend/codedna/calibration/calibrators.py',
        'backend/codedna/test_history/features.py', 'scripts/run_study.py']


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(root, name):
    spec = importlib.util.spec_from_file_location(name, root / f'scripts/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def auc(scores, positives):
    """Probability that a missed commit has a higher estimate than a safe one (ties half)."""
    pos = [s for s, y in zip(scores, positives) if y]
    neg = [s for s, y in zip(scores, positives) if not y]
    if not pos or not neg:
        return None
    wins = sum((p > n) + .5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def evaluate(dataset, rolling):
    """Per block: B10 and B11 outcomes on the block, B11 tuned on the calibration window."""
    groups = dataset.rows_by_commit()
    order = lambda rows: order_by_baseline('recent_failures', rows)
    report, tuning = {'commits': len(dataset.commits), 'blocks': []}, []
    for a, b in rolling.blocks(dataset.commits):
        test = [groups[c] for c in dataset.commits[a:b]]
        block = {'start': a, 'end': b, 'commits': b - a}
        try:
            ranker, calibrator, evidence, info = fit_audited(
                rolling.prefix(dataset, a), LIVE_FEATURES, RISK)
        except Exception as exc:  # recorded, never hidden
            block.update(fit_error=f'{type(exc).__name__}: {exc}', b10=None, b11=None)
            report['blocks'].append(block)
            continue
        block['accepted'] = evidence.accepted
        calibrated = lambda rows: calibrator.transform(ranker.predict_proba(rows))

        def b10(rows):
            d = decide(rows, calibrated(rows), RiskPolicy(budget=None, risk_target=RISK),
                       order=order(rows))
            return d.selected, d
        block['b10'] = _outcomes(test, b10)
        cal = [(groups[c], ranker.predict_proba(groups[c])) for c in info['calibration_commits']]
        try:
            cutoffs = pts.tune(cal)
        except ValueError as exc:
            block.update(tune_error=str(exc), b11=None)
            report['blocks'].append(block)
            continue
        scores = [ranker.predict_proba(rows) for rows in test]
        chosen = {rows[0].commit: set(pts.select(rows, s, cutoffs)) for rows, s in zip(test, scores)}
        block['cutoffs'] = {'score': cutoffs.score, 'count': cutoffs.count}
        block['b11'] = _outcomes(test, lambda rows: (sorted(chosen[rows[0].commit]), None))
        block['b11_estimated_skip_risk'] = [
            round(_skip_risk(dict(zip([r.test_id for r in rows], calibrated(rows))),
                             chosen[rows[0].commit]), 6) for rows in test]
        report['blocks'].append(block)
        tuning.append((len(report['blocks']) - 1, test, cal, scores))
    if not tuning:
        return report

    def matched_b11(target):
        out = []
        for _, test, cal, scores in tuning:
            c = pts.tune(cal, test_recall=target)
            picked = {rows[0].commit: pts.select(rows, s, c) for rows, s in zip(test, scores)}
            out += _outcomes(test, lambda rows: (picked[rows[0].commit], None))
        return out
    b10 = [o for i, *_ in tuning for o in report['blocks'][i]['b10']]
    target, same_time = match_budget(matched_b11, metrics(b10)['time'])
    report.update(b10=b10, b11_paper=[o for i, *_ in tuning for o in report['blocks'][i]['b11']],
                  b11_matched=same_time, b11_matched_test_recall_target=target,
                  residual_time=metrics(b10)['time'] - metrics(same_time)['time'])
    return report


def stated_targets(report):
    paper = report['b11_paper']
    failing = [o for o in paper if o[1]]
    caught = sum(o[1] - o[2] for o in paper)
    risks = [r for i, x in enumerate(report['blocks']) if x.get('b11') is not None
             for r in x['b11_estimated_skip_risk']]
    missed = [o[2] > 0 for o in paper]
    return {
        'b11_test_recall': caught / sum(o[1] for o in paper) if failing else None,
        'b11_change_recall': sum(o[2] < o[1] for o in failing) / len(failing) if failing else None,
        'b11': metrics(paper),
        'b10_observed_miss_rate': sum(o[2] > 0 for o in report['b10']) / len(report['b10']),
        'b11_observed_miss_rate': sum(missed) / len(missed),
        'b11_mean_estimated_skip_risk': sum(risks) / len(risks),
        'b11_risk_auc': auc(risks, missed),
    }


def run(root, inputs, out):
    rolling, study = load(root, 'run_rolling_evidence'), load(root, 'run_study')
    out.mkdir(parents=True, exist_ok=True)
    config = {'protocol': 'docs/PTS_BASELINE_PROTOCOL.md', 'risk_target': RISK,
              'test_recall_target': pts.TEST_RECALL, 'change_recall_target': pts.CHANGE_RECALL,
              'python': platform.python_version(),
              'packages': {n: version(n) for n in ['scikit-learn', 'numpy']},
              'input_sha256': {n: digest(p) for n, p in sorted(inputs.items())},
              'code_sha256': {n: digest(root / n) for n in CODE}}
    config_path = out / 'config.json'
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError('Protocol, code or inputs changed; use a new output folder')
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    summary, reports = {'projects': {}}, {}
    for name, path in sorted(inputs.items()):
        dataset = Dataset.from_csv(path)
        region = [c for a, b in rolling.blocks(dataset.commits) for c in dataset.commits[a:b]]
        count = rolling.failing_commits(dataset, region)
        record = {'set': 'exploratory' if name in rolling.STUDY11 else 'confirmatory',
                  'evaluation_failing_commits': count, 'eligible': count >= rolling.MIN_FAILING}
        if record['eligible']:
            p = out / f'{name}.json'
            report = json.loads(p.read_text()) if p.exists() else evaluate(dataset, rolling)
            p.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
            reports[name] = report
            record.update(fit_failures=sum('fit_error' in x for x in report['blocks']),
                          tune_failures=sum('tune_error' in x for x in report['blocks']))
            if 'b10' in report:
                record.update(b10=metrics(report['b10']), b11_matched=metrics(report['b11_matched']),
                              b11_matched_test_recall_target=report['b11_matched_test_recall_target'],
                              residual_time=report['residual_time'],
                              stated_targets=stated_targets(report))
        summary['projects'][name] = record
        print(f'{name}: {"evaluated" if record["eligible"] else "ineligible"}', flush=True)
    for group in ('confirmatory', 'exploratory'):
        names = [n for n, r in summary['projects'].items()
                 if r['set'] == group and 'b10' in reports.get(n, {})]
        entry = {'projects': names}
        if names:
            data = {n: [(reports[n]['b10'], reports[n]['b11_matched'])] for n in names}
            point = study._mean_over_seeds(data)
            draws = study._hierarchical_draws(data, 2000, random.Random(0))
            entry['b10_minus_b11_matched'] = {m: {'estimate': point[m],
                                                  'ci': study._percentile(draws[m])}
                                              for m in ('time', 'recall', 'safety')}
            positive = sum((summary['projects'][n]['b10']['safety'] or 0) >
                           (summary['projects'][n]['b11_matched']['safety'] or 0) for n in names)
            s = entry['b10_minus_b11_matched']['safety']
            entry['safety_positive_projects'] = positive
            entry['verdict'] = rolling.verdict(s['estimate'], s['ci'], positive, len(names))
            paper = [o for n in names for o in reports[n]['b11_paper']]
            b10 = [o for n in names for o in reports[n]['b10']]
            entry['pooled_commits'] = {'b11_paper': metrics(paper), 'b10': metrics(b10)}
        else:
            entry['verdict'] = 'inconclusive'
        if group == 'exploratory':
            entry['note'] = 'previously inspected projects; exploratory only'
        summary[group] = entry
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    fmt = lambda v: 'n/a' if v is None else f'{v:.4f}' if isinstance(v, float) else str(v)
    lines = ['# B10 against a Predictive Test Selection baseline (B11)', '',
             'Rules fixed in docs/PTS_BASELINE_PROTOCOL.md before results.', '',
             '| Project | B10 time | B10 safety | B11 matched safety | B11 paper time | '
             'B11 paper test recall | B11 paper safety | B10 miss rate | B11 miss rate | '
             'B11 est. skip risk | Risk AUC |', '|' + '---|' * 11]
    for n, r in summary['projects'].items():
        if 'b10' not in r:
            lines.append(f'| {n} | not evaluated |' + ' |' * 9)
            continue
        t = r['stated_targets']
        lines.append('| ' + ' | '.join([n, fmt(r['b10']['time']), fmt(r['b10']['safety']),
            fmt(r['b11_matched']['safety']), fmt(t['b11']['time']), fmt(t['b11_test_recall']),
            fmt(t['b11']['safety']), fmt(t['b10_observed_miss_rate']),
            fmt(t['b11_observed_miss_rate']), fmt(t['b11_mean_estimated_skip_risk']),
            fmt(t['b11_risk_auc'])]) + ' |')
    for group in ('confirmatory', 'exploratory'):
        lines += ['', f'## {group}', '', f"Verdict: **{summary[group]['verdict']}**", '',
                  '```json', json.dumps(summary[group], indent=2), '```']
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datasets', type=Path,
                        help='folder holding <project>/dataset.csv for each project')
    parser.add_argument('--out', type=Path, default=Path('experiments/results/pts-check-2026-10-25'))
    args = parser.parse_args()
    found = {p.parent.name: p for p in sorted(args.datasets.glob('*/dataset.csv'))}
    if not found:
        parser.error('no <project>/dataset.csv files found')
    run(Path.cwd(), found, args.out)
    print('Completed ' + str(args.out / 'summary.md'), flush=True)
