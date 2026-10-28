"""Observation-isolated research replay; not a replacement for the live brake.

Only the evaluator reads current truth. Decisions see code metadata and their
own previously executed outcomes. Original full-history CSV features are ignored.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from hashlib import sha256
import json
from math import fsum, isfinite
from time import perf_counter
from types import MappingProxyType
from typing import Mapping

from codedna.test_history.features import (
    CHANGE_FEATURES, TEST_FEATURES, STRUCTURAL_FEATURES, Dataset, Row, NEVER,
)


@dataclass(frozen=True)
class ReplayConfig:
    warmup: int = 240
    audit_every: int = 10
    refit_every: int = 20
    target: float = .05

    def __post_init__(self):
        if self.warmup < 0 or self.audit_every < 1 or self.refit_every < 1 or not 0 < self.target < 1:
            raise ValueError('invalid replay configuration')


@dataclass(frozen=True)
class StructuralPlan:
    selected: frozenset[str]
    pinned: frozenset[str] = frozenset()
    available: bool = True
    analysis_seconds: float = 0.

    def __post_init__(self):
        object.__setattr__(self, 'selected', frozenset(self.selected))
        object.__setattr__(self, 'pinned', frozenset(self.pinned))
        if not isfinite(self.analysis_seconds) or self.analysis_seconds < 0:
            raise ValueError('invalid structural overhead')


@dataclass(frozen=True)
class DecisionTest:
    test_id: str
    features: Mapping[str, float]


@dataclass(frozen=True)
class DecisionView:
    commit: str
    index: int
    tests: tuple[DecisionTest, ...]
    structural: StructuralPlan

    @property
    def universe(self):
        return frozenset(test.test_id for test in self.tests)

    def prediction_rows(self):
        # Current labels and runtimes are placeholders, never supplied to policy.
        return [Row(self.commit, self.index, t.test_id, 0, 0., dict(t.features)) for t in self.tests]


@dataclass(frozen=True)
class ObservedTest:
    test_id: str
    label: int
    duration: float
    features: Mapping[str, float]  # frozen before this outcome was revealed


@dataclass(frozen=True)
class Observation:
    commit: str
    index: int
    complete: bool
    tests: tuple[ObservedTest, ...]


def complete_dataset(history: tuple[Observation, ...], feature_names: list[str]) -> Dataset:
    complete = [batch for batch in history if batch.complete]
    return Dataset([Row(batch.commit, batch.index, t.test_id, t.label, t.duration, dict(t.features))
                    for batch in complete for t in batch.tests], feature_names,
                   [batch.commit for batch in complete])


@dataclass
class Proposal:
    selected: frozenset[str]
    status: str
    evidence: dict = field(default_factory=dict)


class FullPolicy:
    structural = False

    def decide(self, view, history):
        return Proposal(view.universe, 'full_reference')


class StructuralPolicy:
    structural = True

    def decide(self, view, history):
        return Proposal(view.structural.selected if view.structural.available else view.universe,
                        'structural' if view.structural.available else 'structural_unavailable')


class AuditedPolicy:
    """Existing B10 model/gate fitted only on this policy's complete observations."""
    def __init__(self, feature_names, config, *, combined=False):
        self.feature_names, self.config = list(feature_names), config
        self.structural = combined
        self.model = None
        self.last_fit = None
        self.fit_error = 'no prior complete audit history'
        self.evidence = {}
        self.basis = frozenset()

    def decide(self, view, history):
        allowed = frozenset(batch.commit for batch in history)
        if (self.last_fit is None or not self.basis <= allowed
                or (view.index - self.config.warmup) % self.config.refit_every == 0):
            from codedna.selection.live import fit_audited
            self.last_fit = view.index
            data = complete_dataset(history, self.feature_names)
            self.basis = frozenset(data.commits)
            self.model = None
            self.evidence = {'complete_history_commits': len(data.commits)}
            if len(data.commits) < 40:
                self.fit_error = 'fewer than 40 complete observed commits'
            else:
                try:
                    ranker, calibrator, audit, provenance = fit_audited(data, self.feature_names, self.config.target)
                    self.evidence.update(audit.to_dict())
                    self.evidence['provenance'] = provenance
                    self.fit_error = '; '.join(audit.reasons)
                    if audit.accepted:
                        self.model = (ranker, calibrator)
                except ValueError as exc:
                    self.fit_error = str(exc)
        if self.model is None:
            return Proposal(view.universe, 'unvalidated_full', {**self.evidence, 'reason': self.fit_error})
        from codedna.models.rankers import order_by_baseline
        from codedna.selection.risk import RiskPolicy, decide
        ranker, calibrator = self.model
        rows = view.prediction_rows()
        decision = decide(rows, calibrator.transform(ranker.predict_proba(rows)),
                          RiskPolicy(budget=None, risk_target=self.config.target),
                          order=order_by_baseline('recent_failures', rows))
        return Proposal(frozenset(decision.selected), 'validated_history', dict(self.evidence))


@dataclass
class _State:
    runs: int = 0
    failures: int = 0
    recent: deque = field(default_factory=lambda: deque(maxlen=5))
    last_failure: int | None = None
    total_duration: float = 0.
    last_duration: float = 0.

    def features(self, index):
        return {'past_runs': float(self.runs), 'past_failures': float(self.failures),
                'failure_rate': self.failures / self.runs if self.runs else 0.,
                'recent_failures': float(sum(self.recent)),
                'failed_last_run': float(self.recent[-1]) if self.recent else 0.,
                'commits_since_failure': float(index-self.last_failure) if self.last_failure is not None else float(NEVER),
                'mean_duration': self.total_duration/self.runs if self.runs else 0.,
                'last_duration': self.last_duration}


def run_replay(dataset: Dataset, plans: Mapping[str, StructuralPlan], config: ReplayConfig,
               policies: Mapping[str, object], *, changed_paths: Mapping[str, tuple[str, ...]] | None = None,
               eligible_history: Mapping[str, frozenset[str]] | None = None):
    """Run fresh policy factories independently; return evaluator metrics/traces."""
    if len(dataset.commits) != len(set(dataset.commits)):
        raise ValueError('duplicate commits')
    groups = dataset.rows_by_commit()
    for commit in dataset.commits:
        rows = groups.get(commit, [])
        if not rows or len(rows) != len({r.test_id for r in rows}):
            raise ValueError('each reference commit needs unique test units')
        if any(r.label not in (0, 1) or not isfinite(r.duration) or r.duration < 0 for r in rows):
            raise ValueError('invalid reference truth')
        if commit not in plans:
            raise ValueError(f'missing structural plan for {commit}')
        if any(name not in r.features for r in rows for name in CHANGE_FEATURES+TEST_FEATURES):
            raise ValueError('missing decision-time code metadata')
    outputs = {}
    instances = []
    for name, factory in policies.items():
        policy = factory()
        if any(policy is existing for existing in instances):
            raise ValueError('each policy requires a fresh isolated instance')
        instances.append(policy)
        history = []
        traces = []
        seen_failures = set()  # evaluator only; never placed in a decision view
        for index, commit in enumerate(dataset.commits):
            truth = {row.test_id: row for row in groups[commit]}
            universe = frozenset(truth)
            plan = plans[commit]
            if not (plan.selected | plan.pinned) <= universe:
                raise ValueError('structural plan includes an unknown reference class')
            paths = tuple(sorted(set((changed_paths or {}).get(commit, ()))))
            started = perf_counter()
            if eligible_history is not None and commit not in eligible_history:
                raise ValueError('missing decision-time ancestry scope')
            allowed = eligible_history[commit] if eligible_history is not None else None
            prior = tuple(batch for batch in history if allowed is None or batch.commit in allowed)
            # Rebuild only from eligible earlier observations. A branch switch
            # cannot carry counters from unrelated commits into its features.
            states = defaultdict(_State)
            co = defaultdict(lambda: defaultdict(int))
            for age, batch in enumerate(prior):
                old_paths = set((changed_paths or {}).get(batch.commit, ()))
                for item in batch.tests:
                    state = states[item.test_id]
                    state.runs += 1; state.failures += item.label; state.recent.append(item.label)
                    state.total_duration += item.duration; state.last_duration = item.duration
                    if item.label:
                        state.last_failure = age
                        for path in old_paths: co[path][item.test_id] += 1
            tests = []
            for test_id in sorted(universe):
                original = truth[test_id]
                features = {key: float(original.features[key]) for key in CHANGE_FEATURES+TEST_FEATURES}
                features.update({key: float(original.features[key]) for key in STRUCTURAL_FEATURES if key in original.features})
                features.update(states[test_id].features(len(prior)))
                features['co_failures'] = float(sum(co[path][test_id] for path in paths))
                if not all(isfinite(value) for value in features.values()):
                    raise ValueError('non-finite decision metadata')
                tests.append(DecisionTest(test_id, MappingProxyType(features)))
            view = DecisionView(commit, index, tuple(tests), plan)
            digest = sha256(json.dumps([(t.test_id, dict(t.features)) for t in view.tests], sort_keys=True).encode()).hexdigest()
            warmup = index < config.warmup
            audit = not warmup and (index-config.warmup+1) % config.audit_every == 0
            if warmup or audit:
                proposal = Proposal(universe, 'warmup_full' if warmup else 'scheduled_audit')
                selected = universe
                proposed = None
            else:
                proposal = policy.decide(view, prior)
                if not proposal.selected <= universe:
                    raise ValueError('policy selected an unknown class')
                proposed = sorted(proposal.selected)
                selected = proposal.selected | plan.pinned
                if getattr(policy, 'structural', False):
                    selected |= plan.selected if plan.available else universe
            overhead = perf_counter()-started
            # Reveal only executed results to this policy, after all decisions.
            frozen = {test.test_id: test.features for test in view.tests}
            observed = tuple(ObservedTest(t, truth[t].label, truth[t].duration, frozen[t]) for t in sorted(selected))
            history.append(Observation(commit, index, selected == universe, observed))
            failures = {t for t, row in truth.items() if row.label}
            first = failures-seen_failures
            recurring = failures & seen_failures
            missed = failures-selected
            traces.append({'commit': commit, 'index': index, 'evaluation': not warmup,
                'input_digest': digest, 'proposed': proposed, 'selected': sorted(selected),
                'total_tests': len(universe), 'status': proposal.status,
                'scheduled_audit': audit, 'complete_observation': selected == universe,
                'observed_tests': len(observed), 'eligible_prior_commits': len(prior), 'failing_classes': len(failures), 'missed_classes': len(missed),
                'build_escape': bool(failures and not failures & selected),
                'first_failure_classes': len(first), 'missed_first_failure_classes': len(first-selected),
                'recurring_failure_classes': len(recurring), 'missed_recurring_failure_classes': len(recurring-selected),
                'test_seconds': fsum(truth[t].duration for t in selected),
                'reference_seconds': fsum(row.duration for row in truth.values()),
                'replay_overhead_seconds': overhead,
                'structural_analysis_seconds': plan.analysis_seconds if not warmup and getattr(policy, 'structural', False) else 0.,
                'evidence': proposal.evidence})
            seen_failures.update(failures)
        evaluation = [row for row in traces if row['evaluation']]
        failing = [row for row in evaluation if row['failing_classes']]
        n_fail = sum(row['failing_classes'] for row in evaluation)
        n_miss = sum(row['missed_classes'] for row in evaluation)
        reference = fsum(row['reference_seconds'] for row in traces)
        cost = fsum(row['test_seconds'] for row in traces)
        outputs[name] = {'trace': traces, 'metrics': {
            'evaluation_commits': len(evaluation), 'failing_commits': len(failing),
            'zero_omission_safe_commits': sum(not row['missed_classes'] for row in failing),
            'zero_omission_safety': sum(not row['missed_classes'] for row in failing)/len(failing) if failing else None,
            'build_escape_commits': sum(row['build_escape'] for row in failing),
            'build_escape_rate': sum(row['build_escape'] for row in failing)/len(failing) if failing else None,
            'failing_classes': n_fail, 'missed_classes': n_miss,
            'missed_class_fraction': n_miss/n_fail if n_fail else None,
            'failing_class_recall': 1-n_miss/n_fail if n_fail else None,
            'reduced_suite_commits': sum(len(row['selected']) < row['total_tests'] for row in evaluation),
            'reduced_suite_coverage': sum(len(row['selected']) < row['total_tests'] for row in evaluation)/len(evaluation) if evaluation else None,
            'recorded_test_seconds_including_warmup': cost,
            'reference_test_seconds_including_warmup': reference,
            'recorded_time_ratio_including_warmup': cost/reference if reference else None,
            'recorded_evaluation_test_seconds': fsum(row['test_seconds'] for row in evaluation),
            'recorded_evaluation_reference_seconds': fsum(row['reference_seconds'] for row in evaluation),
            'scheduled_audits': sum(row['scheduled_audit'] for row in evaluation),
            'complete_observation_commits': sum(row['complete_observation'] for row in traces),
            'replay_overhead_seconds': fsum(row['replay_overhead_seconds'] for row in traces),
            'structural_analysis_seconds': fsum(row['structural_analysis_seconds'] for row in traces),
            'first_failure_classes': sum(row['first_failure_classes'] for row in evaluation),
            'missed_first_failure_classes': sum(row['missed_first_failure_classes'] for row in evaluation),
            'recurring_failure_classes': sum(row['recurring_failure_classes'] for row in evaluation),
            'missed_recurring_failure_classes': sum(row['missed_recurring_failure_classes'] for row in evaluation),
            'simulated_additional_repeated_executions': 0}}
    return outputs
