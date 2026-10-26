"""Exact parity with the old forward scan, including floating-point boundaries."""
import math
import random
from dataclasses import asdict

import pytest

from codedna.selection import risk
from codedna.test_history.features import Row


def slow_extend(prob, selected, order, target):
    for row in order:
        if risk._skip_risk(prob, selected) <= target:
            break
        selected.add(row.test_id)


def candidates(n, rng):
    return [Row('c', 0, f't{i}', 0, 1.0,
                {'mean_duration': rng.choice([0.0, 1.0, 4.0]),
                 'past_runs': 5.0, 'test_file_changed': float(rng.random() < .1)})
            for i in range(n)]


@pytest.mark.parametrize('seed', range(24))
def test_whole_decision_matches_old_scan(seed, monkeypatch):
    rng = random.Random(seed)
    fast = risk._extend_to_risk_target
    for _ in range(20):
        rows = candidates(rng.randrange(0, 110), rng)
        probabilities = [rng.choice([0.0, 1.0, 1e-14, .001, .03, .5, rng.random()])
                         for _ in rows]
        order = [r.test_id for r in rows]
        rng.shuffle(order)
        if rows and rng.random() < .5:
            order = order[:rng.randrange(len(order) + 1)] + order[:3] + ['unknown']
        policy = risk.RiskPolicy(budget=rng.choice([None, 0.0, .25, 1.0]),
                                 risk_target=rng.choice([0.0, .0001, .05, .5, 1.0]),
                                 fallback=rng.choice([True, False]))
        kwargs = {'order': rng.choice([None, order]),
                  'always': {r.test_id for r in rows if rng.random() < .1} | {'unknown'}}
        monkeypatch.setattr(risk, '_extend_to_risk_target', fast)
        actual = asdict(risk.decide(rows, probabilities, policy, **kwargs))
        monkeypatch.setattr(risk, '_extend_to_risk_target', slow_extend)
        expected = asdict(risk.decide(rows, probabilities, policy, **kwargs))
        assert actual == expected


def test_exact_threshold_and_adjacent_floats():
    rng = random.Random(99)
    rows = candidates(22, rng)
    prob = {r.test_id: rng.choice([0.0, 1e-14, .001, .05, .3, 1.0]) for r in rows}
    order = rows[::-1] + rows[:3]
    initial = {'t2', 't8'}
    for k in range(len(order) + 1):
        boundary = risk._skip_risk(prob, initial.union(r.test_id for r in order[:k]))
        for target in [boundary, math.nextafter(boundary, -math.inf),
                       math.nextafter(boundary, math.inf)]:
            actual, expected = set(initial), set(initial)
            risk._extend_to_risk_target(prob, actual, order, target)
            slow_extend(prob, expected, order, target)
            assert actual == expected


def test_large_suite_uses_logarithmic_number_of_full_risk_scans(monkeypatch):
    rows = candidates(10000, random.Random(0))
    prob = {r.test_id: .01 for r in rows}
    original, calls = risk._skip_risk, []
    def counted(prob, selected):
        calls.append(len(selected))
        return original(prob, selected)
    monkeypatch.setattr(risk, '_skip_risk', counted)
    selected = set()
    risk._extend_to_risk_target(prob, selected, rows, .05)
    assert len(calls) <= math.ceil(math.log2(len(rows) + 1))
    assert original(prob, selected) <= .05
    assert original(prob, selected - {rows[len(selected) - 1].test_id}) > .05


@pytest.mark.parametrize('target', [-1.0, 0.0, .05, 1.0])
def test_empty_or_incomplete_order_and_zero_probabilities(target):
    rows = candidates(5, random.Random(5))
    for values in [[0.0]*5, [1.0]*5, [.1]*5]:
        prob = dict(zip((r.test_id for r in rows), values))
        for order in [[], rows[:2], rows + rows]:
            actual, expected = set(), set()
            risk._extend_to_risk_target(prob, actual, order, target)
            slow_extend(prob, expected, order, target)
            assert actual == expected
