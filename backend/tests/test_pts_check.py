"""Predictive Test Selection baseline (B11) and its offline check."""
import importlib.util
from pathlib import Path

import pytest
from test_live_risk import dataset

from codedna.selection import pts
from codedna.test_history.features import Row

ROOT = Path(__file__).resolve().parents[2]


def row(commit, test, label=0, changed=0):
    return Row(commit, 0, test, label, 1.0, {'test_file_changed': changed})


def load():
    spec = importlib.util.spec_from_file_location('pts_check', ROOT / 'scripts/run_pts_check.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_select_unions_score_count_and_changed_tests_with_ties():
    rows = [row('c', t, changed=t == 'd') for t in 'abcde']
    scores = [.9, .5, .5, .1, .2]
    assert pts.select(rows, scores, pts.Cutoffs(.8, 0)) == ['a', 'd']
    # count 2 reaches the tie at 0.5, so both tied tests are selected
    assert pts.select(rows, scores, pts.Cutoffs(float('inf'), 2)) == ['a', 'b', 'c', 'd']
    assert pts.select(rows, scores, pts.Cutoffs(float('inf'), 9)) == list('abcde')


def test_tune_reaches_both_aggregate_targets_on_the_tuning_commits():
    commits = []
    for i in range(20):
        rows = [row(f'c{i}', f't{j}', label=int(j == i % 5)) for j in range(10)]
        # the failing test scores lower on some commits than passing tests do
        scores = [(.9 if i % 4 else .3) if j == i % 5 else j / 20 for j in range(10)]
        commits.append((rows, scores))
    cut = pts.tune(commits, test_recall=.95, change_recall=.999)
    # 15 failing rows score .9 and 5 score .3: recall .95 needs all 20, so .3
    assert cut == pts.Cutoffs(.3, 4)
    picked = [set(pts.select(r, s, pts.Cutoffs(cut.score, 0))) for r, s in commits]
    assert sum(1 for (r, _), p in zip(commits, picked) for x in r if x.label and x.test_id in p) == 20
    # the low-scoring failures rank 4th behind passing tests at .35, .40 and .45
    caught = lambda n: [any(x.label and x.test_id in set(pts.select(r, s, pts.Cutoffs(float('inf'), n)))
                            for x in r) for r, s in commits]
    assert all(caught(4)) and not all(caught(3))


def test_changed_failing_tests_need_no_cutoff_and_no_failures_cannot_tune():
    rows = [row('c', 'a', label=1, changed=1), row('c', 'b')]
    assert pts.tune([(rows, [.1, .9])]) == pts.Cutoffs(float('inf'), 0)
    with pytest.raises(ValueError, match='no failing tests'):
        pts.tune([([row('c', 'a')], [.5])])


def test_auc_counts_ties_as_half_and_needs_both_classes():
    check = load()
    assert check.auc([.9, .1, .5], [1, 0, 0]) == 1.0
    assert check.auc([.5, .5], [1, 0]) == .5
    assert check.auc([.5], [1]) is None


def test_check_tunes_only_on_history_and_matches_time(repo, monkeypatch):
    check = load()
    rolling = check.load(ROOT, 'run_rolling_evidence')
    data = dataset([f'c{i}' for i in range(120)])
    tuned_on = []
    real = check.pts.tune
    monkeypatch.setattr(check.pts, 'tune', lambda c, **k: (
        tuned_on.append({rows[0].commit for rows, _ in c}), real(c, **k))[1])
    report = check.evaluate(data, rolling)
    tuned = [x for x in report['blocks'] if x.get('b11') is not None]
    assert tuned
    position = {c: i for i, c in enumerate(data.commits)}
    # calls go block by block, then once per block for each matching step
    for i, seen in enumerate(tuned_on):
        assert max(position[c] for c in seen) < tuned[i % len(tuned)]['start']
    if 'b10' in report:
        assert len(report['b11_matched']) == len(report['b10']) == len(report['b11_paper'])
        assert 0 <= report['b11_matched_test_recall_target'] <= 1


def test_runner_refuses_changed_protocol(repo):
    check = load()
    for rel in check.CODE:
        p = repo.path / rel; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / rel).read_bytes())
    new = repo.path / 'data/newproject/dataset.csv'; new.parent.mkdir(parents=True)
    dataset([f'n{i}' for i in range(120)]).to_csv(new)
    out = repo.path / 'results'
    summary = check.run(repo.path, {'newproject': new}, out)
    assert summary['projects']['newproject']['set'] == 'confirmatory'
    assert summary['confirmatory']['verdict'] == 'inconclusive'  # one project < 3
    assert check.run(repo.path, {'newproject': new}, out) == summary
    (repo.path / 'docs/PTS_BASELINE_PROTOCOL.md').write_text('changed protocol')
    with pytest.raises(ValueError, match='Protocol, code or inputs changed'):
        check.run(repo.path, {'newproject': new}, out)
