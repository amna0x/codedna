"""Conservative empirical gate for one frozen policy on prior target commits.

A one-sided Wilson bound is an evidence screen, not an arbitrary-shift guarantee.
Commit dependence, missing outcomes and future drift can invalidate its premise.
"""
from dataclasses import asdict, dataclass
from math import sqrt


@dataclass
class ValidationEvidence:
    commits: int
    failing_commits: int
    missed_commits: int
    failing_tests: int
    missed_tests: int
    observed_miss_rate: float | None
    miss_upper_bound: float
    failure_recall: float | None
    accepted: bool
    reasons: list[str]

    def to_dict(self):
        return asdict(self)


def validate_outcomes(outcomes, risk_target=.05, min_failing_commits=10, min_recall=.9):
    if not 0 < risk_target < 1:
        raise ValueError('Risk target must lie strictly between zero and one')
    n = len(outcomes)
    failures = sum(o[1] for o in outcomes)
    missed = sum(o[2] for o in outcomes)
    failing_commits = sum(o[1] > 0 for o in outcomes)
    misses = sum(o[2] > 0 for o in outcomes)
    if any(f < 0 or m < 0 or m > f for _, f, m in outcomes):
        raise ValueError('Invalid validation outcomes')
    rate = misses / n if n else None
    z = 1.6448536269514722  # one-sided 95% normal quantile
    upper = ((rate + z*z/(2*n) + z*sqrt(rate*(1-rate)/n + z*z/(4*n*n))) /
             (1+z*z/n)) if n else 1.
    recall = 1 - missed/failures if failures else None
    reasons = []
    if upper > risk_target:
        reasons.append('upper confidence bound on historical miss rate exceeds target')
    if failing_commits < min_failing_commits:
        reasons.append(f'fewer than {min_failing_commits} failure-bearing audit commits')
    if recall is None or recall < min_recall:
        reasons.append(f'historical failure recall below {min_recall:.0%} or undefined')
    return ValidationEvidence(n, failing_commits, misses, failures, missed, rate,
                              upper, recall, not reasons, reasons)
