"""Class-weight check for RQ3 (D-037): balanced vs unweighted models.

Reuses each project's ``dataset.csv`` from a study folder, writes
``class-weight-seed<N>.json`` per project and seed, then
``class-weight-summary.json`` / ``class-weight-summary.md`` with means over
seeds per project and an unweighted mean over projects. The hybrid B10 is
also run per variant with raw and isotonic probabilities and compared with
the rules (B3) at the same test time, using run_study.py's hierarchical
bootstrap.

Usage (from the repository root):
    python scripts/class_weight_check.py --out experiments/results/study11-2026-10-21 \\
        --seeds 0 1 2 3 4 --workers 6 hikaricp littleproxy ...
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import mean

VARIANTS = ("balanced", "unweighted")
METHODS = ("none", "platt", "isotonic")
METRICS = ("brier", "ece", "skip_risk_gap")
B10_KEYS = ("balanced/isotonic", "balanced/none", "unweighted/none", "unweighted/isotonic")
B10_METRICS = ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")


def run_project(name: str, out: str, seeds: list[int]) -> str:
    from codedna.models.experiment import class_weight_check
    from codedna.test_history.features import Dataset

    folder = Path(out) / name
    dataset = Dataset.from_csv(folder / "dataset.csv")
    for seed in seeds:
        target = folder / f"class-weight-seed{seed}.json"
        if not target.is_file():
            target.write_text(json.dumps(class_weight_check(dataset, seed=seed), indent=2) + "\n",
                              encoding="utf-8")
    return f"{name}: done"


def summarise(out: Path, names: list[str], seeds: list[int]) -> dict:
    summary: dict = {"seeds": seeds, "projects": {}, "pooled": {}}
    for name in names:
        runs = [json.loads((out / name / f"class-weight-seed{s}.json").read_text(encoding="utf-8"))
                for s in seeds]
        project = {}
        for variant in VARIANTS:
            entries = [r["variants"][variant] for r in runs if variant in r["variants"]]
            project[variant] = {"pr_auc": _mean([e["pr_auc"] for e in entries])}
            for method in METHODS:
                for metric in METRICS:
                    project[variant][f"{method}_{metric}"] = _mean(
                        [e["methods"][method][metric] for e in entries if method in e["methods"]])
        project["warnings"] = sorted({w for r in runs for w in r["warnings"]})
        project["b10"] = {}
        for key in B10_KEYS:
            variant, method = key.split("/")
            entries = [r["variants"][variant]["methods"][method]["B10"] for r in runs
                       if method in r["variants"].get(variant, {}).get("methods", {})]
            if entries:
                project["b10"][key] = {m: _mean([e[m] for e in entries]) for m in B10_METRICS}
        summary["projects"][name] = project
    for variant in VARIANTS:
        keys = [k for k in summary["projects"][names[0]][variant]]
        summary["pooled"][variant] = {}
        for key in keys:
            values = [p[variant][key] for p in summary["projects"].values() if p[variant][key] is not None]
            summary["pooled"][variant][key] = {"mean": _mean(values), "projects": len(values)}
    summary["b10"] = _b10_pooled(out, names, seeds, summary)
    return summary


def _b10_pooled(out: Path, names: list[str], seeds: list[int], summary: dict,
                resamples: int = 2000) -> dict:
    import random

    study = _load_run_study()
    result = {}
    for key in B10_KEYS:
        data = {}
        for name in names:
            runs = [json.loads((out / name / f"class-weight-seed{s}.json").read_text(encoding="utf-8"))
                    .get("per_commit", {}).get(key) for s in seeds]
            runs = [(r["B10"], r["B3@B10"]) for r in runs if r]
            if runs:
                data[name] = runs
        if not data:
            continue
        point = study._mean_over_seeds(data)
        draws = study._hierarchical_draws(data, resamples, random.Random(0))
        contributing = study._contributing(data)
        per_project = [summary["projects"][n]["b10"][key] for n in data]
        target = json.loads((out / names[0] / f"class-weight-seed{seeds[0]}.json")
                            .read_text(encoding="utf-8"))["risk_target"]
        result[key] = {
            "metrics": {m: {"mean": _mean([p[m] for p in per_project]),
                            "projects": sum(p[m] is not None for p in per_project)}
                        for m in B10_METRICS},
            "within_target": f"{sum(p['observed_miss_rate'] <= target for p in per_project)}"
                             f"/{len(per_project)}",
            "vs_rules_same_time": {m: {"estimate": point[m], "ci": study._percentile(draws[m]),
                                       "projects": contributing[m]}
                                   for m in ("time", "recall", "safety")},
        }
    return result


def _load_run_study():
    import importlib.util
    spec = importlib.util.spec_from_file_location("run_study", Path(__file__).with_name("run_study.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def to_markdown(summary: dict) -> str:
    names = list(summary["projects"])
    lines = [f"# Class-weight check (D-037) — test split, seeds {summary['seeds']}", "",
             "Gradient boosting trained with balanced class weights (as in the study) and "
             "without. ECE/Brier on the test split, raw (`none`) and calibrated on the "
             "validation split; skip-risk gap = |mean estimated skip risk − observed miss "
             "rate| of the 50 % budget policy. Means over seeds; \"All\" = unweighted mean over "
             "projects (n = projects where defined). Generated by scripts/class_weight_check.py.", ""]
    columns = ["pr_auc"] + [f"{m}_{k}" for k in METRICS for m in METHODS]
    for variant in VARIANTS:
        lines += [f"## {variant}", "", "| Project | " + " | ".join(columns) + " |",
                  "|---|" + "---|" * len(columns)]
        for name in names:
            row = summary["projects"][name][variant]
            lines.append(f"| {name} | " + " | ".join(_fmt(row[c]) for c in columns) + " |")
        pooled = summary["pooled"][variant]
        lines.append("| **All** | " + " | ".join(
            f"{_fmt(pooled[c]['mean'])} (n = {pooled[c]['projects']})" for c in columns) + " |")
        lines.append("")
    lines += ["## Hybrid B10 by model variant", "",
              "B10 = rules order (recent failures, then shortest), stop when the estimated skip "
              "risk is at most the target. Δ vs B3 = B10 − rules at the budget spending the same "
              "time (hierarchical bootstrap over seeds and commits; projects weighted equally).", "",
              "| Model / probabilities | Time | Recall | Safety | Est. risk | Observed miss "
              "| Within target | Safety Δ vs B3 [95 % CI] | Recall Δ vs B3 [95 % CI] |",
              "|---|---|---|---|---|---|---|---|---|"]
    for key, entry in summary.get("b10", {}).items():
        m, d = entry["metrics"], entry["vs_rules_same_time"]
        lines.append(f"| {key} | " + " | ".join(_fmt(m[k]["mean"]) for k in B10_METRICS)
                     + f" | {entry['within_target']} | {_fmt(d['safety']['estimate'])} "
                     f"{_ci(d['safety']['ci'])} | {_fmt(d['recall']['estimate'])} "
                     f"{_ci(d['recall']['ci'])} |")
    return "\n".join(lines) + "\n"


def _ci(interval) -> str:
    return f"[{interval[0]:.3f}, {interval[1]:.3f}]" if interval else "[n/a]"


def _mean(values):
    values = [v for v in values if v is not None]
    return round(mean(values), 4) if values else None


def _fmt(value) -> str:
    return "–" if value is None else f"{value:.4f}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("projects", nargs="+", help="project folder names inside --out")
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    out = Path(args.out)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for message in pool.map(run_project, args.projects, [str(out)] * len(args.projects),
                                [args.seeds] * len(args.projects)):
            print(message, flush=True)
    summary = summarise(out, args.projects, args.seeds)
    (out / "class-weight-summary.json").write_text(json.dumps(summary, indent=2) + "\n",
                                                   encoding="utf-8")
    (out / "class-weight-summary.md").write_text(to_markdown(summary), encoding="utf-8")
    print(f"wrote {out / 'class-weight-summary.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
