"""Pin every controlled program and record package-only adaptation before execution."""
from hashlib import sha256
import json
from pathlib import Path
import re

from codedna.git_analysis.git import run_git
from codedna_java.parser import parse_java
from codedna_java.witness import _method

IDENTITY=['-c','user.name=CodeDNA benchmark','-c','user.email=codedna-benchmark@invalid','-c','commit.gpgsign=false']


def main():
    root=Path(__file__).resolve().parents[1];upstream=root/'build/d093-quixbugs'
    pin='4257f44b0ff1181dedaedee6a447e133219fcebf'
    if run_git(upstream,'rev-parse','HEAD').strip()!=pin:raise ValueError('Benchmark revision changed')
    names=sorted(p.name for p in (upstream/'correct_java_programs').glob('*.java'))
    if len(names)!=40:raise ValueError('Retain all forty benchmark programs')
    repo=root/'build/d093-quixbugs-snapshots';repo.mkdir(exist_ok=False)
    run_git(repo,'init','--quiet');run_git(repo,'config','core.autocrlf','false')
    helpers=[name for name in ['Node.java','WeightedEdge.java'] if (upstream/'java_programs'/name).exists()]
    original={};adapted={}
    for name in names:
        buggy=(upstream/'java_programs'/name).read_bytes()
        fixed=(upstream/'correct_java_programs'/name).read_bytes()
        normalized=re.sub(rb'(?m)^package\s+correct_java_programs\s*;',b'package java_programs;',fixed,count=1)
        original[name]=(buggy,fixed);adapted[name]=(buggy,normalized)
        (repo/name).write_bytes(buggy)
    for name in helpers:(repo/name).write_bytes((upstream/'java_programs'/name).read_bytes())
    (repo/'LICENSE').write_bytes((upstream/'LICENSE').read_bytes())
    run_git(repo,'add','--all');run_git(repo,*IDENTITY,'commit','--quiet','-m','Pinned buggy benchmark sources')
    base=run_git(repo,'rev-parse','HEAD').strip()
    for name in names:(repo/name).write_bytes(adapted[name][1])
    run_git(repo,'add','--all');run_git(repo,*IDENTITY,'commit','--quiet','-m','Corrected sources with declared package normalization')
    head=run_git(repo,'rev-parse','HEAD').strip();cases=[]
    for name in names:
        pair=adapted[name];parsed=[parse_java(s) for s in pair]
        declarations=[{d.id:d for d in p.declarations if d.kind=='method'} for p in parsed]
        candidates=[];refused=[]
        for symbol in sorted(set(declarations[0]) & set(declarations[1])):
            if declarations[0][symbol].tokens==declarations[1][symbol].tokens:continue
            try:
                for source in pair:_method(source,symbol)
                candidates.append(symbol)
            except ValueError as error:refused.append({'symbol':symbol,'reason':str(error)})
        cases.append({'program':name.removesuffix('.java'),'file':name,
            'symbol':candidates[0] if candidates else None,'refusals':refused,
            'original_source_sha256':[sha256(s).hexdigest() for s in original[name]],
            'adapted_source_sha256':[sha256(s).hexdigest() for s in pair],
            'json_tests':name.removesuffix('.java').lower()+'.json',
            'status':'source_contract_eligible' if candidates else 'unsupported_at_source_selection'})
    manifest={'benchmark':'QuixBugs educational challenge programs; not production changes',
        'upstream':'https://github.com/jkoppel/QuixBugs','upstream_commit':pin,
        'application_source':'a02d20f','base':base,'head':head,'helpers':helpers,
        'seed':7,'max_inputs':16,'reduce_budget':4,'timeout_seconds':60,
        'adaptation':'Only corrected package declaration normalized; bodies unchanged',
        'cases':cases}
    with (root/'experiments/quixbugs-d093.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(manifest,stream,indent=2);stream.write('\n')
    print('All programs:',len(cases),'source-contract eligible:',sum(bool(c['symbol']) for c in cases),flush=True)


if __name__=='__main__':main()
