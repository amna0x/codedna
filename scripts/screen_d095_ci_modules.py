"""Availability/identity-only screen of all preserved CI child reports."""
import json
from pathlib import Path
from collections import defaultdict
from codedna.git_analysis.git import run_git
from codedna.selection import select_tests
from run_d092_main_ci import parse_report


def main():
    root=Path(__file__).resolve().parents[1]
    audit=json.loads((root/'experiments/results/source-universe-d093-2026-10-29.json').read_text())
    repo=root/'build/d093-source-snapshot.git';revision=audit['commit']
    paths=run_git(repo,'ls-tree','-r','--name-only',revision).splitlines()
    owners=defaultdict(set)
    for path in paths:
        if '/src/test/java/' in path and path.endswith('.java'):
            module,relative=path.split('/src/test/java/',1)
            owners[relative[:-5].replace('/','.')].add(module)
    discovery=select_tests(repo,audit['parent'],revision,'all').to_dict()
    default=defaultdict(set);unmapped=[]
    for row in discovery['selected']:
        name=row['test'];modules=owners.get(name,set())
        if len(modules)==1:default[next(iter(modules))].add(name)
        else:unmapped.append(name)
    raw=json.loads((root/'experiments/results/rolling-main-ci-d092-corrected-2026-10-29/report-3012.json').read_text())
    children=[];seen=defaultdict(list)
    for index,child in enumerate(raw['childReports']):
        report=parse_report(child['result']);modules=set();unresolved=[]
        for name in report.classes:
            candidates=owners.get(name,set())
            if len(candidates)==1:modules.update(candidates)
            else:unresolved.append(name)
        module=next(iter(modules)) if len(modules)==1 else None
        exact=bool(module and not unresolved and report.complete_as_published and report.classes==default[module])
        row={'child_index':index,'class_count':len(report.classes),'complete_as_published':report.complete_as_published,
             'source_module_candidates':sorted(modules),'unresolved_classes':sorted(unresolved),
             'exact_single_module_default_match':exact,'inferred_module':module,
             'selection_rule':'All children retained; identity/completeness only, no failure or saving ranking'}
        if module:
            seen[module].append(index)
            row.update(default_class_count=len(default[module]),report_only=sorted(report.classes-default[module]),
                       default_only=sorted(default[module]-report.classes))
        children.append(row)
    result={'commit':revision,'build':3012,'children':children,'unmapped_source_default':sorted(unmapped),
            'multiple_children_for_module':{m:indices for m,indices in seen.items() if len(indices)>1},
            'candidate_children':[r['child_index'] for r in children if r['exact_single_module_default_match']],
            'limitations':['Module ownership inferred from exact source paths, not Jenkins child URLs.',
                          'One-build compatibility is not historical coverage, efficacy, or whole-project savings.',
                          'Every unmatched module remains required; no skip permission granted.']}
    out=root/'experiments/results/module-compatibility-d095-2026-10-30.json'
    with out.open('x',encoding='utf-8',newline='\n') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({'children':len(children),'candidate_children':result['candidate_children'],
                      'candidate_modules':[r['inferred_module'] for r in children if r['exact_single_module_default_match']]}),flush=True)


if __name__=='__main__':main()

