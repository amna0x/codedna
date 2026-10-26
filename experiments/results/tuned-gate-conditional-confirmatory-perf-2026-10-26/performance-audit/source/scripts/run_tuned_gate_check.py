"""Tuned-threshold gate against the gated product.

B13 (default): rules in docs/TUNED_GATE_PROTOCOL.md. B13f (``--conditional``): the check
uses failing audit commits only, rules in docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md.
"""
import argparse
import hashlib
import importlib.util
import json
import math
import platform
import random
from importlib.metadata import version
from pathlib import Path

from codedna.models.experiment import _outcomes
from codedna.models.uncertainty import metrics
from codedna.plugins.java_live import LIVE_FEATURES
from codedna.selection import tuned
from codedna.selection.live import fit_audited
from codedna.selection.validation import validate_outcomes
from codedna.test_history.features import Dataset

ALPHA = .05
CODE = ['scripts/run_tuned_gate_check.py', 'docs/TUNED_GATE_PROTOCOL.md',
        'backend/codedna/selection/tuned.py', 'backend/codedna/selection/validation.py',
        'scripts/run_crc_check.py', 'scripts/run_rolling_evidence.py',
        'backend/codedna/selection/live.py', 'backend/codedna/selection/risk.py',
        'backend/codedna/plugins/java_live.py', 'backend/codedna/models/rankers.py',
        'backend/codedna/models/uncertainty.py', 'backend/codedna/calibration/calibrators.py',
        'backend/codedna/test_history/features.py', 'scripts/run_study.py',
        'docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md']


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(root, name):
    spec = importlib.util.spec_from_file_location(name, root / f'scripts/{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def full(test):
    return [(1., sum(r.label for r in rows), 0) for rows in test]


def evaluate(dataset, rolling, crc, conditional=False):
    """Per block: B13's threshold from the audit window, B13 and the gated product on the block."""
    groups = dataset.rows_by_commit()
    report = {'commits': len(dataset.commits), 'blocks': []}
    for a, b in rolling.blocks(dataset.commits):
        test = [groups[c] for c in dataset.commits[a:b]]
        block = {'start': a, 'end': b, 'commits': b - a}
        try:
            ranker, calibrator, evidence, info = fit_audited(
                rolling.prefix(dataset, a), LIVE_FEATURES, ALPHA)
        except Exception as exc:  # recorded, never hidden: both policies run the full suite
            block.update(fit_error=f'{type(exc).__name__}: {exc}', accepted=False,
                         threshold='full', b13=full(test), product=full(test))
            report['blocks'].append(block)
            continue
        audit = [groups[c] for c in info['audit_commits']]
        if conditional:  # B13f: check the miss rate among failing commits
            audit = [rows for rows in audit if any(r.label for r in rows)]
        chosen, tested = tuned.search(
            lambda v: _outcomes(audit, crc.stopper(ranker, calibrator, v)), ALPHA)
        b13 = full(test) if chosen is tuned.FULL else \
            _outcomes(test, crc.stopper(ranker, calibrator, chosen))
        product = _outcomes(test, crc.stopper(ranker, calibrator, ALPHA)) \
            if evidence.accepted else full(test)
        block.update(accepted=evidence.accepted, audit_commits=len(audit),
                     tested=[{'threshold': v, **e.to_dict()} for v, e in tested],
                     threshold='full' if chosen is tuned.FULL else chosen,
                     b13=b13, product=product)
        report['blocks'].append(block)
    for key in ('b13', 'product'):
        report[key] = [o for x in report['blocks'] for o in x[key]]
    return report


def run(root, inputs, out, conditional=False):
    rolling, study, crc = (load(root, n) for n in ('run_rolling_evidence', 'run_study',
                                                    'run_crc_check'))
    out.mkdir(parents=True, exist_ok=True)
    config = {'protocol': 'docs/TUNED_GATE_CONDITIONAL_PROTOCOL.md' if conditional
              else 'docs/TUNED_GATE_PROTOCOL.md', 'conditional': conditional, 'alpha': ALPHA, 'grid': list(tuned.GRID),
              'python': platform.python_version(),
              'packages': {n: version(n) for n in ['scikit-learn', 'numpy']},
              'input_sha256': {n: digest(p) for n, p in sorted(inputs.items())},
              'code_sha256': {n: digest(root / n) for n in CODE}}
    config_path = out / 'config.json'
    if config_path.exists() and json.loads(config_path.read_text()) != config:
        raise ValueError('Protocol, code or inputs changed; use a new output folder')
    config_path.write_text(json.dumps(config, indent=2) + '\n')
    summary, reports = {'projects': {}}, {}
    label = 'B13f' if conditional else 'B13'
    for name, path in sorted(inputs.items()):
        dataset = Dataset.from_csv(path)
        region = [c for a, b in rolling.blocks(dataset.commits) for c in dataset.commits[a:b]]
        count = rolling.failing_commits(dataset, region)
        record = {'set': 'exploratory' if name in rolling.STUDY11 else 'confirmatory',
                  'evaluation_failing_commits': count, 'eligible': count >= rolling.MIN_FAILING}
        if record['eligible']:
            p = out / f'{name}.json'
            report = json.loads(p.read_text()) if p.exists() else evaluate(dataset, rolling, crc,
                                                                               conditional)
            p.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
            reports[name] = report
            record.update(
                fit_failures=sum('fit_error' in x for x in report['blocks']),
                thresholds=[x['threshold'] for x in report['blocks']],
                gate_accepted_blocks=sum(bool(x['accepted']) for x in report['blocks']),
                b13_tuned_blocks=sum(x['threshold'] != 'full' for x in report['blocks']),
                **{k: {**metrics(report[k]), 'miss_rate': crc.miss_rate(report[k])}
                   for k in ('b13', 'product')})
        summary['projects'][name] = record
        print(f'{name}: {"evaluated" if record["eligible"] else "ineligible"}', flush=True)
    for group in ('confirmatory', 'exploratory'):
        names = [n for n, r in summary['projects'].items() if r['set'] == group and n in reports]
        entry = {'projects': names}
        if names:
            data = {n: [(reports[n]['b13'], reports[n]['product'])] for n in names}
            point = study._mean_over_seeds(data)
            draws = study._hierarchical_draws(data, 2000, random.Random(0))
            entry['b13_minus_product'] = {m: {'estimate': point[m],
                                              'ci': study._percentile(draws[m])}
                                          for m in ('time', 'recall', 'safety')}
            need = math.ceil(.75 * len(names))
            kept = (lambda m: (m['safety'] or 0) >= 1 - ALPHA) if conditional \
                else (lambda m: m['miss_rate'] <= ALPHA)
            keeps = sum(kept(summary['projects'][n]['b13']) for n in names)
            entry['projects_keeping_target'] = {'b13': keeps, 'needed': need,
                                                'product': sum(kept(summary['projects'][n]['product'])
                                                               for n in names)}
            tuned_outcomes = [o for n in names for x in reports[n]['blocks']
                              if x['threshold'] != 'full' for o in x['b13']]
            if tuned_outcomes:
                e = validate_outcomes(tuned_outcomes, ALPHA)
                f = validate_outcomes([o for o in tuned_outcomes if o[1]], ALPHA)
                entry['tuned_blocks'] = {'commits': e.commits, 'miss_rate': e.observed_miss_rate,
                                         'wilson_upper': e.miss_upper_bound,
                                         'failing_commits': f.commits,
                                         'failing_miss_rate': f.observed_miss_rate,
                                         'failing_wilson_upper': f.miss_upper_bound}
            time, safety = (entry['b13_minus_product'][m]['ci'] for m in ('time', 'safety'))
            if len(names) < 3 or time is None:
                entry['verdict'] = 'inconclusive'
            elif time[1] < 0 and safety is not None and safety[0] >= -ALPHA and keeps >= need:
                entry['verdict'] = f'{label} saves time'
            elif time[0] > 0:
                entry['verdict'] = f'{label} costs time'
            else:
                entry['verdict'] = 'inconclusive'
            entry['pooled_commits'] = {k: {**metrics([o for n in names for o in reports[n][k]]),
                                           'miss_rate': crc.miss_rate([o for n in names
                                                                       for o in reports[n][k]])}
                                       for k in ('b13', 'product')}
        else:
            entry['verdict'] = 'inconclusive'
        entry['note'] = 'exploratory: the B13 design used the confirmatory gate evidence'
        summary[group] = entry
    (out / 'summary.json').write_text(json.dumps(summary, indent=2, allow_nan=False) + '\n')
    fmt = lambda v: 'n/a' if v is None else f'{v:.4f}' if isinstance(v, float) else str(v)
    lines = [f'# Tuned-threshold gate ({label}) against the gated product', '',
             f"Rules fixed in {config['protocol']} before results. Exploratory.", '',
             '| Project | Gate blocks | B13 blocks | Product time | Product miss | Product safety | '
             f'{label} time | {label} miss | {label} safety | Thresholds |', '|' + '---|' * 10]
    for n, r in summary['projects'].items():
        if 'b13' not in r:
            lines.append(f'| {n} | not evaluated |' + ' |' * 8)
            continue
        lines.append('| ' + ' | '.join([n, str(r['gate_accepted_blocks']),
            str(r['b13_tuned_blocks']), fmt(r['product']['time']),
            fmt(r['product']['miss_rate']), fmt(r['product']['safety']), fmt(r['b13']['time']),
            fmt(r['b13']['miss_rate']), fmt(r['b13']['safety']),
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
    parser.add_argument('--out', type=Path)
    parser.add_argument('--conditional', action='store_true',
                        help='B13f: check failing audit commits only')
    args = parser.parse_args()
    args.out = args.out or Path('experiments/results/' + (
        'tuned-gate-conditional-2026-10-26' if args.conditional else 'tuned-gate-2026-10-26'))
    found = {p.parent.name: p for p in sorted(args.datasets.glob('*/dataset.csv'))}
    if not found:
        parser.error('no <project>/dataset.csv files found')
    run(Path.cwd(), found, args.out, args.conditional)
    print('Completed ' + str(args.out / 'summary.md'), flush=True)
