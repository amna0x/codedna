"""Evaluate necessary fixed evidence gates on four frozen larger cohorts."""
import csv
import argparse
from hashlib import sha256
import io
import json
import math
from pathlib import Path
from time import perf_counter
import zipfile

from codedna.git_analysis.git import run_git
from codedna.selection.validation import validate_outcomes
from codedna.selection.conformal import MIN_FAILING


def read_build(root,project,build,members):
    failures=set();classes=set();seconds=0.;observations=0
    for job in build['jobs']:
        name='long_running_test_suites/processed_test_result/'+project+'/'+job['pr_name']+'_build'+job['build_id']+'/stage_'+job['stage_id']+'/test_class.csv.zip'
        if name not in members:raise ValueError('Inventory unavailable: '+name)
        pin=members[name]
        raw=(root/'build/d091-inputs/inventories'/(pin['sha256']+'.zip')).read_bytes()
        if sha256(raw).hexdigest()!=pin['sha256']:raise ValueError('Inventory hash changed')
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if archive.namelist()!=['test_class.csv'] or archive.getinfo('test_class.csv').file_size>16*1024*1024:
                raise ValueError('Unexpected inventory structure/size')
            with archive.open('test_class.csv') as stream:
                seen=set()
                for row in csv.DictReader(io.TextIOWrapper(stream,encoding='utf-8')):
                    test=row['testclass'];duration=float(row['duration'])
                    if not test or test in seen or not math.isfinite(duration) or duration<0:
                        raise ValueError('Invalid class/duration inventory')
                    if row['outcome'] not in ('0','1'):raise ValueError('Unknown raw label')
                    seen.add(test);classes.add(test);seconds+=duration;observations+=1
                    if row['outcome']=='1':failures.add(test)
                if not seen:raise ValueError('Empty job inventory')
    return {'failed_classes':sorted(failures),'unique_classes':len(classes),
            'class_observations':observations,'historical_class_duration_sum':seconds}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['hadoop','hive','jackrabbit-oak','kafka'])
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if run_git(root,'diff','a02d20f','--','backend/codedna','plugins/codedna-java').strip():
        raise ValueError('Frozen application changed')
    out=root/'experiments/results/larger-history-d091-2026-10-29'
    for project in ([args.project] if args.project else ['hadoop','hive','jackrabbit-oak','kafka']):
        target=out/(project+'-gate-results.json')
        if target.exists():raise ValueError('Retain prior results; do not overwrite '+project)
        started=perf_counter()
        path=root/'experiments/d091-cohorts'/(project+'.json')
        cohort=json.loads(path.read_text())
        ancestry=json.loads((out/(project+'-ancestry.json')).read_text())
        if ancestry['cohort_sha256']!=sha256(path.read_bytes()).hexdigest():raise ValueError('Cohort changed')
        inventory=json.loads((root/'build/d091-inputs'/(project+'-inventories.json')).read_text())
        if inventory['cohort_sha256']!=ancestry['cohort_sha256']:raise ValueError('Inventory cohort mismatch')
        members={r['member']:r for r in inventory['members']}
        builds={b['head']:b for b in cohort['builds']}
        cache={};decisions=[]
        def historical(head):
            if builds[head]['split']=='evaluation':raise ValueError('Evaluation label leaked into the audit')
            if head not in cache:cache[head]=read_build(root,project,builds[head],members)
            return cache[head]
        for item in ancestry['evaluation']:
            decision={'head':item['head'],'prior_history_count':item['prior_history_count'],
                      'audit_heads':item['live_audit_heads']}
            if item.get('status')=='source_unavailable':
                decision.update(b10='source_unavailable',crc='source_unavailable')
                decisions.append(decision);continue
            try:
                counts=[]
                for head in item['live_audit_heads']:
                    if builds[head]['timestamp']>=builds[item['head']]['timestamp']:
                        raise ValueError('Future evidence in audit')
                    counts.append(len(historical(head)['failed_classes']))
                best=validate_outcomes([(0,n,0) for n in counts],.05)
                failing=sum(n>0 for n in counts)
                decision.update(b10='requires_model_evaluation' if best.accepted else 'full_suite_required_by_evidence_gate',
                    crc='full_suite_required_by_evidence_gate' if failing<MIN_FAILING or 1/(failing+1)>.05 else 'requires_model_evaluation',
                    b10_zero_miss_best_case_evidence=best.to_dict(),crc_failing_audit_commits=failing)
            except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error:
                decision.update(b10='input_unavailable',crc='input_unavailable',reason=str(error)[:400])
            decisions.append(decision)
        with (out/(project+'-decisions-before-evaluation-labels.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(decisions,stream,indent=2);stream.write('\n')
        for decision in decisions:
            # Do not unseal any row still requiring fitted-model decisions.
            if 'requires_model_evaluation' in (decision['b10'],decision['crc']):continue
            try:decision['recorded_full_suite']=read_build(root,project,builds[decision['head']],members)
            except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error:
                decision['outcome_error']=str(error)[:400]
        summary={'project':project,'application_source':'a02d20f','risk_target':.05,
            'cohort_sha256':ancestry['cohort_sha256'],
            'selected_heads':len(cohort['builds']),'evaluation_heads':len(decisions),
            'policies':{p:{s:sum(d[p]==s for d in decisions) for s in sorted({d[p] for d in decisions})} for p in ['b10','crc']},
            'outcomes_read':sum('recorded_full_suite' in d for d in decisions),
            'recorded_failing_commits':sum(bool(d.get('recorded_full_suite',{}).get('failed_classes')) for d in decisions),
            'runner_seconds':perf_counter()-started,
            'scope':'Necessary evidence-gate replay. Feasible counts are not skip approval; model-pending outcomes remain sealed. No live model/structural/new-CI-speedup claim.'}
        with target.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump({'summary':summary,'records':decisions},stream,indent=2);stream.write('\n')
        print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
