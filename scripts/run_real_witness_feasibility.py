"""Execute the pinned real-change feasibility audit; retain every case/status."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from time import perf_counter

from codedna.behavior import find_difference
from codedna.git_analysis.git import run_git
from codedna_java.witness import _tools

ROOT=Path(__file__).resolve().parents[1]


def source_hashes():
    files=[p for d in ['backend/codedna','plugins/codedna-java/codedna_java'] for p in (ROOT/d).rglob('*.py')]
    files += [Path(__file__),ROOT/'experiments/moonshot-real-change-feasibility-d086.json']
    return {p.relative_to(ROOT).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-build',action='store_true')
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if not args.allow_build:parser.error('explicit --allow-build required for pinned trusted Java execution')
    output=args.out.resolve()
    if output.exists():parser.error('preserve existing results; output must be new')
    pins=source_hashes()
    if run_git(ROOT,'diff','--name-only','HEAD','--',*pins).strip():
        parser.error('commit pinned source and protocol before execution')
    tracked=set(run_git(ROOT,'ls-files','--',*pins).splitlines())
    if tracked!=set(pins):parser.error('commit all pinned source files first')
    protocol=json.loads((ROOT/'experiments/moonshot-real-change-feasibility-d086.json').read_text())
    audit=json.loads((ROOT/'build/d086-real-inputs/source-feasibility.json').read_text())
    assert audit['protocol_sha256']==pins['experiments/moonshot-real-change-feasibility-d086.json']
    repo=ROOT/'build/d086-real-inputs/TheAlgorithms-Java'
    javac,java=_tools(repo)
    output.mkdir(parents=True)
    (output/'manifest.json').write_text(json.dumps({'source_commit':run_git(ROOT,'rev-parse','HEAD').strip(),
        'source_sha256':pins,'protocol':protocol,'source_audit':audit,'scope':'real historical source feasibility, not production-CI research or a bug oracle'},indent=2)+'\n',encoding='utf-8')
    results=[]
    budget=protocol['budget_per_case_per_mode']
    for index,case in enumerate(audit['cases']):
        for mode in (['guided','simple'] if index%2==0 else ['simple','guided']):
            assert source_hashes()==pins,'source changed during frozen comparison'
            start=perf_counter();folder=output/(case['id']+'-'+mode)
            if case['status']!='source_contract_supported':
                report={'status':'unsupported','reason':case['reason'],'source_contract_audit_only':True}
                folder.mkdir();(folder/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
            else:
                report=find_difference(repo,case['base'],case['head'],file=case['file'],symbol=case['symbol'],
                    output_dir=folder,allow_build=True,max_inputs=budget['max_inputs'],seed=budget['seed'],
                    timeout=budget['timeout_seconds'],reduce_budget=budget['reduce_budget'],generation=mode)
            row={'case':case['id'],'generation':mode,'status':report['status'],'seconds':perf_counter()-start,
                 'report':str(folder.relative_to(output))+'/report.json','reproduction':None}
            if report['status']=='difference':
                compiled=subprocess.run([javac,'-encoding','UTF-8','-proc:none','ReproduceDifference.java'],cwd=folder,
                    capture_output=True,timeout=30)
                replay=subprocess.run([java,'-Dfile.encoding=UTF-8','-cp','.','ReproduceDifference'],cwd=folder,
                    capture_output=True,timeout=30) if compiled.returncode==0 else None
                row['reproduction']={'compile_exit':compiled.returncode,'run_exit':replay.returncode if replay else None,
                                     'passed':compiled.returncode==0 and replay is not None and replay.returncode==0}
                (folder/'reproduction.txt').write_bytes(compiled.stdout+compiled.stderr+(replay.stdout+replay.stderr if replay else b''))
            results.append(row)
            (output/'results.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
            print(f"{len(results)}/48 {case['id']} {mode}: {report['status']}",flush=True)
    assert source_hashes()==pins
    summary={'planned':48,'completed':len(results),'scope':'feasibility only; differences are not automatically regressions',
        'modes':{mode:dict(Counter(r['status'] for r in results if r['generation']==mode)) for mode in ['guided','simple']},
        'witnesses':sum(r['status']=='difference' for r in results),
        'independently_reproduced':sum(bool(r['reproduction'] and r['reproduction']['passed']) for r in results)}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary),flush=True)


if __name__=='__main__':main()
