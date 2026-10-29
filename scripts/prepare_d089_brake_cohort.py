"""Revise an ActiveMQ cohort from availability only; never read outcome columns."""
import csv
from hashlib import sha256
import json
from pathlib import Path

FIELDS = ['project', 'pr_name', 'pr_base_branch', 'build_id', 'build_timestamp',
          'build_head_sha', 'trunk_sha', 'trunk_sha_source', 'stage_id']


def choose(rows):
    # Project/base branch fixed before opening outcome columns. A common target
    # branch does not prove ancestry; this output explicitly leaves it unvalidated.
    rows = [r for r in rows if r['project'] == 'activemq' and r['pr_base_branch'] == 'main']
    grouped = {}
    for row in rows:
        key = row['build_head_sha']
        grouped.setdefault(key, []).append(row)
    builds = []
    for head, jobs in grouped.items():
        first = min(jobs, key=lambda r: (float(r['build_timestamp']), r['build_id']))
        same_build = [r for r in jobs if r['build_id'] == first['build_id']
                      and r['pr_name'] == first['pr_name']]
        builds.append({'head': head, 'timestamp': float(first['build_timestamp']),
                       'jobs': sorted(same_build, key=lambda r: r['stage_id']),
                       'excluded_later_rerun_rows': len(jobs)-len(same_build)})
    builds.sort(key=lambda r: (r['timestamp'], r['head']))
    if len(builds) < 200:
        raise ValueError('Fewer than 200 distinct main-target builds; stop this candidate')
    train, audit = int(len(builds)*0.6), int(len(builds)*0.2)
    for index, build in enumerate(builds):
        build['split'] = 'train' if index < train else 'audit' if index < train+audit else 'evaluation'
        build['ancestry_status'] = 'unverified_do_not_authorize_skipping'
        build['inventory_status'] = 'unverified'
    return builds


def main():
    root = Path(__file__).resolve().parents[1]
    path = root/'build/d088-inputs/lrts-dataset.csv'
    # Project away outcomes as records are parsed; selection uses identities/time.
    with path.open(newline='', encoding='utf-8') as stream:
        rows = [{key: row[key] for key in FIELDS} for row in csv.DictReader(stream)]
    builds = choose(rows)
    result = {'protocol': 'docs/RESEARCH_EVALUATION_D089.md',
        'metadata_sha256': sha256(path.read_bytes()).hexdigest(),
        'scope': 'Outcome-blind candidate selection, not eligibility or evaluation',
        'counts': {s: sum(b['split'] == s for b in builds) for s in ['train', 'audit', 'evaluation']},
        'builds': builds}
    out = root/'experiments/brake-cohort-d089.json'
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print('Candidate split:',result['counts'],'Ancestry and inventories remain unverified.')


if __name__ == '__main__':
    main()
