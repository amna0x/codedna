"""Development-only automatic search on the pinned real bug, without oracle inputs."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from codedna.behavior import find_difference
from codedna.git_analysis.git import run_git
from codedna_java.witness import _tools


def main():
    root = Path(__file__).resolve().parents[1]
    if run_git(root, 'diff', 'HEAD', '--', 'backend/codedna', 'plugins/codedna-java/codedna_java').strip():
        raise ValueError('Commit application source before this development comparison')
    application = run_git(root, 'rev-parse', 'HEAD').strip()
    case = next(c for c in json.loads((root/'experiments/moonshot-real-bug-selection-d088.json').read_text())['cases']
                if c['repository']=='nikoo28/java-solutions')
    output = root/'experiments/results/stockspan-automatic-development-d089-2026-10-29'
    output.mkdir(exist_ok=False)
    records = []
    repo = root/'build/d089-stockspan-source.git'
    javac, java = _tools(root)
    pins = {p.relative_to(root).as_posix(): sha256(p.read_bytes()).hexdigest()
            for base in ['backend/codedna', 'plugins/codedna-java/codedna_java'] for p in (root/base).rglob('*.py')}
    (output/'manifest.json').write_text(json.dumps({'source_commit': application, 'source_sha256': pins,
        'case': case, 'max_inputs': 32, 'seed': 7, 'timeout': 120, 'reduce_budget': 4,
        'scope': 'One known development bug; not held-out effectiveness or superiority evidence',
        'supplied_expectation': None, 'oracle_input_injected': False}, indent=2)+'\n')
    for mode in ['guided', 'simple']:
        folder = output/mode
        report = find_difference(repo, case['previous_commit_hash'], case['commit_hash'],
            file='src/main/java/leetcode/medium/OnlineStockSpan.java',
            symbol='leetcode.medium.OnlineStockSpan#calculateSpans(int[])',
            output_dir=folder, allow_build=True, max_inputs=32, seed=7,
            timeout=120, reduce_budget=4, generation=mode)
        record = {'mode': mode, 'status': report['status'],
                  'input': report.get('witness',{}).get('input'), 'independent_replay': None}
        if report['status']=='difference':
            compiled = subprocess.run([javac, '-encoding', 'UTF-8', '-proc:none', 'ReproduceDifference.java'],
                cwd=folder, capture_output=True, timeout=30)
            replay = subprocess.run([java, '-cp', '.', 'ReproduceDifference'], cwd=folder,
                capture_output=True, timeout=30) if compiled.returncode==0 else None
            record['independent_replay'] = compiled.returncode==0 and replay is not None and replay.returncode==0
            (folder/'replay.txt').write_bytes(compiled.stdout+compiled.stderr+(replay.stdout+replay.stderr if replay else b''))
        records.append(record)
        print(json.dumps(record),flush=True)
    (output/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
    for name, digest in pins.items():
        if sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Application source changed during development run')


if __name__ == '__main__':
    main()
