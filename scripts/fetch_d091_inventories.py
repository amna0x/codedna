"""Acquire frozen larger-cohort raw inventories without interpreting labels."""
import importlib.util
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import urlencode
import zipfile

from inspect_lrts_archive import DownloadForm


def main():
    root=Path(__file__).resolve().parents[1]
    folder=root/'build/d091-inputs'
    folder.mkdir(exist_ok=True)
    form=DownloadForm()
    form.feed((root/'build/d088-inputs/lrts-download-page.html').read_text())
    if form.action!='https://drive.usercontent.google.com/download':raise ValueError('Unexpected source host')
    spec=importlib.util.spec_from_file_location('ranges',root/'scripts/fetch_rtptorrent_subset.py')
    ranges=importlib.util.module_from_spec(spec);spec.loader.exec_module(ranges)
    ranges.URL=form.action+'?'+urlencode(form.fields)
    class BudgetZip(ranges.RemoteZip):
        origin=0
        def _range_bytes(self,start,end):
            if self.downloaded-self.origin+end-start+1>256*1024*1024:
                raise ValueError('Prespecified 256 MiB project range budget reached')
            return super()._range_bytes(start,end)
        def read(self,n=-1):
            n=min(self.length-self.position,n if n>=0 else self.length-self.position)
            if n<=0:return b''
            start,end=self.position,self.position+n-1
            block=256*1024  # Avoid 4 MiB overfetch for tiny, scattered class ZIPs.
            key=start//block
            if n<=block and key==end//block:
                if key not in self.cache:
                    first,last=key*block,min(self.length-1,(key+1)*block-1)
                    self.cache[key]=self._range_bytes(first,last)
                    self.downloaded+=len(self.cache[key])
                    while len(self.cache)>2:self.cache.popitem(last=False)
                data=self.cache[key][start-key*block:end-key*block+1]
            else:
                data=self._range_bytes(start,end);self.downloaded+=len(data)
            if len(data)!=n:raise ValueError('Short archive range')
            self.position+=n
            return data
    destination=folder/'inventories'
    destination.mkdir(exist_ok=True)
    with BudgetZip() as remote,zipfile.ZipFile(remote) as archive:
        if remote.length!=3016466104:raise ValueError('Archive length changed')
        for project in ['hadoop','hive','jackrabbit-oak','kafka']:
            cohort_path=root/'experiments/d091-cohorts'/(project+'.json')
            cohort=json.loads(cohort_path.read_text())
            names={'long_running_test_suites/processed_test_result/'+project+'/'+j['pr_name']+'_build'+j['build_id']+'/stage_'+j['stage_id']+'/test_class.csv.zip'
                   for b in cohort['builds'] for j in b['jobs']}
            known=set(archive.namelist())
            missing=[{'member':name,'reason':'Member absent from frozen public archive'} for name in sorted(names-known)]
            names=sorted(names & known,key=lambda name:archive.getinfo(name).header_offset)
            records=[];remote.origin=remote.downloaded
            report_path=folder/(project+'-inventories.json')
            if report_path.exists():
                previous=json.loads(report_path.read_text())
                if previous['cohort_sha256']!=sha256(cohort_path.read_bytes()).hexdigest():raise ValueError('Cohort changed')
                if 'project_range_bytes' in previous:
                    saved=folder/(project+'-inventories-prior-acquisition.json')
                    if not saved.exists():saved.write_bytes(report_path.read_bytes())
                previous={r['member']:r for r in previous['members']}
            else:previous={}
            for index,name in enumerate(names):
                if name in previous:
                    record=previous[name]
                    raw=(destination/(record['sha256']+'.zip')).read_bytes()
                    if sha256(raw).hexdigest()!=record['sha256']:raise ValueError('Cached inventory changed')
                    records.append(record)
                    continue
                info=archive.getinfo(name)
                if info.file_size>1024*1024:
                    missing.append({'member':name,'reason':'Member exceeds 1 MiB size bound'});continue
                try:raw=archive.read(info)
                except ValueError as error:
                    if 'range budget' not in str(error):raise
                    missing.extend({'member':n,'reason':str(error)} for n in names[index:]);break
                digest=sha256(raw).hexdigest()
                target=destination/(digest+'.zip')
                if target.exists():
                    if target.read_bytes()!=raw:raise ValueError('Cache hash collision')
                else:target.write_bytes(raw)
                records.append({'member':name,'sha256':digest,'bytes':len(raw),'crc32':info.CRC})
                if index%100==0:
                    print(project,'inventories',index+1,'/',len(names),flush=True)
                    report_path.write_text(json.dumps({'project':project,'cohort_sha256':sha256(cohort_path.read_bytes()).hexdigest(),
                        'members':records,'unavailable':missing,'scope':'Raw acquisition only; outcomes uninterpreted'},indent=2)+'\n')
            result={'project':project,'cohort_sha256':sha256(cohort_path.read_bytes()).hexdigest(),
                'archive_bytes':remote.length,'project_range_bytes':remote.downloaded-remote.origin,
                'members':records,'unavailable':missing,'scope':'Raw acquisition only; no outcomes interpreted; whole-archive hash not verified'}
            report_path.write_text(json.dumps(result,indent=2)+'\n')
            print(project,'DONE inventories',len(records),'unavailable',len(missing),flush=True)


if __name__=='__main__':main()
