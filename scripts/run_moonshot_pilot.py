"""One bounded, serial engineering pilot on prespecified synthetic fixtures.

Never reads or changes D076, downloads data, calls paid AI, or tunes risk gates.
The protocol/case manifest/source are pinned before any result is measured.
"""
from __future__ import annotations

import argparse
import importlib.metadata
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import re
from statistics import median
import subprocess
import sys
from time import perf_counter

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from codedna.behavior import find_difference
from codedna.git_analysis.git import run_git
from codedna_java.witness import _tools

PINNED = sorted(p.relative_to(ROOT).as_posix()
    for directory in [ROOT/'backend/codedna', ROOT/'plugins/codedna-java/codedna_java']
    for p in directory.rglob('*.py')) + [
        'scripts/run_moonshot_pilot.py', 'scripts/desktop_core_entry.py',
        'experiments/moonshot-engineering-cases.json', 'docs/MOONSHOT_PILOT_PROTOCOL.md']


def fingerprints():
    return {name:sha256((ROOT/name).read_bytes()).hexdigest() for name in PINNED}


def fixture(folder,case):
    folder.mkdir(parents=True,exist_ok=False)
    def git(*args):
        return run_git(folder,'-c','user.name=CodeDNA synthetic pilot',
                       '-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false',*args)
    git('init','--quiet')
    path=folder/'src/main/java/example/Fee.java';path.parent.mkdir(parents=True)
    commits=[]
    for label in ('base','head'):
        path.write_text('package example; public class Fee { public static int fee(int x) { '+case[label+'_body']+' } }\n',
                        encoding='utf-8',newline='\n')
        git('add','--','src/main/java/example/Fee.java')
        git('commit','--quiet','--allow-empty','-m',label)
        commits.append(git('rev-parse','HEAD').strip())
    return commits


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True,help='New results folder; existing folders are preserved.')
    parser.add_argument('--allow-build',action='store_true',help='Execute only the fixed trusted synthetic fixtures.')
    args=parser.parse_args(argv)
    if not args.allow_build:
        parser.error('explicit --allow-build is required for synthetic Java execution')
    output=args.out.resolve()
    if output.exists():
        parser.error('results folder already exists; preserve it and inspect before a new run')
    cases=json.loads((ROOT/'experiments/moonshot-engineering-cases.json').read_text(encoding='utf-8'))
    if not cases.get('cases') or any(not re.fullmatch(r'[a-z0-9_-]{1,64}', str(case.get('id',''))) for case in cases['cases']):
        parser.error('case IDs must be bounded local fixture names')
    if len({case['id'] for case in cases['cases']}) != len(cases['cases']):
        parser.error('case IDs must be unique')
    tracked=set(run_git(ROOT,'ls-files','--',*PINNED).splitlines())
    if set(PINNED)-tracked:
        parser.error('commit every pinned source/protocol file before executing')
    source=fingerprints()
    source_commit=run_git(ROOT,'rev-parse','HEAD').strip()
    dirty=run_git(ROOT,'diff','--name-only','HEAD','--',*PINNED).splitlines()
    if dirty:
        parser.error('commit the pinned source/protocol first: '+', '.join(dirty))
    fixture_root=ROOT/'build'/('moonshot-fixtures-'+output.name)
    if fixture_root.exists():
        parser.error('fixture folder already exists; preserve it')
    fixture_root.mkdir(parents=True)
    output.mkdir(parents=True)
    manifest={'schema_version':1,'scope':cases['scope'],'protocol':'docs/MOONSHOT_PILOT_PROTOCOL.md',
              'source_commit':source_commit,'source_sha256':source,'case_definition':cases,
              'python':sys.version,'platform':platform.platform(),
              'machine':platform.machine(),'logical_cpus':os.cpu_count(),
              'packages':{name:importlib.metadata.version(name) for name in ['codedna','codedna-java','tree-sitter','tree-sitter-java']},
              'execution_order':'serial, alternated guided/simple order within each case/seed pair',
              'limits':['Illustrative synthetic fixtures, not independent real-world failure detection or novelty confirmation.',
                        'Designed boundary cases deliberately favor syntax guidance; all cases/statuses retained.',
                        'Each seed repeats the same cases; repetitions are not independent projects/bugs.',
                        'Equal maximum executed-input/time budgets; confirmation/reduction/reproduction costs recorded.',
                        'No new risk stopping/recall or net CI speedup claim.']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    results=[]
    total=len(cases['cases'])*len(cases['seeds'])*len(cases['generations'])
    original_dates={name:os.environ.get(name) for name in ['GIT_AUTHOR_DATE','GIT_COMMITTER_DATE']}
    os.environ['GIT_AUTHOR_DATE']='2026-10-28T00:00:00+00:00'
    os.environ['GIT_COMMITTER_DATE']='2026-10-28T00:00:00+00:00'
    try:
        fixtures={case['id']:fixture(fixture_root/case['id'],case) for case in cases['cases']}
    finally:
        for name,value in original_dates.items():
            if value is None:os.environ.pop(name,None)
            else:os.environ[name]=value
    for seed_index,seed in enumerate(cases['seeds']):
        for case_index,case in enumerate(cases['cases']):
            order=cases['generations'] if (seed_index+case_index)%2==0 else list(reversed(cases['generations']))
            for mode in order:
                assert fingerprints()==source,'Pinned implementation changed; stop without retuning/resuming'
                repo=fixture_root/case['id'];base,head=fixtures[case['id']]
                before=run_git(repo,'status','--porcelain')
                export=output/f"{case['id']}-seed{seed}-{mode}"
                started=perf_counter()
                report=find_difference(repo,base,head,file='src/main/java/example/Fee.java',
                    symbol='example.Fee#fee(int)',output_dir=export,allow_build=True,max_inputs=cases['max_inputs'],
                    seed=seed,timeout=cases['timeout_seconds'],reduce_budget=cases['reduce_budget'],generation=mode)
                seconds=perf_counter()-started
                assert run_git(repo,'status','--porcelain')==before,'Fixture unexpectedly mutated'
                row={'case':case['id'],'seed':seed,'generation':mode,'status':report['status'],
                     'wall_seconds':seconds,'search_inputs':report.get('search_inputs'),
                     'reduction_inputs':report.get('reduction_inputs'),'jvm_runs':report.get('jvm_runs'),
                     'witness':report.get('witness'),'report_sha256':sha256((export/'report.json').read_bytes()).hexdigest(),
                     'regression_established':report['regression_established'],'reproduction':None}
                if report['status']=='difference':
                    javac,java=_tools(repo)
                    repro_start=perf_counter()
                    compiled=subprocess.run([javac,'-proc:none','ReproduceDifference.java'],cwd=export,
                        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30)
                    reproduced=(subprocess.run([java,'-cp','.','ReproduceDifference'],cwd=export,
                        stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=30) if compiled.returncode==0 else None)
                    row['reproduction']={'seconds':perf_counter()-repro_start,
                        'compile_exit_code':compiled.returncode,'run_exit_code':reproduced.returncode if reproduced else None,
                        'passed':compiled.returncode==0 and reproduced is not None and reproduced.returncode==0}
                    text=(compiled.stdout+(reproduced.stdout if reproduced else b'')).decode('utf-8',errors='replace')
                    (export/'reproduction.txt').write_text(text,encoding='utf-8')
                results.append(row)
                (output/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
                print(f"{len(results)}/{total} {case['id']} seed={seed} {mode}: {report['status']} ({seconds:.3f}s)",flush=True)
    assert fingerprints()==source
    summary={'scope':cases['scope'],'completed':len(results),'planned':total,'by_generation':{}}
    for mode in cases['generations']:
        group=[r for r in results if r['generation']==mode]
        counts={status:sum(r['status']==status for r in group) for status in sorted({r['status'] for r in group})}
        witnesses=[r for r in group if r['status']=='difference']
        summary['by_generation'][mode]={'statuses':counts,'median_wall_seconds':median(r['wall_seconds'] for r in group),
            'reproduced':sum(bool(r['reproduction'] and r['reproduction']['passed']) for r in witnesses),
            'witnesses':len(witnesses)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,indent=2),flush=True)
    return 0


if __name__=='__main__':
    raise SystemExit(main())
