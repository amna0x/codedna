"""Read-only explanation of a pinned CI/source mismatch; never grants skipping."""
import argparse
import json
from pathlib import Path
from hashlib import sha256
from codedna.git_analysis.git import run_git


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',default='experiments/results/ci-profile-investigation-d094-2026-10-30.json')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    audit=json.loads((root/'experiments/results/source-universe-d093-2026-10-29.json').read_text())
    repo=root/'build/d093-source-snapshot.git';revision=audit['commit']
    paths=run_git(repo,'ls-tree','-r','--name-only',revision).splitlines()
    missing=[]
    for name in audit['report_not_source_default']:
        suffix='/'+name.replace('.','/')+'.java'
        matches=[p for p in paths if p.endswith(suffix)]
        missing.append({'class':name,'exact_fqcn_source_paths':matches,
                        'interpretation':'Source path exists; discovery/runtime identity needs inspection' if matches else
                        'No exact FQCN source path in this revision; external/generated origin not yet proven'})
    absent=[]
    for name in audit['source_default_without_report']:
        suffix='/'+name.replace('.','/')+'.java'
        absent.append({'class':name,'exact_fqcn_source_paths':[p for p in paths if p.endswith(suffix)]})
    snippets=[]
    for path,needles in [('Jenkinsfile',['-PintegrationTesting','junit(testResults:']),
                         ('oak-parent/pom.xml',['<id>integrationTesting</id>','<artifactId>maven-failsafe-plugin</artifactId>']),
                         ('oak-exercise/pom.xml',['maven-surefire-plugin','<skip>true</skip>']),
                         ('oak-jcr/pom.xml',['jackrabbit-jcr-tests']),
                         ('oak-store-document/src/test/java/org/apache/jackrabbit/oak/plugins/document/RevisionGCTest.java',['@RunWith(Parameterized.class)'])]:
        raw=run_git(repo,'show',revision+':'+path);lines=raw.splitlines()
        snippets.append({'path':path,'decoded_text_sha256':sha256(raw.encode()).hexdigest(),
                         'excerpts':[{'line':i+1,'text':'\n'.join(lines[max(0,i-2):i+4])} for i,line in enumerate(lines) if any(n in line for n in needles)]})
    result={'commit':revision,'ci_build':3012,'reported_only':missing,'source_only':absent,
            'source_configuration':snippets,'exact_match':False,'selective_replay_authorized':False,
            'limitations':['Path matching does not verify runtime class identity or external dependency contents.',
                          'Parameterized report identity and effective CI profile remain unverified.',
                          'Do not remove unmatched tests, invent outcomes, or claim validated model efficacy.']}
    out=root/args.out
    with out.open('x',encoding='utf-8',newline='\n') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'reported_only':len(missing),'with_source_path':sum(bool(x['exact_fqcn_source_paths']) for x in missing),
                      'source_only':len(absent),'exercise_source_only':sum(any(p.startswith('oak-exercise/') for p in x['exact_fqcn_source_paths']) for x in absent)}))


if __name__=='__main__':main()
