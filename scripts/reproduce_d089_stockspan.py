"""Replay the published development trigger against pinned unmodified sources."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from codedna_java.witness import HARNESS, _tools
from codedna_java.witness_values import instance_array_probe, normal_value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-build', action='store_true')
    args = parser.parse_args()
    if not args.allow_build:
        parser.error('Explicit project-code execution consent required')
    root = Path(__file__).resolve().parents[1]
    case = next(c for c in json.loads((root/'experiments/moonshot-real-bug-selection-d088.json').read_text())['cases']
                if c['repository'] == 'nikoo28/java-solutions' and c['split'] == 'development')
    source_path = 'src/main/java/leetcode/medium/OnlineStockSpan.java'
    pinned = next(f for r in json.loads((root/'experiments/results/research-feasibility-d088-2026-10-29/development-source-contract.json').read_text())
                  if r['repository'] == case['repository'] for f in r['files'] if f['file'] == source_path)
    work = root/'build/d089-stockspan'
    work.mkdir(exist_ok=False)
    javac, java = _tools(root)
    observations = []
    for index, revision in enumerate([case['previous_commit_hash'], case['commit_hash']]):
        url = 'https://raw.githubusercontent.com/'+case['repository']+'/'+revision+'/'+source_path
        source = (root/'build/d088-inputs/source-cache'/sha256(url.encode()).hexdigest()).read_bytes()
        if sha256(source).hexdigest() != pinned['source_sha256'][index]:
            raise ValueError('Pinned development source changed')
        folder = work/str(index)
        folder.mkdir()
        (folder/'OnlineStockSpan.java').write_bytes(source)
        (folder/'CodeDNABehaviorProbe.java').write_text(instance_array_probe(HARNESS), encoding='utf-8')
        compiled = subprocess.run([javac, '-encoding', 'UTF-8', '-proc:none', '-d', '.',
            'OnlineStockSpan.java', 'CodeDNABehaviorProbe.java'], cwd=folder, capture_output=True, timeout=30)
        if compiled.returncode:
            raise RuntimeError(compiled.stderr.decode(errors='replace')[:2000])
        values = []
        for _ in range(3):
            run = subprocess.run([java, '-Xmx64m', '-cp', '.', 'CodeDNABehaviorProbe',
                'leetcode.medium.OnlineStockSpan', 'calculateSpans', '10,10,10,10',
                'D089:', 'int[]'], cwd=folder, capture_output=True, text=True, timeout=5)
            lines = [s[len('D089:value:'):] for s in run.stdout.splitlines() if s.startswith('D089:value:')]
            if run.returncode or len(lines) != 1:
                raise RuntimeError('Incomplete or ambiguous probe result')
            values.append(normal_value(lines[0]))
        if values[1:] != values[:-1]:
            raise RuntimeError('Repeated results disagreed')
        observations.append({'commit': revision, 'source_sha256': pinned['source_sha256'][index],
                             'repeated_outputs': values})
    expected = [1, 1, 1, 1]  # Published added regression test; not derived from fixed output.
    result = {'repository': case['repository'], 'input': [10,10,10,10],
        'expected_from_published_test': expected, 'observations': observations,
        'confirmed_against_published_test': observations[0]['repeated_outputs'][0] != expected
            and observations[1]['repeated_outputs'][0] == expected,
        'scope': 'Known-trigger development probe; not automatic discovery, held-out evaluation or integrated Moonshot validation'}
    out = root/'experiments/results/development-stockspan-d089-2026-10-29.json'
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
