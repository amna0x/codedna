"""scripts/make_hikaricp_demo.py on a tiny local repository (no download)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from codedna.test_history.features import Dataset, Row

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "make_hikaricp_demo.py"
JAVA = "package a;\npublic class Core {\n    int value() { return %d; }\n}\n"
TEST = ("package a;\nimport org.junit.jupiter.api.Test;\nclass %s {\n    Core core;\n"
        "    @Test void t() {}\n}\n")


def bare(repo, tmp_path) -> str:
    """The script reads a bare repository, as RTPTorrent ships them."""
    target = tmp_path / "bare.git"
    repo.git("clone", "--quiet", "--bare", str(repo.path), str(target))
    return str(target)


def load_script():
    spec = importlib.util.spec_from_file_location("make_hikaricp_demo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_workspace_holds_only_prior_history_and_the_real_outcome(repo, tmp_path):
    repo.write("pom.xml", "<project/>\n")
    repo.write("src/test/java/a/CoreTest.java", TEST % "CoreTest")
    repo.write("src/test/java/a/OtherTest.java", TEST.replace("Core core;", "") % "OtherTest")
    shas = []
    for value in range(4):
        repo.write("src/main/java/a/Core.java", JAVA % value)
        shas.append(repo.commit(f"v{value}"))
    rows = [Row(sha, i, test, int(i == 3 and test == "a.CoreTest"), 2.0 if test == "a.CoreTest" else 6.0,
                {"past_runs": float(i)})
            for i, sha in enumerate(shas) for test in ("a.CoreTest", "a.OtherTest")]
    dataset = tmp_path / "dataset.csv"
    Dataset(rows, ["past_runs"], shas).to_csv(dataset)
    dest = tmp_path / "demo"

    script = load_script()
    assert script.main([str(dest), "--repo", bare(repo, tmp_path), "--dataset", str(dataset),
                        "--commit", shas[3]]) == 0

    history = Dataset.from_csv(dest / ".codedna/history.csv")
    assert history.commits == shas[:3]  # nothing of the demo commit or later
    assert (dest / ".git/HEAD").read_text().strip() == "ref: refs/heads/codedna-demo"
    summary = json.loads((dest / ".codedna/demo.json").read_text())
    assert summary["base"] == shas[2] and summary["head"] == shas[3]
    assert summary["real"]["failing_tests"] == ["a.CoreTest"]
    assert summary["dependency"]["caught"] == ["a.CoreTest"]
    assert summary["dependency"]["missed"] == []
    assert summary["dependency"]["share_of_ci_test_time"] == 0.25
    assert summary["risk"]["status"] == "unvalidated"  # three commits are far too little history


def test_demo_refuses_untested_commits_and_existing_folders(repo, tmp_path):
    import pytest
    repo.write("pom.xml", "<project/>\n")
    first = repo.commit("one")
    second = repo.commit("two")
    dataset = tmp_path / "dataset.csv"
    Dataset([Row(first, 0, "a.T", 0, 1.0, {})], [], [first]).to_csv(dataset)
    script = load_script()
    source = bare(repo, tmp_path)
    with pytest.raises(SystemExit, match="2"):  # argparse error: not a tested pair
        script.main([str(tmp_path / "x"), "--repo", source, "--dataset", str(dataset),
                     "--commit", second])
    with pytest.raises(SystemExit, match="2"):  # argparse error: folder exists
        script.main([str(tmp_path), "--repo", source, "--dataset", str(dataset),
                     "--commit", second])
    assert not (tmp_path / "x").exists()
