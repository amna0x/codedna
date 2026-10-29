"""Freeze four larger cohorts from identity/timestamp availability only."""
import csv
from hashlib import sha256
import json
from pathlib import Path

from prepare_d089_brake_cohort import FIELDS

TARGETS = {'hadoop': ('trunk','apache/hadoop'), 'hive': ('master','apache/hive'),
           'jackrabbit-oak': ('trunk','apache/jackrabbit-oak'), 'kafka': ('trunk','apache/kafka')}


def choose(rows, project, branch, maximum=2000):
    groups = {}
    for row in rows:
        if row['project']==project and row['pr_base_branch']==branch:
            groups.setdefault(row['build_head_sha'], []).append(row)
    builds = []
    for head, jobs in groups.items():
        first = min(jobs, key=lambda r:(float(r['build_timestamp']),r['build_id']))
        earliest = [r for r in jobs if r['build_id']==first['build_id'] and r['pr_name']==first['pr_name']]
        builds.append({'head':head,'timestamp':float(first['build_timestamp']),
                       'jobs':sorted(earliest,key=lambda r:r['stage_id']),
                       'excluded_later_rerun_rows':len(jobs)-len(earliest)})
    builds.sort(key=lambda b:(b['timestamp'],b['head']))
    selected = builds[:maximum]
    a = int(len(selected)*.6)
    b = a+int(len(selected)*.2)
    for i,build in enumerate(selected):
        build['split']='train' if i<a else 'audit' if i<b else 'evaluation'
    return selected, len(builds)


def main():
    root=Path(__file__).resolve().parents[1]
    path=root/'build/d088-inputs/lrts-dataset.csv'
    provenance=json.loads((root/'build/d088-inputs/lrts-metadata-provenance.json').read_text())
    if sha256(path.read_bytes()).hexdigest()!=provenance['sha256']:
        raise ValueError('Pinned metadata changed')
    with path.open(newline='',encoding='utf-8') as stream:
        rows=[{key:row[key] for key in FIELDS} for row in csv.DictReader(stream)]
    output=root/'experiments/d091-cohorts'
    output.mkdir(exist_ok=False)
    for project,(branch,repo) in TARGETS.items():
        builds,total=choose(rows,project,branch)
        manifest={'protocol':'docs/RESEARCH_EVALUATION_D091.md','project':project,'branch':branch,
            'repository':'https://github.com/'+repo+'.git','metadata_sha256':provenance['sha256'],
            'available_distinct_heads':total,'selected_heads':len(builds),
            'status':'candidate_only' if len(builds)>=500 else 'insufficient_availability',
            'counts':{s:sum(b['split']==s for b in builds) for s in ['train','audit','evaluation']},
            'builds':builds}
        with (output/(project+'.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(manifest,stream,indent=2);stream.write('\n')
        print(project,'available:',total,'selected:',len(builds),manifest['counts'],flush=True)


if __name__=='__main__':main()
