"""Conformal-risk-control stopping (B12) and its offline check."""
import importlib.util
from pathlib import Path

import pytest
from test_live_risk import dataset

from codedna.selection import conformal

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location('crc_check', ROOT / 'scripts/run_crc_check.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_threshold_uses_the_corrected_bound():
    # 39 commits: (k + 1) / 40 <= 0.05 allows at most one miss
    losses = {None: [0.] * 39, .01: [0.] * 39, .05: [1.] + [0.] * 38, .1: [1., 1.] + [0.] * 37}
    assert conformal.threshold(losses, .05) == .05


def test_threshold_needs_enough_commits_and_stops_at_first_violation():
    assert conformal.threshold({None: [0.] * 18, .5: [0.] * 18}, .05) is conformal.FULL
    assert conformal.threshold({None: [0.] * 19, .5: [0.] * 19}, .05) == .5
    # a violation at .01 blocks .05 even though .05 alone would pass
    losses = {.001: [0.] * 39, .01: [1., 1.] + [0.] * 37, .05: [0.] * 39}
    assert conformal.threshold(losses, .05) == .001


def test_check_tunes_on_history_and_pairs_every_commit(monkeypatch):
    check = load()
    rolling = check.load(ROOT, 'run_rolling_evidence')
    data = dataset([f'c{i}' for i in range(120)])
    seen = []
    real = check.fit_audited
    monkeypatch.setattr(check, 'fit_audited', lambda h, *a: (seen.append(list(h.commits)),
                                                             real(h, *a))[1])
    report = check.evaluate(data, rolling)
    for history, block in zip(seen, report['blocks']):
        assert history == data.commits[:block['start']]
    region = sum(x['commits'] for x in report['blocks'])
    assert len(report['b12']) == len(report['product']) == region
    for block in report['blocks']:
        if block['threshold'] == 'full':
            assert all(o[2] == 0 for o in block['b12'])


def test_runner_refuses_changed_protocol(repo):
    check = load()
    for rel in check.CODE:
        p = repo.path / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / rel).read_bytes())
    new = repo.path / 'data/newproject/dataset.csv'; new.parent.mkdir(parents=True)
    dataset([f'n{i}' for i in range(120)]).to_csv(new)
    out = repo.path / 'results'
    summary = check.run(repo.path, {'newproject': new}, out)
    assert summary['confirmatory']['verdict'] == 'inconclusive'  # one project < 3
    assert check.run(repo.path, {'newproject': new}, out) == summary
    (repo.path / 'docs/CRC_STOP_PROTOCOL.md').write_text('changed protocol')
    with pytest.raises(ValueError, match='Protocol, code or inputs changed'):
        check.run(repo.path, {'newproject': new}, out)


def test_saves_time_needs_the_target_on_three_quarters_of_projects():
    check = load()
    assert check.required_keeps(4) == 3  # the 4-project protocols' rule
    assert check.required_keeps(9) == 7  # 3 of 9 is not enough
    assert check.required_keeps(1) == 1


def test_conditional_mode_tunes_on_failing_audit_commits_only(monkeypatch):
    check = load()
    rolling = check.load(ROOT, 'run_rolling_evidence')
    data = dataset([f'c{i}' for i in range(120)])
    sizes = []
    real = check.conformal.threshold
    monkeypatch.setattr(check.conformal, 'threshold', lambda losses, alpha: (
        sizes.append({len(v) for v in losses.values()}), real(losses, alpha))[1])
    report = check.evaluate(data, rolling, conditional=True)
    fitted = [x for x in report['blocks'] if 'fit_error' not in x]
    assert len(sizes) == len(fitted)
    groups = data.rows_by_commit()
    for size, block in zip(sizes, fitted):
        failing = sum(any(r.label for r in groups[c])
                      for c in data.commits[int(block['start'] * .75):block['start']])
        assert size == {failing}


def test_crc_script_cli_runs_on_tiny_synthetic_history(repo, tmp_path):
    import json
    import os
    import subprocess
    import sys
    inputs = repo.path / "synthetic/smoke/dataset.csv"
    inputs.parent.mkdir(parents=True)
    dataset([f"smoke{i}" for i in range(120)]).to_csv(inputs)
    output = tmp_path / "crc-smoke-output"
    env = {**os.environ, "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
    result = subprocess.run([sys.executable, str(ROOT / "scripts/run_crc_check.py"),
                             str(inputs.parent.parent), "--conditional", "--out", str(output)],
                            cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
    assert result.returncode == 0, result.stderr
    assert "Completed" in result.stdout
    summary = json.loads((output / "summary.json").read_text())
    assert "smoke" in summary["projects"]
    assert summary["confirmatory"]["verdict"] == "inconclusive"
