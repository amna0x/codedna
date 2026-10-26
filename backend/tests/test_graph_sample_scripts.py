"""The M2 graph precision tools: seeded sampling and Wilson scoring (D-058)."""

from __future__ import annotations

import csv
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"scripts/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project(repo):
    repo.write("a/Core.java", "package a;\npublic class Core {}\n")
    repo.write("a/Use.java", "package a;\nclass Use {\n  Core core;\n}\n")
    repo.write("b/Wild.java", "package b;\nimport a.*;\nclass Wild { Core c; }\n")
    repo.commit("base")
    return repo


def test_sample_is_seeded_stratified_and_never_overwrites(project, tmp_path):
    sampler = load("sample_graph_edges")
    first = tmp_path / "s.csv"
    assert sampler.main([str(project.path), "--per-label", "5", "--out", str(first)]) == 0
    rows = list(csv.DictReader(open(first, encoding="utf-8")))
    assert {r["confidence"] for r in rows} == {"confirmed", "heuristic"}
    use = next(r for r in rows if r["source"] == "type:a.Use")
    assert use["evidence_file"] == "a/Use.java" and use["line_text"] == "Core core;"
    again = sampler.sample_edges(project.path, "HEAD", 5, 0)[1]
    assert [r["target"] for r in again] == [r["target"] for r in rows]
    with pytest.raises(SystemExit):
        sampler.main([str(project.path), "--out", str(first)])


def test_score_counts_labels_and_rejects_unlabelled_rows(tmp_path):
    scorer = load("score_graph_sample")
    path = tmp_path / "labelled.csv"
    fields = ["row", "confidence", "label"]
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fields)
        writer.writeheader()
        writer.writerows([{"row": 1, "confidence": "confirmed", "label": "correct"},
                          {"row": 2, "confidence": "heuristic", "label": "incorrect"},
                          {"row": 3, "confidence": "heuristic", "label": "unclear"}])
    result = scorer.score([path])["by_confidence"]
    assert result["confirmed"]["precision"] == 1.0
    assert result["heuristic"] == {"correct": 0, "incorrect": 1, "unclear": 1, "precision": 0.0,
                                   "wilson_95": scorer.wilson(0, 1)}
    assert result["all"]["precision"] == 0.5
    assert scorer.wilson(160, 160)[0] == pytest.approx(0.9766, abs=1e-4)
    with open(path, "a", newline="", encoding="utf-8") as handle:
        handle.write("4,confirmed,\n")
    with pytest.raises(SystemExit, match="row 4"):
        scorer.score([path])
