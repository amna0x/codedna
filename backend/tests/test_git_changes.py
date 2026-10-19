"""Tests for file-level Git change extraction (Milestone 1, first slice)."""

from __future__ import annotations

from pathlib import Path

import pytest

from codedna.git_analysis import (
    InvalidCommitError,
    InvalidRepositoryError,
    extract_changes,
)
from conftest import numbered_lines

JAVA_CLASS = """package example;

public class OrderService {
    public int total(int price, int quantity) {
        return price * quantity;
    }
}
"""


def by_path(report):
    return {changed.path: changed for changed in report.changed_files}


# --- repository and commit validation --------------------------------------


def test_valid_repository_reports_full_shas(repo):
    repo.write("README.md", "hello\n")
    base = repo.commit("base")
    repo.write("README.md", "hello world\n")
    head = repo.commit("head")

    report = extract_changes(repo.path, base, head)

    assert Path(report.repository) == repo.path.resolve()
    assert report.base_commit == base
    assert report.head_commit == head
    assert report.analysis_level == "file"
    assert report.warnings == []


def test_short_sha_and_symbolic_revisions_are_resolved(repo):
    repo.write("a.txt", "1\n")
    base = repo.commit("base")
    repo.write("a.txt", "2\n")
    head = repo.commit("head")

    report = extract_changes(repo.path, base[:8], "HEAD")

    assert report.base_commit == base
    assert report.head_commit == head


def test_missing_repository_path_fails_clearly(tmp_path):
    with pytest.raises(InvalidRepositoryError, match="does not exist"):
        extract_changes(tmp_path / "nope", "HEAD", "HEAD")


def test_directory_that_is_not_a_repository_fails_clearly(tmp_path):
    plain_dir = tmp_path / "plain"
    plain_dir.mkdir()
    with pytest.raises(InvalidRepositoryError, match="not a Git repository"):
        extract_changes(plain_dir, "HEAD", "HEAD")


def test_file_instead_of_directory_fails_clearly(tmp_path):
    some_file = tmp_path / "file.txt"
    some_file.write_text("x", encoding="utf-8")
    with pytest.raises(InvalidRepositoryError, match="not a directory"):
        extract_changes(some_file, "HEAD", "HEAD")


@pytest.mark.parametrize(
    "bad_revision",
    ["0123456789abcdef0123456789abcdef01234567", "not-a-branch", "", "--output=evil"],
)
def test_invalid_commit_fails_clearly(repo, bad_revision):
    repo.write("a.txt", "1\n")
    good = repo.commit("base")
    with pytest.raises(InvalidCommitError):
        extract_changes(repo.path, good, bad_revision)
    with pytest.raises(InvalidCommitError):
        extract_changes(repo.path, bad_revision, good)


def test_repository_without_commits_reports_invalid_commit(repo):
    with pytest.raises(InvalidCommitError):
        extract_changes(repo.path, "HEAD", "HEAD")


# --- change kinds -----------------------------------------------------------


def test_modified_java_file_reports_head_and_base_line_ranges(repo):
    repo.write("src/main/java/example/OrderService.java", JAVA_CLASS)
    base = repo.commit("base")
    repo.write(
        "src/main/java/example/OrderService.java",
        JAVA_CLASS.replace("return price * quantity;", "int sum = price * quantity;\n        return sum;"),
    )
    head = repo.commit("head")

    changed = by_path(extract_changes(repo.path, base, head))["src/main/java/example/OrderService.java"]

    assert changed.status == "modified"
    assert changed.is_java is True
    assert changed.changed_lines == [[5, 6]]
    assert changed.removed_lines == [[5, 5]]


def test_multiple_hunks_and_pure_deletion_ranges(repo):
    repo.write("notes.txt", numbered_lines(20))
    base = repo.commit("base")
    lines = numbered_lines(20).splitlines(keepends=True)
    lines[1] = "changed 2\n"          # modify line 2
    del lines[9:12]                   # delete lines 10-12
    lines.append("line 21\n")         # append at end
    repo.write("notes.txt", "".join(lines))
    head = repo.commit("head")

    changed = by_path(extract_changes(repo.path, base, head))["notes.txt"]

    assert changed.changed_lines == [[2, 2], [18, 18]]
    assert changed.removed_lines == [[2, 2], [10, 12]]


def test_added_java_file(repo):
    repo.write("README.md", "x\n")
    base = repo.commit("base")
    repo.write("src/main/java/example/OrderService.java", JAVA_CLASS)
    head = repo.commit("head")

    changed = by_path(extract_changes(repo.path, base, head))["src/main/java/example/OrderService.java"]

    assert changed.status == "added"
    assert changed.is_java is True
    assert changed.changed_lines == [[1, 7]]
    assert changed.removed_lines == []


def test_deleted_java_file(repo):
    repo.write("src/main/java/example/OrderService.java", JAVA_CLASS)
    repo.write("README.md", "x\n")
    base = repo.commit("base")
    (repo.path / "src/main/java/example/OrderService.java").unlink()
    head = repo.commit("head")

    changed = by_path(extract_changes(repo.path, base, head))["src/main/java/example/OrderService.java"]

    assert changed.status == "deleted"
    assert changed.is_java is True
    assert changed.changed_lines == []
    assert changed.removed_lines == [[1, 7]]


def test_renamed_java_file_without_content_change(repo):
    repo.write("src/main/java/example/OrderService.java", JAVA_CLASS)
    base = repo.commit("base")
    repo.git("mv", "src/main/java/example/OrderService.java", "src/main/java/example/Orders.java")
    head = repo.commit("head")

    report = extract_changes(repo.path, base, head)

    assert len(report.changed_files) == 1
    changed = report.changed_files[0]
    assert changed.status == "renamed"
    assert changed.path == "src/main/java/example/Orders.java"
    assert changed.old_path == "src/main/java/example/OrderService.java"
    assert changed.similarity == 100
    assert changed.is_java is True
    assert changed.changed_lines == []
    assert changed.removed_lines == []


def test_renamed_and_edited_file_reports_line_ranges(repo):
    content = numbered_lines(30)
    repo.write("old/Big.java", content)
    base = repo.commit("base")
    (repo.path / "old/Big.java").unlink()
    repo.write("new/Big.java", content.replace("line 15\n", "line fifteen\n"))
    head = repo.commit("head")

    changed = extract_changes(repo.path, base, head).changed_files[0]

    assert changed.status == "renamed"
    assert changed.old_path == "old/Big.java"
    assert changed.path == "new/Big.java"
    assert changed.similarity is not None and changed.similarity < 100
    assert changed.changed_lines == [[15, 15]]
    assert changed.removed_lines == [[15, 15]]


def test_non_java_files_are_reported_but_not_marked_java(repo):
    repo.write("pom.xml", "<project/>\n")
    repo.write("docs/guide.md", "a\n")
    base = repo.commit("base")
    repo.write("pom.xml", "<project></project>\n")
    repo.write("docs/guide.md", "a\nb\n")
    head = repo.commit("head")

    files = by_path(extract_changes(repo.path, base, head))

    assert set(files) == {"pom.xml", "docs/guide.md"}
    assert all(not changed.is_java for changed in files.values())
    assert files["docs/guide.md"].changed_lines == [[2, 2]]


def test_empty_diff_between_identical_commits(repo):
    repo.write("a.txt", "1\n")
    base = repo.commit("base")
    head = repo.commit("empty commit")

    assert extract_changes(repo.path, base, head).changed_files == []
    assert extract_changes(repo.path, base, base).changed_files == []


def test_filenames_with_spaces(repo):
    repo.write("src/main/java/my pkg/Order Service.java", JAVA_CLASS)
    repo.write("docs/release notes.txt", "v1\n")
    base = repo.commit("base")
    repo.write("src/main/java/my pkg/Order Service.java", JAVA_CLASS.replace("price", "unitPrice"))
    repo.git("mv", "docs/release notes.txt", "docs/old release notes.txt")
    head = repo.commit("head")

    files = by_path(extract_changes(repo.path, base, head))

    java = files["src/main/java/my pkg/Order Service.java"]
    assert java.status == "modified"
    assert java.changed_lines == [[4, 5]]
    renamed = files["docs/old release notes.txt"]
    assert renamed.status == "renamed"
    assert renamed.old_path == "docs/release notes.txt"


def test_binary_file_is_flagged_with_warning(repo):
    repo.write_bytes("lib/data.bin", b"\x00\x01\x02")
    base = repo.commit("base")
    repo.write_bytes("lib/data.bin", b"\x00\x09\x09\x09")
    head = repo.commit("head")

    report = extract_changes(repo.path, base, head)

    changed = report.changed_files[0]
    assert changed.is_binary is True
    assert changed.changed_lines == []
    assert report.warnings == ["binary file, line ranges unavailable: lib/data.bin"]


def test_comparison_across_several_commits(repo):
    repo.write("A.java", "class A {}\n")
    base = repo.commit("c1")
    repo.write("B.java", "class B {}\n")
    repo.commit("c2")
    repo.write("A.java", "class A { int x; }\n")
    head = repo.commit("c3")

    files = by_path(extract_changes(repo.path, base, head))

    assert files["A.java"].status == "modified"
    assert files["B.java"].status == "added"
