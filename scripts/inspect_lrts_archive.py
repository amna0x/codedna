"""Inspect public LRTS ZIP metadata by bounded HTTP ranges; execute no artifact code."""
import importlib.util
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import urlencode
import zipfile
import argparse
from hashlib import sha256


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = None
        self.fields = {}

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'form':
            self.action = attrs.get('action')
        if tag == 'input' and attrs.get('name'):
            self.fields[attrs['name']] = attrs.get('value', '')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-metadata', action='store_true')
    parser.add_argument('--fetch-activemq-inventories', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    folder = root/'build/d088-inputs'
    form = DownloadForm()
    form.feed((folder/'lrts-download-page.html').read_text(encoding='utf-8'))
    if form.action != 'https://drive.usercontent.google.com/download':
        raise ValueError('Unexpected public dataset download host')
    spec = importlib.util.spec_from_file_location('ranges', root/'scripts/fetch_rtptorrent_subset.py')
    ranges = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ranges)
    ranges.URL = form.action+'?'+urlencode(form.fields)

    class BoundedZip(ranges.RemoteZip):
        def _range_bytes(self, start, end):
            if self.downloaded+end-start+1 > 96*1024*1024:
                raise ValueError('Metadata inspection exceeded 96 MiB range budget')
            return super()._range_bytes(start, end)

    with BoundedZip() as remote, zipfile.ZipFile(remote) as archive:
        entries = [{'name': i.filename, 'bytes': i.file_size, 'compressed_bytes': i.compress_size}
                   for i in archive.infolist()]
        result = {'scope': 'Archive listing only, no test outcomes read',
                  'archive_bytes': remote.length, 'downloaded_bytes': remote.downloaded,
                  'entries': entries}
        (folder/'lrts-archive-listing.json').write_text(json.dumps(result, indent=2)+'\n')
        print('Archive bytes:',remote.length,'Range bytes:',remote.downloaded,'Entries:',len(entries))
        print('Metadata candidates:',[e for e in entries if e['name'].endswith('dataset.csv')][:5])
        if args.fetch_metadata:
            member = archive.getinfo('long_running_test_suites/dataset.csv')
            if member.file_size > 32*1024*1024:
                raise ValueError('Metadata exceeds its declared limit')
            raw = archive.read(member)  # ZipFile checks the selected entry CRC.
            with (folder/'lrts-dataset.csv').open('xb') as stream:
                stream.write(raw)
            provenance = {'source': 'LRTS public processed archive',
                'archive_bytes': remote.length, 'member': member.filename,
                'member_crc32': member.CRC, 'sha256': sha256(raw).hexdigest(),
                'bytes': len(raw), 'range_bytes': remote.downloaded,
                'whole_archive_checksum_verified': False,
                'scope': 'Downloaded metadata only; no CodeDNA evaluation'}
            (folder/'lrts-metadata-provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
            print('Metadata saved and CRC/SHA256 recorded. No full archive download.')
        if args.fetch_activemq_inventories:
            cohort = json.loads((root/'experiments/brake-cohort-d089.json').read_text())
            names = sorted({'long_running_test_suites/processed_test_result/activemq/'+
                job['pr_name']+'_build'+job['build_id']+'/stage_'+job['stage_id']+'/test_class.csv.zip'
                for build in cohort['builds'] for job in build['jobs']},
                key=lambda name: archive.getinfo(name).header_offset)
            destination = folder/'lrts-inventories'
            destination.mkdir(exist_ok=True)
            records = []
            for name in names:
                info = archive.getinfo(name)
                if info.file_size > 1024*1024:
                    raise ValueError('Inventory member exceeds 1 MiB bound')
                raw = archive.read(info)
                digest = sha256(raw).hexdigest()
                target = destination/(digest+'.zip')
                if target.exists():
                    if target.read_bytes() != raw:
                        raise ValueError('Cached inventory fingerprint mismatch')
                else:
                    target.write_bytes(raw)
                records.append({'member': name, 'sha256': digest, 'bytes': len(raw), 'crc32': info.CRC})
            (folder/'lrts-inventory-manifest.json').write_text(json.dumps({
                'scope': 'Uninterpreted raw inventory acquisition; evaluation outcomes not read',
                'range_bytes': remote.downloaded, 'members': records}, indent=2)+'\n')
            print('Pinned raw inventories:',len(records),'Range bytes:',remote.downloaded)


if __name__ == '__main__':
    main()
