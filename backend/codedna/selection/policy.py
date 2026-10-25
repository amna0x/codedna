"""Must-run (pinned) tests: tests a selection may never skip (D-050).

A project lists them in ``.codedna/policy.toml``::

    [[must_run]]
    tests = ["example.PaymentTest", "example.security.*"]
    reason = "payment and security checks run on every change"

``tests`` holds test IDs or ``fnmatch`` patterns (``*``, ``?``, ``[...]``)
over the IDs the language plugin reports (for Java: qualified class names).
Patterns are case-sensitive.

Rules of the policy, chosen so that a change cannot weaken its own checks:

* The file is read from the BASE commit, never from HEAD or the working tree.
  A change that edits the policy is analysed under the old one, with a warning;
  the new policy applies from the next change on.
* A policy that cannot be read or is malformed pins *every* test: when the
  pinned set is unknown, nothing may be skipped.
* A pattern that matches no test is reported, so a typo is never silent.

Pinned tests only ever add to a selection. Research baselines in
``compare_strategies`` and the experiments ignore the policy, so study numbers
are unaffected.

Other rules (for example later security checks) plug in through the
``codedna.policies`` entry-point group: each entry point names a zero-argument
callable returning an object with a ``name`` and a
``pinned(context) -> dict[test_id, reason]`` method. Rules come from installed
packages only; nothing is loaded from the analysed repository.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from fnmatch import fnmatchcase
from importlib.metadata import entry_points
from pathlib import Path
from typing import Protocol

from codedna.git_analysis.git import GitCommandError, run_git

POLICY_FILE = ".codedna/policy.toml"
ENTRY_POINT_GROUP = "codedna.policies"


class PolicyRule(Protocol):
    name: str

    def pinned(self, context: "PolicyContext") -> dict[str, str]:
        """Test ID → reason for every test this rule forbids skipping."""


@dataclass(frozen=True)
class PolicyContext:
    repo: Path
    base_commit: str
    head_commit: str
    tests: tuple[str, ...]  # the selection universe
    changed_paths: frozenset[str]


@dataclass
class PatternRule:
    patterns: list[str]
    reason: str
    name: str = "must_run"

    def matches(self, tests) -> dict[str, list[str]]:
        return {p: [t for t in tests if fnmatchcase(t, p)] for p in self.patterns}

    def pinned(self, context: PolicyContext) -> dict[str, str]:
        return {t: self.reason for found in self.matches(context.tests).values() for t in found}


@dataclass
class PolicyResult:
    pinned: dict[str, list[str]] = field(default_factory=dict)  # test ID → reasons
    warnings: list[str] = field(default_factory=list)
    source: str | None = None  # where the project policy came from

    def to_dict(self) -> dict:
        return {"pinned": sorted(self.pinned), "source": self.source}


def read_policy(repo: Path, base_commit: str) -> tuple[list[PatternRule], str | None]:
    """Pattern rules from BASE's policy file; ``([], None)`` when there is none.

    Raises ``ValueError`` when the file exists but is not a valid policy.
    """
    if not run_git(repo, "ls-tree", "--name-only", base_commit, "--", POLICY_FILE).strip():
        return [], None
    try:
        text = run_git(repo, "show", f"{base_commit}:{POLICY_FILE}")
    except GitCommandError as exc:
        raise ValueError(f"{POLICY_FILE} at BASE cannot be read") from exc
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"{POLICY_FILE} is not valid TOML: {exc}") from exc
    unknown = set(data) - {"must_run"}
    if unknown:
        raise ValueError(f"{POLICY_FILE} has unknown sections: {sorted(unknown)}")
    groups = data.get("must_run", [])
    if not isinstance(groups, list):
        raise ValueError(f"{POLICY_FILE}: write each group as [[must_run]]")
    rules = []
    for number, group in enumerate(groups, 1):
        if not isinstance(group, dict) or set(group) - {"tests", "reason"}:
            raise ValueError(f"{POLICY_FILE}: must_run group {number} may only have "
                             "'tests' and 'reason'")
        tests, reason = group.get("tests"), group.get("reason", "listed in the project policy")
        if (not isinstance(tests, list) or not tests
                or not all(isinstance(t, str) and t.strip() for t in tests)):
            raise ValueError(f"{POLICY_FILE}: must_run group {number} needs a non-empty "
                             "'tests' list of strings")
        if not isinstance(reason, str) or not reason.strip():
            raise ValueError(f"{POLICY_FILE}: must_run group {number} has an empty 'reason'")
        rules.append(PatternRule([t.strip() for t in tests], reason.strip()))
    return rules, f"{POLICY_FILE} at {base_commit[:12]}"


def installed_rules() -> list:
    """Entry points of add-on rules; loaded lazily so a broken one fails safe."""
    return list(entry_points(group=ENTRY_POINT_GROUP))


def apply_policy(repo: Path, base_commit: str, head_commit: str, tests: list[str],
                 changed_paths: set[str], *, extra: list[str] | None = None) -> PolicyResult:
    """Which of ``tests`` must run for this change, and why.

    ``extra`` holds patterns given for this one request (CLI ``--must-run``).
    """
    result = PolicyResult()

    def pin(test: str, reason: str) -> None:
        reasons = result.pinned.setdefault(test, [])
        if reason not in reasons:
            reasons.append(reason)

    if POLICY_FILE in changed_paths:
        result.warnings.append(f"this change edits {POLICY_FILE}; the BASE policy is used, "
                               "the new one applies from the next change")
    rules: list = []
    try:
        project_rules, result.source = read_policy(repo, base_commit)
        rules += project_rules
    except ValueError as exc:
        result.warnings.append(f"{exc}; every test is pinned until the policy is fixed")
        for test in tests:
            pin(test, "must-run policy unreadable: nothing may be skipped")
        return result
    if extra:
        rules.append(PatternRule(list(extra), "pinned by request"))
    for rule in rules:
        for pattern, found in rule.matches(tests).items():
            if not found:
                result.warnings.append(f"must-run pattern {pattern!r} matches no test")
            for test in found:
                pin(test, f"must-run: {rule.reason}")
    context = PolicyContext(repo, base_commit, head_commit, tuple(tests), frozenset(changed_paths))
    for entry in installed_rules():
        try:
            rule = entry.load()()
            name = str(getattr(rule, "name", entry.name))
            pinned = {str(t): str(r) for t, r in dict(rule.pinned(context)).items()}
        except Exception as exc:  # a broken add-on rule must fail safe, not silently
            result.warnings.append(f"policy rule {entry.name!r} failed ({exc}); "
                                   "every test is pinned")
            for test in tests:
                pin(test, "a policy rule failed: nothing may be skipped")
            continue
        for test, reason in pinned.items():
            if test in tests:
                pin(test, f"{name}: {reason}")
    return result
