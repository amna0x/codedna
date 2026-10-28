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
* must-run tests of the project policy are always selected (D-050);
* for ``coverage``, tests without coverage data are selected;
* when a file no installed language plugin analyses changed, every test is
  selected unless ``non_java="ignore"`` (build files and resources can
  change behaviour, and nothing here analyses them). The option keeps its
  historical name; it covers every unanalysed file, not only non-Java ones;
* a changed file of a language that has no tests in the universe counts as
  unanalysed too: dependencies between languages are not analysed (D-060),
  so such a change (a Python build script in a Java project, say) could
  only be caught by running everything.

The universe is the set of tests the build runs by default in HEAD, over
every installed language plugin (Maven Surefire's for Java, pytest's for
Python; see each plugin's discovery).
"""

from __future__ import annotations

from codedna.performance import timed

from dataclasses import asdict, dataclass, field
from pathlib import Path

from codedna.git_analysis.git import reuse_git_validation
from codedna.dependency_graph.cache import reuse_parse_cache, operation_parse_cache
from codedna.git_analysis.git import resolve_commit, resolve_repository
from codedna.impact_analysis import compute_impact
from codedna.plugins import load_plugins
from codedna.plugins.languages import analyze_changes, commit_tests, type_kinds
from codedna.selection.policy import apply_policy
from codedna.test_mapping.results import CoverageMap, TestRunResult

STRATEGIES = ("all", "dependency", "coverage")


class SelectionError(ValueError):
    """The requested selection cannot be computed (e.g. missing coverage map)."""


@dataclass
class SelectedTest:
    test: str
    reasons: list[str] = field(default_factory=list)
    file: str | None = None  # where discovery found the test, for opening it


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
    policy: dict | None = None  # must-run tests (D-050); None when the policy was not applied

    @property
    def selected_ids(self) -> set[str]:
        return {item.test for item in self.selected}

    def to_dict(self) -> dict:
        data = asdict(self)
        data["selected_count"] = len(self.selected)
        return data


@reuse_git_validation
@timed('test_selection')
@reuse_parse_cache
def select_tests(repo_path: str | Path, base: str, head: str, strategy: str, *,
                 coverage_map: CoverageMap | None = None, durations: TestRunResult | None = None,
                 non_java: str = "retest-all", must_run: list[str] | None = None,
                 policy: bool = True, cache: dict | None = None) -> SelectionReport:
    """Select tests for BASE..HEAD.

    With ``policy`` (default), tests pinned by the project's must-run policy
    or by ``must_run`` patterns are always selected (D-050). ``cache`` is an
    optional parse cache keyed by blob SHA, reused across calls on one
    repository (results are the same; only parsing is skipped).
    """
    if strategy not in STRATEGIES:
        raise SelectionError(f"unknown strategy {strategy!r}; choose from {STRATEGIES}")
    if strategy == "coverage" and coverage_map is None:
        raise SelectionError("the coverage strategy needs a coverage map (run-tests --per-test-coverage)")
    repo = resolve_repository(repo_path)
    base_sha, head_sha = resolve_commit(repo, base), resolve_commit(repo, head)

    registry = load_plugins()
    if cache is None:
        cache = operation_parse_cache(repo, registry)
    discovery = commit_tests(repo, head_sha, registry=registry, cache=cache)
    universe = sorted(t.id for t in discovery.tests if t.runs_by_default)
    test_files = {t.id: t.file for t in discovery.tests}
    tested_languages = {discovery.language_of(t) for t in universe}
    changes = analyze_changes(repo, base_sha, head_sha, registry=registry)
    warnings = list(changes.warnings)
    chosen: dict[str, SelectedTest] = {}

    def pick(test_id: str, reason: str) -> None:
        if test_id in universe:
            entry = chosen.setdefault(test_id, SelectedTest(test_id, file=test_files[test_id]))
            if reason not in entry.reasons:
                entry.reasons.append(reason)

    changed_paths = {p for c in changes.changed_files for p in (c.path, c.old_path) if p}
    for test_id in universe:
        if test_files[test_id] in changed_paths:
            pick(test_id, "test class changed")

    unanalysed = [c.path for c in changes.changed_files
                  if c.language is None or c.language not in tested_languages]
    untested = sorted({c.language for c in changes.changed_files
                       if c.language is not None and c.language not in tested_languages}
                      if universe else ())
    for language in untested:
        count = sum(c.language == language for c in changes.changed_files)
        warnings.append(f"{count} changed {language} file(s) count as unanalysed: no {language} "
                        "tests were found, and dependencies between languages are not analysed")
    if strategy == "all":
        for test_id in universe:
            pick(test_id, "retest-all")
    elif unanalysed and non_java == "retest-all":
        for test_id in universe:
            pick(test_id, f"unanalysed file changed ({unanalysed[0]}"
                          f"{' and others' if len(unanalysed) > 1 else ''}); "
                          "falling back to retest-all")
    elif strategy == "dependency":
        impact = compute_impact(repo, base_sha, head_sha, cache=cache, changes=changes,
                                registry=registry)
        for candidate in impact.candidate_tests:
            pick(candidate["type"].removeprefix("type:"), candidate["reason"])
        if impact.unanalysed_changes and non_java == "retest-all":
            # Impact could not follow these changes, so no test may be left out.
            first = impact.unanalysed_changes[0]["path"]
            for test_id in universe:
                pick(test_id, f"impact not analysed for {first}; falling back to retest-all")
    else:
        if coverage_map.commit != base_sha:
            warnings.append(f"coverage map is from commit {coverage_map.commit[:12]}, not BASE "
                            f"{base_sha[:12]}; selection may miss or over-select tests")
        _select_by_coverage(changes, coverage_map, universe, pick, type_kinds(registry))

    if unanalysed and non_java == "ignore":
        warnings.append(f"{len(unanalysed)} unanalysed change(s) ignored by request: "
                        f"{unanalysed[:5]}")
    hidden = [t.id for t in discovery.tests if not t.runs_by_default]
    if hidden:
        warnings.append(f"{len(hidden)} test class(es) the build does not run by default are "
                        f"not considered: {hidden[:5]}")

    policy_report = None
    if policy:
        pins = apply_policy(repo, base_sha, head_sha, universe, changed_paths, extra=must_run)
        for test_id, reasons in pins.pinned.items():
            for reason in reasons:
                pick(test_id, reason)
        warnings.extend(pins.warnings)
        policy_report = pins.to_dict()
    elif must_run:
        raise SelectionError("must-run patterns need the policy to be applied")

    selected = [chosen[t] for t in universe if t in chosen]
    skipped = [t for t in universe if t not in chosen]
    return SelectionReport(
        repository=str(repo), base_commit=base_sha, head_commit=head_sha, strategy=strategy,
        total_tests=len(universe), selected=selected, skipped=skipped,
        selection_ratio=round(len(selected) / len(universe), 4) if universe else 0.0,
        estimated_time=_estimate_time(selected, universe, durations),
        warnings=warnings, policy=policy_report,
    )


def _select_by_coverage(changes, coverage_map: CoverageMap, universe: list[str], pick,
                        type_kinds: frozenset[str]) -> None:
    for test_id in universe:
        if test_id not in coverage_map.tests:
            pick(test_id, "no coverage data for this test")

    for changed in changes.changed_files:
        if changed.language is None:
            continue
        base_path = changed.old_path or changed.path
        mapping = changed.mapping
        if mapping is None or mapping.unresolved:
            for test_id, cov in coverage_map.tests.items():
                if base_path in cov.files:
                    pick(test_id, f"covers {base_path}, whose change could not be mapped")
            continue
        for declaration in mapping.declarations:
            if declaration.code_changed is False:
                continue
            is_type = declaration.kind in type_kinds
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
        if any(o.code_changed is not False for o in mapping.outside_declarations):
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
        # Baselines are compared as published: no must-run policy (D-050).
        report = select_tests(repo, base, head, strategy, coverage_map=coverage_map,
                              durations=ground_truth, non_java=non_java, policy=False)
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
