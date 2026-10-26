"""Conformal-risk-control stopping (B12) against B10; rules fixed in docs/CRC_STOP_PROTOCOL.md."""
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
from codedna.models.uncertainty import metrics
from codedna.plugins.java_live import LIVE_FEATURES
from codedna.selection import conformal
from codedna.selection.live import fit_audited
from codedna.selection.risk import RiskPolicy, decide
from codedna.test_history.features import Dataset

ALPHA = .05
CODE = ['scripts/run_crc_check.py', 'docs/CRC_STOP_PROTOCOL.md',
        'backend/codedna/selection/conformal.py', 'scripts/run_rolling_evidence.py',
        'backend/codedna/selection/live.py', 'backend/codedna/selection/risk.py',
        'backend/codedna/plugins/java_live.py', 'backend/codedna/models/rankers.py',
        'backend/codedna/models/uncertainty.py', 'backend/codedna/calibration/calibrators.py',
        'backend/codedna/test_history/features.py', 'scripts/run_study.py']


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(root, name):
    spec = importlib.util.spec_from_file_location(name, root / f'scripts/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stopper(ranker, calibrator, value):
    """B10-style stop at estimated skip risk ``value``; ``FULL`` runs every test."""
    def choose(rows):
        if value is conformal.FULL:
            return [r.test_id for r in rows], None
        d = decide(rows, calibrator.transform(ranker.predict_proba(rows)),
                   RiskPolicy(budget=None, risk_target=value),
                   order=order_by_baseline('recent_failures', rows))
        return d.selected, d
    return choose


def miss_rate(outcomes):
    return sum(o[2] > 0 for o in outcomes) / len(outcomes) if outcomes else None


def evaluate(dataset, rolling):
    """Per block: B12 tuned on the audit window, B10 and the gated product on the block."""
    groups = dataset.rows_by_commit()
    report = {'commits': len(dataset.commits), 'blocks': []}
    for a, b in rolling.blocks(dataset.commits):
        test = [groups[c] for c in dataset.commits[a:b]]
        block = {'start': a, 'end': b, 'commits': b - a}
        try:
            ranker, calibrator, evidence, info = fit_audited(
                rolling.prefix(dataset, a), LIVE_FEATURES, ALPHA)
        except Exception as exc:  # recorded, never hidden: every policy runs the full suite
            full = [(1., sum(r.label for r in rows), 0) for rows in test]
            block.update(fit_error=f'{type(exc).__name__}: {exc}', accepted=False,
                         b10=None, b12=full, product=full, threshold='full')
            report['blocks'].append(block)
            continue
        audit = [groups[c] for c in info['audit_commits']]
        losses = {v: [float(o[2] > 0) for o in _outcomes(audit, stopper(ranker, calibrator, v))]
                  for v in conformal.GRID}
        chosen = conformal.threshold(losses, ALPHA)
        b10 = _outcomes(test, stopper(ranker, calibrator, ALPHA))
        block.update(accepted=evidence.accepted, audit_commits=len(audit),
                     audit_miss_rate={'full' if v is None else str(v): sum(x) / len(x)
                                      for v, x in losses.items() if x},
                     threshold='full' if chosen is None else chosen, b10=b10,
                     b12=_outcomes(test, stopper(ranker, calibrator, chosen)),
                     product=b10 if evidence.accepted else [(1., sum(r.label for r in rows), 0)
                                                            for rows in test])
        report['blocks'].append(block)
    for key in ('b10', 'b12', 'product'):
        report[key] = [o for x in report['blocks'] if x[key] is not None for o in x[key]]
    return report


def run(root, inputs, out):
    rolling, study = load(root, 'run_rolling_evidence'), load(root, 'run_study')
    out.mkdir(parents=True, exist_ok=True)
    config = {'protocol': 'docs/CRC_STOP_PROTOCOL.md', 'alpha': ALPHA,
              'grid': ['full' if v is None else v for v in conformal.GRID],
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
            record.update(
                fit_failures=sum('fit_error' in x for x in report['blocks']),
                thresholds=[x['threshold'] for x in report['blocks']],
                **{k: {**metrics(report[k]), 'miss_rate': miss_rate(report[k])}
                   for k in ('b10', 'b12', 'product')})
        summary['projects'][name] = record
        print(f'{name}: {"evaluated" if record["eligible"] else "ineligible"}', flush=True)
    for group in ('confirmatory', 'exploratory'):
        names = [n for n, r in summary['projects'].items() if r['set'] == group and n in reports]
        entry = {'projects': names}
        if names:
            data = {n: [(reports[n]['b12'], reports[n]['product'])] for n in names}
            point = study._mean_over_seeds(data)
            draws = study._hierarchical_draws(data, 2000, random.Random(0))
            entry['b12_minus_product'] = {m: {'estimate': point[m],
                                              'ci': study._percentile(draws[m])}
                                          for m in ('time', 'recall', 'safety')}
            keeps = {k: sum(summary['projects'][n][k]['miss_rate'] <= ALPHA for n in names)
                     for k in ('b10', 'b12', 'product')}
            entry['projects_keeping_target'] = keeps
            ci = entry['b12_minus_product']['time']['ci']
            if len(names) < 3 or ci is None:
                entry['verdict'] = 'inconclusive'
            elif ci[1] < 0 and keeps['b12'] >= 3:
                entry['verdict'] = 'B12 saves time'
            elif ci[0] > 0:
                entry['verdict'] = 'B12 costs time'
            else:
                entry['verdict'] = 'inconclusive'
            entry['pooled_commits'] = {k: {**metrics([o for n in names for o in reports[n][k]]),
                                           'miss_rate': miss_rate([o for n in names
                                                                   for o in reports[n][k]])}
                                       for k in ('b10', 'b12', 'product')}
        else:
            entry['verdict'] = 'inconclusive'
        if group == 'exploratory':
            entry['note'] = 'previously inspected projects; exploratory only'
        summary[group] = entry
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    fmt = lambda v: 'n/a' if v is None else f'{v:.4f}' if isinstance(v, float) else str(v)
    lines = ['# Conformal-risk-control stopping (B12) against B10 and the gated product', '',
             'Rules fixed in docs/CRC_STOP_PROTOCOL.md before results.', '',
             '| Project | B10 time | B10 miss | B12 time | B12 miss | B12 safety | Product time | '
             'Product miss | Thresholds |', '|' + '---|' * 9]
    for n, r in summary['projects'].items():
        if 'b12' not in r:
            lines.append(f'| {n} | not evaluated |' + ' |' * 7)
            continue
        lines.append('| ' + ' | '.join([n, fmt(r['b10']['time']), fmt(r['b10']['miss_rate']),
            fmt(r['b12']['time']), fmt(r['b12']['miss_rate']), fmt(r['b12']['safety']),
            fmt(r['product']['time']), fmt(r['product']['miss_rate']),
            ', '.join(str(t) for t in r['thresholds'])]) + ' |')
    for group in ('confirmatory', 'exploratory'):
        lines += ['', f'## {group}', '', f"Verdict: **{summary[group]['verdict']}**", '',
                  '```json', json.dumps(summary[group], indent=2), '```']
    (out / 'summary.md').write_text('\n'.join(lines) + '\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('datasets', type=Path,
                        help='folder holding <project>/dataset.csv for each project')
    parser.add_argument('--out', type=Path, default=Path('experiments/results/crc-check-2026-10-26'))
    args = parser.parse_args()
    found = {p.parent.name: p for p in sorted(args.datasets.glob('*/dataset.csv'))}
    if not found:
        parser.error('no <project>/dataset.csv files found')
    run(Path.cwd(), found, args.out)
    print('Completed ' + str(args.out / 'summary.md'), flush=True)
