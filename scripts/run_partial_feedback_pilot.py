"""Run the frozen D-076 development protocol without executing project code.

Every source plan is checkpointed before outcomes are evaluated. Mapping errors
stop the pilot rather than treating missing outcomes as passes.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.metadata
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from time import perf_counter

from codedna.git_analysis.git import run_git
from codedna.models.partial_feedback import (
    AuditedPolicy, FullPolicy, ReplayConfig, StructuralPlan, StructuralPolicy, run_replay,
)
from codedna.test_history.features import Dataset

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / 'docs/PARTIAL_FEEDBACK_PILOT_D076.json'
PROTOCOL_COMMIT = '1965665'


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')
    temp.replace(path)


def check_mapping(report, reference):
    selected = [item['test'] for item in report['selected']]
    skipped = report['skipped']
    discovered = set(selected) | set(skipped)
    if (discovered != set(reference) or len(selected) != len(set(selected))
            or len(skipped) != len(set(skipped)) or set(selected) & set(skipped)
            or report['total_tests'] != len(discovered)):
        raise ValueError(json.dumps({'error': 'reference/source universe mismatch',
            'reference_not_discovered': sorted(set(reference)-discovered),
            'discovered_without_outcome': sorted(discovered-set(reference)),
            'total_tests': report['total_tests'], 'reference_tests': len(reference)}))
    if not set((report.get('policy') or {}).get('pinned', [])) <= discovered:
        raise ValueError('policy pins contain unknown classes')


def checked_cache(path, binding):
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding='utf-8'))
    if value.get('binding') != binding or value.get('payload_sha256') != digest(value.get('payload')):
        raise ValueError(f'incompatible or damaged checkpoint: {path}')
    return value['payload']


def read_history(database, commits):
    # Do not use HistoryStore here: its constructor creates schema and metadata.
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        connection.execute('PRAGMA query_only=ON')
        metadata = dict(connection.execute('SELECT key,value FROM meta'))
        bases = dict(connection.execute('SELECT sha,parent FROM commits'))
        paths = {commit: tuple(row[0] for row in connection.execute(
            'SELECT path FROM changed_files WHERE sha=? ORDER BY path', (commit,))) for commit in commits}
    if any(not bases.get(commit) for commit in commits):
        raise ValueError('reference commit lacks recorded push base')
    return Path(metadata['repository']), {c: bases[c] for c in commits}, paths


def source_fingerprint():
    files = sorted([*ROOT.glob('backend/codedna/**/*.py'),
                    *ROOT.glob('plugins/codedna-java/codedna_java/**/*.py'), Path(__file__)])
    return {str(path.relative_to(ROOT)).replace('\\', '/'): file_hash(path) for path in files}


def source_plan(repo, base, head, strategy):
    from codedna.selection import select_tests
    started = perf_counter()
    report = select_tests(repo, base, head, strategy).to_dict()
    return {'report': report, 'analysis_seconds': perf_counter()-started}


def collect_plan(repo, base, head, strategy):
    # A bounded child protects the laptop from an unexpectedly slow snapshot.
    process = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--source-plan',
        str(repo), base, head, strategy], capture_output=True, text=True, timeout=90,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
    if process.returncode:
        raise ValueError(f'source extraction failed: {process.stderr[-4000:]}')
    return json.loads(process.stdout)


def run(out):
    protocol = json.loads(PROTOCOL.read_text(encoding='utf-8'))
    committed = json.loads(run_git(ROOT, 'show', f'{PROTOCOL_COMMIT}:docs/PARTIAL_FEEDBACK_PILOT_D076.json'))
    if protocol != committed:
        raise ValueError('protocol differs from frozen pre-evaluation commit')
    for key in ('dataset', 'database'):
        if file_hash(ROOT / protocol[key]) != protocol[key+'_sha256']:
            raise ValueError(f'{key} hash differs from frozen protocol')
    original = Dataset.from_csv(ROOT / protocol['dataset'])
    commits = original.commits[:protocol['prefix_commits']]
    if len(commits) != protocol['prefix_commits']:
        raise ValueError('insufficient reference commits')
    data = Dataset([r for r in original.rows if r.commit in set(commits)], original.feature_names, commits)
    repo, bases, paths = read_history(ROOT / protocol['database'], commits)
    fingerprint = source_fingerprint()
    binding = {'protocol_sha256': digest(protocol), 'source_sha256': digest(fingerprint),
        'dataset_sha256': protocol['dataset_sha256'], 'database_sha256': protocol['database_sha256']}
    manifest = {'binding': binding, 'protocol': protocol, 'protocol_commit': PROTOCOL_COMMIT,
        'source_files': fingerprint, 'head': run_git(ROOT, 'rev-parse', 'HEAD').strip(),
        'working_tree': run_git(ROOT, 'status', '--porcelain'), 'python': sys.version,
        'packages': {name: importlib.metadata.version(name) for name in ('scikit-learn', 'numpy')}}
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / 'manifest.json'
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding='utf-8'))
        if previous['binding'] != binding:
            raise ValueError('output belongs to another protocol/source/input; preserve it')
    else:
        write_json(manifest_path, manifest)
    if (out / 'results.json').exists():
        print('Pilot already evaluated; preserving existing results.', flush=True)
        return
    groups = data.rows_by_commit()
    plans, eligibility = {}, {}
    prior = set()
    for index, commit in enumerate(commits):
        checkpoint = out / 'plans' / f'{index:04d}-{commit}.json'
        plan_binding = {**binding, 'commit': commit, 'base': bases[commit],
                        'strategy': 'all' if index < protocol['warmup_commits'] else 'dependency'}
        payload = checked_cache(checkpoint, plan_binding)
        if payload is None:
            try:
                payload = collect_plan(repo, bases[commit], commit, plan_binding['strategy'])
                check_mapping(payload['report'], {r.test_id for r in groups[commit]})
                payload['eligible_history'] = sorted(prior & set(run_git(repo, 'rev-list', bases[commit], '--').split()))
            except (ValueError, subprocess.TimeoutExpired) as exc:
                write_json(out / 'STOP.json', {'index': index, 'commit': commit,
                    'binding': binding, 'error': str(exc), 'outcomes_evaluated': False})
                raise
            write_json(checkpoint, {'binding': plan_binding, 'payload': payload, 'payload_sha256': digest(payload)})
        check_mapping(payload['report'], {r.test_id for r in groups[commit]})
        report = payload['report']
        plans[commit] = StructuralPlan(frozenset(t['test'] for t in report['selected']),
            frozenset((report.get('policy') or {}).get('pinned', [])), True, payload['analysis_seconds'])
        eligibility[commit] = frozenset(payload['eligible_history'])
        prior.add(commit)
        write_json(out / 'progress.json', {'phase': 'source_mapping', 'completed': index+1,
            'total': len(commits), 'outcomes_evaluated': False})
        print(f'Source mapping {index+1}/{len(commits)}', flush=True)
    if fingerprint != source_fingerprint():
        raise ValueError('source changed during extraction; no evaluation permitted')
    from codedna_java.live import LIVE_FEATURES
    config = ReplayConfig(protocol['warmup_commits'], protocol['audit_every'], protocol['refit_every'], protocol['risk_target'])
    write_json(out / 'progress.json', {'phase': 'replay', 'outcomes_evaluated': False})
    results = run_replay(data, plans, config, {'full': FullPolicy,
        'history': lambda: AuditedPolicy(LIVE_FEATURES, config), 'structural': StructuralPolicy,
        'combined': lambda: AuditedPolicy(LIVE_FEATURES, config, combined=True)},
        changed_paths=paths, eligible_history=eligibility)
    write_json(out / 'results.json', {'binding': binding, 'classification': protocol['classification'], 'policies': results})
    write_json(out / 'progress.json', {'phase': 'complete', 'outcomes_evaluated': True})
    print('Replay complete. Development results only; inspect traces before conclusions.', flush=True)


def main():
    os.environ.update(GIT_NO_LAZY_FETCH='1', GIT_OPTIONAL_LOCKS='0')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'experiments/results/partial-feedback-pilot-d076-2026-10-27')
    parser.add_argument('--source-plan', nargs=4, metavar=('REPO', 'BASE', 'HEAD', 'STRATEGY'))
    args = parser.parse_args()
    if args.source_plan:
        print(json.dumps(source_plan(*args.source_plan)))
    else:
        run(args.out.resolve())


if __name__ == '__main__':
    main()
