"""Availability-only scan of public Apache main-branch CI jobs."""
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import argparse
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import urlopen

HOST='ci-builds.apache.org'
TREE='name,url,builds[number,url,timestamp,duration,building,actions[_class,lastBuiltRevision[SHA1,branch[name]],revision[hash]]]{0,500}'


def get(url,tree):
    if urlparse(url).hostname!=HOST:raise ValueError('Unexpected CI host')
    with urlopen(url+'api/json?tree='+quote(tree,safe=',[]'),timeout=30) as response:
        raw=response.read(8*1024*1024+1)
    if len(raw)>8*1024*1024:raise ValueError('Metadata size limit')
    return raw,json.loads(raw)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='experiments/d092-ci-availability.json')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1];folder=root/'build/d092-main-ci'
    folder.mkdir(exist_ok=True)
    catalog=json.loads((folder/'root-jobs.json').read_text())['jobs']
    roots=[j for j in catalog if j['name'] in ['Jackrabbit','james','Kafka','Karaf']]
    candidates=[];errors=[]
    for parent in roots:
        _,data=get(parent['url'],'jobs[name,url,_class]')
        for job in data.get('jobs',[]):
            name=job['name'].lower()
            if 'multibranch' in job.get('_class','').lower():
                if any(x in name for x in ['website','site','-pr']):continue
                try:
                    _,children=get(job['url'],'jobs[name,url,_class]')
                    candidates.extend(j for j in children.get('jobs',[]) if j['name'] in ['main','master','trunk'])
                except Exception as error:errors.append({'url':job['url'],'error':str(error)[:200]})
            elif 'trunk' in name and '-pr' not in name and 'MavenModuleSet' in job.get('_class',''):
                candidates.append(job)
    def inspect(job):
        try:
            raw,data=get(job['url'],TREE)
            digest=sha256(raw).hexdigest();(folder/(digest+'.json')).write_bytes(raw)
            builds=[b for b in data.get('builds',[]) if not b.get('building') and b.get('duration',0)>0]
            identified=sum(any(a.get('lastBuiltRevision',{}).get('SHA1') or a.get('revision',{}).get('hash') for a in b.get('actions',[])) for b in builds)
            return {'url':job['url'],'name':data.get('name'),'completed_builds':len(builds),
                    'scm_identified_builds':identified,'metadata_sha256':digest}
        except Exception as error:return {'url':job['url'],'error':str(error)[:200]}
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(inspect,sorted(candidates,key=lambda j:j['url'])))
    eligible=[r for r in records if r.get('completed_builds',0)>=240 and r.get('scm_identified_builds',0)>=240]
    result={'scope':'Availability only; no build result/test outcome fields requested',
            'candidates':records,'discovery_errors':errors,
            'selected':eligible[0] if eligible else None,
            'pilot':'https://ci-builds.apache.org/job/Jackrabbit/job/jackrabbit-oak-trunk/' if not eligible else None}
    output=root/args.out
    with output.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print('Candidates:',len(records),'availability-qualified:',len(eligible))
    print([(r.get('name'),r.get('completed_builds'),r.get('scm_identified_builds')) for r in records])
    print('Selected:',result['selected'],'Pilot:',result['pilot'])


if __name__=='__main__':main()
