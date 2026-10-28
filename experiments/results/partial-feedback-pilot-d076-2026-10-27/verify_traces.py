"""Verify saved pilot traces against reference truth; never rerun selection/model fitting."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

from codedna.test_history.features import Dataset

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'experiments/results/partial-feedback-pilot-d076-2026-10-27'


def canonical(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def save(name, value):
    path = OUT / name
    if path.exists():
        assert json.loads(path.read_text(encoding='utf-8')) == value, f'existing summary differs: {path}'
        return
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n', encoding='utf-8', newline='\n')


protocol = json.loads((ROOT/'docs/PARTIAL_FEEDBACK_PILOT_D076.json').read_text())
manifest = json.loads((OUT/'manifest.json').read_text())
result = json.loads((OUT/'results.json').read_text())
assert result['binding'] == manifest['binding']
assert manifest['binding']['protocol_sha256'] == canonical(protocol)
for key in ['dataset', 'database']:
    assert hashlib.sha256((ROOT/Path(protocol[key].replace('\\', '/'))).read_bytes()).hexdigest() == protocol[key+'_sha256']
data = Dataset.from_csv(ROOT/Path(protocol['dataset'].replace('\\', '/')))
commits = data.commits[:360]
groups = data.rows_by_commit()
plans = {}
prior = set()
for i, commit in enumerate(commits):
    value = json.loads((OUT/'plans'/f'{i:04d}-{commit}.json').read_text())
    payload = value['payload']; binding = value['binding']; report = payload['report']
    assert canonical(payload) == value['payload_sha256']
    assert all(binding[key] == expected for key, expected in manifest['binding'].items())
    assert binding['commit'] == commit
    assert binding['strategy'] == ('all' if i < 240 else 'dependency')
    universe = {row.test_id for row in groups[commit]}
    chosen = {item['test'] for item in report['selected']}
    assert chosen | set(report['skipped']) == universe
    assert not chosen & set(report['skipped'])
    assert report['total_tests'] == len(universe)
    assert set(payload['eligible_history']) <= prior
    assert set(report['policy']['pinned']) <= universe
    plans[commit] = payload
    prior.add(commit)
assert len(list((OUT/'plans').glob('*.json'))) == 360
summary = {}
for name, output in result['policies'].items():
    trace = output['trace']; metrics = output['metrics']
    assert [row['commit'] for row in trace] == commits
    cost = 0.; failures = missed = escapes = safe = reduced = complete = audits = 0
    eval_cost = eval_reference = 0.
    for i, row in enumerate(trace):
        truth = {r.test_id: r for r in groups[row['commit']]}
        selected = set(row['selected']); universe = set(truth)
        assert len(selected) == len(row['selected'])
        failed = {test for test, actual in truth.items() if actual.label}
        omitted = failed-selected
        audit = i >= 240 and (i-240+1) % 10 == 0
        assert row['index'] == i and row['evaluation'] == (i >= 240)
        assert selected <= universe
        assert row['scheduled_audit'] == audit
        if i < 240 or audit: assert selected == universe
        if name in ['structural', 'combined']:
            assert {x['test'] for x in plans[row['commit']]['report']['selected']} <= selected
        assert set(plans[row['commit']]['report']['policy']['pinned']) <= selected
        expected_cost = math.fsum(truth[test].duration for test in selected)
        reference_cost = math.fsum(t.duration for t in truth.values())
        assert math.isclose(row['test_seconds'], expected_cost, abs_tol=1e-9)
        assert math.isclose(row['reference_seconds'], reference_cost, abs_tol=1e-9)
        assert row['missed_classes'] == len(omitted)
        assert row['build_escape'] == bool(failed and not failed & selected)
        cost += expected_cost; complete += selected == universe
        if i >= 240:
            failures += bool(failed); safe += bool(failed) and not omitted
            missed += len(omitted); escapes += bool(failed and not failed & selected)
            reduced += selected != universe; audits += audit
            eval_cost += expected_cost; eval_reference += reference_cost
    assert (failures, safe, missed, escapes, reduced, audits, complete) == (
        metrics['failing_commits'], metrics['zero_omission_safe_commits'], metrics['missed_classes'],
        metrics['build_escape_commits'], metrics['reduced_suite_commits'], metrics['scheduled_audits'],
        metrics['complete_observation_commits'])
    assert math.isclose(cost, metrics['recorded_test_seconds_including_warmup'], abs_tol=1e-8)
    assert math.isclose(eval_cost, metrics['recorded_evaluation_test_seconds'], abs_tol=1e-8)
    evaluation = [row for row in trace if row['evaluation']]
    summary[name] = {'metrics': metrics,
        'evaluation_status_counts': dict(Counter(row['status'] for row in evaluation)),
        'refusal_reason_counts': dict(Counter(row['evidence'].get('reason', '') for row in evaluation if row['status']=='unvalidated_full')),
        'recorded_evaluation_savings_fraction': 1-eval_cost/eval_reference,
        'trace_canonical_sha256': canonical(trace)}
qa = {'schema_version': 1, 'date': '2026-10-27', 'classification': protocol['classification'],
    'protocol_commit': '1965665', 'engine_source_checkpoint': '72e6043',
    'results_canonical_sha256': canonical(result), 'source_snapshots_verified': 360,
    'checks': ['input CSV/DB hashes unchanged', 'all mapping payload hashes and bindings',
        'exact reference/source universes', 'eligible history contains only earlier reference commits',
        'trace order and selected IDs', 'warmup and audit full-suite replacement', 'structural/policy floors',
        'missed classes and build escapes', 'recorded test seconds and aggregate counts'],
    'policies': summary, 'runtime_limits': [
        'Most source mapping overlapped full-suite/IDE/Graphify validation on an 8 GB laptop.',
        'One extraction exceeded 90 seconds. The unchanged-protocol retry resumed saved plans and completed.',
        'Measured function times exclude worker startup, failed attempts, dataset loading and checkpoint I/O.',
        'Full-suite analysis overhead was not separately timed on the evaluation snapshots.',
        'Recorded test seconds and local analysis wall times are not a measured CI wall-clock speedup.']}
save('summary.json', qa)
structural = summary['structural']['metrics']
findings = f'''# D-076 observation-isolated development pilot

**Verdict:** implementation/mapping verification completed; no demonstrated
risk-gated reduction. This is one development prefix of previously inspected
HikariCP data, not independent confirmation or a deployment safety guarantee.

Protocol v2 was frozen in `1965665` before evaluation. Engine/source checkpoint:
`72e6043`; full input/code fingerprints are in [manifest.json](manifest.json).
All 360 source snapshots matched the reference test universe exactly. The
pilot uses 240 common full-suite warm-up commits and 120 evaluation commits,
with a scheduled full audit every tenth evaluation commit (12 per policy).
Ancestry-scoped earlier observations alone enter features and fitting.

| Policy | Reduced evaluation suites | Failing commits with no omission | Missed failing classes | Recorded evaluation test seconds | Recorded seconds including warm-up |
|---|---:|---:|---:|---:|---:|
'''
for name in ['full','history','structural','combined']:
    m = summary[name]['metrics']
    findings += f"| {name} | {m['reduced_suite_commits']}/120 | {m['zero_omission_safe_commits']}/{m['failing_commits']} | {m['missed_classes']}/{m['failing_classes']} | {m['recorded_evaluation_test_seconds']:.3f} | {m['recorded_test_seconds_including_warmup']:.3f} |\n"
findings += f'''
Only three evaluation commits failed, with four failing class outcomes. No
policy had a build escape. There was one first-recorded failing class outcome
and three recurring outcomes; none was missed. These tiny denominators do not
establish 95% future safety or superiority.

## Why the risk gate refused reduction

History and combined each refused all 108 ordinary evaluation decisions; the
other 12 were scheduled full-suite audits. In their first prior audit, the
candidate missed six of 60 audit commits and seven of 11 failing class outcomes
(failure recall 36.36%, all-commit miss-rate upper bound 18.19%). Subsequent
refusals also included fewer than ten failure-bearing audit commits. Keep
these refusal criteria; removing them merely to obtain savings is not a fix.

Both gated policies therefore observed complete outcomes at all 360 commits.
This real-data pilot does **not** demonstrate the performance of a selectively
learning risk policy under feedback starvation. The synthetic mutation tests
exercise that isolation; this pilot verifies mapping, accounting and refusal.
Structural-only had 40 partial observations, but its decisions do not train a
history model. Do not present that as validation of partial-feedback ML.

## Cost and runtime

Structural-only saved 160.933 recorded evaluation test seconds (15.32%) and
7.78% including the common warm-up. It reduced 40/120 suites. Risk-gated history
and combined saved no recorded test seconds. Audits replace the reduced run;
no additional repeated executions are simulated. These costs include selected,
mandatory and warm-up test classes exactly once.

Measured structural-analysis function time was {structural['structural_analysis_seconds']:.3f} seconds
over the 120 evaluation snapshots. This exceeds the recorded test seconds saved,
but baseline discovery overhead was not separately timed, so it is not a
matched net-slowdown estimate. Most mapping overlapped other local validation.
Startup, failed attempts and checkpoint I/O are excluded. No net CI speedup is
established. Measure matched cold/warm analysis before claiming a speed benefit
or scaling this pilot into a large run.

An initial extraction at reference index 329 exceeded its unchanged 90-second
deadline. The retry reused 329 verified mappings and completed. [STOP.json](STOP.json)
retains that initial diagnostic; [progress.json](progress.json) is the newer
completed state. No source, threshold, input, cohort or outcome-driven setting
was changed to complete the retry.

## Evidence and next engineering work

[summary.json](summary.json) recomputes trace counts and recorded durations from
the original reference truth and verifies mapping hashes/floors/audit timing.
[results.json](results.json) contains the four complete policy traces. Original
studies and inputs remain unchanged. No analysed project was built in this pilot.

The source passed 591 tests with Maven/Gradle included and zero skips. This
supports software correctness, not a new scientific safety claim. Next: measure
and improve analysis overhead, then implement bounded per-operation cancellation
and progress. Keep B10 as default and CRC opt-in. Broader risk-gated effectiveness
remains unestablished; do not tune this prefix until a positive result appears.
'''
path = OUT/'FINDINGS.md'
if not path.exists(): path.write_text(findings, encoding='utf-8', newline='\n')
print('Verified all 360 saved mappings and four traces. Summary verified; no overwrite or selection/model rerun.')
