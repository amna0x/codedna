"""Tuned-threshold gate (B13) and its offline check."""
import importlib.util
from pathlib import Path

import pytest
from test_live_risk import dataset

from codedna.selection import tuned

ROOT = Path(__file__).resolve().parents[2]


def load():
    spec = importlib.util.spec_from_file_location('tuned_check',
                                                  ROOT / 'scripts/run_tuned_gate_check.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def outcomes(commits, failing, missed):
    """``commits`` audit commits, ``failing`` of them failing, ``missed`` of those missed."""
    return [(.5, 1, 1)] * missed + [(.5, 1, 0)] * (failing - missed) + \
        [(.5, 0, 0)] * (commits - failing)


def test_search_takes_the_largest_threshold_before_the_first_failure():
    table = {v: outcomes(200, 40, 0) for v in tuned.GRID if v <= .02}
    table.update({.05: outcomes(200, 40, 1), .1: outcomes(200, 40, 30), .2: outcomes(200, 40, 0)})
    chosen, tested = tuned.search(lambda v: table.get(v, outcomes(200, 40, 40)))
    assert chosen == .05  # .1 fails, so .2 is never tested although it would pass
    assert [v for v, _ in tested][-1] == .1 and not tested[-1][1].accepted


def test_search_falls_back_to_full_when_the_strictest_fails():
    small = outcomes(29, 29, 0)  # zero misses but too few commits for the Wilson bound
    chosen, tested = tuned.search(lambda v: small)
    assert chosen is tuned.FULL and len(tested) == 1
    low_recall = [(.5, 10, 9)] * 10 + [(.5, 0, 0)] * 290  # few missed commits, most tests missed
    assert tuned.search(lambda v: low_recall)[0] is tuned.FULL


def test_check_tunes_on_history_and_pairs_every_commit(monkeypatch):
    check = load()
    rolling = check.load(ROOT, 'run_rolling_evidence')
    data = dataset([f'c{i}' for i in range(120)])
    seen = []
    real = check.fit_audited
    monkeypatch.setattr(check, 'fit_audited', lambda h, *a: (seen.append(list(h.commits)),
                                                             real(h, *a))[1])
    crc = check.load(ROOT, 'run_crc_check')
    report = check.evaluate(data, rolling, crc)
    for history, block in zip(seen, report['blocks']):
        assert history == data.commits[:block['start']]
    region = sum(x['commits'] for x in report['blocks'])
    assert len(report['b13']) == len(report['product']) == region
    for block in report['blocks']:
        if block['threshold'] == 'full':
            assert all(o[2] == 0 for o in block['b13'])
        if 'fit_error' not in block and not block['accepted']:
            assert all(o[2] == 0 for o in block['product'])


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
    (repo.path / 'docs/TUNED_GATE_PROTOCOL.md').write_text('changed protocol')
    with pytest.raises(ValueError, match='Protocol, code or inputs changed'):
        check.run(repo.path, {'newproject': new}, out)
