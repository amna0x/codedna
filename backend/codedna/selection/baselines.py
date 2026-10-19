"""Regression test selection baselines and their comparison.

Strategies (names follow docs/RESEARCH_PLAN.md):

* ``all`` (B0) — run every test class.
* ``dependency`` (B4) — test classes that depend, directly or transitively,
  on a changed type in the static code graph (``impact_analysis``).
* ``coverage`` — test classes whose recorded JaCoCo coverage (at the BASE
  commit) includes a changed method/constructor/field or type; a
  class/method-level variant of Ekstazi-style selection.

Rules shared by all strategies, chosen to stay *safe*:

* changed or new test classes are always selected;
* for ``coverage``, tests without coverage data are selected;
* when a non-Java file changed, every test is selected unless
  ``non_java="ignore"`` (build files and resources can change behaviour,
  and nothing here analyses them).

The universe is the set of test classes Maven Surefire runs by default in
HEAD (see ``discovery``).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path

from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna.impact_analysis import compute_impact
from codedna.java_analysis import analyze_changes
from codedna.java_analysis.parser import TYPE_NODES
from codedna.test_mapping.discovery import discover_tests_for_commit
from codedna.test_mapping.results import CoverageMap, TestRunResult

STRATEGIES = ("all", "dependency", "coverage")
_TYPE_KINDS = frozenset(TYPE_NODES.values())


class SelectionError(ValueError):
    """The requested selection cannot be computed (e.g. missing coverage map)."""


@dataclass
class SelectedTest:
    test: str
    reasons: list[str] = field(default_factory=list)


@dataclass
class SelectionReport:
    repository: str
    base_commit: str
    head_commit: str
    strategy: str
    total_tests: int
    selected: list[SelectedTest]
    skipped: list[str]
    selection_ratio: float
    estimated_time: dict | None
    warnings: list[str]

    @property
    def selected_ids(self) -> set[str]:
        return {item.test for item in self.selected}

    def to_dict(self) -> dict:
        data = asdict(self)
        data["selected_count"] = len(self.selected)
        return data


def select_tests(repo_path: str | Path, base: str, head: str, strategy: str, *,
                 coverage_map: CoverageMap | None = None, durations: TestRunResult | None = None,
                 non_java: str = "retest-all") -> SelectionReport:
    if strategy not in STRATEGIES:
        raise SelectionError(f"unknown strategy {strategy!r}; choose from {STRATEGIES}")
    if strategy == "coverage" and coverage_map is None:
        raise SelectionError("the coverage strategy needs a coverage map (run-tests --per-test-coverage)")
    repo = resolve_repository(repo_path)
    base_sha, head_sha = resolve_commit(repo, base), resolve_commit(repo, head)

    discovery = discover_tests_for_commit(repo, head_sha)
    universe = sorted(t.id for t in discovery.tests if t.runs_by_default)
    test_files = {t.id: t.file for t in discovery.tests}
    changes = analyze_changes(repo, base_sha, head_sha)
    warnings = list(changes.warnings)
    chosen: dict[str, SelectedTest] = {}

    def pick(test_id: str, reason: str) -> None:
        if test_id in universe:
            entry = chosen.setdefault(test_id, SelectedTest(test_id))
            if reason not in entry.reasons:
                entry.reasons.append(reason)

    changed_paths = {p for c in changes.changed_files for p in (c.path, c.old_path) if p}
    for test_id in universe:
        if test_files[test_id] in changed_paths:
            pick(test_id, "test class changed")

    non_java_changes = [c.path for c in changes.changed_files if not c.is_java]
    if strategy == "all":
        for test_id in universe:
            pick(test_id, "retest-all")
    elif non_java_changes and non_java == "retest-all":
        for test_id in universe:
            pick(test_id, f"non-Java file changed ({non_java_changes[0]}"
                          f"{' and others' if len(non_java_changes) > 1 else ''}); "
                          "falling back to retest-all")
    elif strategy == "dependency":
        impact = compute_impact(repo, base_sha, head_sha)
        for candidate in impact.candidate_tests:
            pick(candidate["type"].removeprefix("type:"), candidate["reason"])
    else:
        if coverage_map.commit != base_sha:
            warnings.append(f"coverage map is from commit {coverage_map.commit[:12]}, not BASE "
                            f"{base_sha[:12]}; selection may miss or over-select tests")
        _select_by_coverage(changes, coverage_map, universe, pick)

    if non_java_changes and non_java == "ignore":
        warnings.append(f"{len(non_java_changes)} non-Java change(s) ignored by request: "
                        f"{non_java_changes[:5]}")
    hidden = [t.id for t in discovery.tests if not t.runs_by_default]
    if hidden:
        warnings.append(f"{len(hidden)} test class(es) outside Surefire's default includes are "
                        f"not considered: {hidden[:5]}")

    selected = [chosen[t] for t in universe if t in chosen]
    skipped = [t for t in universe if t not in chosen]
    return SelectionReport(
        repository=str(repo), base_commit=base_sha, head_commit=head_sha, strategy=strategy,
        total_tests=len(universe), selected=selected, skipped=skipped,
        selection_ratio=round(len(selected) / len(universe), 4) if universe else 0.0,
        estimated_time=_estimate_time(selected, universe, durations),
        warnings=warnings,
    )


def _select_by_coverage(changes, coverage_map: CoverageMap, universe: list[str], pick) -> None:
    for test_id in universe:
        if test_id not in coverage_map.tests:
            pick(test_id, "no coverage data for this test")

    for changed in changes.changed_files:
        if not changed.is_java:
            continue
        base_path = changed.old_path or changed.path
        java = changed.java
        if java is None or java.unresolved:
            for test_id, cov in coverage_map.tests.items():
                if base_path in cov.files:
                    pick(test_id, f"covers {base_path}, whose change could not be mapped")
            continue
        for declaration in java.declarations:
            if declaration.code_changed is False:
                continue
            is_type = declaration.kind in _TYPE_KINDS
            for test_id, cov in coverage_map.tests.items():
                if is_type and declaration.id in cov.types:
                    pick(test_id, f"covers changed type {declaration.id}")
                elif not is_type and declaration.id in cov.members:
                    pick(test_id, f"covers {declaration.change} {declaration.kind} {declaration.id}")
                elif not is_type and declaration.change == "added" \
                        and declaration.parent in cov.types:
                    # A new member (e.g. an overload or override) can change
                    # behaviour of a class the test already uses.
                    pick(test_id, f"covers {declaration.parent}, which gained {declaration.id}")
        if any(o.code_changed is not False for o in java.outside_declarations):
            for test_id, cov in coverage_map.tests.items():
                if base_path in cov.files:
                    pick(test_id, f"covers {base_path}, whose imports/package changed")


def _estimate_time(selected: list[SelectedTest], universe: list[str],
                   durations: TestRunResult | None) -> dict | None:
    if durations is None:
        return None
    known = {t: r.time for t, r in durations.tests.items()}
    unknown = [t for t in universe if t not in known]
    selected_time = sum(known.get(s.test, 0.0) for s in selected)
    total_time = sum(known.get(t, 0.0) for t in universe)
    return {
        "selected_seconds": round(selected_time, 3),
        "all_seconds": round(total_time, 3),
        "saved_ratio": round(1 - selected_time / total_time, 4) if total_time else 0.0,
        "tests_without_duration": unknown,
        "source_commit": durations.commit,
        "note": "sum of Surefire test-class times; excludes build start-up and compilation",
    }


def compare_strategies(repo_path: str | Path, base: str, head: str, ground_truth: TestRunResult,
                       *, coverage_map: CoverageMap | None = None,
                       non_java: str = "retest-all") -> dict:
    """Compare strategies against a full-suite run of HEAD (the ground truth)."""
    repo = resolve_repository(repo_path)
    head_sha = resolve_commit(repo, head)
    warnings = []
    if ground_truth.commit != head_sha:
        warnings.append(f"ground truth was run on {ground_truth.commit[:12]}, not HEAD "
                        f"{head_sha[:12]}; failure detection numbers are not valid")
    if ground_truth.per_test_coverage:
        warnings.append("ground truth comes from per-test runs; prefer a single full-suite run")

    rows = []
    strategies = [s for s in STRATEGIES if s != "coverage" or coverage_map is not None]
    if coverage_map is None:
        warnings.append("no coverage map given; the coverage strategy was not evaluated")
    for strategy in strategies:
        report = select_tests(repo, base, head, strategy, coverage_map=coverage_map,
                              durations=ground_truth, non_java=non_java)
        universe = set(report.skipped) | report.selected_ids
        failing = sorted(t for t in ground_truth.failing_tests if t in universe)
        caught = [t for t in failing if t in report.selected_ids]
        missed = [t for t in failing if t not in report.selected_ids]
        rows.append({
            "strategy": strategy,
            "selected": len(report.selected),
            "total": report.total_tests,
            "selection_ratio": report.selection_ratio,
            "estimated_time": report.estimated_time,
            "failing_tests": failing,
            "caught": caught,
            "missed": missed,
            "safe": not missed,
            "warnings": report.warnings,
        })
    return {
        "repository": str(repo),
        "base_commit": resolve_commit(repo, base),
        "head_commit": head_sha,
        "ground_truth": {"commit": ground_truth.commit,
                         "failing_tests": ground_truth.failing_tests,
                         "test_count": len(ground_truth.tests)},
        "strategies": rows,
        "warnings": warnings,
        "note": "one commit pair only; aggregate over many commits before drawing conclusions",
    }
