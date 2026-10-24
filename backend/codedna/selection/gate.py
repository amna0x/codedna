"""Target-validation gate for calibrated stopping (D-041).

The cross-project check (D-039) showed that a risk estimate is only worth
something once it has been checked on the project it is used for. This module
turns that into the default runtime behaviour:

1. **Validate** on the project's own, earlier history (chronological split):
   train on the oldest 60 % of commits with results, calibrate on the next
   20 %, and replay the hybrid B10 (rules order, stop when the calibrated
   estimated skip risk ≤ target) on the newest 20 %. The gate passes only if

   * the calibration slice has both classes and enough failing commits,
   * the validation slice has enough commits and failing commits,
   * the observed miss rate on validation is ≤ the target **and** its 95 %
     Wilson upper bound is ≤ ``max_upper_miss``.

2. **Decide** for a new change with exactly the validated model. The full
   suite is recommended instead, with the reason, when the gate did not pass
   ("risk unvalidated"), when the evidence is stale (too many commits since
   the last recorded full-suite run — skipped-test failures can only be found
   by running everything now and then), or when non-Java files changed (not
   analysed; this only adds tests, so it cannot raise the miss rate).

Nothing here is a guarantee. A passed gate means "the estimate held on the
newest earlier commits of this project", and the evidence is reported.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from codedna.models.evaluate import chronological_split
from codedna.selection.dante import wilson
from codedna.selection.risk import RiskPolicy, SelectionDecision, decide
from codedna.test_history.features import Dataset, Row


@dataclass
class GateConfig:
    risk_target: float = 0.05
    min_validation_commits: int = 20
    min_failing_commits_calibration: int = 3
    min_failing_commits_validation: int = 3
    max_upper_miss: float = 0.10  # 95 % Wilson upper bound of the observed miss rate
    max_commits_since_full_run: int = 50
    model: str = "gradient_boosting"
    calibration: str = "isotonic"
    seed: int = 0


@dataclass
class GateReport:
    status: str  # "validated" or "unvalidated"
    reasons: list[str]
    evidence: dict
    config: dict
    validated_through: str | None  # newest commit used as evidence

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RiskGate:
    report: GateReport
    ranker: object | None = field(default=None, repr=False)
    calibrator: object | None = field(default=None, repr=False)

    @property
    def validated(self) -> bool:
        return self.report.status == "validated"

    def probabilities(self, rows: list[Row]) -> list[float] | None:
        if self.ranker is None or self.calibrator is None:
            return None
        return self.calibrator.transform(self.ranker.predict_proba(rows))


def validate(dataset: Dataset, config: GateConfig | None = None) -> RiskGate:
    from codedna.calibration.calibrators import Calibrator
    from codedna.models.rankers import MLRanker, order_by_baseline

    config = config or GateConfig()
    splits = chronological_split(dataset)
    by_commit = dataset.rows_by_commit()
    groups = {name: [by_commit[sha] for sha in splits[name] if sha in by_commit]
              for name in ("train", "validation", "test")}
    failing = {name: sum(1 for rows in groups[name] if any(r.label for r in rows)) for name in groups}
    evidence: dict = {"history_commits": len(dataset.commits),
                      "commits": {"train": len(groups["train"]), "calibration": len(groups["validation"]),
                                  "validation": len(groups["test"])},
                      "failing_commits": {"train": failing["train"],
                                          "calibration": failing["validation"],
                                          "validation": failing["test"]}}
    reasons: list[str] = []
    settings = asdict(config)
    newest = dataset.commits[-1] if dataset.commits else None

    if failing["train"] == 0:
        reasons.append("no failing commits in the training history")
    if failing["validation"] < config.min_failing_commits_calibration:
        reasons.append(f"calibration slice has {failing['validation']} failing commit(s); "
                       f"needs ≥ {config.min_failing_commits_calibration}")
    if len(groups["test"]) < config.min_validation_commits:
        reasons.append(f"validation slice has {len(groups['test'])} commit(s); "
                       f"needs ≥ {config.min_validation_commits}")
    if failing["test"] < config.min_failing_commits_validation:
        reasons.append(f"validation slice has {failing['test']} failing commit(s); "
                       f"needs ≥ {config.min_failing_commits_validation}")
    if reasons:
        return RiskGate(GateReport("unvalidated", reasons, evidence, settings, newest))

    ranker = MLRanker(config.model, dataset.feature_names, seed=config.seed)
    try:
        ranker.fit([r for rows in groups["train"] for r in rows])
        valid = [r for rows in groups["validation"] for r in rows]
        calibrator = Calibrator(config.calibration).fit(ranker.predict_proba(valid),
                                                        [r.label for r in valid])
    except ValueError as exc:
        return RiskGate(GateReport("unvalidated", [f"model or calibrator not fitted: {exc}"],
                                   evidence, settings, newest))

    policy = RiskPolicy(budget=None, risk_target=config.risk_target)
    missed_commits, times, estimates = 0, [], []
    for rows in groups["test"]:
        decision = decide(rows, calibrator.transform(ranker.predict_proba(rows)), policy,
                          order=order_by_baseline("recent_failures", rows))
        chosen = set(decision.selected)
        missed_commits += any(r.label and r.test_id not in chosen for r in rows)
        total = sum(r.duration for r in rows)
        times.append(sum(r.duration for r in rows if r.test_id in chosen) / total if total
                     else len(chosen) / len(rows))
        estimates.append(decision.estimated_skip_risk)
    n = len(groups["test"])
    low, high = wilson(missed_commits, n)
    evidence["validation"] = {
        "observed_miss_rate": round(missed_commits / n, 4),
        "observed_miss_rate_95ci": [round(low, 4), round(high, 4)],
        "mean_estimated_skip_risk": round(sum(estimates) / n, 4),
        "mean_time_ratio": round(sum(times) / n, 4),
    }
    if missed_commits / n > config.risk_target:
        reasons.append(f"observed miss rate {missed_commits / n:.3f} on validation is above the "
                       f"target {config.risk_target:.3f}")
    if high > config.max_upper_miss:
        reasons.append(f"evidence too weak: 95% upper bound of the miss rate is {high:.3f} "
                       f"(> {config.max_upper_miss:.3f}) over {n} commits")
    status = "unvalidated" if reasons else "validated"
    if not reasons:
        reasons.append(f"estimated skip risk held on the newest {n} earlier commits: observed miss "
                       f"{missed_commits / n:.3f}, 95% CI [{low:.3f}, {high:.3f}]")
    return RiskGate(GateReport(status, reasons, evidence, settings, newest), ranker, calibrator)


def gated_decision(gate: RiskGate, rows: list[Row], *,
                   commits_since_full_run: int | None) -> tuple[SelectionDecision, list[float] | None]:
    """B10 for a validated, fresh gate; otherwise the full suite with the reason."""
    config = GateConfig(**gate.report.config)
    probabilities = gate.probabilities(rows)
    everything = [r.test_id for r in rows]

    def full(reason: str) -> SelectionDecision:
        return SelectionDecision(everything, [], 0.0, 0.0, 1.0, fallback=True,
                                 reasons=[f"run the full suite: {reason}"])

    if not gate.validated:
        return full("risk unvalidated (" + "; ".join(gate.report.reasons) + ")"), probabilities
    if commits_since_full_run is None:
        return full("cannot tell how old the evidence is"), probabilities
    if commits_since_full_run > config.max_commits_since_full_run:
        return full(f"evidence stale: {commits_since_full_run} commits since the last recorded "
                    f"full-suite run (limit {config.max_commits_since_full_run}); a full run "
                    "is the only way to find failures among skipped tests"), probabilities
    if rows and rows[0].features.get("non_java_files_changed", 0) > 0:
        return full(f"{int(rows[0].features['non_java_files_changed'])} non-Java file(s) changed "
                    "(not analysed)"), probabilities
    from codedna.models.rankers import order_by_baseline

    decision = decide(rows, probabilities, RiskPolicy(budget=None, risk_target=config.risk_target),
                      order=order_by_baseline("recent_failures", rows))
    decision.reasons.insert(0, "risk validated on this project's earlier history")
    return decision, probabilities


def assess_change(store, base: str, head: str, *, repo_path=None, structural: bool = True,
                  config: GateConfig | None = None, gate: RiskGate | None = None) -> dict:
    """Validate (unless ``gate`` is given) and decide for ``base → head``; JSON-ready."""
    from codedna.git_analysis.git import resolve_commit, resolve_repository, run_git
    from codedna.test_history.features import build_dataset, change_rows

    repo = resolve_repository(repo_path or store.get_meta("repository") or ".")
    if gate is None:
        gate = validate(build_dataset(store, repo, structural=structural), config)
    rows = change_rows(store, base, head, repo_path=repo, structural=structural)
    since = None
    if gate.report.validated_through:
        try:
            since = int(run_git(repo, "rev-list", "--count",
                                f"{gate.report.validated_through}..{resolve_commit(repo, head)}").strip())
        except Exception:  # noqa: BLE001 - unknown commit: treat the evidence age as unknown
            since = None
    decision, probabilities = gated_decision(gate, rows, commits_since_full_run=since)
    chosen = set(decision.selected)
    per_test = [{"test": r.test_id, "probability": None if probabilities is None
                 else round(p, 6), "selected": r.test_id in chosen,
                 "estimated_seconds": round(r.features.get("mean_duration", 0.0), 3)}
                for r, p in zip(rows, probabilities or [None] * len(rows))]
    return {
        "base": base, "head": resolve_commit(repo, head),
        "gate": gate.report.to_dict(),
        "commits_since_full_run": since,
        "decision": {"mode": "full_suite" if decision.fallback else "calibrated_stop",
                     "selected": decision.selected, "skipped": decision.skipped,
                     "estimated_skip_risk": None if decision.fallback else decision.estimated_skip_risk,
                     "estimated_time_fraction": decision.estimated_time_fraction,
                     "reasons": decision.reasons},
        "tests": per_test,
        "note": "estimated skip risk is an estimate from this project's history, not a guarantee",
    }
