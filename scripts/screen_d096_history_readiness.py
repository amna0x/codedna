"""Optimistic historical readiness bound; synthetic assumptions are never outcomes."""
import json
from pathlib import Path
from codedna.selection.validation import validate_outcomes


def readiness(build,builds,available):
    # Deliberately optimistic: no source mismatch, skips, reruns or missing module
    # reports are deducted. Real usable evidence can only be smaller.
    prior={b['commit'] for b in builds if b['number'] in available and b['finished']<=build['started'] and b['commit']!=build['commit']}
    n=len(prior)
    bound=validate_outcomes([(1,1,0)]*n,.05)
    crc_floor=1/(n+1)
    return {'optimistic_prior_unique_commits':n,'base_has_available_completed_root_report':build['parent'] in prior,
            'optimistic_b10_zero_miss_bound':bound.miss_upper_bound,
            'optimistic_crc_resolution_floor':crc_floor,
            'can_meet_either_gate_even_optimistically':bound.accepted or (n>=19 and crc_floor<=.05),
            'interpretation':'All prior root reports hypothetically assigned to audit with one failure and zero misses; not measured model outcomes'}


def main():
    root=Path(__file__).resolve().parents[1];results=root/'experiments/results'
    manifest=json.loads((root/'experiments/d092-main-ci-pilot.json').read_text())
    records=json.loads((results/'rolling-main-ci-d092-corrected-2026-10-29/records.json').read_text())
    available={r['build'] for r in records if r['complete_as_published']}
    screen=json.loads((results/'module-compatibility-d095-2026-10-30.json').read_text())
    raw=json.loads((results/'rolling-main-ci-d092-corrected-2026-10-29/report-3012.json').read_text())
    modules=sorted(r['inferred_module'] for r in screen['children'] if r['exact_single_module_default_match']
                   and raw['childReports'][r['child_index']]['result']['skipCount']==0)
    decisions=[{'module':module,'build':b['number'],**readiness(b,manifest['builds'],available)} for module in modules for b in manifest['builds']]
    output={'modules':modules,'targets':len(decisions),'available_root_reports':len(available),
            'optimistically_gate_feasible_targets':sum(d['can_meet_either_gate_even_optimistically'] for d in decisions),
            'targets_with_completed_base_root_report':sum(d['base_has_available_completed_root_report'] for d in decisions),
            'maximum_optimistic_prior':max(d['optimistic_prior_unique_commits'] for d in decisions),
            'decisions':decisions,'source_history_analysis_performed':False,'models_fitted':0,
            'reason':'Even the optimistic upper bound is insufficient; expensive source histories cannot change that fact.',
            'limits':['Current module candidate availability was inspected; this is a feasibility screen, not prospective efficacy.',
                      'No hypothetical outcomes may be imported into training or presented as real failures.',
                      'Does not establish model performance, actual recall, missed failures or CI savings.']}
    with (results/'module-history-readiness-d096-2026-10-30.json').open('x',encoding='utf-8',newline='\n') as stream:json.dump(output,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in output.items() if k not in ['decisions','modules','limits']}))


if __name__=='__main__':main()
