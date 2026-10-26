"""Render completed, verified saved results; never fit or tune a model."""
import hashlib,json,platform,shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26'
DATA=ROOT/'experiments/datasets/confirmatory-windowsfix-2026-10-26'
REPORT=ROOT/'docs/CONFIRMATORY_RESULTS_2026-10-26.md'
FIGURES=ROOT/'docs/figures/confirmatory-2026-10-26'

def digest(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def pct(value):return 'n/a' if value is None else f'{100*value:.2f}%'
def number(value):return 'n/a' if value is None else f'{value:.6f}'

def main():
    status=json.loads((DATA/'continuation-status.json').read_text())
    assert status['phase']=='complete','The fixed study must finish before exporting its interpretation'
    manifest=json.loads((STUDY/'manifest.json').read_text()); original=digest(STUDY/'manifest.json')
    for relative,expected in manifest['outputs'].items():
        path=(STUDY/relative).resolve();assert path.is_relative_to(STUDY.resolve())
        assert digest(path)==expected,relative
    config=json.loads((STUDY/'config.json').read_text());assert config==manifest['config']
    summary=json.loads((STUDY/'summary.json').read_text());projects=summary['projects'];pooled=summary['sets']['confirmatory']
    assert len(projects)==9 and set(projects)==set(config['input_sha256'])
    assert config['blocks']==5 and config['min_failing_commits']==20 and config['risk_target']==.05
    preparation=json.loads((STUDY/'preparation-provenance.json').read_text())
    frozen=preparation['frozen_sources']['code_sha256']
    for name,expected in frozen.items():assert digest(ROOT/name)==expected,name
    assert not REPORT.exists(),'Preserve an existing report; inspect it before regenerating'
    FIGURES.mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    eligible=[name for name,row in projects.items() if row['eligible']]
    compared=[name for name in eligible if projects[name].get('b10',{}).get('safety') is not None and projects[name].get('b3',{}).get('safety') is not None]
    figure_paths=[]
    if compared:
        fig,ax=plt.subplots(figsize=(11,4.8));xs=list(range(len(compared)))
        ax.bar([x-.2 for x in xs],[100*projects[n]['b10']['safety'] for n in compared],width=.4,label='B10 calibrated stopping',color='#2466a8')
        ax.bar([x+.2 for x in xs],[100*projects[n]['b3']['safety'] for n in compared],width=.4,label='B3 matched-time baseline',color='#9c6d3d')
        ax.set_xticks(xs,compared,rotation=25,ha='right');ax.set_ylim(0,105)
        ax.set_ylabel('Failure-bearing commits with no missed failure (%)')
        ax.set_title('Fixed confirmation: observed commit safety at matched test time')
        ax.legend(loc='lower left');ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        fig.tight_layout()
        for suffix in ('png','svg'):
            path=FIGURES/f'project-safety.{suffix}';fig.savefig(path,dpi=170,bbox_inches='tight');figure_paths.append(path)
        plt.close(fig)
    estimates=pooled.get('b10_minus_b3',{})
    available=[name for name in ('time','recall','safety') if estimates.get(name,{}).get('estimate') is not None and estimates[name].get('ci') is not None]
    if available:
        fig,ax=plt.subplots(figsize=(8.5,3.4))
        for y,name in enumerate(available):
            item=estimates[name];lo,hi=item['ci'];color='#2466a8' if name=='safety' else '#666666'
            ax.hlines(y,100*lo,100*hi,color=color,linewidth=3);ax.scatter(100*item['estimate'],y,color=color,zorder=3)
        ax.axvline(0,color='#999999',linestyle='--');ax.set_yticks(range(len(available)),[{'time':'Normalized test time','recall':'Failing-test recall','safety':'Commit safety (primary)'}[n] for n in available])
        ax.set_xlabel('B10 minus matched B3 (percentage points), 95% percentile interval')
        ax.set_title('Equal-project pooled differences');ax.grid(axis='x',alpha=.2);fig.tight_layout()
        for suffix in ('png','svg'):
            path=FIGURES/f'pooled-differences.{suffix}';fig.savefig(path,dpi=170,bbox_inches='tight');figure_paths.append(path)
        plt.close(fig)
    gate=pooled['gate'];accepted,rejected=gate['accepted'],gate['rejected']
    reading={'helps':'The fixed comparison supports improved safety in this measured cohort; it does not establish universal superiority or a future safety guarantee.',
             'harms':'The fixed comparison found lower safety for B10 at matched actual test time. A superiority claim is not supported.',
             'no meaningful difference':'The fixed interval lies within the predeclared safety margin. This study does not support a meaningful safety improvement over matched B3.',
             'inconclusive':'The fixed comparison is inconclusive. Neither superiority nor equivalence should be claimed.'}
    assert pooled['verdict'] in reading
    lines=['# Nine-project confirmatory results â€” 2026-10-26','',
      f"The fixed stopping-rule verdict is **{pooled['verdict']}**. The gate verdict is **{gate['verdict']}**.",'',reading[pooled['verdict']],'',
      '## Design and scope','',
      'Nine previously uninspected RTPTorrent v1.1 projects were fixed before this confirmation. Each project uses five rolling blocks in the last half of its recorded commits. Models fit only prior history (50/25/25 train/calibrate/audit); the seed is 0 and risk target is 5%. Eligibility requires at least 20 failure-bearing evaluation commits. B3 uses the same ordering with its fixed budget matched to B10\'s actual test time. This is within-project chronological confirmation, not another cross-project transfer experiment.','',
      f"Projects supplied: **9**; eligible: **{len(eligible)}**; with defined B10/B3 commit safety: **{len(compared)}**.",'',
      '## Pooled result','', '| Metric | B10 minus B3 | 95% interval |','|---|---:|---|']
    for name in ('time','recall','safety'):
        row=estimates.get(name,{})
        interval=row.get('ci');ci='n/a' if interval is None else f"[{number(interval[0])}, {number(interval[1])}]"
        lines.append(f"| {name} | {number(row.get('estimate'))} | {ci} |")
    lines+=['','Differences above use proportions; multiply by 100 for percentage points. Projects receive equal weight. The fixed hierarchical bootstrap uses 2,000 draws and seed 0. The verdict uses the predeclared Â±0.05 safety margin and project-count/sign rules.','',
      '## Per-project observations','',
      '| Project | Evaluation failing commits | Eligible | Accepted blocks | Fit failures | B10 time | B10 safety | B3 safety | Product time | Product miss |',
      '|---|---:|---|---:|---:|---:|---:|---:|---:|---:|']
    for name,row in projects.items():
        b10,b3,product=row.get('b10',{}),row.get('b3',{}),row.get('product',{})
        values=[name,str(row['evaluation_failing_commits']),str(row['eligible']),str(row.get('accepted_blocks','n/a')),str(row.get('fit_failures','n/a')),pct(b10.get('time')),pct(b10.get('safety')),pct(b3.get('safety')),pct(product.get('mean_time')),pct(product.get('observed_miss_rate'))]
        lines.append('| '+' | '.join(values)+' |')
    lines+=['','Time is a fraction of recorded full-suite test duration; it excludes compilation, CI startup and feature extraction. Product means the existing gate chooses B10 on accepted blocks and the full suite otherwise. Safety is conditional on failure-bearing commits; product miss rate uses all evaluation commits.','',
      '## Gate evidence','',
      '| Blocks | Accepted | Rejected |','|---|---:|---:|',
      f"| Number of blocks | {accepted['blocks']} | {rejected['blocks']} |",f"| Evaluation commits | {accepted['commits']} | {rejected['commits']} |",
      f"| Observed B10 miss rate | {pct(accepted['observed_miss_rate'])} | {pct(rejected['observed_miss_rate'])} |",
      f"| One-sided 95% Wilson upper bound | {pct(accepted['wilson_upper'])} | {pct(rejected['wilson_upper'])} |",'',
      'The gate verdict follows the fixed observed-rate rules. It is not proof of a calibrated future probability; accepted blocks are observational subsets, not a randomized comparison. An unexercised gate supplies insufficient evidence. Rejected blocks fall back to the full suite in the product.','',
      '## Limitations and claim boundaries','',
      '- Bootstrap commit resampling ignores serial dependence; intervals are indicative and have no multiplicity correction.',
      '- Recorded CI test-class outcomes can include flaky failures and reflect older open-source Java projects.',
      '- Input preparation warnings, missing commits, repeated runs and excluded/ineligible projects remain part of the evidence; no project is removed to improve the verdict.',
      '- Matching recorded test time does not establish end-to-end CI speedup.',
      '- The source-only transfer failure remains a separate finding. Missing or unvalidated target history still requires the full-suite fallback.',
      '- The Windows repair changes Git transport/error reporting, not the fixed feature, model, calibration, gate or statistical rules. Three completed inputs were reused with verified hashes and preserved parent provenance.','',
      '## Reproducibility','',f"Python: `{config['python']}`. Packages: `{json.dumps(config['packages'],sort_keys=True)}`.",'',
      f"Saved study: `../experiments/results/{STUDY.name}/`. Original result manifest SHA-256: `{original}`.",'',
      'Every original output checksum was checked before rendering. The original reports/manifest are untouched. Export/source provenance is stored separately under the study\'s `audit/` folder. This report renders saved results and does not refit models.','']
    for png in [p for p in figure_paths if p.suffix=='.png']:
        lines += [f'![{png.stem.replace("-"," ")}](figures/confirmatory-2026-10-26/{png.name})','']
    REPORT.write_text('\n'.join(lines),encoding='utf-8')
    audit=STUDY/'audit';audit.mkdir(exist_ok=True)
    for name in ('resume-provenance.json','parent-continuation-code.json','resume-code-change.patch'):
        shutil.copy2(DATA/name,audit/name)
    for name,expected in frozen.items():
        target=audit/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,target);assert digest(target)==expected
    shutil.copy2(Path(__file__),audit/'export-confirmatory-report.py')
    outputs={str(REPORT.relative_to(ROOT)):digest(REPORT),**{str(p.relative_to(ROOT)):digest(p) for p in figure_paths}}
    source_files={str(p.relative_to(audit)):digest(p) for p in audit.rglob('*') if p.is_file() and p.name!='manifest.json'}
    (audit/'manifest.json').write_text(json.dumps({'original_study_manifest_sha256':original,'original_outputs_verified':len(manifest['outputs']),'derived_outputs':outputs,'audit_files':source_files},indent=2),encoding='utf-8')
    assert digest(STUDY/'manifest.json')==original
    print(json.dumps({'report':str(REPORT),'figures':len(figure_paths),'verdict':pooled['verdict'],'gate':gate['verdict'],'original_outputs_verified':len(manifest['outputs'])}))

if __name__=='__main__':main()
