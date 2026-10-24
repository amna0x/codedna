"""Study figure exports use saved reports, equal project weights and matched cohorts."""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


spec = importlib.util.spec_from_file_location(
    "make_study_figures", Path(__file__).resolve().parents[2] / "scripts" / "make_study_figures.py")
figures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(figures)


@pytest.fixture
def saved_study(repo):
    """Two unequal-sized projects, two seeds, and one project with no failures."""
    folder = repo.path / "study"
    folder.mkdir()
    projects, weighted = {}, {}
    for name, commits, ece in (("large", 1000, .2), ("small", 1, .8)):
        (folder / name).mkdir()
        projects[name] = {"test_commits": commits, "graph": {"reachability": {
            "failing_rows": 20 if name == "large" else 0,
            "failing_reachable": .8 if name == "large" else None,
            "all_reachable": .4 if name == "large" else None,
            "lift": 2 if name == "large" else None}}}
        weighted[name] = {"balanced": {}, "unweighted": {}, "b10": {}}
        for key, _ in figures.VARIANTS:
            variant, method = key.split("/")
            weighted[name][variant].update({f"{method}_{m}": ece for m in
                                            ("ece", "brier", "skip_risk_gap")})
            weighted[name]["b10"][key] = {
                "time": .5, "recall": 1 if name == "large" else None,
                "safety": 1 if name == "large" else None,
                "estimated_skip_risk": .02, "observed_miss_rate": .04 if name == "large" else 0}
        for seed in (0, 1):
            time = (.2 + .2 * seed) if name == "large" else .8
            rows = [{"budget": b, "mean_time_ratio": time,
                     "failing_test_recall": float(seed) if name == "large" else None,
                     "commit_safety_rate": float(seed) if name == "large" else None}
                    for b in (.25, .5)]
            (folder / name / f"experiment-seed{seed}.json").write_text(json.dumps({
                "risk_coverage": {"B8_budget_sweep": rows}}), encoding="utf-8")
            (folder / name / f"class-weight-seed{seed}.json").write_text(
                json.dumps({"risk_target": .05}), encoding="utf-8")
    stat = {"mean": .5, "projects": 1}
    ordering = {key: {"mean_apfdc": stat} for key in figures.ORDER_LABELS}
    summary = {"seeds": [0, 1], "split": "test", "projects": projects,
               "pooled": {"ordering": ordering}, "pooled_bootstrap": {
                   "method": "saved bootstrap", "comparisons": {"policy minus baseline": {
                       "safety": {"estimate": .1, "ci": [-.1, .3], "projects": 1}}}}}
    (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (folder / "class-weight-summary.json").write_text(json.dumps({
        "seeds": [0, 1], "projects": weighted}), encoding="utf-8")
    return folder


def test_budget_averages_seeds_then_projects_without_zero_filling(saved_study):
    data, _ = figures.collect_data(saved_study)
    row = data["budget_sweep"][0]
    assert row["time"]["mean"] == pytest.approx(.55)
    assert row["time"]["projects"] == 2
    assert row["recall"] == {"mean": .5, "projects": 1}
    assert row["safety"] == {"mean": .5, "projects": 1}
    assert data["calibration"][0]["ece"]["mean"] == pytest.approx(.5)
    assert data["b10"][0]["within_target"] == 2
    assert data["b10"][0]["recall"]["projects"] == 1


def test_calibration_and_stopping_use_common_cohorts(saved_study):
    path = saved_study / "class-weight-summary.json"
    report = json.loads(path.read_text())
    report["projects"]["small"]["unweighted"]["isotonic_ece"] = None
    del report["projects"]["small"]["b10"]["unweighted/isotonic"]
    path.write_text(json.dumps(report), encoding="utf-8")
    data, _ = figures.collect_data(saved_study)
    assert data["calibration_cohort"] == ["large"]
    assert data["b10_cohort"] == ["large"]
    assert all(row["ece"] == {"mean": .2, "projects": 1} for row in data["calibration"])
    assert all(row["target_projects"] == 1 for row in data["b10"])


def test_missing_seed_does_not_silently_shrink_the_study(saved_study):
    (saved_study / "large/experiment-seed1.json").unlink()
    with pytest.raises(FileNotFoundError, match="experiment-seed1"):
        figures.collect_data(saved_study)


def test_inconsistent_budget_grid_is_rejected(saved_study):
    path = saved_study / "large/experiment-seed1.json"
    report = json.loads(path.read_text())
    report["risk_coverage"]["B8_budget_sweep"].pop()
    path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ValueError, match="Inconsistent budget grid"):
        figures.collect_data(saved_study)


def test_different_risk_targets_cannot_share_a_target_line(saved_study):
    (saved_study / "small/class-weight-seed1.json").write_text('{"risk_target": 0.1}')
    with pytest.raises(ValueError, match="different B10 risk targets"):
        figures.collect_data(saved_study)


def test_export_fingerprints_inputs_and_is_repeatable(saved_study, tmp_path):
    before = {p.relative_to(saved_study).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in saved_study.rglob("*.json")}
    out = tmp_path / "figures"
    first = figures.export(saved_study, out, data_only=True)
    second = figures.export(saved_study, out, data_only=True)
    assert first == second
    assert first["sources"] == before
    for filename, digest in first["outputs"].items():
        assert hashlib.sha256((out / filename).read_bytes()).hexdigest() == digest
    assert before == {p.relative_to(saved_study).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in saved_study.rglob("*.json")}


def test_nonfinite_numbers_are_rejected():
    with pytest.raises(ValueError, match="finite number"):
        figures._stats([float("nan")])
    with pytest.raises(ValueError, match="finite number"):
        figures._stats([True])


def test_render_all_figures_from_saved_reports(saved_study, tmp_path):
    pytest.importorskip("matplotlib")
    from PIL import Image

    out = tmp_path / "plots"
    manifest = figures.export(saved_study, out)
    assert len(manifest["outputs"]) == 12
    for stem, _, _ in figures.FIGURES:
        with Image.open(out / f"{stem}.png") as image:
            assert image.width >= 800 and image.height >= 400
        assert (out / f"{stem}.svg").stat().st_size > 1000
