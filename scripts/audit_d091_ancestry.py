"""Bounded-memory ancestry screening of frozen larger history cohorts."""
import argparse
from hashlib import sha256
import json
import re
from pathlib import Path

from codedna.git_analysis.git import run_git, run_git_bytes, GitCommandError


def prior_heads(parents, head, candidates):
    seen, pending, found = set(), list(parents.get(head, [])), set()
    while pending:
        node=pending.pop()
        if node in seen:continue
        seen.add(node)
        if node in candidates:found.add(node)
        pending.extend(parents.get(node, []))
    return found


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',choices=['hadoop','hive','jackrabbit-oak','kafka'])
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    path=root/'experiments/d091-cohorts'/(args.project+'.json')
    cohort=json.loads(path.read_text())
    cache=root/'build/d091-inputs'
    cache.mkdir(exist_ok=True)
    repo=cache/(args.project+'-ancestry.git')
    repo.mkdir(exist_ok=True)
    run_git(repo,'init','--bare','--quiet')
    heads=[b['head'] for b in cohort['builds']]
    unavailable={}
    requests=0
    def fetch(batch):
        nonlocal requests
        if requests>=512:
            unavailable.update({h:'Unresolved at the 512-request resumed screening budget' for h in batch})
            return
        requests+=1
        try:
            run_git(repo,'fetch','--quiet','--no-tags','--filter=blob:none','--depth=256',cohort['repository'],*batch)
        except GitCommandError as error:
            if 'not our ref' not in str(error):raise
            missing=re.search(r'not our ref ([0-9a-f]{40})',str(error))
            if missing and missing[1] in batch:
                unavailable[missing[1]]='Public upstream did not serve the exact recorded commit'
                remaining=[h for h in batch if h!=missing[1]]
                if remaining:fetch(remaining)
                return
            if len(batch)==1:
                unavailable[batch[0]]='Public upstream did not serve the exact recorded commit'
            else:
                middle=len(batch)//2
                fetch(batch[:middle]);fetch(batch[middle:])
    for start in range(0,len(heads),48):
        marker=cache/(args.project+'-fetch-'+str(start)+'.json')
        batch=heads[start:start+48]
        if marker.exists():
            cached=json.loads(marker.read_text())
            if isinstance(cached,list):
                if cached!=batch:raise ValueError('Cached fetch cohort changed')
            else:
                if cached['heads']!=batch:raise ValueError('Cached fetch cohort changed')
                unavailable.update(cached['unavailable'])
        else:
            fetch(batch)
            marker.write_text(json.dumps({'heads':batch,'unavailable':{h:unavailable[h] for h in batch if h in unavailable}}))
        print(args.project,'fetched',min(start+48,len(heads)),'/',len(heads),flush=True)
    parents={}
    available=[h for h in heads if h not in unavailable]
    graph = run_git_bytes(repo,'rev-list','--parents','--stdin',
                          stdin=('\n'.join(available)+'\n').encode()) if available else b''
    for line in graph.decode().splitlines():
        node,*edges=line.split();parents[node]=edges
    historical={b['head']:b for b in cohort['builds'] if b['split']!='evaluation'}
    order={h:i for i,h in enumerate(heads)}
    records=[]
    for build in cohort['builds']:
        if build['split']!='evaluation':continue
        if build['head'] in unavailable:
            records.append({'head':build['head'],'status':'source_unavailable',
                            'known_prior_history_heads':[],'prior_history_count':0,'live_audit_heads':[]})
            continue
        candidates={h for h,b in historical.items() if b['timestamp']<build['timestamp']}
        known=sorted(prior_heads(parents,build['head'],candidates),key=order.__getitem__)
        n=len(known)
        records.append({'head':build['head'],'status':'known_ancestry_partial_if_missing_or_shallow','known_prior_history_heads':known,
                        'prior_history_count':n,'live_audit_heads':known[int(n*.75):]})
    out=root/'experiments/results/larger-history-d091-2026-10-29'
    out.mkdir(exist_ok=True)
    report={'project':args.project,'cohort_sha256':sha256(path.read_bytes()).hexdigest(),
        'depth':256,'shallow':(repo/'shallow').exists(),'commits_in_fetched_graph':len(parents),
        'unavailable_heads':unavailable,
        'fetch_requests_this_invocation':requests,
        'scope':'Positive ancestry only; unresolved shallow history is not asserted absent',
        'evaluation':records}
    with (out/(args.project+'-ancestry.json')).open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(report,stream,indent=2);stream.write('\n')
    print(args.project,'DONE: eval',len(records),'live audit range',
          min(len(r['live_audit_heads']) for r in records),max(len(r['live_audit_heads']) for r in records),flush=True)


if __name__=='__main__':main()
