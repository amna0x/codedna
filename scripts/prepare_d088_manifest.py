"""Select real-bug cases by frozen repository/chronology rules, without running code."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from codedna.git_analysis.git import run_git

PREFIX = 'codedna-d088-20261029:'


def select(rows):
    groups = {}
    for row in rows:
        repo = row['repository']
        if repo.casefold() == 'adoble/adr-j':
            continue
        groups.setdefault(repo, []).append(row)
    ranked = sorted(groups, key=lambda r: sha256((PREFIX+r).encode()).hexdigest())
    result = []
    for index, repo in enumerate(ranked[:18]):
        row = min(groups[repo], key=lambda r: (r['commit_timestamp'], r['commit_hash']))
        result.append({
            'split': 'development' if index < 6 else 'held_out',
            **{key: row[key] for key in ['repository', 'clone_url', 'commit_hash',
                'previous_commit_hash', 'commit_timestamp']},
            'metadata_file': row['metadata_file'], 'metadata_line': row['metadata_line'],
            'metadata_sha256': row['metadata_sha256'],
            'status': 'selected_not_executed'})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    benchmark = args.metadata.resolve().parents[1]
    if run_git(benchmark, 'rev-parse', 'HEAD').strip() != 'fe986fb7919be62c2a6f611ee16659e849646798':
        raise ValueError('Benchmark commit does not match the frozen protocol')
    if run_git(benchmark, 'status', '--porcelain', '--', 'data/bugs').strip():
        raise ValueError('Benchmark metadata has local changes')
    rows = []
    for file in sorted(args.metadata.glob('*.json')):
        raw = file.read_bytes()
        digest = sha256(raw).hexdigest()
        for number, line in enumerate(raw.decode('utf-8').splitlines(), 1):
            if line.strip():
                row = json.loads(line)
                rows.append({**row, 'metadata_file': file.name,
                             'metadata_line': number, 'metadata_sha256': digest})
    cases = select(rows)
    if len(cases) != 18:
        raise ValueError('Need eighteen distinct repositories; do not silently shrink the sample')
    manifest = {'protocol': 'docs/RESEARCH_EVALUATION_D088.md',
                'protocol_sha256': sha256((Path(__file__).resolve().parents[1]/
                    'docs/RESEARCH_EVALUATION_D088.md').read_bytes()).hexdigest(),
                'benchmark_commit': 'fe986fb7919be62c2a6f611ee16659e849646798',
                'application_commit': 'a30ce70', 'selection_seed': PREFIX,
                'scope': 'Selection only; no benchmark behavior or effectiveness evaluated',
                'cases': cases}
    with args.out.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, indent=2)
        stream.write('\n')
    print('Pinned 6 development and 12 held-out repositories. No project code executed.')


if __name__ == '__main__':
    main()
