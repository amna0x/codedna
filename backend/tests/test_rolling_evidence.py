"""Offline miniature of the rolling-origin evidence study."""
import importlib.util
from pathlib import Path

import pytest
from test_live_risk import dataset

from codedna.test_history.features import Dataset, Row

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location('rolling', ROOT / 'scripts/run_rolling_evidence.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_blocks_cover_only_the_later_half_in_order():
    runner = load()
    cuts = runner.blocks([str(i) for i in range(23)])
    assert cuts[0][0] == 11 and cuts[-1][1] == 23 and len(cuts) == 5
    assert all(a[1] == b[0] for a, b in zip(cuts, cuts[1:]))


def test_block_labels_never_reach_fitting(monkeypatch):
    runner = load()
    seen = []
    real = runner.fit_audited
    def spy(history, *args):
        seen.append(list(history.commits))
        return real(history, *args)
    monkeypatch.setattr(runner, 'fit_audited', spy)
    data = dataset([f'c{i}' for i in range(120)])
    report = runner.evaluate(data)
    for history, block in zip(seen, report['blocks']):
        assert history == data.commits[:block['start']]
    assert 'b3' in report and len(report['b3']) == len(report['b10'])


def test_verdict_rules_are_the_fixed_ones():
    runner = load()
    assert runner.verdict(.1, [.02, .2], 3, 4) == 'helps'
    assert runner.verdict(-.1, [-.2, -.01], 0, 4) == 'harms'
    assert runner.verdict(0., [-.04, .04], 2, 4) == 'no meaningful difference'
    assert runner.verdict(.1, [-.1, .3], 3, 4) == 'inconclusive'
    assert runner.verdict(.1, [.02, .2], 2, 2) == 'inconclusive'
    gate = lambda b, r: {'blocks': b, 'observed_miss_rate': r}
    assert runner.gate_verdict(gate(2, 0.), gate(3, .2)) == 'gate unexercised'
    assert runner.gate_verdict(gate(3, .1), gate(3, .2)) == 'gate not supported'
    assert runner.gate_verdict(gate(3, .01), gate(3, .2)) == 'gate supported'


def test_runner_sets_eligibility_and_resume_fingerprints(repo):
    runner = load()
    for rel in runner.CODE:
        p = repo.path / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / rel).read_bytes())
    new = repo.path / 'data/newproject/dataset.csv'; new.parent.mkdir(parents=True)
    dataset([f'n{i}' for i in range(120)]).to_csv(new)
    quiet = dataset([f'q{i}' for i in range(60)])
    quiet = Dataset([Row(r.commit, r.seq, r.test_id, 0, r.duration, r.features)
                     for r in quiet.rows], quiet.feature_names, quiet.commits)
    old = repo.path / 'data/hikaricp/dataset.csv'; old.parent.mkdir(parents=True)
    quiet.to_csv(old)
    inputs = {'newproject': new, 'hikaricp': old}
    out = repo.path / 'results'
    summary = runner.run(repo.path, inputs, out)
    assert summary['projects']['newproject']['set'] == 'confirmatory'
    assert summary['projects']['hikaricp'] == {
        'set': 'exploratory', 'evaluation_failing_commits': 0, 'eligible': False}
    assert summary['sets']['confirmatory']['verdict'] == 'inconclusive'  # one project < 3
    assert (out / 'summary.md').exists() and (out / 'manifest.json').exists()
    assert runner.run(repo.path, inputs, out) == summary
    (repo.path / 'docs/EVIDENCE_STUDY_PROTOCOL.md').write_text('changed protocol')
    with pytest.raises(ValueError, match='Protocol, code or inputs changed'):
        runner.run(repo.path, inputs, out)
