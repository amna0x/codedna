"""Pin the availability-selected CI pilot and verify immutable source lineage."""
from hashlib import sha256
import json
from pathlib import Path
import re

from codedna.git_analysis.git import run_git


def main():
    root=Path(__file__).resolve().parents[1];cache=root/'build/d092-main-ci'
    availability=json.loads((root/'experiments/d092-ci-availability-corrected.json').read_text())
    if availability['selected'] is not None:raise ValueError('Use the qualified research cohort, not this underpowered pilot')
    chosen=next(r for r in availability['candidates'] if r['url']==availability['pilot'])
    raw=(cache/(chosen['metadata_sha256']+'.json')).read_bytes()
    if sha256(raw).hexdigest()!=chosen['metadata_sha256']:raise ValueError('Availability changed')
    metadata=json.loads(raw);builds=[]
    for build in metadata['builds']:
        if build.get('building') or build.get('duration',0)<=0:continue
        revisions={a.get('lastBuiltRevision',{}).get('SHA1') or a.get('revision',{}).get('hash')
                   for a in build.get('actions',[])}-{None}
        commit=next(iter(revisions)) if len(revisions)==1 else None
        if commit and not re.fullmatch('[0-9a-f]{40}',commit):raise ValueError('Invalid revision')
        branches=sorted({b['name'] for a in build.get('actions',[]) for b in a.get('lastBuiltRevision',{}).get('branch',[])})
        builds.append({'number':build['number'],'commit':commit,'url':build['url'],
            'started':build['timestamp']/1000,'finished':(build['timestamp']+build['duration'])/1000,
            'branches':branches})
    repo=cache/'source.git';repo.mkdir(exist_ok=True);run_git(repo,'init','--bare','--quiet')
    commits=sorted({b['commit'] for b in builds if b['commit']})
    run_git(repo,'fetch','--quiet','--no-tags','--filter=blob:none','--depth=512',
            'https://github.com/apache/jackrabbit-oak.git','refs/heads/trunk',*commits)
    tip=run_git(repo,'rev-parse','FETCH_HEAD').strip()
    main=set(run_git(repo,'rev-list','--first-parent',tip).splitlines())
    for build in builds:
        build['source_verified']=False;build['parent']=None
        if not build['commit']:continue
        ids=run_git(repo,'rev-list','--parents','-n','1',build['commit']).split()
        build['parent']=ids[1] if len(ids)>1 else None
        build['source_verified']=build['commit'] in main and any(name in ('origin/trunk','trunk') for name in build['branches'])
    manifest={'job':chosen['url'],'metadata_sha256':chosen['metadata_sha256'],
        'source_repository':'https://github.com/apache/jackrabbit-oak.git','pinned_trunk_tip':tip,
        'scope':'Availability-selected engineering pilot; insufficient retained history for effectiveness claims',
        'builds':sorted(builds,key=lambda b:(b['started'],b['number']))}
    with (root/'experiments/d092-main-ci-pilot.json').open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(manifest,stream,indent=2);stream.write('\n')
    print('Pinned completed builds:',len(builds),'source/branch verified:',sum(b['source_verified'] for b in builds))


if __name__=='__main__':main()
