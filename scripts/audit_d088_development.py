"""Verify published failing-to-passing evidence for development cases only."""
from hashlib import sha256
import json
from pathlib import Path


def outcomes(stage):
    result = {}
    for run in stage:
        for test in run['tests']:
            key = test['classname']+'#'+test['name']
            statuses = {entry['result'] for entry in test['results']}
            result.setdefault(key, set()).update(statuses)
    return result


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root/'experiments/moonshot-real-bug-selection-d088.json').read_text())
    reports = []
    for case in manifest['cases']:
        if case['split'] != 'development':
            continue
        raw = (root/'build/d088-inputs/gitbug-java/data/bugs'/case['metadata_file']).read_bytes()
        if sha256(raw).hexdigest() != case['metadata_sha256']:
            raise ValueError('Pinned metadata changed')
        row = json.loads(raw.decode('utf-8').splitlines()[case['metadata_line']-1])
        stages = row['actions_runs']
        before = outcomes(stages[0 if row['strategy'] == 'FAIL_PASS' else 1])
        after = outcomes(stages[2])
        failed = {test for test, status in before.items() if status & {'Failure', 'Error'}}
        fixed = sorted(test for test in failed if after.get(test) == {'Passed'})
        reports.append({'repository': case['repository'], 'fix': case['commit_hash'],
            'strategy': row['strategy'], 'published_failing_tests': len(failed),
            'published_failing_to_passing_tests': fixed,
            'source_changes': [line for line in row['bug_patch'].splitlines()
                               if line.startswith('diff --git')],
            'scope': 'Published test evidence only; no local reproduction or Moonshot detection claim'})
    output = root/'build/d088-inputs/development-oracle-audit.json'
    output.write_text(json.dumps(reports, indent=2)+'\n')
    print('Development cases:',len(reports),'with published failing-to-passing evidence:',
          sum(bool(r['published_failing_to_passing_tests']) for r in reports))
    print('Held-out test outcomes were not audited.')


if __name__ == '__main__':
    main()
