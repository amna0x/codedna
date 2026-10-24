"""Rolling-origin evidence study; rules fixed in docs/EVIDENCE_STUDY_PROTOCOL.md."""
import argparse
import hashlib
import importlib.util
import json
import platform
import random
from importlib.metadata import version
from math import sqrt
from pathlib import Path
from statistics import mean
from time import perf_counter

from codedna.models.experiment import _outcomes
from codedna.models.rankers import order_by_baseline
from codedna.models.uncertainty import match_budget, metrics
from codedna.plugins.java_live import LIVE_FEATURES
from codedna.selection.live import fit_audited
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import Dataset

STUDY11 = {'achilles', 'dynjs', 'graylog2-server', 'hikaricp', 'jade4j', 'jcabi-github',
           'jooq', 'jsprit', 'littleproxy', 'optiq', 'wicket-bootstrap'}
BLOCKS, MIN_FAILING, RISK, MARGIN = 5, 20, .05, .05
CODE = ['scripts/run_rolling_evidence.py', 'docs/EVIDENCE_STUDY_PROTOCOL.md',
        'backend/codedna/selection/live.py', 'backend/codedna/selection/validation.py',
        'backend/codedna/selection/risk.py', 'backend/codedna/plugins/java_live.py',
        'backend/codedna/models/rankers.py', 'backend/codedna/models/experiment.py',
        'backend/codedna/models/uncertainty.py', 'backend/codedna/calibration/calibrators.py',
        'backend/codedna/test_history/features.py', 'scripts/run_study.py']


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def blocks(commits, k=BLOCKS):
    """Last 50% of commits in k consecutive near-equal blocks: (start, end) indices."""
    start = len(commits) // 2
    size = len(commits) - start
    cuts = [start + round(i * size / k) for i in range(k + 1)]
    return [(a, b) for a, b in zip(cuts, cuts[1:]) if b > a]


def failing_commits(dataset, commits):
    groups = dataset.rows_by_commit()
    return sum(any(r.label for r in groups[c]) for c in commits)


def prefix(dataset, end):
    keep = set(dataset.commits[:end])
    return Dataset([r for r in dataset.rows if r.commit in keep], dataset.feature_names,
                   dataset.commits[:end])


def wilson_upper(misses, n, z=1.6448536269514722):
    if not n:
        return None
    p = misses / n
    return (p + z*z/(2*n) + z*sqrt(p*(1-p)/n + z*z/(4*n*n))) / (1 + z*z/n)


def evaluate(dataset):
    """Per-block gate verdict and per-commit B10 outcomes; block labels never fitted."""
    groups = dataset.rows_by_commit()
    order = lambda rows: order_by_baseline('recent_failures', rows)
    report = {'commits': len(dataset.commits), 'blocks': []}
    for a, b in blocks(dataset.commits):
        test = [groups[c] for c in dataset.commits[a:b]]
        block = {'start': a, 'end': b, 'commits': b - a,
                 'failing_commits': failing_commits(dataset, dataset.commits[a:b])}
        started = perf_counter()
        try:
            ranker, calibrator, evidence, _ = fit_audited(prefix(dataset, a), LIVE_FEATURES, RISK)
        except Exception as exc:  # recorded, never hidden: product runs the full suite
            block.update(fit_error=f'{type(exc).__name__}: {exc}', accepted=False, b10=None)
            report['blocks'].append(block)
            continue
        block['fit_seconds'] = perf_counter() - started
        block['evidence'] = evidence.to_dict()
        block['accepted'] = evidence.accepted

        def choose(rows):
            d = decide(rows, calibrator.transform(ranker.predict_proba(rows)),
                       RiskPolicy(budget=None, risk_target=RISK), order=order(rows))
            return d.selected, d
        block['b10'] = _outcomes(test, choose)
        report['blocks'].append(block)
    compared = [i for i, x in enumerate(report['blocks']) if x['b10'] is not None]
    test = [groups[c] for i in compared
            for c in dataset.commits[report['blocks'][i]['start']:report['blocks'][i]['end']]]
    b10 = [o for i in compared for o in report['blocks'][i]['b10']]
    if b10:
        budget, matched = match_budget(
            lambda x: _outcomes(test, lambda rows: (decide(
                rows, [0.] * len(rows), RiskPolicy(budget=x), order=order(rows)).selected, None)),
            metrics(b10)['time'])
        report['b3_budget'], report['b3'], report['b10'] = budget, matched, b10
        report['residual_time'] = metrics(b10)['time'] - metrics(matched)['time']
    return report


def gate_rows(reports, accepted):
    blocks_ = [x for r in reports for x in r['blocks'] if x['b10'] is not None
               and x['accepted'] == accepted]
    outcomes = [o for x in blocks_ for o in x['b10']]
    misses = sum(o[2] > 0 for o in outcomes)
    return {'blocks': len(blocks_), 'commits': len(outcomes),
            'observed_miss_rate': misses / len(outcomes) if outcomes else None,
            'wilson_upper': wilson_upper(misses, len(outcomes))}


def product(report):
    """Gated product per commit: B10 on accepted blocks, full suite otherwise."""
    out = []
    for x in report['blocks']:
        out += x['b10'] if x['accepted'] else [(1., 0, 0)] * x['commits']
    m = metrics(out)
    return {'mean_time': m['time'],
            'observed_miss_rate': sum(o[2] > 0 for o in out) / len(out) if out else None}


def verdict(estimate, ci, positive, eligible):
    if eligible < 3 or ci is None or estimate is None:
        return 'inconclusive'
    if ci[0] > 0 and positive > eligible / 2:
        return 'helps'
    if ci[1] < 0:
        return 'harms'
    if -MARGIN <= ci[0] and ci[1] <= MARGIN:
        return 'no meaningful difference'
    return 'inconclusive'


def gate_verdict(accepted, rejected):
    if accepted['blocks'] < 3:
        return 'gate unexercised'
    if accepted['observed_miss_rate'] > RISK:
        return 'gate not supported'
    if rejected['observed_miss_rate'] is not None and \
            accepted['observed_miss_rate'] > rejected['observed_miss_rate']:
        return 'inconclusive'
    return 'gate supported'


def run(root, inputs, out):
    """``inputs`` maps project name to dataset CSV path."""
    out.mkdir(parents=True, exist_ok=True)
    config = {'protocol': 'docs/EVIDENCE_STUDY_PROTOCOL.md', 'blocks': BLOCKS,
              'min_failing_commits': MIN_FAILING, 'risk_target': RISK,
              'python': platform.python_version(),
              'packages': {n: version(n) for n in ['scikit-learn', 'numpy']},
              'input_sha256': {n: digest(p) for n, p in sorted(inputs.items())},
              'code_sha256': {n: digest(root / n) for n in CODE}}
    config_path = out / 'config.json'
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError('Protocol, code or inputs changed; use a new output folder')
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    spec = importlib.util.spec_from_file_location('study', root / 'scripts/run_study.py')
    study = importlib.util.module_from_spec(spec); spec.loader.exec_module(study)
    summary = {'sets': {}, 'projects': {}}
    reports = {}
    for name, path in sorted(inputs.items()):
        dataset = Dataset.from_csv(path)
        region = [c for a, b in blocks(dataset.commits) for c in dataset.commits[a:b]]
        count = failing_commits(dataset, region)
        record = {'set': 'exploratory' if name in STUDY11 else 'confirmatory',
                  'evaluation_failing_commits': count, 'eligible': count >= MIN_FAILING}
        if record['eligible']:
            p = out / f'{name}.json'
            if p.exists():
                report = json.loads(p.read_text())
            else:
                report = evaluate(dataset)
                p.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
            reports[name] = report
            record.update(fit_failures=sum('fit_error' in x for x in report['blocks']),
                          accepted_blocks=sum(x['accepted'] for x in report['blocks']),
                          product=product(report))
            if 'b10' in report:
                record.update(b3_budget=report['b3_budget'], residual_time=report['residual_time'],
                              b10=metrics(report['b10']), b3=metrics(report['b3']))
        summary['projects'][name] = record
        print(f'{name}: {"evaluated" if record["eligible"] else "ineligible"}', flush=True)
    for group in ('confirmatory', 'exploratory'):
        names = [n for n, r in summary['projects'].items() if r['set'] == group and r['eligible']]
        data = {n: [(reports[n]['b10'], reports[n]['b3'])] for n in names if 'b10' in reports[n]}
        entry = {'eligible_projects': names}
        if data:
            point = study._mean_over_seeds(data)
            draws = study._hierarchical_draws(data, 2000, random.Random(0))
            entry['b10_minus_b3'] = {m: {'estimate': point[m], 'ci': study._percentile(draws[m])}
                                     for m in ('time', 'recall', 'safety')}
            positive = sum((summary['projects'][n]['b10']['safety'] or 0) >
                           (summary['projects'][n]['b3']['safety'] or 0) for n in data)
            entry['safety_positive_projects'] = positive
            s = entry['b10_minus_b3']['safety']
            entry['verdict'] = verdict(s['estimate'], s['ci'], positive, len(names))
        else:
            entry['verdict'] = 'inconclusive'
        chosen = [reports[n] for n in names]
        entry['gate'] = {'accepted': gate_rows(chosen, True), 'rejected': gate_rows(chosen, False)}
        entry['gate']['verdict'] = gate_verdict(entry['gate']['accepted'], entry['gate']['rejected'])
        if group == 'exploratory':
            entry['note'] = 'previously inspected projects; replication only, not verdict evidence'
        summary['sets'][group] = entry
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    fmt = lambda v: 'n/a' if v is None else f'{v:.4f}' if isinstance(v, float) else str(v)
    lines = ['# Rolling-origin evidence study', '',
             'Rules fixed in docs/EVIDENCE_STUDY_PROTOCOL.md before results.', '',
             '| Project | Set | Failing commits | Accepted blocks | Fit failures | B10 time | '
             'B10 safety | B3 safety | Product time | Product miss |', '|' + '---|' * 10]
    for n, r in summary['projects'].items():
        if not r['eligible']:
            lines.append(f"| {n} | {r['set']} | {r['evaluation_failing_commits']} | ineligible |"
                         + ' |' * 6)
            continue
        b10, b3 = r.get('b10', {}), r.get('b3', {})
        lines.append('| ' + ' | '.join([n, r['set'], str(r['evaluation_failing_commits']),
            str(r['accepted_blocks']), str(r['fit_failures']), fmt(b10.get('time')),
            fmt(b10.get('safety')), fmt(b3.get('safety')), fmt(r['product']['mean_time']),
            fmt(r['product']['observed_miss_rate'])]) + ' |')
    for group, entry in summary['sets'].items():
        lines += ['', f'## {group}', '', f"Verdict: **{entry['verdict']}**; gate: "
                  f"**{entry['gate']['verdict']}**", '', '```json',
                  json.dumps({k: v for k, v in entry.items() if k != 'verdict'}, indent=2), '```']
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    manifest = {'config': config, 'outputs': {p.relative_to(out).as_posix(): digest(p)
                for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'manifest.json'}}
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datasets', type=Path,
                        help='folder holding <project>/dataset.csv for each project')
    parser.add_argument('--out', type=Path,
                        default=Path('experiments/results/rolling-evidence-2026-10-24'))
    args = parser.parse_args()
    found = {p.parent.name: p for p in sorted(args.datasets.glob('*/dataset.csv'))}
    if not found:
        parser.error('no <project>/dataset.csv files found')
    run(Path.cwd(), found, args.out)
    print('Completed ' + str(args.out / 'summary.md'), flush=True)
