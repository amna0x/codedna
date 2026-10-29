"""Check pinned inventory identities/counts without interpreting failure labels."""
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import zipfile


def inspect(raw):
    if len(raw) > 1024*1024:
        raise ValueError('Compressed inventory exceeds limit')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.namelist() != ['test_class.csv']:
            raise ValueError('Unexpected nested inventory structure')
        if archive.getinfo('test_class.csv').file_size > 16*1024*1024:
            raise ValueError('Expanded inventory exceeds limit')
        rows = list(csv.DictReader(io.TextIOWrapper(archive.open('test_class.csv'), encoding='utf-8')))
    names = [r['testclass'] for r in rows]
    if not names or len(set(names)) != len(names) or any(not name for name in names):
        raise ValueError('Empty or duplicate class inventory')
    for row in rows:
        duration = float(row['duration'])
        if not math.isfinite(duration) or duration < 0:
            raise ValueError('Invalid historical duration')
    return len(names)


def main():
    root = Path(__file__).resolve().parents[1]
    folder = root/'build/d088-inputs'
    cohort = json.loads((root/'experiments/brake-cohort-d089.json').read_text())
    manifest = json.loads((folder/'lrts-inventory-manifest.json').read_text())
    members = {r['member']: r for r in manifest['members']}
    with (folder/'lrts-dataset.csv').open(newline='', encoding='utf-8') as stream:
        expected = {(r['pr_name'], r['build_id'], r['stage_id']): int(r['num_pass_class'])+int(r['num_fail_class'])
                    for r in csv.DictReader(stream) if r['project']=='activemq'}
    results = []
    for build in cohort['builds']:
        for job in build['jobs']:
            name = 'long_running_test_suites/processed_test_result/activemq/'+job['pr_name']+'_build'+job['build_id']+'/stage_'+job['stage_id']+'/test_class.csv.zip'
            member = members[name]
            raw = (folder/'lrts-inventories'/(member['sha256']+'.zip')).read_bytes()
            if sha256(raw).hexdigest() != member['sha256']:
                raise ValueError('Inventory fingerprint changed')
            count = inspect(raw)
            results.append({'head': build['head'], 'split': build['split'], 'member': name,
                'sha256': member['sha256'], 'classes': count,
                'matches_published_executed_count': count == expected[(job['pr_name'],job['build_id'],job['stage_id'])]})
    result = {'scope': 'Inventory integrity/counts only; failure labels not interpreted. Published executed counts do not establish absence of skipped tests.',
              'jobs': results, 'all_counts_match': all(r['matches_published_executed_count'] for r in results)}
    out = root/'experiments/results/brake-inventories-d089-2026-10-29.json'
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Jobs verified:',len(results),'All published executed counts match:',result['all_counts_match'])


if __name__ == '__main__':
    main()
