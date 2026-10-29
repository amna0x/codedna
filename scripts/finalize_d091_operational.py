"""Replay exact frozen live eligibility on fixed cohorts; make no fake predictions."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter

from codedna.git_analysis.git import run_git
from codedna.selection.validation import validate_outcomes
from evaluate_d091_gates import read_build


def decision(row):
    if row['status']=='exact_source_unavailable':return 'blocked_source_identity'
    if not row['current_base_has_earlier_recorded_outcomes']:
        return 'full_suite_required_missing_latest_base_history'
    n=len(row['first_parent_history']);audit_n=n-int(n*.75)
    b10_floor=validate_outcomes([(0,0,0)]*audit_n,.05).miss_upper_bound
    crc_floor=1/(audit_n+1)
    if b10_floor>.05 and crc_floor>.05:
        return 'full_suite_required_even_with_best_possible_audit'
    return 'requires_actual_fitted_model_and_remaining_eligibility_checks'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['hadoop','hive','jackrabbit-oak','kafka'])
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if run_git(root,'diff','a02d20f','--','backend/codedna','plugins/codedna-java').strip():
        raise ValueError('Frozen application changed')
    folder=root/'experiments/results/larger-history-d091-2026-10-29'
    for project in ([args.project] if args.project else ['hadoop','hive','jackrabbit-oak','kafka']):
        started=perf_counter()
        path=root/'experiments/d091-cohorts'/(project+'.json')
        cohort=json.loads(path.read_text());builds={b['head']:b for b in cohort['builds']}
        lineage=json.loads((folder/(project+'-operational-lineage.json')).read_text())
        if lineage['cohort_sha256']!=sha256(path.read_bytes()).hexdigest():raise ValueError('Cohort changed')
        decisions=[{**row,'b10_and_crc_decision':decision(row)} for row in lineage['evaluation']]
        with (folder/(project+'-operational-decisions-before-labels.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(decisions,stream,indent=2);stream.write('\n')
        inventory=json.loads((root/'build/d091-inputs'/(project+'-inventories.json')).read_text())
        if inventory['cohort_sha256']!=lineage['cohort_sha256']:raise ValueError('Inventory identity changed')
        members={r['member']:r for r in inventory['members']}
        for row in decisions:
            if row['b10_and_crc_decision'].startswith('requires_actual'):continue
            try:row['recorded_ci_full_suite']=read_build(root,project,builds[row['head']],members)
            except Exception as error:row['recorded_outcome_unavailable']=str(error)[:300]
        kinds=sorted({r['b10_and_crc_decision'] for r in decisions})
        summary={'project':project,'application_source':'a02d20f','risk_target':.05,
            'evaluation_commits':len(decisions),
            'decisions':{k:sum(r['b10_and_crc_decision']==k for r in decisions) for k in kinds},
            'recorded_outcomes_available':sum('recorded_ci_full_suite' in r for r in decisions),
            'recorded_failing_commits':sum(bool(r.get('recorded_ci_full_suite',{}).get('failed_classes')) for r in decisions),
            'recorded_failing_class_occurrences':sum(len(r.get('recorded_ci_full_suite',{}).get('failed_classes',[])) for r in decisions),
            'selection_saving_on_full_suite_fallbacks':0,
            'new_ci_wall_time_measured':False,'runner_seconds':perf_counter()-started,
            'scope':'Exact frozen-history operational eligibility and recorded CI outcomes; no model accuracy/CI speedup claim. Blocked source cases are not successful full-suite executions.'}
        with (folder/(project+'-operational-results.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump({'summary':summary,'records':decisions},stream,indent=2);stream.write('\n')
        print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
