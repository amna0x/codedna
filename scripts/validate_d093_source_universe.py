"""Compare a pinned CI report with source discovery and the real live brake."""
import json
from pathlib import Path
from time import perf_counter

from codedna.git_analysis.git import run_git
from codedna.selection import select_tests
from codedna_java.live import recommend


def main():
    root=Path(__file__).resolve().parents[1]
    cohort=json.loads((root/'experiments/d092-main-ci-pilot.json').read_text())
    chosen=next(b for b in cohort['builds'] if b['number']==3012)
    source=root/'build/d093-source-snapshot.git';source.mkdir(exist_ok=True)
    run_git(source,'init','--bare','--quiet')
    if 'origin' not in run_git(source,'remote').split():
        run_git(source,'remote','add','origin','https://github.com/apache/jackrabbit-oak.git')
    run_git(source,'config','remote.origin.promisor','true')
    run_git(source,'config','remote.origin.partialclonefilter','blob:limit=1m')
    run_git(source,'fetch','--quiet','--depth=2','--filter=blob:limit=1m','origin',chosen['commit'])
    started=perf_counter()
    baseline=select_tests(source,chosen['parent'],chosen['commit'],'all').to_dict()
    discovery_seconds=perf_counter()-started
    cached=root/'experiments/results/rolling-main-ci-d092-corrected-2026-10-29'
    from run_d092_main_ci import parse_report
    truth=parse_report(json.loads((cached/'report-3012.json').read_text()))
    discovered={r['test'] for r in baseline['selected']}
    # Deliberately absent history exercises the actual live fallback, not a mock.
    missing=root/'build/d093-intentionally-absent-history.csv'
    if missing.exists():raise ValueError('The missing-history probe must remain absent')
    live=recommend(source,chosen['parent'],chosen['commit'],history_csv=missing,method='crc')
    required={r['test'] for r in live['selected']}
    result={'scope':'Source/CI-universe compatibility and actual live full-suite fallback; no fitted-model efficacy',
        'ci_build':3012,'commit':chosen['commit'],'parent':chosen['parent'],
        'discovered_tests':len(discovered),'reported_classes':len(truth.classes),
        'report_not_source_default':sorted(truth.classes-discovered),
        'source_default_without_report':sorted(discovered-truth.classes),
        'exact_universe_match':discovered==truth.classes,
        'live_status':live['risk']['status'],'live_reasons':live['risk']['reasons'],
        'live_preserves_all_discovered':required==discovered and not live['skipped'],
        'source_discovery_seconds':discovery_seconds,
        'note':'No name/profile mappings guessed; exact mismatch cannot authorize selective replay.'}
    out=root/'experiments/results/source-universe-d093-2026-10-29.json'
    with out.open('x',encoding='utf-8',newline='\n') as stream:
        json.dump(result,stream,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['report_not_source_default','source_default_without_report']}),flush=True)


if __name__=='__main__':main()
