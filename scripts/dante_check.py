"""Run the DANTE-H / calibrated-stopping check (D-040, docs/DANTE_B10_PROTOCOL.md).

Reads each project's ``dataset.csv`` from ``--data`` (a study folder), writes
``dante-seed<N>.json`` per project and seed to ``--out``, then
``summary.json`` / ``summary.md``: means over seeds per project and the
decision-rule verdict fixed in the protocol.

Usage (from the repository root):
    python scripts/dante_check.py --data experiments/results/study11-2026-10-21 \\
        --out experiments/results/dante-b10-2026-10-24 --seeds 0 1 2 3 4 --workers 4 \\
        hikaricp littleproxy jade4j wicket-bootstrap
"""

from __future__ import annotations

import argparse
import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import mean

POLICIES = ("D2_dante_stop", "B10_hybrid")
POLICY_METRICS = ("mean_time_ratio", "failing_test_recall", "commit_safety_rate",
                  "mean_estimated_skip_risk", "observed_miss_rate")
PAIRS = ("D2 − D1 at same time", "D2 − B10", "B10 − B3 at same time", "D1 − B3 at D2 time")


def run_project(name: str, data: str, out: str, seeds: list[int]) -> str:
    from codedna.models.dante_check import dante_check
    from codedna.test_history.features import Dataset

    csv_path = Path(data) / name / "dataset.csv"
    dataset = Dataset.from_csv(csv_path)
    folder = Path(out) / name
    folder.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    for seed in seeds:
        target = folder / f"dante-seed{seed}.json"
        if not target.is_file():
            report = dante_check(dataset, seed=seed)
            report["input"] = {"dataset_csv_sha256": digest, "rows": len(dataset.rows)}
            target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return f"{name}: done"


def _mean(values):
    values = [v for v in values if v is not None]
    return round(mean(values), 4) if values else None


def summarise(out: Path, names: list[str], seeds: list[int], risk_target: float = 0.05) -> dict:
    summary: dict = {"seeds": seeds, "projects": {}}
    for name in names:
        runs = [json.loads((out / name / f"dante-seed{s}.json").read_text(encoding="utf-8"))
                for s in seeds]
        runs = [r for r in runs if "policies" in r]
        project: dict = {"runs": len(runs),
                         "test_commits": runs[0]["policies"]["B10_hybrid"]["commits"] if runs else None,
                         "test_commits_with_failures":
                             runs[0]["policies"]["B10_hybrid"]["commits_with_failures"] if runs else None,
                         "warnings": sorted({w for r in runs for w in r["warnings"]})}
        for policy in POLICIES:
            project[policy] = {m: _mean([r["policies"][policy][m] for r in runs])
                               for m in POLICY_METRICS}
            observed = project[policy]["observed_miss_rate"]
            project[policy]["meets_risk_target"] = None if observed is None else observed <= risk_target
        for key in ("D1@D2", "B3@D2", "B3@B10"):
            project[key] = {m: _mean([r["cost_matched"][key][m] for r in runs])
                            for m in ("budget", "time", "recall", "safety")}
        project["differences"] = {}
        for pair in PAIRS:
            entry = {}
            for metric in ("time", "recall", "safety"):
                diffs = [r["bootstrap"]["differences"][pair][metric] for r in runs]
                cis = [d["ci"] for d in diffs if d["ci"]]
                entry[metric] = {
                    "estimate": _mean([d["estimate"] for d in diffs]),
                    "ci_mean": [_mean([c[0] for c in cis]), _mean([c[1] for c in cis])] if cis else None,
                    "seeds_ci_excludes_zero_positive": sum(1 for c in cis if c[0] > 0),
                    "seeds_ci_excludes_zero_negative": sum(1 for c in cis if c[1] < 0),
                    "seeds_with_ci": len(cis)}
            project["differences"][pair] = entry
        project["overhead"] = {
            "dante_scoring_seconds_all_rows": _mean(
                [r["overhead"]["dante_scoring_seconds_all_rows"] for r in runs]),
            "d2_decide_ms_per_test_commit": _mean(
                [r["overhead"]["d2_decide_ms_per_test_commit"] for r in runs]),
            "rows": runs[0]["overhead"]["rows"] if runs else None}
        summary["projects"][name] = project
    summary["verdict"] = _verdict(summary["projects"])
    return summary


def _verdict(projects: dict) -> dict:
    """Decision rule from docs/DANTE_B10_PROTOCOL.md, on seed-mean estimates and intervals."""
    safety = {n: p["differences"]["D2 − D1 at same time"]["safety"] for n, p in projects.items()}
    non_negative = all(s["estimate"] is not None and s["estimate"] >= 0 for s in safety.values())
    excludes_zero = sum(1 for s in safety.values() if s["ci_mean"] and s["ci_mean"][0] > 0)
    below_zero = [n for n, s in safety.items() if s["ci_mean"] and s["ci_mean"][1] < 0]
    meets = sum(1 for p in projects.values() if p["D2_dante_stop"]["meets_risk_target"])
    fails = sum(1 for p in projects.values() if p["D2_dante_stop"]["meets_risk_target"] is False)
    if below_zero or fails >= 2:
        verdict = "not supported"
    elif non_negative and excludes_zero >= 2 and meets >= 3:
        verdict = "supported"
    else:
        verdict = "inconclusive"
    return {"verdict": verdict, "d2_minus_d1_safety_non_negative_all": non_negative,
            "projects_ci_excludes_zero": excludes_zero, "projects_ci_below_zero": below_zero,
            "projects_meeting_target": meets, "projects_failing_target": fails}


def to_markdown(summary: dict) -> str:
    lines = ["# DANTE-H / calibrated stopping: summary", "",
             "Generated by `scripts/dante_check.py`; protocol in `docs/DANTE_B10_PROTOCOL.md`.",
             "Means over seeds. DANTE-H is a history-only approximation of DANTE.", "",
             f"**Verdict (pre-specified rule): {summary['verdict']['verdict']}**", "",
             "| Project | Policy | Time | Recall | Safety | Est. risk | Obs. miss | Target met |",
             "|---|---|---|---|---|---|---|---|"]
    for name, p in summary["projects"].items():
        for policy in POLICIES:
            m = p[policy]
            lines.append(f"| {name} | {policy} | {m['mean_time_ratio']} | {m['failing_test_recall']} | "
                         f"{m['commit_safety_rate']} | {m['mean_estimated_skip_risk']} | "
                         f"{m['observed_miss_rate']} | {m['meets_risk_target']} |")
        for key in ("D1@D2", "B3@D2", "B3@B10"):
            m = p[key]
            lines.append(f"| {name} | {key} (budget {m['budget']}) | {m['time']} | {m['recall']} | "
                         f"{m['safety']} | | | |")
    lines += ["", "## Paired differences (estimate, mean 95% interval over seeds)", "",
              "| Project | Comparison | Δ time | Δ recall | Δ safety |", "|---|---|---|---|---|"]
    for name, p in summary["projects"].items():
        for pair, d in p["differences"].items():
            cell = lambda m: f"{d[m]['estimate']} {d[m]['ci_mean']}"  # noqa: E731
            lines.append(f"| {name} | {pair} | {cell('time')} | {cell('recall')} | {cell('safety')} |")
    lines += ["", "## Overhead", "", "| Project | Rows | DANTE-H scoring (s, all rows) | "
              "D2 decide (ms / test commit) |", "|---|---|---|---|"]
    for name, p in summary["projects"].items():
        o = p["overhead"]
        lines.append(f"| {name} | {o['rows']} | {o['dante_scoring_seconds_all_rows']} | "
                     f"{o['d2_decide_ms_per_test_commit']} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("projects", nargs="+")
    args = parser.parse_args()
    out = Path(args.out)
    with ProcessPoolExecutor(args.workers) as pool:
        for message in pool.map(run_project, args.projects, [args.data] * len(args.projects),
                                [args.out] * len(args.projects), [args.seeds] * len(args.projects)):
            print(message, flush=True)
    summary = summarise(out, args.projects, args.seeds)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(to_markdown(summary), encoding="utf-8")
    print(json.dumps(summary["verdict"], indent=2))


if __name__ == "__main__":
    main()
