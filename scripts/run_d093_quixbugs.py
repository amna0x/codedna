"""Fixed controlled comparison; retains every program and every unsuccessful trial."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from time import perf_counter

from codedna.behavior import find_difference
from codedna.git_analysis.git import run_git
from codedna_java.witness import _tools
from codedna_java.witness_inputs import encode,parameter_types


def valid_expected(value):
    return (type(value) is int and -(2**63)<=value<2**63 or isinstance(value,list)
            and len(value)<=128 and all(type(x) is int and -(2**31)<=x<2**31 for x in value))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--allow-build',action='store_true')
    args=parser.parse_args()
    if not args.allow_build:parser.error('Explicit benchmark-code execution consent required')
    root=Path(__file__).resolve().parents[1]
    if run_git(root,'diff','a02d20f','--','backend/codedna','plugins/codedna-java').strip():raise ValueError('Application changed')
    protocol_path=root/'experiments/quixbugs-d093.json';protocol=json.loads(protocol_path.read_text())
    repo=root/'build/d093-quixbugs-snapshots';upstream=root/'build/d093-quixbugs'
    out=root/'experiments/results/quixbugs-controlled-d093-2026-10-29';out.mkdir(exist_ok=False)
    pins={str(p.relative_to(root)):sha256(p.read_bytes()).hexdigest() for directory in
          ['backend/codedna','plugins/codedna-java/codedna_java'] for p in (root/directory).rglob('*.py')}
    (out/'execution-manifest.json').write_bytes((json.dumps({'application_source':'a02d20f',
        'runner_commit':run_git(root,'rev-parse','HEAD').strip(),'protocol_sha256':sha256(protocol_path.read_bytes()).hexdigest(),
        'source_sha256':pins,'oracle_rule':'After both search modes, first four compatible published inputs; stop on first confirmed correction',
        'scope':'Single-seed educational controlled benchmark, not production CI or broad superiority'},indent=2)+'\n').encode())
    (out/'UPSTREAM_LICENSE').write_bytes((upstream/'LICENSE').read_bytes())
    javac,java=_tools(root);trials=[];oracles=[]
    def call(case,folder,mode,maximum=16,expectation=None):
        return find_difference(repo,protocol['base'],protocol['head'],file=case['file'],symbol=case['symbol'],
            output_dir=folder,allow_build=True,max_inputs=maximum,seed=7,reduce_budget=0 if expectation else 4,
            timeout=60,generation=mode,support_files=protocol['helpers'],expectation=expectation)
    for index,case in enumerate(protocol['cases']):
        modes=['guided','simple'] if index%2==0 else ['simple','guided']
        for mode in modes:
            start=perf_counter();row={'program':case['program'],'mode':mode,'seed':7,'executed':bool(case['symbol'])}
            if not case['symbol']:
                row.update(status='unsupported_at_source_selection',replay=None)
            else:
                folder=out/(case['program']+'-'+mode)
                report=call(case,folder,mode)
                row.update(status=report['status'],replay=None,witness_input=(report.get('witness') or {}).get('input'))
                if report.get('further_execution_blocked'):raise RuntimeError('Owned cleanup unconfirmed; benchmark stopped')
                if report['status']=='difference':
                    compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=folder,
                        capture_output=True,timeout=30)
                    reproduced=subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=folder,capture_output=True,timeout=30) if compiled.returncode==0 else None
                    row['replay']=compiled.returncode==0 and reproduced is not None and reproduced.returncode==0
                    (folder/'replay.txt').write_bytes(compiled.stdout+compiled.stderr+(reproduced.stdout+reproduced.stderr if reproduced else b''))
            row['whole_trial_seconds']=perf_counter()-start;trials.append(row)
            (out/'trials.json').write_bytes((json.dumps(trials,indent=2)+'\n').encode())
            print(len(trials),'/80',case['program'],mode,row['status'],'replay',row['replay'],flush=True)
        # Published triggering inputs never influence either search mode above.
        if case['symbol']:
            tests=upstream/'json_testcases'/case['json_tests'];attempts=0;confirmed=False;details=[]
            if tests.exists():
                for line in tests.read_text().splitlines():
                    if attempts==4:break
                    try:
                        inputs,expected=json.loads(line);types=parameter_types(case['symbol'])
                        value=inputs[0] if len(types)==1 else inputs
                        encode(types,value)
                        if not valid_expected(expected):continue
                    except (ValueError,TypeError,IndexError):continue
                    attempts+=1
                    report=call(case,out/(case['program']+'-oracle-'+str(attempts)),'simple',1,
                        {'input':value,'expected':expected,'requirement':'Published QuixBugs testcase expectation'})
                    assessment=report.get('expectation_assessment',{})
                    corrected=(assessment.get('status')=='confirmed_at_supplied_input'
                               and assessment.get('base_satisfies') is False and assessment.get('head_satisfies') is True)
                    details.append({'input':value,'expected':expected,'status':report['status'],'confirmed_correction':corrected})
                    if report.get('further_execution_blocked'):raise RuntimeError('Owned cleanup unconfirmed')
                    if corrected:confirmed=True;break
            oracles.append({'program':case['program'],'published_inputs_attempted':attempts,
                'confirmed_published_correction':confirmed,'details':details,
                'note':'Separate known-trigger validation, not automatic-search success or witness-specific oracle proof'})
            (out/'oracle-checks.json').write_bytes((json.dumps(oracles,indent=2)+'\n').encode())
    for name,digest in pins.items():
        if sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Application changed during comparison')
    from collections import Counter
    summary={'programs':40,'eligible_programs':sum(bool(c['symbol']) for c in protocol['cases']),
        'planned_trials':80,'completed_trials':len(trials),'executed_searches':sum(r['executed'] for r in trials),
        'modes':{mode:dict(Counter(r['status'] for r in trials if r['mode']==mode)) for mode in ['guided','simple']},
        'exported_witnesses':sum(r['status']=='difference' for r in trials),
        'independently_replayed':sum(r['replay'] is True for r in trials),
        'programs_with_confirmed_published_correction':sum(o['confirmed_published_correction'] for o in oracles),
        'scope':'Controlled educational benchmark; unsupported cases retained; one seed, no broad superiority or CI-savings claim'}
    (out/'summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode());print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
