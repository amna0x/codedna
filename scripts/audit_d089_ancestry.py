"""Verify ancestor evidence for a pinned candidate cohort without reading failures."""
import argparse
from hashlib import sha256
import json
from pathlib import Path

from codedna.git_analysis.git import run_git


def ancestor_sets(repo, heads):
    parents = {}
    for line in run_git(repo, 'rev-list', '--parents', *heads).splitlines():
        node, *edges = line.split()
        parents[node] = edges
    result = {}
    for head in heads:
        seen, pending = set(), list(parents.get(head, []))
        while pending:
            node = pending.pop()
            if node not in seen:
                seen.add(node)
                pending.extend(parents.get(node, []))
        result[head] = seen
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    path = root/'experiments/brake-cohort-d089.json'
    cohort = json.loads(path.read_text())
    repo = root/'build/d089-activemq-ancestry.git'
    repo.mkdir(exist_ok=True)
    run_git(repo, 'init', '--bare', '--quiet')
    heads = [b['head'] for b in cohort['builds']]
    if args.fetch:
        for start in range(0, len(heads), 48):
            run_git(repo, 'fetch', '--quiet', '--no-tags', '--filter=blob:none', '--depth=256',
                    'https://github.com/apache/activemq.git', *heads[start:start+48])
            print('Fetched identities:',min(start+48,len(heads)),'/',len(heads),flush=True)
    ancestors = ancestor_sets(repo, heads)
    evidence = []
    for index, build in enumerate(cohort['builds']):
        prior = [b for b in cohort['builds'][:index]
                 if b['timestamp'] < build['timestamp'] and b['head'] in ancestors[build['head']]]
        evidence.append({'head': build['head'], 'split': build['split'],
                         'known_prior_ancestor_heads': [b['head'] for b in prior],
                         'known_train_ancestors': sum(b['split']=='train' for b in prior),
                         'known_audit_ancestors': sum(b['split']=='audit' for b in prior)})
    result = {'cohort_sha256': sha256(path.read_bytes()).hexdigest(), 'fetch_depth': 256,
              'scope': 'Positive ancestry evidence only; absence at shallow boundaries is unresolved',
              'shallow': (repo/'shallow').exists(), 'builds': evidence}
    out = root/'experiments/results/brake-ancestry-d089-2026-10-29.json'
    with out.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    evaluation = [b for b in evidence if b['split']=='evaluation']
    print('Evaluation heads:',len(evaluation),'with known train ancestors:',
          sum(b['known_train_ancestors']>0 for b in evaluation),
          'and known audit ancestors:',sum(b['known_audit_ancestors']>0 for b in evaluation))
    print('No outcome labels or skip permissions evaluated.')


if __name__ == '__main__':
    main()
