"""Final bounded availability search; no test outcomes requested or tuned."""
import gzip
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import quote,urlparse
from urllib.request import urlopen

ROOTS=['ActiveMQ','Artemis','Commons','HttpComponents','Jena','PDFBox','POI','Tika']
TREE='name,url,builds[number,url,timestamp,duration,building,actions[lastBuiltRevision[SHA1,branch[name]],revision[hash]]]{0,500}'


def main():
    root=Path(__file__).resolve().parents[1]
    out=root/'experiments/results/final-availability-d097-2026-10-30';out.mkdir(exist_ok=False)
    snapshots=out/'inputs';snapshots.mkdir();receipts=[];errors=[];requests=0
    def get(url,tree):
        nonlocal requests
        if requests>=100:raise ValueError('Fixed 100-request search budget exhausted')
        if urlparse(url).hostname!='ci-builds.apache.org':raise ValueError('Unexpected host')
        requests+=1;target=url+'api/json?tree='+quote(tree,safe=',[]')
        with urlopen(target,timeout=15) as response:raw=response.read(8*1024*1024+1)
        if len(raw)>8*1024*1024:raise ValueError('Metadata byte limit')
        digest=sha256(raw).hexdigest();path=snapshots/(digest+'.json.gz')
        if not path.exists():path.write_bytes(gzip.compress(raw,mtime=0))
        receipts.append({'url':target,'sha256':digest,'bytes':len(raw),'file':'inputs/'+path.name})
        return json.loads(raw)
    catalog=json.loads((root/'build/d092-main-ci/root-jobs.json').read_text())['jobs']
    candidates=[];nested=[]
    for name in ROOTS:
        parent=next(j for j in catalog if j['name']==name)
        try:
            data=get(parent['url'],'jobs[name,url,_class]')
            for job in data.get('jobs',[]):
                lower=job['name'].lower()
                if any(n in lower for n in ['website','-pr','pull-request']):continue
                if 'multibranch' in job.get('_class','').lower():nested.append(job)
                elif 'MavenModuleSet' in job.get('_class','') and any(n in lower for n in ['trunk','master','main']):candidates.append(job)
        except Exception as e:errors.append({'url':parent['url'],'error':str(e)[:200]})
    for job in sorted(nested,key=lambda j:j['url'])[:30]:
        try:
            data=get(job['url'],'jobs[name,url,_class]')
            candidates.extend(j for j in data.get('jobs',[]) if j['name'] in ['main','master','trunk'])
        except Exception as e:errors.append({'url':job['url'],'error':str(e)[:200]})
    records=[]
    unique={j['url']:j for j in candidates}
    for url,job in sorted(unique.items())[:60]:
        try:
            data=get(url,TREE);builds=[b for b in data.get('builds',[]) if not b.get('building') and b.get('duration',0)>0]
            identified=sum(any(a.get('lastBuiltRevision',{}).get('SHA1') or a.get('revision',{}).get('hash') for a in b.get('actions',[])) for b in builds)
            records.append({'url':url,'completed':len(builds),'scm_identified':identified,'availability_qualified':len(builds)>=240 and identified>=240})
        except Exception as e:errors.append({'url':url,'error':str(e)[:200]})
    result={'roots':ROOTS,'request_limit':100,'requests':requests,'nested_discovered':len(nested),'nested_inspected':min(len(nested),30),
            'candidate_jobs_discovered':len(unique),'candidates':records,'errors':errors,'inputs':receipts,
            'availability_qualified':[r for r in records if r['availability_qualified']],
            'rule':'At least 240 completed SCM-identified builds; no outcomes requested. Qualification alone still needs report/source/lineage verification.',
            'scope':'Finite public Apache search, not proof no suitable dataset exists elsewhere.'}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['inputs','candidates','errors']}),flush=True)


if __name__=='__main__':main()
