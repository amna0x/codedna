"""Completion-aware, decision-before-report pilot on pinned genuine trunk CI."""
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import urlopen
import os
import argparse

from codedna.git_analysis.git import run_git
from codedna.selection.validation import validate_outcomes
from d092_prequential import Build, Outcome, replay, eligible_history

TREE='failCount,passCount,skipCount,suites[cases[className,name,duration,status]],childReports[result[failCount,passCount,skipCount,suites[cases[className,name,duration,status]]]]'


def parse_report(data):
    failed=set();classes=set();states={};known=True;count=0
    reports=[data] if data.get('suites') else [item['result'] for item in data.get('childReports',[]) if 'result' in item]
    for report in reports:
        for suite in report.get('suites',[]):
            for case in suite.get('cases',[]):
                count+=1;name=case.get('className');status=case.get('status')
                if not name or status not in ('PASSED','FIXED','FAILED','REGRESSION','SKIPPED'):
                    known=False;continue
                classes.add(name);states.setdefault(name,set()).add(status)
                if status in ('FAILED','REGRESSION'):failed.add(name)
    keys=('passCount','failCount','skipCount')
    expected=[data.get(k) for k in keys]
    if not all(type(x) is int and x>=0 for x in expected) and not data.get('suites') and reports:
        # Maven's aggregated report exports fail/skip at the root, but its pass
        # count is available only in child results. Check every child and every
        # exposed root total; never fill an unknown count with zero.
        child_counts=[[report.get(k) for k in keys] for report in reports]
        if all(type(x) is int and x>=0 for row in child_counts for x in row):
            totals=[sum(row[i] for row in child_counts) for i in range(3)]
            if all(data.get(k) is None or data[k]==totals[i] for i,k in enumerate(keys)):
                expected=totals
    complete=bool(classes) and known and all(type(x) is int and x>=0 for x in expected) and sum(expected)==count
    skipped=frozenset(name for name,statuses in states.items() if statuses=={'SKIPPED'})
    return Outcome(frozenset(classes),frozenset(failed),complete,
        None if complete else 'Missing/unknown cases or aggregate-count mismatch',skipped)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='experiments/results/rolling-main-ci-d092-2026-10-29')
    parser.add_argument('--cached-from',type=Path)
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    if run_git(root,'diff','a02d20f','--','backend/codedna','plugins/codedna-java').strip():raise ValueError('Application changed')
    manifest_path=root/'experiments/d092-main-ci-pilot.json'
    manifest=json.loads(manifest_path.read_text())
    out=root/args.out
    out.mkdir(exist_ok=False)
    metadata={b['number']:b for b in manifest['builds']}
    cached=root/args.cached_from if args.cached_from else None
    old_records={r['build']:r for r in json.loads((cached/'records.json').read_text())} if cached else {}
    if cached and set(old_records)!=set(metadata):raise ValueError('Cached cohort mismatch')
    builds=[Build(b['number'],b['commit'],b['parent'],b['started'],b['finished'],b['source_verified']) for b in manifest['builds']]
    source=root/'build/d092-main-ci/source.git'
    chains={b.number:set(run_git(source,'rev-list','--first-parent',b.parent).splitlines()) if b.parent else set() for b in builds}
    loaded=set();payload_bytes=0
    def decide(build,history):
        if build.number in loaded:raise ValueError('Current outcome read before decision')
        usable,unstable=eligible_history(history,chains[build.number],build.started)
        common={'action':'run_full_suite','model_fitted':False,'available_complete_unique_commits':len(usable),
                'unstable_commits_excluded':sorted(unstable)}
        if not build.source_verified:return {**common,'action':'blocked_unverified_source','reason':'Exact main-branch source not verified'}
        if build.parent not in usable:return {**common,'reason':'No completed, complete result at BASE'}
        n=len(usable);audit_n=n-int(n*.75)
        floor=validate_outcomes([(0,0,0)]*audit_n,.05).miss_upper_bound
        if floor>.05 and 1/(audit_n+1)>.05:
            return {**common,'reason':'Existing evidence floor cannot allow skipping','audit_commit_count':audit_n}
        return {**common,'reason':'Research model evaluation pending real source features/inventory; no guessed scores',
                'selective_evaluation_pending':True}
    def persist(build,decision,visible):
        with (out/('decision-'+str(build.number)+'.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump({'build':build.number,'commit':build.commit,'started':build.started,
                       'visible_completed_builds':visible,'decision':decision},stream,indent=2)
            stream.write('\n');stream.flush();os.fsync(stream.fileno())
    def truth(build):
        nonlocal payload_bytes
        if not (out/('decision-'+str(build.number)+'.json')).exists():raise ValueError('Decision was not persisted')
        url=metadata[build.number]['url']
        if urlparse(url).hostname!='ci-builds.apache.org' or not url.startswith(manifest['job']):raise ValueError('Unexpected report origin')
        try:
            if cached:
                old=cached/('report-'+str(build.number)+'.json')
                if not old.exists():raise ValueError('Preserved initial report failure: '+str(old_records[build.number]['report_limitation']))
                raw=old.read_bytes()
            else:
                with urlopen(url+'testReport/api/json?tree='+quote(TREE,safe=',[]'),timeout=45) as response:
                    raw=response.read(32*1024*1024+1)
            if len(raw)>32*1024*1024:raise ValueError('Report size limit')
            payload_bytes+=len(raw)
            if payload_bytes>256*1024*1024:raise ValueError('Pilot download budget')
            (out/('report-'+str(build.number)+'.json')).write_bytes(raw)
            result=parse_report(json.loads(raw))
        except Exception as error:result=Outcome(frozenset(),frozenset(),False,str(error)[:300])
        loaded.add(build.number)
        print('Build',build.number,'decision persisted first; report classes',len(result.classes),
              'complete as published',result.complete_as_published,flush=True)
        return result
    records=replay(builds,decide,truth,persist)
    summary={'scope':'Genuine trunk CI engineering pilot, not independent effectiveness/net-CI savings',
        'manifest_sha256':sha256(manifest_path.read_bytes()).hexdigest(),'application_source':'a02d20f',
        'builds':len(records),'source_verified_builds':sum(b.source_verified for b in builds),
        'complete_published_reports':sum(r['complete_as_published'] for r in records),
        'recorded_failing_builds':sum(r['recorded_failed_classes']>0 for r in records),
        'model_fits':0,'selective_decisions':0,'report_payload_bytes':payload_bytes,
        'network_report_bytes':0 if cached else payload_bytes,
        'replay_of_inspected_cached_reports':bool(cached),
        'source_test_universe_verified':False,'new_ci_execution':False,
        'limitation':'None of 26 inspected jobs met 240 retained builds; existing evidence guards remain mandatory.'}
    (out/'records.json').write_bytes((json.dumps(records,indent=2)+'\n').encode())
    (out/'summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode())
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
