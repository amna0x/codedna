"""Record every refused held-out trial and the completed source validation evidence."""
from hashlib import sha256
import json
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    source_audit = root/'build/d088-inputs/held-out-source-contract-d090.json'
    audit = json.loads(source_audit.read_text())
    if len(audit) != 12 or any(r['candidates'] or r['errors'] for r in audit):
        raise ValueError('This finalizer only handles the observed complete twelve-case refusal audit; execute eligible/error cases separately')
    out = root/'experiments/results/moonshot-held-out-d090-2026-10-29'
    out.mkdir(exist_ok=False)
    (out/'source-contract.json').write_bytes(source_audit.read_bytes())
    trials = []
    for index, case in enumerate(audit):
        for seed_index, seed in enumerate([7,19,41]):
            modes = ['guided','simple'] if (index+seed_index)%2==0 else ['simple','guided']
            for mode in modes:
                trials.append({'repository': case['repository'], 'mode': mode, 'seed': seed,
                    'status': 'unsupported_at_frozen_source_selection',
                    'reason': 'No changed same-identity method satisfies the frozen public bounded numeric/array contract',
                    'jvm_runs': 0, 'search_executed': False, 'search_seconds': None})
    (out/'trials.json').write_text(json.dumps(trials,indent=2)+'\n')
    summary = {'application_source': 'a02d20f', 'held_out_cases': 12,
        'cases_with_eligible_changed_method': 0, 'source_errors': 0,
        'planned_trial_records': len(trials), 'executed_searches': 0,
        'emitted_witnesses': 0, 'independently_replayed_witnesses': 0,
        'bug_detection_sensitivity': None, 'guided_superiority': None,
        'scope': 'Held-out source-selection coverage evaluation; refused trials are not executed search failures. No search efficacy estimate can be made.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    pointer = root.parents[1]
    log = pointer/'.diagnostics/d089-full-maven.log'
    exit_file = pointer/'.diagnostics/d089-full-maven.exit'
    if exit_file.read_text().strip() != '0' or '780 passed, 1 warning in 3919.80s' not in log.read_text():
        raise ValueError('Full validation completion was not verified')
    destination = root/'docs/validation-logs/d089-full-maven.log'
    destination.parent.mkdir(exist_ok=True)
    with destination.open('xb') as stream:
        stream.write(log.read_bytes())
    validation = {'source_commit': 'a02d20f4d36b451dd80b2948d5bdcc0a6620ecd7',
        'command': 'python -m pytest --run-maven -q', 'passed': 780,
        'failed': 0, 'skipped': 0, 'warnings': 1, 'seconds': 3919.80,
        'log': 'docs/validation-logs/d089-full-maven.log', 'log_sha256': sha256(log.read_bytes()).hexdigest(),
        'gradle_opts': '-Dorg.gradle.jvmargs= -Dorg.gradle.daemon=false',
        'scope': 'Complete source suite with Maven and real Gradle; no new frozen-executable/installer validation.',
        'prior_d087': 'Interrupted; never count as a completed pass'}
    (root/'docs/ENGINEERING_VALIDATION_D089_2026-10-29.json').write_text(json.dumps(validation,indent=2)+'\n')
    print(json.dumps(summary))
    print('Full validation log copied and SHA256 recorded.')


if __name__ == '__main__':
    main()
