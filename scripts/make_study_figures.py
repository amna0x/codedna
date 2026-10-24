"""Export the RQ1-RQ5 figures from saved study reports without rerunning models.

Usage: python scripts/make_study_figures.py --study experiments/results/study11-2026-10-21
Install the optional plotting dependency with: pip install -e ".[plots]"
Use --data-only to export the plotted numbers and provenance without Matplotlib.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from statistics import mean


VARIANTS = (
    ("balanced/none", "Balanced, raw"),
    ("balanced/isotonic", "Balanced, isotonic"),
    ("unweighted/none", "Unweighted, raw"),
    ("unweighted/isotonic", "Unweighted, isotonic"),
)
ORDER_LABELS = {
    "recent_failures": "Recent failures (B3)",
    "shortest_first": "Shortest first (B2)",
    "random": "Random (B1)",
    "logistic_regression": "Logistic regression",
    "gradient_boosting": "Gradient boosting",
    "failure_history": "Failure history (B5)",
}
FIGURES = (
    ("rq1-ordering", "Ordering quality", "APFDc is cost-aware. Means over seeds, then projects; no confidence intervals are inferred from seed spread."),
    ("rq2-budget", "Time and detection", "B8 budget sweep. Each point shows actual time spent, not the requested budget. Time and detection may have different contributing project counts."),
    ("rq3-calibration", "Calibration and stopping decisions", "All four variants use the same available project cohort within each panel. Estimated risk and observed miss rate refer to B10, not individual-test ECE. A pooled mean below target does not mean every project met it."),
    ("rq4-cost-matched", "Safety at matched test time", "Saved hierarchical bootstrap 95% intervals. Intervals touching or crossing zero do not establish an improvement. Time matching is approximate; exact time differences are in figure-data.json."),
    ("rq5-graph-signal", "Dependency-graph reachability", "All projects with defined reachability are shown. n counts failing test rows, not independent faults. Sparse projects have unstable estimates; reachability does not establish failure causation."),
)


def _number(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Expected a finite number or null, got {value!r}")
    return float(value)


def _stats(values):
    defined = [_number(v) for v in values if v is not None]
    return {"mean": mean(defined) if defined else None, "projects": len(defined)}


def _reject_constant(value):
    raise ValueError(f"Non-finite JSON constant: {value}")


def collect_data(study: Path) -> tuple[dict, dict]:
    """Read only saved reports; retain missing metrics and equal project weights."""
    sources = {}

    def load(relative):
        raw = (study / relative).read_bytes()
        sources[relative] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)

    summary = load("summary.json")
    weights = load("class-weight-summary.json")
    seeds = summary["seeds"]
    if not seeds or len(set(seeds)) != len(seeds) or weights["seeds"] != seeds:
        raise ValueError("Study and class-weight reports must have the same nonempty, unique seed list")
    names = list(summary["projects"])
    if not names or set(weights["projects"]) != set(names) or summary["split"] != "test":
        raise ValueError("Both summaries must cover the same projects on the test split")

    # Every seed contributes once within its project. A large project never
    # receives more weight because it contains more commits or test classes.
    budget_by_project = {}
    expected_grid = None
    targets = set()
    for name in names:
        runs = []
        for seed in seeds:
            report = load(f"{name}/experiment-seed{seed}.json")
            sweep = report["risk_coverage"]["B8_budget_sweep"]
            grid = [_number(row["budget"]) for row in sweep]
            if not grid or len(set(grid)) != len(grid):
                raise ValueError(f"Empty or duplicate budget grid in {name}, seed {seed}")
            if expected_grid is None:
                expected_grid = sorted(grid)
            if sorted(grid) != expected_grid:
                raise ValueError(f"Inconsistent budget grid in {name}, seed {seed}")
            runs.append({row["budget"]: row for row in sweep})
            check = load(f"{name}/class-weight-seed{seed}.json")
            target = _number(check["risk_target"])
            if target is None or not 0 <= target <= 1:
                raise ValueError(f"Invalid B10 risk target in {name}, seed {seed}")
            targets.add(target)
        budget_by_project[name] = runs
    if len(targets) != 1:
        raise ValueError("Class-weight runs use different B10 risk targets")
    target = targets.pop()
    budget_rows = []
    for budget in expected_grid:
        row = {"budget": budget}
        for label, metric in (("time", "mean_time_ratio"), ("recall", "failing_test_recall"),
                              ("safety", "commit_safety_rate")):
            project_means = [_stats([run[budget][metric] for run in runs])["mean"]
                             for runs in budget_by_project.values()]
            row[label] = _stats(project_means)
        budget_rows.append(row)

    # Raw probabilities exist for more projects than calibrated probabilities.
    # Use the intersection, rather than comparing differently sized pools.
    calibration_cohort = [name for name in names if all(
        weights["projects"][name][variant].get(f"{method}_{metric}") is not None
        for key, _ in VARIANTS for variant, method in [key.split("/")]
        for metric in ("ece", "brier", "skip_risk_gap"))]
    b10_cohort = [name for name in names if all(
        key in weights["projects"][name]["b10"] for key, _ in VARIANTS)]
    if not calibration_cohort or not b10_cohort:
        raise ValueError("No common project cohort for calibration or B10 comparisons")
    calibration, b10 = [], []
    for key, label in VARIANTS:
        variant, method = key.split("/")
        calibration.append({"key": key, "label": label, **{
            metric: _stats([weights["projects"][name][variant][f"{method}_{metric}"]
                            for name in calibration_cohort])
            for metric in ("ece", "brier", "skip_risk_gap")}})
        entries = [weights["projects"][name]["b10"][key] for name in b10_cohort]
        observed = [entry["observed_miss_rate"] for entry in entries]
        if any(value is None for value in observed):
            raise ValueError("B10 target attainment requires an observed miss rate for every project")
        b10.append({"key": key, "label": label, **{
            metric: _stats([entry[metric] for entry in entries]) for metric in
            ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")},
            "within_target": sum(_number(value) <= target for value in observed),
            "target_projects": len(entries)})

    ordering = [{"key": key, "label": label,
                 **summary["pooled"]["ordering"][key]} for key, label in ORDER_LABELS.items()]
    comparisons = [{"label": label, **metrics} for label, metrics in
                   summary["pooled_bootstrap"]["comparisons"].items()]
    graph = []
    for name, project in summary["projects"].items():
        reach = (project.get("graph") or {}).get("reachability")
        graph.append({"project": name, **(reach or {
            "failing_rows": None, "failing_reachable": None, "all_reachable": None, "lift": None})})
    data = {"seeds": seeds, "projects": names, "ordering": ordering,
            "budget_sweep": budget_rows, "calibration_cohort": calibration_cohort,
            "calibration": calibration, "b10_cohort": b10_cohort, "risk_target": target,
            "b10": b10, "cost_matched": comparisons,
            "bootstrap_method": summary["pooled_bootstrap"]["method"], "graph": graph}
    return data, dict(sorted(sources.items()))


def render_figures(data: dict, out: Path) -> list[Path]:
    try:
        import matplotlib
    except ImportError as exc:
        raise RuntimeError('Install plotting support with: pip install -e ".[plots]"') from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.titleweight": "bold", "svg.hashsalt": "codedna-study"})
    blue, orange, grey = "#2563a6", "#c96329", "#64748b"
    paths = []

    def save(fig, stem):
        for suffix in ("png", "svg"):
            path = out / f"{stem}.{suffix}"
            metadata = {"Software": "CodeDNA"} if suffix == "png" else {"Date": None}
            fig.savefig(path, dpi=180, bbox_inches="tight", metadata=metadata)
            paths.append(path)
        plt.close(fig)

    rows = sorted(data["ordering"], key=lambda row: row["mean_apfdc"]["mean"], reverse=True)
    fig, ax = plt.subplots(figsize=(8.4, 4.4), layout="constrained")
    y = list(range(len(rows)))
    bars = ax.barh(y, [row["mean_apfdc"]["mean"] for row in rows], color=blue)
    ax.set_yticks(y, [f"{r['label']} (n={r['mean_apfdc']['projects']})" for r in rows])
    ax.invert_yaxis()
    ax.set(xlim=(0, 1), xlabel="APFDc (higher is better)", title="RQ1: cost-aware test ordering")
    ax.bar_label(bars, fmt="%.4f", padding=5)
    save(fig, "rq1-ordering")

    rows = data["budget_sweep"]
    fig, ax = plt.subplots(figsize=(8.4, 4.4), layout="constrained")
    for metric, color in (("recall", blue), ("safety", orange)):
        valid = [row for row in rows if row[metric]["mean"] is not None and row["time"]["mean"] is not None]
        counts = sorted({row[metric]["projects"] for row in valid})
        ax.plot([r["time"]["mean"] for r in valid], [r[metric]["mean"] for r in valid],
                "o-", color=color, label=f"{metric.capitalize()} (n={','.join(map(str, counts))})")
    time_counts = sorted({row["time"]["projects"] for row in rows})
    ax.axhline(0.9, color=grey, linestyle="--", linewidth=1, label="90% detection")
    ax.set(xlim=(0, 1.02), ylim=(0, 1.04), xlabel=f"Actual test-time ratio (n={','.join(map(str, time_counts))})",
           ylabel="Detection rate", title="RQ2: B8 time and detection on the saved budget grid")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="lower right")
    save(fig, "rq2-budget")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout="constrained")
    y = list(range(len(VARIANTS)))
    labels = [row["label"] for row in data["calibration"]]
    axes[0].barh(y, [row["ece"]["mean"] for row in data["calibration"]], color=blue)
    axes[0].set_yticks(y, labels)
    axes[0].invert_yaxis()
    axes[0].set(xlabel="ECE (lower is better)", title=f"Individual-test calibration (n={len(data['calibration_cohort'])})")
    axes[1].barh([i - .18 for i in y], [r["estimated_skip_risk"]["mean"] for r in data["b10"]],
                 height=.34, color=blue, label="Estimated skip risk")
    axes[1].barh([i + .18 for i in y], [r["observed_miss_rate"]["mean"] for r in data["b10"]],
                 height=.34, color=orange, label="Observed miss rate")
    axes[1].set_yticks(y, [f"{r['within_target']}/{r['target_projects']} within target" for r in data["b10"]])
    axes[1].invert_yaxis()
    axes[1].axvline(data["risk_target"], color=grey, linestyle="--", linewidth=1,
                    label=f"{data['risk_target']:.0%} target")
    axes[1].xaxis.set_major_formatter(PercentFormatter(1))
    axes[1].set(xlabel="Commit-level rate", title=f"B10 stopping decisions (n={len(data['b10_cohort'])})")
    axes[1].legend(loc="upper center", bbox_to_anchor=(.5, -.16), ncol=1, fontsize=9)
    fig.suptitle("RQ3: low ECE alone does not establish a useful stopping rule")
    save(fig, "rq3-calibration")

    rows = [row for row in data["cost_matched"] if row["safety"]["estimate"] is not None]
    fig, ax = plt.subplots(figsize=(9, 4.4), layout="constrained")
    for i, row in enumerate(rows):
        stats = row["safety"]
        if stats["ci"] is not None:
            ax.plot(stats["ci"], [i, i], color=blue, linewidth=2)
        ax.plot(stats["estimate"], i, "o", color=blue)
    ax.set_yticks(range(len(rows)), [f"{r['label']} (n={r['safety']['projects']})" for r in rows])
    ax.invert_yaxis()
    ax.axvline(0, color=grey, linestyle="--", linewidth=1)
    ax.set(xlabel="Safety difference, policy minus baseline (95% CI)",
           title="RQ4: safety differences at matched test time")
    save(fig, "rq4-cost-matched")

    rows = [row for row in data["graph"] if row["failing_reachable"] is not None]
    fig, ax = plt.subplots(figsize=(8.4, max(4.4, .42 * len(rows) + 1.6)), layout="constrained")
    y = list(range(len(rows)))
    ax.scatter([r["all_reachable"] for r in rows], y, color=grey, marker="s", label="All test rows")
    ax.scatter([r["failing_reachable"] for r in rows], y, color=orange, marker="o", label="Failing test rows")
    ax.set_yticks(y, [f"{r['project']} (n={r['failing_rows']})" for r in rows])
    ax.invert_yaxis()
    ax.set(xlim=(-.02, 1.02), xlabel="Share reachable from the changed code",
           title="RQ5: graph reachability varies across projects")
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.13), ncol=2)
    save(fig, "rq5-graph-signal")
    return paths


def export(study: Path, out: Path, *, data_only: bool = False) -> dict:
    data, sources = collect_data(study)
    out.mkdir(parents=True, exist_ok=True)
    paths = [] if data_only else render_figures(data, out)
    data_path = out / "figure-data.json"
    data_path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    paths.append(data_path)
    lines = ["# Saved-study figures", "", "Generated by `scripts/make_study_figures.py`.", "",
             "Means weight projects equally after averaging seeds. Missing metrics remain null;",
             "projects without failures do not count toward recall or safety. Model fitting and",
             "dataset extraction are not rerun. Source reports and their SHA-256 hashes are in",
             "`manifest.json`; exact plotted values and project counts are in `figure-data.json`.", "",
             "Reproduce from the repository root:", "", "```powershell",
             'python -m pip install -e ".[plots]"',
             f'python scripts/make_study_figures.py --study "{study.as_posix()}"', "```", ""]
    for stem, title, caption in FIGURES:
        lines += [f"## {title}", "", caption, ""]
        if not data_only:
            lines += [f"![{title}]({stem}.png)", "", f"[Vector figure]({stem}.svg)", ""]
    index = out / "FIGURES.md"
    index.write_text("\n".join(lines), encoding="utf-8")
    paths.append(index)
    versions = {"python": platform.python_version()}
    if not data_only:
        import matplotlib
        versions["matplotlib"] = matplotlib.__version__
    manifest = {"schema_version": 1, "source_root": study.as_posix(), "seeds": data["seeds"],
                "versions": versions, "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "sources": sources, "outputs": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                                                 for path in sorted(paths)}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--study", type=Path, required=True, help="saved study folder with both summary JSON reports")
    parser.add_argument("--out", type=Path, help="default: STUDY/figures")
    parser.add_argument("--data-only", action="store_true", help="export numbers and hashes without Matplotlib")
    args = parser.parse_args(argv)
    try:
        manifest = export(args.study, args.out or args.study / "figures", data_only=args.data_only)
    except (OSError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(f"Exported {len(manifest['outputs'])} files; {len(manifest['sources'])} saved inputs fingerprinted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
