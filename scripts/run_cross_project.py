"""Run the pre-specified four-project, five-seed transfer study (D-039).

Use prepare_transfer_features.py first. Each source model/calibrator is
fitted without target labels. Cross-project source history is conservatively
restricted to a prefix older than the target test window's earliest Git
committer date. Target past history is available; this is not a cold-start
study. The diagonal is a newly fitted within-project control.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import random
import sqlite3
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from statistics import mean

DEFAULT_PROJECTS = ["hikaricp", "littleproxy", "jade4j", "wicket-bootstrap"]
CODE_PATHS = (
    "backend/codedna/models/transfer.py", "scripts/run_cross_project.py",
    "scripts/run_study.py", "backend/codedna/models/experiment.py",
    "backend/codedna/models/evaluate.py", "backend/codedna/models/rankers.py",
    "backend/codedna/models/uncertainty.py", "backend/codedna/selection/risk.py",
    "backend/codedna/calibration/calibrators.py", "backend/codedna/calibration/metrics.py",
    "backend/codedna/test_history/features.py",
)



def _study_helpers():
    spec = importlib.util.spec_from_file_location("run_study", Path(__file__).with_name("run_study.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mean(values):
    defined = [value for value in values if value is not None]
    return mean(defined) if defined else None


def summarise(out: Path, names: list[str], seeds: list[int], *, resamples=2000) -> dict:
    """Describe all pre-specified pairs, including failures and unavailable models.

    Pairwise intervals resample seeds and target commits. Across-pair averages
    weight each target equally; the 12 directions are not 12 independent
    projects, so no pooled significance claim is made.
    """
    study = _study_helpers()
    summary = {"projects": names, "seeds": seeds, "pairs": {}, "targets": {}, "transfer_by_target": {},
               "protocol": "Source-only train/calibration; latest 20% target test; historical target features allowed",
               "limitations": ["Four pre-selected projects only; no universal transfer claim",
                               "Git committer dates proxy time; CI completion dates are unavailable",
                               "Prior target-project history is available; this is not cold-start prediction",
                               "Fixed chronological target split; seeds vary models, not time periods",
                               "Bootstrap treats target commits as independent; serial correlation is ignored",
                               "Source-target directions share projects and are statistically dependent"]}
    for source in names:
        for target in names:
            key = f"{source} -> {target}"
            runs = [json.loads((out / source / f"{target}-seed{seed}.json").read_text(encoding="utf-8"))
                    for seed in seeds]
            valid = [run for run in runs if run["status"] == "ok"]
            if valid and target not in summary["targets"]:
                base = valid[0]["policies"]["retest_all"]
                summary["targets"][target] = {
                    "test_commits": base["commits"],
                    "failing_test_commits": base["commits_with_failures"],
                    "skip_all_miss_rate": base["commits_with_failures"] / base["commits"],
                    "failure_row_rate": valid[0]["probability"]["raw"]["positive_rate"],
                }
            entry = {"source": source, "target": target, "runs": len(valid), "expected_runs": len(seeds),
                     "warnings": sorted({w for run in runs for w in run.get("warnings", [])}),
                     "evaluation": "within_project" if source == target else "cross_project"}
            for variant in ("raw", "calibrated"):
                available = [run for run in valid if variant in run["b10"]]
                section = {"runs": len(available)}
                for metric in ("pr_auc", "positive_rate", "brier", "ece"):
                    section[metric] = _mean([run["probability"][variant][metric] for run in available])
                section["b10"] = {metric: _mean([run["b10"][variant][metric] for run in available])
                                  for metric in ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")}
                section["target_held"] = (section["b10"]["observed_miss_rate"] <= runs[0]["config"]["risk_target"]
                                            if section["b10"]["observed_miss_rate"] is not None else None)
                if available:
                    paired = [(run["per_commit"][variant]["B10"],
                               run["per_commit"][variant]["B3@B10"]) for run in available]
                    data = {key: paired}
                    point = study._mean_over_seeds(data)
                    draws = study._hierarchical_draws(data, resamples, random.Random(0))
                    section["vs_rules_same_time"] = {
                        metric: {"estimate": point[metric], "ci": study._percentile(draws[metric])}
                        for metric in ("time", "recall", "safety")}
                entry[variant] = section
            entry["apfdc_ml_raw"] = _mean([r["ordering"]["ml_raw"]["mean_apfdc"] for r in valid])
            entry["apfdc_rules"] = _mean([r["ordering"]["rules"]["mean_apfdc"] for r in valid])
            entry["source_train_rows"] = sorted({r["source_fitting"]["train_rows"] for r in valid})
            summary["pairs"][key] = entry

    # Require complete seed coverage for cross-pair averages rather than quietly
    # giving an unstable or failed source fewer opportunities to count.
    complete = [entry for entry in summary["pairs"].values()
                if entry["evaluation"] == "cross_project" and entry["calibrated"]["runs"] == len(seeds)]
    for target in names:
        rows = [entry for entry in complete if entry["target"] == target]
        summary["transfer_by_target"][target] = {
            "source_pairs": len(rows), "expected_source_pairs": len(names) - 1,
            **{metric: _mean([r["calibrated"]["b10"][metric] for r in rows])
               for metric in ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")}}
    all_targets = list(summary["transfer_by_target"].values())
    summary["transfer_macro"] = {
        "complete_calibrated_directions": len(complete), "expected_directions": len(names) * (len(names) - 1),
        "within_target_directions": sum(row["calibrated"]["target_held"] is True for row in complete),
        "contributing_targets": sum(row["source_pairs"] > 0 for row in all_targets),
        **{metric: _mean([row[metric] for row in all_targets])
           for metric in ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")}}
    return summary


def markdown(summary: dict) -> str:
    lines = ["# Cross-project transfer study", "",
             "Source train and calibration exclude the target project. The target's latest",
             "20% of commits are tested; past target history remains available as features.",
             "Cross-project source history is restricted to a chronological prefix strictly",
             "older than the target test window's earliest Git committer date. This is a",
             "conservative timestamp check, not proof that CI jobs had completed by then.", "",
             "Projects and seeds were fixed before results were inspected. All directions",
             "and within-project controls are reported; the best source is not selected on",
             "target test results. No target recalibration or target-specific tuning is done.", "",
             "## Calibrated B10: source-trained probabilities, rules order, 5% risk target", "",
             "Means over seeds. n/a denotes an unavailable model/calibrator or metric.", "",
             "| Source | Target | Seeds | Time | Recall | Safety | Estimated risk | Observed miss | Target held | ECE | PR-AUC |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    fmt = lambda value: "n/a" if value is None else f"{value:.4f}"
    target_lines = ["## Target test windows", "",
                    "The skip-all rate is the share of commits with any failure. When this is",
                    "below 5%, even running no tests meets the observed unconditional miss",
                    "target. Target attainment alone therefore does not prove useful transfer;",
                    "recall, safety and the matched-cost comparison remain necessary.", "",
                    "| Target | Test commits | With failures | Skip-all miss rate |", "|---|---|---|---|"]
    for target in summary["projects"]:
        context = summary["targets"].get(target)
        if context:
            target_lines.append(f"| {target} | {context['test_commits']} | {context['failing_test_commits']} "
                                f"| {context['skip_all_miss_rate']:.4f} |")
    target_lines += [""]
    insert_at = lines.index("## Calibrated B10: source-trained probabilities, rules order, 5% risk target")
    lines[insert_at:insert_at] = target_lines
    for pair in summary["pairs"].values():
        c, b = pair["calibrated"], pair["calibrated"]["b10"]
        source = pair["source"] + (" (within control)" if pair["source"] == pair["target"] else "")
        held = "n/a" if c["target_held"] is None else "yes" if c["target_held"] else "no"
        cells = [source, pair["target"], f"{c['runs']}/{pair['expected_runs']}"]
        cells += [fmt(b[m]) for m in ("time", "recall", "safety", "estimated_skip_risk", "observed_miss_rate")]
        cells += [held, fmt(c["ece"]), fmt(c["pr_auc"])]
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", "## Calibrated B10 versus rules at matched actual test time", "",
              "Pairwise 95% hierarchical bootstrap intervals: resample a seed, then target",
              "commits. Intervals crossing zero do not establish a gain. Matching is approximate.", "",
              "| Source → target | Time difference | Safety difference [95% CI] |", "|---|---|---|"]
    for pair in summary["pairs"].values():
        comparison = pair["calibrated"].get("vs_rules_same_time")
        if comparison:
            stat = comparison["safety"]
            interval = "n/a" if stat["ci"] is None else f"[{fmt(stat['ci'][0])}, {fmt(stat['ci'][1])}]"
            lines.append(f"| {pair['source']} → {pair['target']} | {fmt(comparison['time']['estimate'])} "
                         f"| {fmt(stat['estimate'])} {interval} |")
    lines += ["", "## Ordering quality (raw model probability order)", "",
              "| Source | Target | ML APFDc | Rules APFDc |", "|---|---|---|---|"]
    for pair in summary["pairs"].values():
        lines.append(f"| {pair['source']} | {pair['target']} | {fmt(pair['apfdc_ml_raw'])} | {fmt(pair['apfdc_rules'])} |")
    lines += ["", "## Limits", ""] + [f"- {note}" for note in summary["limitations"]]
    lines += ["", "## Warnings", ""]
    for key, pair in summary["pairs"].items():
        for warning in pair["warnings"]:
            lines.append(f"- {key}: {warning}")
    return "\n".join(lines) + "\n"


def run(root: Path, out: Path, names: list[str], seeds: list[int]) -> dict:
    from codedna.models.evaluate import chronological_split
    from codedna.models.transfer import evaluate_target, fit_project, source_prefix_before
    from codedna.test_history.features import Dataset

    if len(names) < 2 or len(set(names)) != len(names) or not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("Need at least two distinct projects and a nonempty unique seed list")
    datasets, times, input_hashes = {}, {}, {}
    for name in names:
        path = root / f"experiments/results/study11-2026-10-21/{name}/dataset.csv"
        datasets[name] = Dataset.from_csv(path)
        input_hashes[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        db = root / f"experiments/datasets/derived/{name}.db"
        if not db.is_file():
            raise FileNotFoundError(db)
        with sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True) as conn:
            times[name] = dict(conn.execute("SELECT sha, committed_at FROM commits"))
        input_hashes[db.relative_to(root).as_posix()] = hashlib.sha256(db.read_bytes()).hexdigest()
    out.mkdir(parents=True, exist_ok=True)
    config = {"projects": names, "seeds": seeds, "model": "gradient_boosting", "calibration": "isotonic",
              "budget": .5, "risk_target": .05,
              "calendar_rule": "source prefix before earliest target test Git committer date",
              "input_sha256": input_hashes,
              "versions": {"python": platform.python_version(), "scikit-learn": version("scikit-learn"),
                           "numpy": version("numpy")},
              "code_sha256": {relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
                              for relative in CODE_PATHS}}
    config_file = out / "config.json"
    if config_file.exists() and json.loads(config_file.read_text(encoding="utf-8")) != config:
        raise ValueError("Existing transfer output has a different protocol or inputs; choose a new output folder")
    config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    for seed in seeds:
        fitted_cache = {}
        for source in names:
            for target in names:
                target_dataset = datasets[target]
                test_shas = chronological_split(target_dataset)["test"]
                cutoff = min(times[target][sha] for sha in test_shas)
                source_dataset = (datasets[source] if source == target else
                                  source_prefix_before(datasets[source], times[source], cutoff))
                cache_key = (source, len(source_dataset.commits))
                path = out / source / f"{target}-seed{seed}.json"
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    continue
                try:
                    if cache_key not in fitted_cache:
                        fitted_cache[cache_key] = fit_project(source, source_dataset, seed=seed)
                    fitted = fitted_cache[cache_key]
                    fitting = fitted.provenance["train_commits"] + fitted.provenance["calibration_commits"]
                    if any(times[source][sha] >= cutoff for sha in fitting):
                        raise ValueError("Source fitting extends into the target test calendar window")
                    report = evaluate_target(fitted, target, target_dataset)
                    report["protocol"].update({"project_calendars_aligned": True,
                        "alignment_basis": "Git committer dates; CI completion times unavailable",
                        "target_test_earliest_utc": datetime.fromtimestamp(cutoff, timezone.utc).isoformat(),
                        "source_available_prefix_commits": len(source_dataset.commits),
                        "source_full_commits": len(datasets[source].commits)})
                    report["status"] = "ok"
                except ValueError as exc:
                    report = {"status": "unavailable", "source": source, "target": target,
                              "warnings": [str(exc)]}
                report["config"] = config
                path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
                print(f"seed {seed}: {source} -> {target}: {report['status']}", flush=True)
    summary = summarise(out, names, seeds)
    (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (out / "summary.md").write_text(markdown(summary), encoding="utf-8")
    manifest = {"config": config, "python": platform.python_version(),
                "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "model_code_sha256": hashlib.sha256((root / "backend/codedna/models/transfer.py").read_bytes()).hexdigest(),
                "result_sha256": {p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted([*out.rglob("*.json"), *out.rglob("*.md")]) if p.name != "manifest.json"}}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Study complete: {out / 'summary.md'}", flush=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, default=Path("experiments/results/cross-project-2026-10-24"))
    parser.add_argument("--projects", nargs="+", default=DEFAULT_PROJECTS)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2, 3, 4])
    args = parser.parse_args(argv)
    run(args.root.resolve(), args.out, args.projects, args.seeds)


if __name__ == "__main__":
    main()
