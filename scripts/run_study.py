"""Run the Milestone 4/5 study over several history databases and seeds.

For every project the feature dataset is built once (``dataset.csv``; the slow
part) and reused for every seed. Each seed writes ``evaluate-seed<N>.json`` and
``experiment-seed<N>.json``. Finally ``summary.json`` / ``summary.md``
aggregate the **test split**: mean and standard deviation over seeds per
project, plus an unweighted mean over projects (each project counts once).

Seeds only change model randomness; the chronological split is fixed, so the
seed spread shows model stability, not data variation.

Usage (from the repository root):
    python scripts/run_study.py --out experiments/results/study-2026-10-21 \\
        --seeds 0 1 2 3 4 --workers 3 \\
        hikaricp=experiments/datasets/derived/hikaricp.db littleproxy=...
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import mean, pstdev

POLICY_METRICS = ("mean_time_ratio", "failing_test_recall", "missed_failures", "commit_safety_rate",
                  "fallback_rate", "mean_estimated_skip_risk", "observed_miss_rate")
ORDER_METRICS = ("mean_apfd", "mean_apfdc", "mean_recall_at_25pct_time", "mean_recall_at_50pct_time")


def run_project(name: str, db: str, out: str, seeds: list[int]) -> str:
    from codedna.models.evaluate import evaluate
    from codedna.models.experiment import run_experiment
    from codedna.test_history.features import Dataset, build_dataset
    from codedna.test_history.store import HistoryStore

    folder = Path(out) / name
    folder.mkdir(parents=True, exist_ok=True)
    csv_path = folder / "dataset.csv"
    started = time.time()
    if csv_path.is_file():
        dataset = Dataset.from_csv(csv_path)
    else:
        with HistoryStore(db) as store:
            dataset = build_dataset(store, structural=True)
        dataset.to_csv(csv_path)
        dataset = Dataset.from_csv(csv_path)  # identical input for every seed
    built = time.time() - started
    for seed in seeds:
        for kind, fn in (("evaluate", lambda: evaluate(dataset, seed=seed)),
                         ("experiment", lambda: run_experiment(dataset, seed=seed))):
            target = folder / f"{kind}-seed{seed}.json"
            if not target.is_file():
                target.write_text(json.dumps(fn(), indent=2) + "\n", encoding="utf-8")
    return f"{name}: dataset {built:.0f}s, total {time.time() - started:.0f}s"


def summarise(out: Path, names: list[str], seeds: list[int]) -> dict:
    summary: dict = {"seeds": seeds, "split": "test", "projects": {}, "pooled": {}}
    for name in names:
        experiments = [json.loads((out / name / f"experiment-seed{s}.json").read_text(encoding="utf-8"))
                       for s in seeds]
        evaluations = [json.loads((out / name / f"evaluate-seed{s}.json").read_text(encoding="utf-8"))
                       for s in seeds]
        first = experiments[0]
        b0 = first["policies"]["B0_retest_all"]
        project = {
            "test_commits": b0["commits"],
            "test_commits_with_failures": b0["commits_with_failures"],
            "test_failure_rate": (first.get("calibration") or {}).get("test_failure_rate"),
            "policies": _agg([e["policies"] for e in experiments], POLICY_METRICS),
            "ordering": _agg([e["results"]["test"]["rankers"] for e in evaluations], ORDER_METRICS),
            "calibration": _agg([(e.get("calibration") or {}).get("methods", {}) for e in experiments],
                                ("brier", "ece")),
            "ablations": _agg([e.get("ablations", {}) for e in experiments], ("pr_auc", "brier")),
            "warnings": sorted({w for e in experiments for w in e["warnings"]}),
        }
        summary["projects"][name] = project
    for section in ("policies", "ordering", "calibration", "ablations"):
        pooled: dict = {}
        for name in names:
            for item, metrics in summary["projects"][name][section].items():
                for metric, stats in metrics.items():
                    if stats["mean"] is not None:
                        pooled.setdefault(item, {}).setdefault(metric, []).append(stats["mean"])
        summary["pooled"][section] = {
            item: {metric: {"mean": round(mean(values), 4), "projects": len(values)}
                   for metric, values in metrics.items()}
            for item, metrics in pooled.items()}
    return summary


def _agg(per_seed: list[dict], metrics: tuple[str, ...]) -> dict:
    result: dict = {}
    for item in per_seed[0] if per_seed else {}:
        result[item] = {}
        for metric in metrics:
            values = [run[item].get(metric) for run in per_seed if item in run]
            values = [v for v in values if v is not None]
            result[item][metric] = {
                "mean": round(mean(values), 4) if values else None,
                "sd": round(pstdev(values), 4) if len(values) > 1 else 0.0 if values else None,
            }
    return result


def to_markdown(summary: dict) -> str:
    names = list(summary["projects"])
    lines = [f"# Study summary — test split, seeds {summary['seeds']}", "",
             "Mean over seeds (± standard deviation over seeds). \"All\" = unweighted mean of "
             "project means. Generated by scripts/run_study.py; do not edit by hand.", "",
             "## Projects", "", "| Project | Test commits | With failures | Failure rate |",
             "|---|---|---|---|"]
    for name in names:
        p = summary["projects"][name]
        lines.append(f"| {name} | {p['test_commits']} | {p['test_commits_with_failures']} | "
                     f"{_fmt(p['test_failure_rate'])} |")
    for title, section, metrics in (
            ("Selection policies", "policies", POLICY_METRICS),
            ("Ordering", "ordering", ORDER_METRICS),
            ("Calibration (full model, test split)", "calibration", ("brier", "ece")),
            ("Ablations", "ablations", ("pr_auc", "brier"))):
        lines += ["", f"## {title}"]
        items = list(summary["pooled"][section]) or list(summary["projects"][names[0]][section])
        for metric in metrics:
            lines += ["", f"### {metric}", "", "| | " + " | ".join(names) + " | All |",
                      "|---|" + "---|" * (len(names) + 1)]
            for item in items:
                cells = []
                for name in names:
                    stats = summary["projects"][name][section].get(item, {}).get(metric)
                    cells.append(_fmt_stats(stats))
                pooled = summary["pooled"][section].get(item, {}).get(metric)
                cells.append(_fmt(pooled["mean"]) if pooled else "–")
                lines.append(f"| {item} | " + " | ".join(cells) + " |")
    lines += ["", "## Warnings", ""]
    for name in names:
        for warning in summary["projects"][name]["warnings"]:
            lines.append(f"- **{name}**: {warning}")
    return "\n".join(lines) + "\n"


def _fmt(value) -> str:
    return "–" if value is None else (f"{value:.3f}" if isinstance(value, float) else str(value))


def _fmt_stats(stats) -> str:
    if not stats or stats["mean"] is None:
        return "–"
    return _fmt(stats["mean"]) + (f" ±{stats['sd']:.3f}" if stats["sd"] else "")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("projects", nargs="+", help="name=path/to/history.db")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    pairs = [p.split("=", 1) for p in args.projects]
    out = Path(args.out)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for message in pool.map(run_project, [n for n, _ in pairs], [d for _, d in pairs],
                                [str(out)] * len(pairs), [args.seeds] * len(pairs)):
            print(message, flush=True)
    summary = summarise(out, [n for n, _ in pairs], args.seeds)
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(to_markdown(summary), encoding="utf-8")
    print(f"wrote {out / 'summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
