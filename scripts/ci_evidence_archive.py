"""Immutable public-CI evidence archive; no model calls, builds or AI requests."""
import argparse
import gzip
from hashlib import sha256
import json
from pathlib import Path
from time import time, time_ns, sleep
from urllib.error import HTTPError
from urllib.parse import quote, urlparse
from urllib.request import urlopen

from discover_d092_ci import TREE as METADATA_TREE
from run_d092_main_ci import TREE as REPORT_TREE

JOB='https://ci-builds.apache.org/job/Jackrabbit/job/jackrabbit-oak-trunk/'


class Archive:
    def __init__(self,path,job=JOB):
        self.path=Path(path);self.job=job
        if urlparse(job).hostname!='ci-builds.apache.org' or not job.endswith('/'):
            raise ValueError('Only the configured public CI host is supported')
        for name in ['objects','events']:(self.path/name).mkdir(parents=True,exist_ok=True)
        binding=self.path/'binding.json'
        if binding.exists():
            if json.loads(binding.read_text())['job']!=job:raise ValueError('Archive is bound to another CI job')
        else:binding.write_bytes((json.dumps({'job':job,'schema':1})+'\n').encode())

    def events(self):
        return [json.loads(p.read_text()) for p in sorted((self.path/'events').glob('*.json'))]

    def record(self,url,status,raw,role,commit=None,note=None):
        if not url.startswith(self.job):raise ValueError('Response origin differs from bound job')
        digest=sha256(raw).hexdigest();target=self.path/'objects'/(digest+'.gz')
        if target.exists():
            if sha256(gzip.decompress(target.read_bytes())).hexdigest()!=digest:raise ValueError('Corrupted archive object')
        else:
            with target.open('xb') as stream:stream.write(gzip.compress(raw,mtime=0))
        event={'url':url,'status':status,'role':role,'bound_commit':commit,'object_sha256':digest,
               'bytes':len(raw),'observed_at':time(),'note':note,
               'availability_note':'Observed at this timestamp; historical publication time is not inferred'}
        with (self.path/'events'/(str(time_ns())+'-'+digest[:12]+'.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(event,stream,indent=2);stream.write('\n')
        return event


def fetch(url):
    if urlparse(url).hostname!='ci-builds.apache.org':raise ValueError('Unexpected report host')
    try:
        with urlopen(url,timeout=45) as response:
            raw=response.read(32*1024*1024+1)
            if len(raw)>32*1024*1024:raise ValueError('Response size limit')
            return response.status,raw,None
    except HTTPError as error:return error.code,b'',str(error)


def collect(archive,get=fetch,retry_missing=False):
    url=archive.job+'api/json?tree='+quote(METADATA_TREE,safe=',[]')
    status,raw,error=get(url);archive.record(url,status,raw,'metadata',note=error)
    if status!=200:return {'metadata_error':status}
    data=json.loads(raw);old=archive.events();saved=0;skipped=0;errors=0
    for build in sorted(data.get('builds',[]),key=lambda b:b['number']):
        if build.get('building') or build.get('duration',0)<=0:continue
        revisions={a.get('lastBuiltRevision',{}).get('SHA1') or a.get('revision',{}).get('hash')
                   for a in build.get('actions',[])}-{None}
        commit=next(iter(revisions)) if len(revisions)==1 else None
        target=build['url']+'testReport/api/json?tree='+quote(REPORT_TREE,safe=',[]')
        matching=[e for e in old if e['role']=='report' and e['url']==target and e['bound_commit']==commit]
        if matching and (any(e['status']==200 for e in matching) or not retry_missing):
            skipped+=1;continue
        status,payload,error=get(target)
        archive.record(target,status,payload,'report',commit,error);saved+=1;errors+=status!=200
    return {'new_report_observations':saved,'already_archived':skipped,'report_errors':errors}


def seed(archive,root):
    manifest=json.loads((root/'experiments/d092-main-ci-pilot.json').read_text())
    if manifest['job']!=archive.job:raise ValueError('Seed job mismatch')
    source=root/'experiments/results/rolling-main-ci-d092-corrected-2026-10-29'
    inputs=json.loads((source/'input-manifest.json').read_text())
    old=archive.events()
    for item in inputs:
        if item['role']=='availability_metadata' and item['url']!=archive.job:continue
        raw=gzip.decompress((source/item['compressed_file']).read_bytes())
        if sha256(raw).hexdigest()!=item['raw_sha256']:raise ValueError('Seed hash mismatch')
        if item['role']=='public_ci_report':
            number=int(item['original_name'].removeprefix('report-').removesuffix('.json'))
            build=next(b for b in manifest['builds'] if b['number']==number)
            url=build['url']+'testReport/api/json?tree='+quote(REPORT_TREE,safe=',[]');role='report';commit=build['commit']
        else:
            url=archive.job+'api/json?tree='+quote(METADATA_TREE,safe=',[]');role='metadata';commit=None
        if any(e['url']==url and e['object_sha256']==item['raw_sha256'] for e in old):continue
        archive.record(url,200,raw,role,commit,'Imported inspected D092 snapshot; not new independent evidence')
    previous=json.loads((source/'records.json').read_text())
    for row in previous:
        if row['complete_as_published'] or '404' not in str(row['report_limitation']):continue
        build=next(b for b in manifest['builds'] if b['number']==row['build'])
        url=build['url']+'testReport/api/json?tree='+quote(REPORT_TREE,safe=',[]')
        if any(e['url']==url and e['status']==404 for e in old):continue
        archive.record(url,404,b'','report',build['commit'],'Imported original D092 unavailable report; no pass inferred')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--seed-d092',action='store_true')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--interval',type=int,default=21600)
    parser.add_argument('--retry-missing',action='store_true')
    args=parser.parse_args()
    if args.interval<3600:parser.error('Use an interval of at least one hour')
    archive=Archive(args.store)
    if args.seed_d092:seed(archive,Path(__file__).resolve().parents[1])
    while True:
        try:print(json.dumps(collect(archive,retry_missing=args.retry_missing)),flush=True)
        except Exception as error:
            print(json.dumps({'collector_error':str(error)[:400]}),flush=True)
            if not args.watch:raise SystemExit(1)
        if not args.watch:break
        sleep(args.interval)


if __name__=='__main__':main()
