"""Finish fixed evaluation inputs with bounded concurrent ranges, not training data."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import struct
from threading import Lock
from urllib.parse import urlencode
import zipfile
import zlib

from inspect_lrts_archive import DownloadForm


def main():
    root=Path(__file__).resolve().parents[1];folder=root/'build/d091-inputs'
    cohort_path=root/'experiments/d091-cohorts/kafka.json'
    cohort=json.loads(cohort_path.read_text())
    form=DownloadForm();form.feed((root/'build/d088-inputs/lrts-download-page.html').read_text())
    if form.action!='https://drive.usercontent.google.com/download':raise ValueError('Unexpected host')
    spec=importlib.util.spec_from_file_location('ranges',root/'scripts/fetch_rtptorrent_subset.py')
    ranges=importlib.util.module_from_spec(spec);spec.loader.exec_module(ranges)
    ranges.URL=form.action+'?'+urlencode(form.fields)
    report_path=folder/'kafka-inventories.json';old=json.loads(report_path.read_text())
    if old['cohort_sha256']!=sha256(cohort_path.read_bytes()).hexdigest():raise ValueError('Cohort changed')
    archive_copy=folder/'kafka-inventories-before-evaluation-only.json'
    if not archive_copy.exists():archive_copy.write_bytes(report_path.read_bytes())
    records={r['member']:r for r in old['members']}
    expected={'long_running_test_suites/processed_test_result/kafka/'+j['pr_name']+'_build'+j['build_id']+'/stage_'+j['stage_id']+'/test_class.csv.zip'
              for b in cohort['builds'] if b['split']=='evaluation' for j in b['jobs']}
    lock=Lock();reserved=0;downloaded=0;errors=[]
    with ranges.RemoteZip() as remote,zipfile.ZipFile(remote) as archive:
        if remote.length!=3016466104:raise ValueError('Archive changed')
        infos=[archive.getinfo(name) for name in sorted(expected) if name not in records]
        def acquire(info):
            nonlocal reserved,downloaded
            if info.file_size>1024*1024:raise ValueError('Inventory exceeds size bound')
            start=info.header_offset
            end=min(remote.length-1,start+30+len(info.filename.encode('utf-8'))+65535+info.compress_size-1)
            with lock:
                if reserved+end-start+1>256*1024*1024:raise ValueError('Evaluation range budget reached')
                reserved+=end-start+1
            with remote._fetch(start,end) as response:chunk=response.read()
            with lock:downloaded+=len(chunk)
            if len(chunk)!=end-start+1 or chunk[:4]!=b'PK\x03\x04':raise ValueError('Invalid local ZIP range')
            header=struct.unpack('<4s5H3I2H',chunk[:30]);offset=30+header[-2]+header[-1]
            compressed=chunk[offset:offset+info.compress_size]
            if len(compressed)!=info.compress_size:raise ValueError('Incomplete ZIP member')
            if info.compress_type==zipfile.ZIP_STORED:raw=compressed
            elif info.compress_type==zipfile.ZIP_DEFLATED:raw=zlib.decompress(compressed,-15)
            else:raise ValueError('Unsupported archive compression')
            if len(raw)!=info.file_size or zlib.crc32(raw)&0xffffffff!=info.CRC:raise ValueError('Member CRC/size mismatch')
            digest=sha256(raw).hexdigest();target=folder/'inventories'/(digest+'.zip')
            with lock:
                if target.exists():
                    if target.read_bytes()!=raw:raise ValueError('Cache collision')
                else:target.write_bytes(raw)
            return {'member':info.filename,'sha256':digest,'bytes':len(raw),'crc32':info.CRC}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures={pool.submit(acquire,info):info.filename for info in infos}
            for index,future in enumerate(as_completed(futures),1):
                try:
                    record=future.result();records[record['member']]=record
                except Exception as error:errors.append({'member':futures[future],'reason':str(error)[:300]})
                if index%50==0:print('Kafka fixed evaluation acquisition:',index,'/',len(infos),flush=True)
        result={'project':'kafka','cohort_sha256':sha256(cohort_path.read_bytes()).hexdigest(),
            'members':list(records.values()),'unavailable':errors,
            'scope':'Fixed evaluation outcomes only after exact operational gate proof; remaining training acquisition intentionally omitted',
            'evaluation_members_expected':len(expected),'evaluation_members_present':sum(n in records for n in expected),
            'evaluation_range_bytes_this_attempt':downloaded,'directory_range_bytes':remote.downloaded}
        report_path.write_text(json.dumps(result,indent=2)+'\n')
        print('Kafka evaluation inventories present',result['evaluation_members_present'],'/',len(expected),'errors',len(errors),flush=True)


if __name__=='__main__':main()
