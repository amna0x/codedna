"""End-to-end tests for ``codedna analyze``."""

from __future__ import annotations

import json

import pytest

from codedna.cli import EXIT_ANALYSIS_ERROR, EXIT_OK, main


def test_analyze_prints_json_report(repo, capsys):
    repo.write("src/main/java/example/A.java", "class A {}\n")
    base = repo.commit("base")
    repo.write("src/main/java/example/A.java", "class A { int x; }\n")
    head = repo.commit("head")

    exit_code = main(["analyze", "--repo", str(repo.path), "--base", base, "--head", head])

    assert exit_code == EXIT_OK
    report = json.loads(capsys.readouterr().out)
    assert report["base_commit"] == base
    assert report["head_commit"] == head
    assert report["changed_files"] == [
        {
            "path": "src/main/java/example/A.java",
            "status": "modified",
            "old_path": None,
            "similarity": None,
            "is_java": True,
            "is_binary": False,
            "changed_lines": [[1, 1]],
            "removed_lines": [[1, 1]],
        }
    ]
    assert report["warnings"] == []


def test_analyze_writes_output_file(repo, tmp_path, capsys):
    repo.write("a.txt", "1\n")
    base = repo.commit("base")
    repo.write("a.txt", "2\n")
    head = repo.commit("head")
    output = tmp_path / "out" / "report.json"
    output.parent.mkdir()

    exit_code = main([
        "analyze", "--repo", str(repo.path), "--base", base, "--head", head,
        "--output", str(output),
    ])

    assert exit_code == EXIT_OK
    assert capsys.readouterr().out == ""
    assert json.loads(output.read_text(encoding="utf-8"))["changed_files"][0]["path"] == "a.txt"


def test_analyze_invalid_repository_exits_with_error(tmp_path, capsys):
    exit_code = main(["analyze", "--repo", str(tmp_path / "missing"), "--base", "a", "--head", "b"])

    assert exit_code == EXIT_ANALYSIS_ERROR
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: repository path does not exist" in captured.err


def test_analyze_invalid_commit_exits_with_error(repo, capsys):
    repo.write("a.txt", "1\n")
    base = repo.commit("base")

    exit_code = main(["analyze", "--repo", str(repo.path), "--base", base, "--head", "deadbeef"])

    assert exit_code == EXIT_ANALYSIS_ERROR
    assert "error: unknown commit: 'deadbeef'" in capsys.readouterr().err


def test_missing_required_argument_is_usage_error(capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(["analyze", "--repo", "."])
    assert excinfo.value.code == 2
    assert "--base" in capsys.readouterr().err
