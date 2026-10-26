"""Offline miniature of the agent brake study on SWE-bench patches (D-062)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CORE = "package a;\npublic class Core {\n  int value() { return 1; }\n}\n"
OTHER = "package a;\npublic class Other {\n  int value() { return 2; }\n}\n"


def load():
    spec = importlib.util.spec_from_file_location("brake_study",
                                                  ROOT / "scripts/swebench_brake_study.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def junit(name, uses, extra=""):
    return (f"package a;\nimport org.junit.jupiter.api.Test;\nclass {name} {{\n"
            f"  @Test void x() {{ new {uses}().value(); }}\n{extra}}}\n")


def test_parsers_read_harness_files():
    study = load()
    script = ("#!/bin/bash\ngit checkout " + "a" * 40 + " src/test/T.java\n"
              "git apply --verbose --reject - <<'EOF_1'\ndiff --git a/x b/x\n+line\nEOF_1\n"
              "echo done\n")
    assert study.test_patch(script) == "diff --git a/x b/x\n+line\n"
    crlf = script.replace("+line\n", "+line\r\n")  # files with CRLF endings stay byte-exact
    assert study.test_patch(crlf) == "diff --git a/x b/x\n+line\r\n"
    assert study.base_commit(script, "") == "a" * 40
    no_reset = "echo 'No test files to reset'\n"
    assert study.base_commit(no_reset, "+ git -c core.fileMode=false diff " + "b" * 40) == "b" * 40
    with pytest.raises(ValueError):
        study.base_commit(no_reset, "")
    assert study.log_base_url("assets:\n  logs: s3://bucket/multi/sub/logs\n") == \
        "https://bucket.s3.amazonaws.com/multi/sub/logs"
    assert study.log_base_url("  logs: https://github.com/O/R/tree/main/logs\n") == \
        "https://raw.githubusercontent.com/O/R/main/logs"


def test_benchmark_test_names_map_to_classes_or_stay_unmapped():
    study = load()
    names = {"NodeTest": ["p.NodeTest"], "Twice": ["p.Twice", "q.Twice"]}
    assert study.test_class("p.ATest#m", names) == "p.ATest"
    assert study.test_class("NodeTest > testX", names) == "p.NodeTest"
    assert study.test_class("NodeTest", names) == "p.NodeTest"
    assert study.test_class("javac-A.java(lombok.transform.TestWithDelombok)", names) == \
        "lombok.transform.TestWithDelombok"
    assert study.test_class("Twice", names) is None and study.test_class("Gone", names) is None


def test_run_builds_harness_states_and_scores_the_plan(repo, tmp_path):
    study = load()
    upstream = repo
    upstream.write("pom.xml", "<project/>")
    upstream.write("src/main/java/a/Core.java", CORE)
    upstream.write("src/main/java/a/Other.java", OTHER)
    upstream.write("src/test/java/a/CoreTest.java", junit("CoreTest", "Core"))
    upstream.write("src/test/java/a/OtherTest.java", junit("OtherTest", "Other"))
    base = upstream.commit("base")
    upstream.git("config", "uploadpack.allowAnySHA1InWant", "true")

    # Benchmark test patch: a new test method in CoreTest.
    upstream.write("src/test/java/a/CoreTest.java",
                   junit("CoreTest", "Core", "  @Test void y() {}\n"))
    tests_patch = upstream.git("diff") + "\n"
    upstream.git("checkout", "--", ".")
    # Agent patch: edits Core and (wrongly) CoreTest; the harness resets CoreTest.
    upstream.write("src/main/java/a/Core.java", CORE.replace("return 1", "return 3"))
    upstream.write("src/test/java/a/CoreTest.java", junit("CoreTest", "Core", "  // agent\n"))
    agent_patch = upstream.git("diff") + "\n"
    upstream.git("checkout", "--", ".")

    data = tmp_path / "data"
    instance = "acme__proj-1"
    (data / "instances" / instance).mkdir(parents=True)
    (data / "instances" / instance / "eval.sh").write_bytes((
        f"git checkout {base} src/test/java/a/CoreTest.java\n"
        f"git apply --verbose --reject - <<'EOF_9'\n{tests_patch}EOF_9\n").encode())
    (data / "instances" / instance / "test_output_head.txt").write_text("")
    reports = {
        "broke": {"resolved": False, "FAIL_TO_PASS": {"success": [], "failure": ["a.CoreTest#y"]},
                  "PASS_TO_PASS": {"success": [], "failure": []}},
        "fixed": {"resolved": True, "FAIL_TO_PASS": {"success": ["CoreTest > y"], "failure": []},
                  "PASS_TO_PASS": {"success": ["a.CoreTest#x"], "failure": []}},
    }
    for name, outcome in reports.items():
        folder = data / "submissions" / name / instance
        folder.mkdir(parents=True)
        (folder / "patch.diff").write_bytes(agent_patch.encode())
        resolved = outcome.pop("resolved")
        (folder / "report.json").write_text(json.dumps({instance: {
            "patch_is_None": False, "patch_successfully_applied": True, "infra_failure": False,
            "resolved": resolved, "tests_status": outcome}}))
    (data / "submissions" / "none" / instance).mkdir(parents=True)
    manifest = {"experiments_commit": "c" * 40, "submissions": {
        s: {"logs": "x", "instances": [instance]} for s in ("broke", "fixed", "none")}}
    (data / "manifest.json").write_text(json.dumps(manifest))

    out = tmp_path / "out"
    summary = study.run(data, tmp_path / "work", out,
                        repo_url=str(upstream.path))
    rows = {r["submission"]: r for r in __import__("csv").DictReader(open(out / "pairs.csv"))}
    assert rows["none"]["status"] == "no_patch"
    assert rows["broke"]["status"] == "analysed" and rows["broke"]["a2_caught"] == "True"
    assert rows["broke"]["a2_selected"] == "1" and rows["broke"]["total_tests"] == "2"
    assert rows["fixed"]["a2_reach"] == "True" and rows["fixed"]["a2_caught"] == ""
    assert summary["all"]["a2_catch"] == [1, 1] and summary["all"]["a1_catch"] == [1, 1]
    assert summary["all"]["a2_ratio_median"] == 0.5
    assert summary["statuses"] == {"analysed": 2, "no_patch": 1}
    assert (out / "partial" / f"{instance}.json").is_file()  # resumable checkpoint
    with pytest.raises(SystemExit, match="never overwritten"):
        study.run(data, tmp_path / "work", out, repo_url=str(upstream.path))
