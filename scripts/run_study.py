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
            "cost_matched": _cost_matched(experiments),
            "graph": _graph_signal(experiments, out / name / "dataset.csv"),
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
    summary["pooled_bootstrap"] = pooled_bootstrap(out, names, seeds)
    return summary


GRAPH_ABLATION_METRICS = ("pr_auc", "failing_test_recall_at_budget", "commit_safety_rate_at_budget")


def _graph_signal(experiments: list[dict], dataset_csv: Path) -> dict:
    """What the dependency-graph (structural) features add, for one project.

    * ``ablation``: mean over seeds of (all features − without structural) for
      the experiment's model, plus in how many seeds PR-AUC improved;
    * ``b4`` / ``b8``: graph-only selection (B4) next to calibrated ML (B8);
    * ``reachability``: on the test split, the share of failing (commit, test)
      rows whose test is reachable from the change in the graph, against the
      share of all rows (lift > 1 means the graph points towards failures).
    """
    result: dict = {"ablation": {}}
    pairs = [e.get("ablations", {}) for e in experiments]
    pairs = [(a["all_features"], a["without_structural"]) for a in pairs
             if "all_features" in a and "without_structural" in a]
    for metric in GRAPH_ABLATION_METRICS:
        result["ablation"][metric] = _mean_or_none(
            [x[metric] - y[metric] for x, y in pairs if x[metric] is not None and y[metric] is not None])
    defined = [(x, y) for x, y in pairs if x["pr_auc"] is not None and y["pr_auc"] is not None]
    result["ablation"]["pr_auc_improved_seeds"] = (
        f"{sum(x['pr_auc'] > y['pr_auc'] for x, y in defined)}/{len(defined)}" if defined else None)
    for key, policy in (("b4", "B4_dependency"), ("b8", "B8_ml_calibrated")):
        runs = [e["policies"][policy] for e in experiments if policy in e["policies"]]
        result[key] = {m: _mean_or_none([r.get(m) for r in runs])
                       for m in ("mean_time_ratio", "failing_test_recall", "commit_safety_rate")}
    result["reachability"] = _reachability(dataset_csv)
    return result


def _reachability(dataset_csv: Path) -> dict | None:
    from codedna.models.evaluate import chronological_split
    from codedna.test_history.features import Dataset

    if not dataset_csv.is_file():
        return None
    dataset = Dataset.from_csv(dataset_csv)
    if "dep_reachable" not in dataset.feature_names:
        return None
    test = set(chronological_split(dataset)["test"])
    rows = [r for r in dataset.rows if r.commit in test]
    failing = [r for r in rows if r.label]
    if not rows or not failing:
        return {"failing_rows": len(failing), "failing_reachable": None, "all_reachable": None, "lift": None}
    share = lambda group: sum(r.features["dep_reachable"] > 0 for r in group) / len(group)
    fail_share, all_share = share(failing), share(rows)
    return {"failing_rows": len(failing), "failing_reachable": round(fail_share, 4),
            "all_reachable": round(all_share, 4),
            "lift": round(fail_share / all_share, 3) if all_share else None}


# label → (cost_matched key in the experiment report, policy, same-time baseline in per_commit)
PAIRS = {
    "B9r − B8 at same time": ("B9r_risk_target_only", "B9r_risk_target_only", "B8@B9r_risk_target_only"),
    "B9 − B8 at same time": ("B9_calibrated_fallback", "B9_calibrated_fallback", "B8@B9_calibrated_fallback"),
    "B9n − B8 at same time": ("B9n_unfamiliar_rule_only", "B9n_unfamiliar_rule_only",
                              "B8@B9n_unfamiliar_rule_only"),
    "B10 − B8 at same time": ("B10_hybrid", "B10_hybrid", "B8@B10_hybrid"),
    "B10 − B3 (rules) at same time": ("B10_hybrid vs B3", "B10_hybrid", "B3@B10_hybrid"),
}


def _cost_matched(experiments: list[dict], resamples: int = 1000) -> dict:
    """Each compared policy vs its baseline at the same test time, for one project.

    Point estimates are means over seeds. Intervals come from a hierarchical
    bootstrap (pick a seed, then resample that seed's test commits), so they
    reflect both model randomness and the limited number of commits.
    """
    import random

    result = {}
    runs_all = [e.get("per_commit", {}) for e in experiments]
    for label, (key, policy, baseline) in PAIRS.items():
        rows = [e.get("cost_matched", {}).get(key) for e in experiments]
        rows = [r for r in rows if r]
        runs = [(pc[policy], pc[baseline]) for pc in runs_all
                if policy in pc and baseline in pc]
        if not rows or not runs:
            continue
        entry = {"baseline": rows[0]["baseline"],
                 "baseline_budget": round(mean(r["baseline_budget"] for r in rows), 4)}
        for side in ("policy", "baseline_same_time"):
            entry[side] = {m: _mean_or_none([r[side][m] for r in rows]) for m in ("time", "recall", "safety")}
        point = _mean_over_seeds({"_": runs})
        draws = _hierarchical_draws({"_": runs}, resamples, random.Random(0))
        entry["difference"] = {m: {"estimate": point[m], "ci": _percentile(draws[m])}
                               for m in ("time", "recall", "safety")}
        result[label] = entry
    return result


def pooled_bootstrap(out: Path, names: list[str], seeds: list[int], *,
                     resamples: int = 2000) -> dict:
    """Paired, stratified, hierarchical bootstrap over projects.

    Each resample picks a seed for every project, resamples that seed's test
    commits within the project, computes the project's difference (policy − B8
    at the same time) and averages over the projects where the metric is
    defined, each project counting once.
    """
    import random

    per_project = {}
    for name in names:
        per_project[name] = [
            json.loads((out / name / f"experiment-seed{s}.json").read_text(encoding="utf-8"))
            .get("per_commit", {}) for s in seeds]
    rng = random.Random(0)
    result = {"method": f"stratified paired hierarchical bootstrap (seed, then commits), "
                        f"{resamples} resamples, seeds {seeds}, projects weighted equally",
              "comparisons": {}}
    for label, (_, policy, baseline) in PAIRS.items():
        data = {}
        for name, runs in per_project.items():
            pairs = [(pc[policy], pc[baseline]) for pc in runs
                     if policy in pc and baseline in pc]
            if pairs:
                data[name] = pairs
        if not data:
            continue
        point = _mean_over_seeds(data)
        draws = _hierarchical_draws(data, resamples, rng)
        contributing = _contributing(data)
        result["comparisons"][label] = {
            m: {"estimate": point[m], "ci": _percentile(draws[m]), "projects": contributing[m]}
            for m in ("time", "recall", "safety")}
    return result


def _project_difference(a, b) -> dict:
    from codedna.models.uncertainty import metrics

    ma, mb = metrics([tuple(x) for x in a]), metrics([tuple(x) for x in b])
    return {m: None if ma[m] is None or mb[m] is None else ma[m] - mb[m]
            for m in ("time", "recall", "safety")}


def _macro(per_project: list[dict]) -> dict:
    return {m: (round(mean(v), 4) if (v := [d[m] for d in per_project if d[m] is not None]) else None)
            for m in ("time", "recall", "safety")}


def _mean_over_seeds(data: dict) -> dict:
    """Macro average over projects of each project's mean-over-seeds difference."""
    per_project = []
    for runs in data.values():
        diffs = [_project_difference(a, b) for a, b in runs]
        per_project.append({m: _mean_or_none([d[m] for d in diffs]) for m in ("time", "recall", "safety")})
    return _macro(per_project)


def _hierarchical_draws(data: dict, resamples: int, rng) -> dict:
    draws = {m: [] for m in ("time", "recall", "safety")}
    for _ in range(resamples):
        per_project = []
        for runs in data.values():
            a, b = runs[rng.randrange(len(runs))]
            index = [rng.randrange(len(a)) for _ in range(len(a))]
            per_project.append(_project_difference([a[i] for i in index], [b[i] for i in index]))
        for metric, value in _macro(per_project).items():
            if value is not None:
                draws[metric].append(value)
    return draws


def _contributing(data: dict) -> dict:
    """Projects whose metric is defined (e.g. safety needs failing test commits)."""
    counts = {m: 0 for m in ("time", "recall", "safety")}
    for runs in data.values():
        diffs = [_project_difference(a, b) for a, b in runs]
        for m in counts:
            counts[m] += any(d[m] is not None for d in diffs)
    return counts


def _percentile(values: list[float], level: float = 0.95):
    if len(values) < 20:
        return None
    values = sorted(values)
    tail = (1 - level) / 2
    return [round(values[int(tail * (len(values) - 1))], 4),
            round(values[int((1 - tail) * (len(values) - 1))], 4)]


def _mean_or_none(values):
    values = [v for v in values if v is not None]
    return round(mean(values), 4) if values else None


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
    lines += ["", "## Policies vs baselines at the same test time", "",
              "Each policy is compared with its baseline (B8, or B3 rules) given the budget that "
              "spends the same real test time. Positive safety/recall differences favour the policy. Estimates are means "
              "over seeds; 95 % intervals come from a hierarchical bootstrap (seed, then test "
              "commits). Pooled: projects weighted equally; n = projects where the metric is "
              "defined.", ""]
    for label in PAIRS:
        lines += [f"### {label}", "", "| Project | Time (policy / baseline) | Recall Δ [95 % CI] | "
                  "Safety Δ [95 % CI] |", "|---|---|---|---|"]
        for name in names:
            entry = summary["projects"][name]["cost_matched"].get(label)
            if not entry:
                continue
            d = entry["difference"]
            lines.append(f"| {name} | {_fmt(entry['policy']['time'])} / {_fmt(entry['baseline_same_time']['time'])} "
                         f"| {_fmt(d['recall']['estimate'])} {_ci(d['recall']['ci'])} "
                         f"| {_fmt(d['safety']['estimate'])} {_ci(d['safety']['ci'])} |")
        pooled = summary["pooled_bootstrap"]["comparisons"].get(label)
        if pooled:
            lines.append(f"| **All** (n = {pooled['safety']['projects']}) | Δ {_fmt(pooled['time']['estimate'])} "
                         f"| {_fmt(pooled['recall']['estimate'])} {_ci(pooled['recall']['ci'])} "
                         f"| {_fmt(pooled['safety']['estimate'])} {_ci(pooled['safety']['ci'])} |")
        lines.append("")
    lines += ["## Dependency-graph signal", "",
              "Ablation Δ = all features − without structural features (mean over seeds; "
              "the experiment's model, uncalibrated). B4 = graph-only selection; B8 = calibrated "
              "ML at budget 0.5. Reachable = share of test-split (commit, test) rows whose test the "
              "graph reaches from the change; lift = failing share / all share.", "",
              "| Project | ΔPR-AUC (seeds better) | ΔRecall | ΔSafety | B4 time / recall / safety "
              "| B8 time / recall / safety | Failing rows reachable / all rows (lift) |",
              "|---|---|---|---|---|---|---|"]
    for name in names:
        g = summary["projects"][name].get("graph")
        if not g:
            continue
        a, reach = g["ablation"], g["reachability"] or {}
        triple = lambda p: " / ".join(_fmt(p[m]) for m in ("mean_time_ratio", "failing_test_recall",
                                                            "commit_safety_rate"))
        reach_cell = (f"{_fmt(reach['failing_reachable'])} / {_fmt(reach['all_reachable'])} "
                      f"({_fmt(reach['lift'])})" if reach.get("lift") is not None else "–")
        lines.append(f"| {name} | {_signed(a['pr_auc'])} ({a['pr_auc_improved_seeds'] or '–'}) "
                     f"| {_signed(a['failing_test_recall_at_budget'])} "
                     f"| {_signed(a['commit_safety_rate_at_budget'])} | {triple(g['b4'])} "
                     f"| {triple(g['b8'])} | {reach_cell} |")
    lines += ["", "## Warnings", ""]
    for name in names:
        for warning in summary["projects"][name]["warnings"]:
            lines.append(f"- **{name}**: {warning}")
    return "\n".join(lines) + "\n"


def _ci(interval) -> str:
    return f"[{interval[0]:.3f}, {interval[1]:.3f}]" if interval else "[n/a]"


def _signed(value) -> str:
    return "–" if value is None else f"{value:+.3f}"


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
