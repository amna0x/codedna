"""History replay: commit-by-commit timelines of what each policy would have done.

An experiment report (``codedna history experiment``) measures policies on the
chronological test split. A replay walks those same test commits in order so
the IDE can play them back: per commit, how much test time each policy spent
and whether it missed a failing test, with running totals.

Two sources, both produced by ``run_experiment`` (so the numbers are the
experiment's own, never recomputed with different code):

* ``per_commit`` — kept in every report: (time ratio, failing, missed) per
  policy. Enough for time and miss curves, but no SHAs, test names or
  estimated risk.
* ``replay`` — written when the experiment runs with ``trace=True``
  (``--replay``): per commit the SHA, suite size and seconds, failing test
  names, and per policy the tests run, seconds, missed test names, the
  estimated skip risk and whether it fell back to the full suite.

Every timeline is checked against the report's own ``policies`` summary;
the result is in ``checks`` and any mismatch is listed in ``notes``.
Nothing is estimated here: missing values stay ``None``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Iterable

if TYPE_CHECKING:
    from codedna.test_history.features import Row

TRACE_VERSION = 1

# Shown in this order. "B3@B10_hybrid" is the rules order stopped at the budget
# that spends the same real time as CodeDNA (from the report's cost matching).
POLICIES = (
    ("B0_retest_all", "Run every test",
     "The full suite on every commit: nothing missed, nothing saved."),
    ("B4_dependency", "Dependency only",
     "Tests reachable from the change in the dependency graph, plus changed tests."),
    ("B3@B10_hybrid", "Simple rules, same time",
     "Recently failing tests first, then the shortest, cut off at CodeDNA's mean time."),
    ("B10_hybrid", "CodeDNA",
     "Recently failing tests first; adds tests until the calibrated estimated "
     "chance of missing a failure is at most the risk target."),
)
CODEDNA = "B10_hybrid"
# The report rounds time ratios to 4 places per commit and in its means.
TIME_TOLERANCE = 5e-4
_REPORT_NAME = re.compile(r"^(?:experiment|replay)(?:-seed(\d+))?\.json$")


class ReplayError(ValueError):
    """The file is not an experiment report a replay can be built from."""


# --- recording (called by run_experiment) ---------------------------------------------


def record_trace(test_commits: list[list[Row]],
                 policies: dict[str, Callable[[list[Row]], tuple]]) -> dict:
    """Per-commit detail for each policy, in test-commit order.

    ``policies`` maps a name to the experiment's own ``choose(rows)`` function,
    which returns (selected test ids, decision or None).
    """
    commits = []
    outcomes: dict[str, list[dict]] = {name: [] for name in policies}
    for rows in test_commits:
        failing = sorted(r.test_id for r in rows if r.label)
        suite = sum(r.duration for r in rows)
        commits.append({"sha": rows[0].commit if rows else None,
                        "seq": rows[0].seq if rows else None,
                        "tests": len(rows), "suite_seconds": round(suite, 3),
                        "failing": failing})
        for name, choose in policies.items():
            selected, decision = choose(rows)
            chosen = set(selected)
            seconds = sum(r.duration for r in rows if r.test_id in chosen)
            outcomes[name].append({
                "selected": len(chosen),
                "seconds": round(seconds, 3),
                "time_ratio": round(seconds / suite if suite else len(chosen) / len(rows), 4)
                if rows else 0.0,
                "missed": [t for t in failing if t not in chosen],
                "estimated_risk": None if decision is None
                else round(decision.estimated_skip_risk, 4),
                "fallback": None if decision is None else bool(decision.fallback),
            })
    return {"version": TRACE_VERSION, "commits": commits, "policies": outcomes}


# --- timelines -------------------------------------------------------------------------


def load_report(path: str | Path) -> dict:
    file = Path(path)
    if not file.is_file():
        raise FileNotFoundError(f"report not found: {file}")
    try:
        report = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ReplayError(f"{file} is not JSON ({exc})") from exc
    if not isinstance(report, dict) or "policies" not in report or "config" not in report:
        raise ReplayError(f"{file} is not an experiment report (no 'policies'/'config')")
    return report


def replay_from_file(path: str | Path) -> dict:
    file = Path(path)
    return replay_timeline(load_report(file), project=_project_name(file),
                           source_path=str(file))


def replay_timeline(report: dict, *, project: str | None = None,
                    source_path: str | None = None) -> dict:
    """Normalise an experiment report into a replay timeline for the IDE."""
    trace = report.get("replay")
    per_commit = report.get("per_commit") or {}
    if trace and trace.get("version") != TRACE_VERSION:
        raise ReplayError(f"unsupported replay trace version {trace.get('version')!r}")
    available = trace["policies"] if trace else per_commit
    if not available or not any(key in available for key, _, _ in POLICIES):
        raise ReplayError("the report has no per-commit outcomes to replay "
                          "(re-run 'codedna history experiment', optionally with --replay)")

    config = report.get("config", {})
    notes: list[str] = []
    shown = [(key, label, text) for key, label, text in POLICIES if key in available]
    for key, label, _ in POLICIES:
        if key not in available:
            notes.append(f"{label} ({key}) is not in this report, so it is not shown")

    if trace:
        commits = _commits_from_trace(trace, [key for key, _, _ in shown])
    else:
        commits = _commits_from_per_commit(per_commit, [key for key, _, _ in shown])
        notes.append("compact report: commit SHAs, test names, seconds and estimated risk "
                     "were not recorded (re-run the experiment with --replay for them)")

    cumulative = {key: _cumulative(commits, key) for key, _, _ in shown}
    summary = {key: _summary(commits, key) for key, _, _ in shown}
    checks = _check(summary, report.get("policies", {}), notes)
    _fill_from_report(summary, report.get("policies", {}))
    matched = (report.get("cost_matched") or {}).get(f"{CODEDNA} vs B3", {})

    return {
        "project": project or report.get("project"),
        "source": {
            "kind": "trace" if trace else "per_commit",
            "path": source_path,
            "seed": config.get("seed"),
            "model": config.get("model"),
            "calibration": config.get("calibration"),
            "dataset_sha256": (report.get("reproducibility") or {}).get("dataset_sha256"),
            "splits": config.get("splits"),
        },
        "risk_target": config.get("risk_target"),
        "rules_budget_at_same_time": matched.get("baseline_budget"),
        "policies": [{"key": key, "label": label, "description": text}
                     for key, label, text in shown],
        "commits": commits,
        "cumulative": cumulative,
        "summary": summary,
        "events": _events(commits),
        "checks": checks,
        "notes": notes,
    }


def _commits_from_trace(trace: dict, keys: list[str]) -> list[dict]:
    result = []
    for index, commit in enumerate(trace["commits"]):
        outcomes = {}
        for key in keys:
            o = trace["policies"][key][index]
            outcomes[key] = {"time_ratio": o["time_ratio"], "missed": len(o["missed"]),
                             "missed_tests": o["missed"], "selected": o["selected"],
                             "seconds": o["seconds"], "estimated_risk": o["estimated_risk"],
                             "fallback": o["fallback"]}
        result.append({"index": index, "sha": commit["sha"], "tests": commit["tests"],
                       "suite_seconds": commit["suite_seconds"],
                       "failing": len(commit["failing"]), "failing_tests": commit["failing"],
                       "outcomes": outcomes})
    return result


def _commits_from_per_commit(per_commit: dict, keys: list[str]) -> list[dict]:
    fields = per_commit.get("fields", ["time_ratio", "failing", "missed"])
    column = {name: fields.index(name) for name in ("time_ratio", "failing", "missed")}
    lengths = {len(per_commit[key]) for key in keys}
    if len(lengths) != 1:
        raise ReplayError(f"policies have different commit counts: {sorted(lengths)}")
    result = []
    for index in range(lengths.pop()):
        failing = {per_commit[key][index][column["failing"]] for key in keys}
        if len(failing) != 1:
            raise ReplayError(f"commit {index}: policies disagree on the failing-test count")
        outcomes = {key: {"time_ratio": per_commit[key][index][column["time_ratio"]],
                          "missed": per_commit[key][index][column["missed"]],
                          "missed_tests": None, "selected": None, "seconds": None,
                          "estimated_risk": None, "fallback": None} for key in keys}
        result.append({"index": index, "sha": None, "tests": None, "suite_seconds": None,
                       "failing": failing.pop(), "failing_tests": None,
                       "outcomes": outcomes})
    return result


def _cumulative(commits: list[dict], key: str) -> dict:
    """Running values after each commit (index-aligned with ``commits``)."""
    series: dict[str, list] = {name: [] for name in (
        "mean_time_ratio", "failures", "failures_missed", "failures_caught",
        "commits_with_miss", "observed_miss_rate", "seconds_run", "seconds_saved",
        "mean_estimated_risk")}
    time_total = failures = missed = commits_missed = 0
    seconds_run = seconds_saved = 0.0
    seconds_known = True
    risk_total, risk_count = 0.0, 0
    for n, commit in enumerate(commits, start=1):
        o = commit["outcomes"][key]
        time_total += o["time_ratio"]
        failures += commit["failing"]
        missed += o["missed"]
        commits_missed += o["missed"] > 0
        if o["seconds"] is None or commit["suite_seconds"] is None:
            seconds_known = False
        else:
            seconds_run += o["seconds"]
            seconds_saved += commit["suite_seconds"] - o["seconds"]
        if o["estimated_risk"] is not None:
            risk_total += o["estimated_risk"]
            risk_count += 1
        series["mean_time_ratio"].append(round(time_total / n, 4))
        series["failures"].append(failures)
        series["failures_missed"].append(missed)
        series["failures_caught"].append(failures - missed)
        series["commits_with_miss"].append(commits_missed)
        series["observed_miss_rate"].append(round(commits_missed / n, 4))
        series["seconds_run"].append(round(seconds_run, 3) if seconds_known else None)
        series["seconds_saved"].append(round(seconds_saved, 3) if seconds_known else None)
        series["mean_estimated_risk"].append(round(risk_total / risk_count, 4)
                                             if risk_count else None)
    return series


def _summary(commits: list[dict], key: str) -> dict:
    n = len(commits)
    outcomes = [c["outcomes"][key] for c in commits]
    failing_commits = [c for c in commits if c["failing"]]
    failures = sum(c["failing"] for c in commits)
    missed = sum(o["missed"] for o in outcomes)
    seconds = [o["seconds"] for o in outcomes]
    suite = [c["suite_seconds"] for c in commits]
    known = n and None not in seconds and None not in suite
    risks = [o["estimated_risk"] for o in outcomes if o["estimated_risk"] is not None]
    fallbacks = [o["fallback"] for o in outcomes if o["fallback"] is not None]
    return {
        "commits": n,
        "commits_with_failures": len(failing_commits),
        "failures": failures,
        "missed_failures": missed,
        "failing_test_recall": round(1 - missed / failures, 4) if failures else None,
        "commit_safety_rate": round(sum(c["outcomes"][key]["missed"] == 0
                                        for c in failing_commits) / len(failing_commits), 4)
        if failing_commits else None,
        "mean_time_ratio": round(sum(o["time_ratio"] for o in outcomes) / n, 4) if n else None,
        "observed_miss_rate": round(sum(o["missed"] > 0 for o in outcomes) / n, 4) if n else None,
        "mean_estimated_skip_risk": round(sum(risks) / len(risks), 4) if risks else None,
        "fallback_rate": round(sum(fallbacks) / len(fallbacks), 4) if fallbacks else None,
        "seconds_run": round(sum(seconds), 3) if known else None,
        "suite_seconds": round(sum(suite), 3) if known else None,
    }


def _check(summary: dict, reported: dict, notes: list[str]) -> list[dict]:
    """Compare the replay's totals with the report's own policy summaries."""
    checks = []
    exact = ("commits", "commits_with_failures", "missed_failures")
    close = ("mean_time_ratio", "observed_miss_rate", "commit_safety_rate",
             "failing_test_recall", "mean_estimated_skip_risk", "fallback_rate")
    for key, ours in summary.items():
        theirs = reported.get(key)
        if theirs is None:  # matched baselines (B3@B10) have no summary in the report
            continue
        for metric in exact + close:
            if metric not in theirs or ours.get(metric) is None or theirs[metric] is None:
                continue
            if metric in exact:
                match = ours[metric] == theirs[metric]
            else:
                match = abs(ours[metric] - theirs[metric]) <= TIME_TOLERANCE
            checks.append({"policy": key, "metric": metric, "replay": ours[metric],
                           "report": theirs[metric], "match": match})
            if not match:
                notes.append(f"{key} {metric}: replay {ours[metric]} but report "
                             f"{theirs[metric]}")
    return checks


def _fill_from_report(summary: dict, reported: dict) -> None:
    """Compact reports keep no per-commit risk or fallback; use the report's own means."""
    for key, ours in summary.items():
        filled = []
        for metric in ("mean_estimated_skip_risk", "fallback_rate"):
            value = (reported.get(key) or {}).get(metric)
            if ours[metric] is None and value is not None:
                ours[metric] = value
                filled.append(metric)
        ours["from_report"] = filled


def _events(commits: list[dict]) -> list[dict]:
    """CodeDNA's notable commits: failures caught or missed, and full-suite fallbacks."""
    events = []
    for commit in commits:
        o = commit["outcomes"].get(CODEDNA)
        if o is None:
            continue
        kind = None
        if commit["failing"]:
            kind = "missed" if o["missed"] else "caught"
        elif o["fallback"]:
            kind = "fallback"
        if kind:
            events.append({"index": commit["index"], "kind": kind, "sha": commit["sha"],
                           "failing": commit["failing"], "missed": o["missed"],
                           "missed_tests": o["missed_tests"], "time_ratio": o["time_ratio"],
                           "estimated_risk": o["estimated_risk"]})
    return events


# --- overview across projects -----------------------------------------------------------

OVERVIEW_METRICS = ("mean_time_ratio", "observed_miss_rate", "mean_estimated_skip_risk",
                    "failing_test_recall", "commit_safety_rate", "missed_failures")


def replay_overview(folders: str | Path | Iterable[str | Path], *,
                    seed: int | None = None) -> dict:
    """Per-project results and the unweighted mean over projects.

    Uses the experiment reports' own per-commit outcomes. With ``seed=None``
    each project is the mean over all its seeds first (as the study summary
    does); a trace and a compact report of the same seed count once.
    """
    by_project: dict[str, dict[int | None, dict]] = {}
    for source in find_replay_sources(folders)["sources"]:
        if seed is not None and source["seed"] != seed:
            continue
        # Sources are sorted traces first, so the first file per seed wins.
        by_project.setdefault(source["project"], {}).setdefault(source["seed"], source)

    projects = []
    for name, seeds in by_project.items():
        timelines = [replay_from_file(s["path"]) for s in seeds.values()]
        first = timelines[0]
        keys = [p["key"] for p in first["policies"]]
        policies = {key: {metric: _mean([t["summary"][key][metric] for t in timelines
                                          if key in t["summary"]])
                          for metric in OVERVIEW_METRICS} for key in keys}
        target = first["risk_target"]
        observed = policies.get(CODEDNA, {}).get("observed_miss_rate")
        projects.append({
            "project": name,
            "seeds": sorted(s for s in seeds if s is not None),
            "kinds": sorted({s["kind"] for s in seeds.values()}),
            "commits": first["summary"][keys[0]]["commits"],
            "commits_with_failures": first["summary"][keys[0]]["commits_with_failures"],
            "risk_target": target,
            "within_risk_target": None if observed is None or target is None
            else observed <= target,
            "policies": policies,
            "mismatches": sum(not c["match"] for t in timelines for c in t["checks"]),
        })
    projects.sort(key=lambda p: p["project"])
    keys = [key for key, _, _ in POLICIES if any(key in p["policies"] for p in projects)]
    overall = {key: {metric: {"mean": _mean(values), "projects": len(values)}
                     for metric in OVERVIEW_METRICS
                     for values in [[p["policies"][key][metric] for p in projects
                                     if key in p["policies"]
                                     and p["policies"][key][metric] is not None]]}
               for key in keys}
    judged = [p for p in projects if p["within_risk_target"] is not None]
    return {
        "seed": seed,
        "policies": [{"key": key, "label": label, "description": text}
                     for key, label, text in POLICIES if key in keys],
        "projects": projects,
        "overall": overall,
        "within_risk_target": {"projects": sum(p["within_risk_target"] for p in judged),
                               "of": len(judged)},
        "note": "unweighted mean over projects (each project counts once); "
                "a project with no failing commits counts as safe but proves little",
    }


def _mean(values: list) -> float | None:
    known = [v for v in values if v is not None]
    return round(sum(known) / len(known), 4) if known else None


# --- discovery -------------------------------------------------------------------------


def find_replay_sources(folders: str | Path | Iterable[str | Path]) -> dict:
    """Experiment reports in ``folders`` (each folder itself and one level down).

    Missing folders are listed in ``missing``; only when none exists is it an error.
    """
    roots = [Path(folders)] if isinstance(folders, (str, Path)) else [Path(f) for f in folders]
    missing = [str(root) for root in roots if not root.is_dir()]
    if len(missing) == len(roots):
        raise FileNotFoundError(f"folder not found: {', '.join(missing)}")
    sources = []
    for root in roots:
        if not root.is_dir():
            continue
        for file in sorted(_candidates(root)):
            match = _REPORT_NAME.match(file.name)
            try:
                report = load_report(file)
            except (ReplayError, OSError):
                continue
            trace = report.get("replay")
            per_commit = report.get("per_commit") or {}
            commits = len(trace["commits"]) if trace else len(per_commit.get(CODEDNA, []))
            if not commits:
                continue
            seed = report.get("config", {}).get("seed")
            if seed is None and match.group(1):
                seed = int(match.group(1))
            sources.append({"project": _project_name(file), "seed": seed, "path": str(file),
                            "kind": "trace" if trace else "per_commit", "commits": commits})
    # Traces first within a project: they carry SHAs, test names and estimated risk.
    sources.sort(key=lambda s: (s["project"], s["kind"] != "trace", s["seed"] or 0, s["path"]))
    return {"folders": [str(root) for root in roots], "missing": missing, "sources": sources}


def _candidates(root: Path) -> Iterable[Path]:
    for pattern in ("*.json", "*/*.json"):
        yield from (file for file in root.glob(pattern) if _REPORT_NAME.match(file.name))


def _project_name(file: Path) -> str:
    """Reports live in a folder named after the project: ``<project>/experiment-seed0.json``."""
    return file.parent.name
