"""An offline, resumable miniature of the fixed experiment."""
import importlib.util
from pathlib import Path
import pytest
from test_live_risk import dataset


def test_runner_reproducibility_and_resume_fingerprints(repo):
    root=Path(__file__).resolve().parents[2]
    spec=importlib.util.spec_from_file_location('dante_runner',root/'scripts/run_dante_check.py')
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    for rel in runner.CODE:
        p=repo.path/rel;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes((root/rel).read_bytes())
    for name in ['one','two']:
        p=repo.path/f'experiments/results/study11-2026-10-21/{name}/dataset.csv'
        p.parent.mkdir(parents=True);dataset([f'{name}-{i}' for i in range(30)]).to_csv(p)
    out=repo.path/'results'
    summary=runner.run(repo.path,out,['one','two'],[0])
    assert len(summary['projects'])==2
    assert 'DANTE-H_calibrated' in summary['comparisons']
    assert runner.run(repo.path,out,['one','two'],[0])==summary
    (repo.path/'docs/DANTE_B10_PROTOCOL.md').write_text('changed protocol')
    with pytest.raises(ValueError,match='Protocol, code or inputs changed'):
        runner.run(repo.path,out,['one','two'],[0])
