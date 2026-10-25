"""History replay (D-049): traces, timelines, discovery, CLI, API and the recording script."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from test_risk_calibration import synthetic_dataset

from codedna.cli import main
from codedna.models.experiment import run_experiment
from codedna.models.replay import (
    CODEDNA,
    ReplayError,
    find_replay_sources,
    replay_from_file,
    replay_overview,
    replay_timeline,
)

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "experiments" / "results" / "study11-2026-10-21"
TRACES = ROOT / "experiments" / "results" / "replay-2026-10-25"
SHOWN = ["B0_retest_all", "B4_dependency", "B3@B10_hybrid", "B10_hybrid"]


@pytest.fixture(scope="module")
def traced():
    return run_experiment(synthetic_dataset(commits=30), sweeps=False, ablations=False, trace=True)


def compact(report: dict) -> dict:
    return {k: v for k, v in report.items() if k != "replay"}


def write(path: Path, report: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report), encoding="utf-8")
    return path


# --- recording -------------------------------------------------------------------------


def test_trace_leaves_the_experiment_unchanged(traced):
    plain = run_experiment(synthetic_dataset(commits=30), sweeps=False, ablations=False)
    assert compact(traced) == plain


def test_trace_matches_per_commit_outcomes_for_every_policy(traced):
    trace, per_commit = traced["replay"], traced["per_commit"]
    assert set(trace["policies"]) == set(SHOWN)
    test_shas = [c["sha"] for c in trace["commits"]]
    assert len(test_shas) == traced["config"]["splits"]["test"]
    assert test_shas == sorted(test_shas)  # chronological, as in the experiment
    for name, outcomes in trace["policies"].items():
        assert len(outcomes) == len(per_commit[name])
        for commit, o, (time, failing, missed) in zip(trace["commits"], outcomes,
                                                      per_commit[name]):
            assert (o["time_ratio"], len(commit["failing"]), len(o["missed"])) == \
                (time, failing, missed)
            assert set(o["missed"]) <= set(commit["failing"])
            assert 0 <= o["seconds"] <= commit["suite_seconds"] + 1e-9
    retest = trace["policies"]["B0_retest_all"]
    assert all(o["missed"] == [] and o["estimated_risk"] is None for o in retest)
    assert all(o["estimated_risk"] is not None for o in trace["policies"][CODEDNA])


# --- timelines -------------------------------------------------------------------------


def test_timeline_from_a_trace_agrees_with_the_report(traced):
    timeline = replay_timeline(traced, project="demo")
    assert timeline["source"]["kind"] == "trace"
    assert timeline["notes"] == []
    assert timeline["checks"] and all(check["match"] for check in timeline["checks"])
    assert [p["key"] for p in timeline["policies"]] == SHOWN
    reported = traced["policies"][CODEDNA]
    ours = timeline["summary"][CODEDNA]
    assert ours["missed_failures"] == reported["missed_failures"]
    assert ours["mean_time_ratio"] == pytest.approx(reported["mean_time_ratio"], abs=5e-4)
    assert ours["mean_estimated_skip_risk"] == pytest.approx(
        reported["mean_estimated_skip_risk"], abs=5e-4)

    commits = timeline["commits"]
    assert commits[0]["sha"] and commits[0]["failing_tests"] is not None
    for key in SHOWN:
        running = timeline["cumulative"][key]
        assert all(len(series) == len(commits) for series in running.values())
        assert running["mean_time_ratio"][-1] == timeline["summary"][key]["mean_time_ratio"]
        assert running["failures_missed"][-1] == timeline["summary"][key]["missed_failures"]
        assert running["seconds_run"][-1] == pytest.approx(timeline["summary"][key]["seconds_run"])
        caught = running["failures_caught"]
        assert caught == sorted(caught)  # running totals never go down
    full = timeline["cumulative"]["B0_retest_all"]
    assert full["seconds_saved"][-1] == 0 and full["failures_missed"][-1] == 0


def test_events_list_codedna_catches_misses_and_fallbacks(traced):
    timeline = replay_timeline(traced)
    by_index = {c["index"]: c for c in timeline["commits"]}
    assert timeline["events"]
    for event in timeline["events"]:
        commit = by_index[event["index"]]
        o = commit["outcomes"][CODEDNA]
        if event["kind"] == "caught":
            assert commit["failing"] and o["missed"] == 0
        elif event["kind"] == "missed":
            assert o["missed"] and event["missed_tests"] == o["missed_tests"]
        else:
            assert event["kind"] == "fallback" and o["fallback"] and not commit["failing"]
    assert {e["index"] for e in timeline["events"] if e["kind"] != "fallback"} == \
        {c["index"] for c in timeline["commits"] if c["failing"]}


def test_compact_report_replays_the_same_totals_without_detail(traced):
    full = replay_timeline(traced)
    lite = replay_timeline(compact(traced))
    assert lite["source"]["kind"] == "per_commit"
    assert any("--replay" in note for note in lite["notes"])
    assert all(check["match"] for check in lite["checks"])
    for key in SHOWN:
        for metric in ("missed_failures", "mean_time_ratio", "observed_miss_rate",
                       "commit_safety_rate"):
            assert lite["summary"][key][metric] == full["summary"][key][metric]
        assert lite["summary"][key]["seconds_run"] is None
        assert lite["cumulative"][key]["seconds_saved"][-1] is None
    assert lite["commits"][0]["sha"] is None


def test_a_report_that_disagrees_with_its_outcomes_is_flagged(traced):
    tampered = copy.deepcopy(traced)
    tampered["policies"][CODEDNA]["missed_failures"] += 1
    timeline = replay_timeline(tampered)
    bad = [c for c in timeline["checks"] if not c["match"]]
    assert [(c["policy"], c["metric"]) for c in bad] == [(CODEDNA, "missed_failures")]
    assert any("missed_failures" in note for note in timeline["notes"])


def test_missing_policies_are_noted_not_invented(traced):
    report = compact(traced)
    report["per_commit"] = {k: v for k, v in report["per_commit"].items() if k != "B4_dependency"}
    timeline = replay_timeline(report)
    assert "B4_dependency" not in timeline["summary"]
    assert any("B4_dependency" in note for note in timeline["notes"])


def test_bad_inputs_raise_clear_errors(tmp_path, traced):
    with pytest.raises(FileNotFoundError):
        replay_from_file(tmp_path / "nope.json")
    (tmp_path / "x.json").write_text("{not json")
    with pytest.raises(ReplayError, match="not JSON"):
        replay_from_file(tmp_path / "x.json")
    with pytest.raises(ReplayError, match="not an experiment report"):
        replay_from_file(write(tmp_path / "y.json", {"hello": 1}))
    with pytest.raises(ReplayError, match="no per-commit outcomes"):
        replay_timeline({"config": {}, "policies": {}})
    future = copy.deepcopy(traced)
    future["replay"]["version"] = 99
    with pytest.raises(ReplayError, match="version"):
        replay_timeline(future)


# --- discovery -------------------------------------------------------------------------


def test_sources_prefer_traces_and_ignore_other_json(tmp_path, traced):
    study, replays = tmp_path / "study", tmp_path / "replays"
    seed1 = copy.deepcopy(compact(traced))
    seed1["config"]["seed"] = 1
    write(study / "alpha" / "experiment-seed1.json", seed1)
    write(study / "alpha" / "experiment-seed0.json", compact(traced))
    write(study / "alpha" / "evaluate-seed0.json", {"config": {}, "policies": {}})
    write(study / "summary.json", {"projects": {}})
    write(replays / "alpha" / "replay-seed0.json", traced)
    found = find_replay_sources([study, replays])
    assert [(s["project"], s["kind"], s["seed"]) for s in found["sources"]] == [
        ("alpha", "trace", 0), ("alpha", "per_commit", 0), ("alpha", "per_commit", 1)]
    assert found["sources"][0]["commits"] == len(traced["replay"]["commits"])
    partly = find_replay_sources([study, tmp_path / "missing"])
    assert partly["missing"] == [str(tmp_path / "missing")] and len(partly["sources"]) == 2
    with pytest.raises(FileNotFoundError):
        find_replay_sources(tmp_path / "missing")


# --- the committed study results --------------------------------------------------------


def test_every_committed_study_report_replays_consistently():
    sources = find_replay_sources(STUDY)["sources"]
    assert len({s["project"] for s in sources}) == 11 and len(sources) == 55
    for source in sources:
        timeline = replay_from_file(source["path"])
        assert all(check["match"] for check in timeline["checks"]), source["path"]


def test_committed_traces_reproduce_the_study_exactly():
    traces = find_replay_sources(TRACES)["sources"]
    assert {s["project"] for s in traces} == {"hikaricp", "jade4j", "littleproxy",
                                              "wicket-bootstrap"}
    for source in traces:
        report = json.loads(Path(source["path"]).read_text(encoding="utf-8"))
        study = json.loads((STUDY / source["project"] / "experiment-seed0.json")
                           .read_text(encoding="utf-8"))
        assert report["policies"] == study["policies"]
        assert report["per_commit"] == study["per_commit"]
        assert report["reproducibility"]["dataset_sha256"] == \
            study["reproducibility"]["dataset_sha256"]
        timeline = replay_from_file(source["path"])
        assert timeline["notes"] == [] and all(c["match"] for c in timeline["checks"])


def test_overview_reproduces_the_study_summary():
    """Mean over seeds, then over projects: the same numbers as the study's summary.json."""
    overview = replay_overview([STUDY, TRACES])
    pooled = json.loads((STUDY / "summary.json").read_text(encoding="utf-8"))["pooled"]["policies"]
    assert len(overview["projects"]) == 11
    assert all(p["mismatches"] == 0 for p in overview["projects"])
    for key in ("B0_retest_all", "B4_dependency", CODEDNA):
        for metric, value in overview["overall"][key].items():
            if metric in pooled[key]:
                assert value["mean"] == pytest.approx(pooled[key][metric]["mean"], abs=2e-4), \
                    (key, metric)
                assert value["projects"] == pooled[key][metric]["projects"]
    within = sum(p["policies"][CODEDNA]["observed_miss_rate"] <= p["risk_target"]
                 for p in overview["projects"])
    assert overview["within_risk_target"] == {"projects": within, "of": 11}

    only_seed0 = replay_overview([STUDY, TRACES], seed=0)
    assert all(p["seeds"] == [0] for p in only_seed0["projects"])
    traced = {p["project"] for p in only_seed0["projects"] if "trace" in p["kinds"]}
    assert traced == {"hikaricp", "jade4j", "littleproxy", "wicket-bootstrap"}


def test_compact_summary_takes_unrecordable_means_from_the_report(traced):
    timeline = replay_timeline(compact(traced))
    ours = timeline["summary"][CODEDNA]
    assert ours["from_report"] == ["mean_estimated_skip_risk", "fallback_rate"]
    assert ours["mean_estimated_skip_risk"] == traced["policies"][CODEDNA]["mean_estimated_skip_risk"]
    assert timeline["summary"]["B3@B10_hybrid"]["from_report"] == []
    assert replay_timeline(traced)["summary"][CODEDNA]["from_report"] == []


# --- CLI -------------------------------------------------------------------------------


def test_cli_lists_and_replays(tmp_path, traced, capsys):
    report = write(tmp_path / "beta" / "experiment-seed0.json", traced)
    assert main(["replay", "--list", str(tmp_path)]) == 0
    listed = json.loads(capsys.readouterr().out)
    assert listed["sources"][0]["path"] == str(report)

    out = tmp_path / "timeline.json"
    assert main(["replay", str(report), "--output", str(out)]) == 0
    timeline = json.loads(out.read_text())
    assert timeline["project"] == "beta" and timeline["source"]["kind"] == "trace"

    assert main(["replay", "--overview", str(tmp_path), "--output", str(out)]) == 0
    assert [p["project"] for p in json.loads(out.read_text())["projects"]] == ["beta"]

    assert main(["replay"]) == 1
    assert "give a REPORT" in capsys.readouterr().err
    assert main(["replay", str(tmp_path / "missing.json")]) == 1


def test_cli_experiment_replay_flag_records_the_trace(tmp_path):
    dataset = tmp_path / "dataset.csv"
    synthetic_dataset(commits=30).to_csv(dataset)
    out = tmp_path / "report.json"
    assert main(["history", "experiment", "--from-dataset", str(dataset), "--no-sweeps",
                 "--no-ablations", "--replay", "--output", str(out)]) == 0
    assert json.loads(out.read_text())["replay"]["version"] == 1


# --- API -------------------------------------------------------------------------------


def test_api_replay_endpoints(tmp_path, traced):
    pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from codedna.api.app import create_app

    token = "r" * 32
    api = TestClient(create_app(token), base_url="http://127.0.0.1:8765")
    auth = {"X-CodeDNA-Token": token}
    report = write(tmp_path / "gamma" / "experiment-seed0.json", traced)

    assert api.post("/api/replay", json={"path": str(report)}).status_code == 401
    timeline = api.post("/api/replay", json={"path": str(report)}, headers=auth).json()
    assert timeline["project"] == "gamma" and timeline["notes"] == []
    sources = api.post("/api/replay/sources", json={"folders": [str(tmp_path)]},
                       headers=auth).json()
    assert [s["project"] for s in sources["sources"]] == ["gamma"]
    overview = api.post("/api/replay/overview", json={"folders": [str(tmp_path)], "seed": 0},
                        headers=auth).json()
    assert overview["projects"][0]["project"] == "gamma"

    missing = api.post("/api/replay", json={"path": str(tmp_path / "no.json")}, headers=auth)
    assert missing.status_code == 400
    broken = write(tmp_path / "broken.json", {"hi": 1})
    assert api.post("/api/replay", json={"path": str(broken)}, headers=auth).status_code == 400
    assert api.post("/api/replay/sources", json={"folders": []}, headers=auth).status_code == 422


# --- recording script ------------------------------------------------------------------


def load_script():
    spec = importlib.util.spec_from_file_location("record_replays",
                                                  ROOT / "scripts" / "record_replays.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_record_script_writes_checked_traces_and_skips_the_rest(tmp_path):
    study, out = tmp_path / "study", tmp_path / "out"
    dataset = synthetic_dataset(commits=30)
    for name in ("ok", "drifted", "nodata"):
        report = run_experiment(dataset, sweeps=False, ablations=False)
        if name == "drifted":
            report["policies"][CODEDNA]["missed_failures"] += 1
        write(study / name / "experiment-seed0.json", report)
        if name != "nodata":
            dataset.to_csv(study / name / "dataset.csv")
    script = load_script()

    result = script.record(study, out, seed=0)
    assert result == {"written": ["ok"], "skipped": ["nodata"], "mismatch": ["drifted"],
                      "exists": []}
    trace = json.loads((out / "ok" / "replay-seed0.json").read_text())
    assert trace["replay"]["version"] == 1
    assert not (out / "drifted").exists()
    assert script.record(study, out, seed=0, projects=["ok"])["exists"] == ["ok"]
    assert script.main(["--study", str(study), "--out", str(tmp_path / "o2")]) == 1
