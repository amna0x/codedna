"""Fixed four-project exploratory DANTE-H / B10 extension; see protocol."""
import argparse
import hashlib
import importlib.util
import json
import platform
from pathlib import Path
from statistics import mean
from time import perf_counter
from importlib.metadata import version

from codedna.models.dante_history import historical_scores, order_history
from codedna.models.evaluate import chronological_split, _ordering_metrics
from codedna.models.experiment import _measure, _outcomes
from codedna.models.rankers import order_by_baseline
from codedna.models.transfer import fit_project
from codedna.models.uncertainty import match_budget, metrics
from codedna.selection.risk import RiskPolicy, decide
from codedna.models.uncertainty import bootstrap
from codedna.test_history.features import Dataset

PROJECTS=['hikaricp','littleproxy','jade4j','wicket-bootstrap']
CODE=['scripts/run_dante_check.py','docs/DANTE_B10_PROTOCOL.md',
      'backend/codedna/models/dante_history.py','backend/codedna/models/transfer.py',
      'backend/codedna/models/rankers.py','backend/codedna/models/evaluate.py',
      'backend/codedna/models/experiment.py','backend/codedna/models/uncertainty.py',
      'backend/codedna/selection/risk.py','backend/codedna/test_history/features.py',
      'backend/codedna/calibration/calibrators.py','scripts/run_study.py']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def evaluate(dataset, seed):
    start=perf_counter()
    scores=historical_scores(dataset)
    history_seconds=perf_counter()-start
    start=perf_counter(); fitted=fit_project('target',dataset,seed=seed)
    fit_seconds=perf_counter()-start
    groups=dataset.rows_by_commit(); test=[groups[c] for c in chronological_split(dataset)['test']]
    rows=[r for group in test for r in group]
    raw=fitted.ranker.predict_proba(rows)
    variants={'raw':raw}
    if fitted.calibrator: variants['calibrated']=fitted.calibrator.transform(raw)
    orders={'DANTE-H':lambda group:order_history(group,scores),
            'rules':lambda group:order_by_baseline('recent_failures',group)}
    report={'seed':seed,'source_fitting':fitted.provenance,'warnings':fitted.warnings,
        'test_commits':[g[0].commit for g in test],
        'test_failing_commits':sum(any(r.label for r in g) for g in test),
        'overhead':{'history_scoring_seconds':history_seconds,'fit_calibration_seconds':fit_seconds,
                    'excluded':'CSV feature extraction, Git analysis, compilation and CI startup'},
        'ordering':{name:_ordering_metrics(test,fn) for name,fn in orders.items()},
        'policies':{},'per_commit':{},'comparisons':{}}
    for variant,values in variants.items():
        lookup={(r.commit,r.test_id):v for r,v in zip(rows,values)}
        probabilities=lambda group:[lookup[(r.commit,r.test_id)] for r in group]
        def choose(order,policy):
            def apply(group):
                decision=decide(group,probabilities(group),policy,order=order(group))
                return decision.selected,decision
            return apply
        fixed=choose(orders['DANTE-H'],RiskPolicy(budget=.5))
        report['policies']['D1_50pct']=_measure(test,fixed)
        for name,order in orders.items():
            started=perf_counter()
            policy=choose(order,RiskPolicy(budget=None,risk_target=.05))
            key=name+'_'+variant
            outcomes=_outcomes(test,policy)
            report['policies'][key]=_measure(test,policy)
            budget,matched=match_budget(lambda b:_outcomes(test,choose(order,RiskPolicy(budget=b))),
                                       metrics(outcomes)['time'])
            report['per_commit'][key]=outcomes
            report['per_commit'][key+'_matched']=matched
            report['comparisons'][key]={'budget':budget,'matched_metrics':metrics(matched),
                'intervals':bootstrap({'stopping':outcomes,'matched':matched},
                    {'stopping_minus_matched':('stopping','matched')},resamples=2000,seed=0)}
            report['overhead'][key+'_selection_and_matching_seconds']=perf_counter()-started
    return report

def run(root,out,names=PROJECTS,seeds=(0,1,2,3,4)):
    out.mkdir(parents=True,exist_ok=True)
    paths={name:root/f'experiments/results/study11-2026-10-21/{name}/dataset.csv' for name in names}
    config={'projects':list(names),'seeds':list(seeds),'protocol':'DANTE-H v2 author-history-score adaptation; 60/20/20; 5% risk; no parameter tuning',
        'python':platform.python_version(),'packages':{n:version(n) for n in ['scikit-learn','numpy']},
        'input_sha256':{n:digest(p) for n,p in paths.items()},
        'code_sha256':{n:digest(root/n) for n in CODE}}
    config_path=out/'config.json'
    if config_path.exists() and json.loads(config_path.read_text())!=config:
        raise ValueError('Protocol, code or inputs changed; use a new output folder')
    config_path.write_text(json.dumps(config,indent=2)+'\n')
    reports={}
    for name,path in paths.items():
        dataset=Dataset.from_csv(path)
        for seed in seeds:
            p=out/name/f'seed{seed}.json';p.parent.mkdir(exist_ok=True)
            if p.exists(): report=json.loads(p.read_text())
            else:
                report=evaluate(dataset,seed)
                p.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
            reports[(name,seed)]=report
            print(f'{name} seed {seed}: complete',flush=True)
    spec=importlib.util.spec_from_file_location('study',root/'scripts/run_study.py')
    study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
    import random
    summary={'projects':{},'comparisons':{},'limits':[
        'DANTE-inspired adaptation, not published DANTE reproduction',
        'Exploratory reuse of inspected historical windows; no universal ordering claim',
        'Few failing commits, four projects, serial dependence ignored by bootstrap',
        'No end-to-end CI speedup claim; overhead excludes feature extraction and build startup']}
    for name in names:
        runs=[reports[(name,s)] for s in seeds]
        policies={key:{metric:mean(r['policies'][key][metric] for r in runs)
                   if all(r['policies'][key][metric] is not None for r in runs) else None
                   for metric in ['mean_time_ratio','failing_test_recall','commit_safety_rate',
                                  'observed_miss_rate','mean_estimated_skip_risk']}
                  for key in runs[0]['policies']}
        summary['projects'][name]={'policies':policies,'test_commits':len(runs[0]['test_commits']),
            'failing_commits':runs[0]['test_failing_commits'],
            'ordering':{k:mean(r['ordering'][k]['mean_apfdc'] for r in runs)
                        for k in runs[0]['ordering']}}
    for key in reports[(names[0],seeds[0])]['per_commit']:
        if key.endswith('_matched'): continue
        data={name:[(reports[(name,s)]['per_commit'][key],
                     reports[(name,s)]['per_commit'][key+'_matched']) for s in seeds] for name in names}
        point=study._mean_over_seeds(data);draws=study._hierarchical_draws(data,2000,random.Random(0))
        summary['comparisons'][key]={m:{'estimate':point[m],'ci':study._percentile(draws[m])}
                                      for m in ('time','recall','safety')}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    lines=['# DANTE-H / B10 exploratory extension','',
        'Independent history-only adaptation; NOT a reproduction of published DANTE.',
        'Protocol fixed before these results; original/transfer outcomes were already inspected.','',
        '| Project | Policy | Time | Recall | Safety | Estimated risk | Observed miss |',
        '|---|---|---|---|---|---|---|']
    fmt=lambda v:'n/a' if v is None else f'{v:.4f}'
    for name,record in summary['projects'].items():
        for policy,values in record['policies'].items():
            lines.append('| '+' | '.join([name,policy]+[fmt(values[m]) for m in
                ['mean_time_ratio','failing_test_recall','commit_safety_rate',
                 'mean_estimated_skip_risk','observed_miss_rate']])+' |')
    lines+=['','## Stopping minus same-order budget baseline at matched actual time','',
            'Hierarchical bootstrap: seeds within equally weighted projects, then commits; 2000 draws.',
            'Intervals are exploratory, assume independent commits and have no multiplicity correction.','']
    for key,record in summary['comparisons'].items():
        lines.append(f"- {key}: {json.dumps(record)}")
    lines+=['','## Limits','']+['- '+s for s in summary['limits']]
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    manifest={'config':config,'outputs':{p.relative_to(out).as_posix():digest(p)
              for p in sorted(out.rglob('*')) if p.is_file() and p.name!='manifest.json'}}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Completed '+str(out/'summary.md'),flush=True)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,default=Path('experiments/results/dante-history-check-2026-10-24'))
    args=parser.parse_args();run(Path.cwd(),args.out)
