"""Replay fixed evidence gates and raw outcomes, without manufacturing model evidence."""
import csv
from hashlib import sha256
import io
import json
from pathlib import Path
from time import perf_counter
import zipfile

from codedna.git_analysis.git import run_git
from codedna.selection.validation import validate_outcomes
from codedna.selection.conformal import MIN_FAILING


def main():
    root = Path(__file__).resolve().parents[1]
    if run_git(root, 'diff', 'a02d20f', '--', 'backend/codedna', 'plugins/codedna-java').strip():
        raise ValueError('Frozen application changed')
    out = root/'experiments/results/brake-fixed-cohort-d090-2026-10-29'
    out.mkdir(exist_ok=False)
    started = perf_counter()
    cohort_path = root/'experiments/brake-cohort-d089.json'
    cohort = json.loads(cohort_path.read_text())
    ancestry = json.loads((root/'experiments/results/brake-ancestry-d089-2026-10-29.json').read_text())
    if ancestry['cohort_sha256'] != sha256(cohort_path.read_bytes()).hexdigest():
        raise ValueError('Cohort changed after ancestry verification')
    folder = root/'build/d088-inputs'
    manifest = json.loads((folder/'lrts-inventory-manifest.json').read_text())
    members = {r['member']: r for r in manifest['members']}

    def outcomes(build):
        failures, durations, counts = set(), [], 0
        for job in build['jobs']:
            name = 'long_running_test_suites/processed_test_result/activemq/'+job['pr_name']+'_build'+job['build_id']+'/stage_'+job['stage_id']+'/test_class.csv.zip'
            pin = members[name]
            raw = (folder/'lrts-inventories'/(pin['sha256']+'.zip')).read_bytes()
            if sha256(raw).hexdigest() != pin['sha256']:
                raise ValueError('Inventory changed')
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                with archive.open('test_class.csv') as stream:
                    rows = list(csv.DictReader(io.TextIOWrapper(stream, encoding='utf-8')))
            for row in rows:
                if row['outcome'] not in ('0', '1'):
                    raise ValueError('Unknown raw outcome label')
                if row['outcome'] == '1':
                    failures.add(row['testclass'])
                durations.append(float(row['duration']))
                counts += 1
        return {'failed_classes': sorted(failures), 'class_observations': counts,
                'historical_class_duration_sum': sum(durations)}

    # Evaluation labels stay sealed until every gate decision is fixed.
    historical = {b['head']: outcomes(b) for b in cohort['builds'] if b['split'] != 'evaluation'}
    builds = {b['head']: b for b in cohort['builds']}
    order = {b['head']: i for i,b in enumerate(cohort['builds'])}
    decisions = []
    for item in ancestry['builds']:
        if item['split'] != 'evaluation':
            continue
        prior = sorted((h for h in item['known_prior_ancestor_heads'] if h in historical), key=order.__getitem__)
        if any(builds[h]['timestamp'] >= builds[item['head']]['timestamp'] for h in prior):
            raise ValueError('Future history reached the audit')
        n = len(prior)
        audit = prior[int(n*.75):]  # Existing live fit_audited uses 50/25/25.
        best = validate_outcomes([(0, len(historical[h]['failed_classes']), 0) for h in audit], .05)
        failing = sum(bool(historical[h]['failed_classes']) for h in audit)
        crc_full = failing < MIN_FAILING or 1/(failing+1) > .05
        decisions.append({'head': item['head'], 'prior_ancestor_count': n, 'audit_heads': audit,
            'b10_zero_miss_best_case_evidence': best.to_dict(),
            'b10': 'requires_model_evaluation' if best.accepted else 'full_suite_required_by_evidence_gate',
            'crc_failing_audit_commits': failing,
            'crc': 'full_suite_required_by_evidence_gate' if crc_full else 'requires_model_evaluation'})
    preflight_seconds = perf_counter()-started
    with (out/'decisions-before-evaluation-labels.json').open('x', encoding='utf-8') as stream:
        json.dump(decisions, stream, indent=2)
        stream.write('\n')
    records = []
    for decision in decisions:
        observed = outcomes(builds[decision['head']])
        records.append({**decision, 'full_suite_observed': observed,
            'b10_observed_missed_classes': 0 if decision['b10'].startswith('full_suite') else None,
            'crc_observed_missed_classes': 0 if decision['crc'].startswith('full_suite') else None})
    summary = {'application_source': 'a02d20f', 'risk_target': .05,
        'evaluation_commits': len(records),
        'observed_failing_commits': sum(bool(r['full_suite_observed']['failed_classes']) for r in records),
        'observed_failing_class_occurrences': sum(len(r['full_suite_observed']['failed_classes']) for r in records),
        'b10_proven_full_suite_fallbacks': sum(r['b10'].startswith('full_suite') for r in records),
        'crc_proven_full_suite_fallbacks': sum(r['crc'].startswith('full_suite') for r in records),
        'historical_full_class_duration_sum': sum(r['full_suite_observed']['historical_class_duration_sum'] for r in records),
        'preflight_runner_seconds': preflight_seconds, 'whole_runner_seconds': perf_counter()-started,
        'scope': 'Existing evidence-gate feasibility and recorded full-suite outcomes, not fitted-model predictions or new CI execution.',
        'cost_note': 'Class-duration sums are historical serial estimates, not wall time; timings measure this audit runner, not the live brake or counterfactual CI savings.',
        'structural_and_simple_baselines': 'not executed; no estimates invented',
        'future_risk_guarantee': False}
    (out/'records.json').write_text(json.dumps(records,indent=2)+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary),flush=True)


if __name__ == '__main__':
    main()
