"""Check the live brake's first-parent and latest-BASE requirements exactly."""
from hashlib import sha256
import json
from pathlib import Path

from codedna.git_analysis.git import run_git_bytes


def main():
    root=Path(__file__).resolve().parents[1]
    output=root/'experiments/results/larger-history-d091-2026-10-29'
    for project in ['hadoop','hive','jackrabbit-oak','kafka']:
        path=root/'experiments/d091-cohorts'/(project+'.json')
        cohort=json.loads(path.read_text())
        ancestry=json.loads((output/(project+'-ancestry.json')).read_text())
        missing=ancestry.get('unavailable_heads',{})
        heads=[b['head'] for b in cohort['builds'] if b['head'] not in missing]
        repo=root/'build/d091-inputs'/(project+'-ancestry.git')
        raw=run_git_bytes(repo,'rev-list','--parents','--stdin',stdin=('\n'.join(heads)+'\n').encode())
        parents={}
        for line in raw.decode().splitlines():
            node,*edges=line.split();parents[node]=edges
        historical={b['head']:b for b in cohort['builds'] if b['split']!='evaluation'}
        rows=[]
        for build in cohort['builds']:
            if build['split']!='evaluation':continue
            if build['head'] in missing:
                rows.append({'head':build['head'],'status':'exact_source_unavailable'});continue
            edges=parents.get(build['head'],[])
            base=edges[0] if edges else None
            chain=[];node=base;seen=set()
            while node and node not in seen:
                seen.add(node)
                if node in historical and historical[node]['timestamp']<build['timestamp']:
                    chain.append(node)
                edges=parents.get(node,[]);node=edges[0] if edges else None
            chain.reverse()
            current=bool(chain) and chain[-1]==base
            rows.append({'head':build['head'],'base':base,'first_parent_history':chain,
                'current_base_has_earlier_recorded_outcomes':current,
                'status':'requires_remaining_evidence_checks' if current else 'full_suite_required_missing_latest_base_history'})
        report={'project':project,'cohort_sha256':sha256(path.read_bytes()).hexdigest(),
                'scope':'Exact existing operational first-parent/latest-BASE check; no model or threshold change',
                'evaluation':rows}
        with (output/(project+'-operational-lineage.json')).open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(report,stream,indent=2);stream.write('\n')
        print(project,'evaluation',len(rows),'BASE-current first-parent histories',
              sum(r['status']=='requires_remaining_evidence_checks' for r in rows),flush=True)


if __name__=='__main__':main()
