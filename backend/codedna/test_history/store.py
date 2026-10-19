"""SQLite store for commit history and test results (docs/DECISIONS.md D-021).

One database file per studied repository. Tables:

* ``commits``      — first-parent history in chronological order (``seq``).
* ``changed_files``— numstat per commit (renames recorded as delete + add).
* ``test_results`` — one row per (commit, test class, run source).

No author names or e-mail addresses are stored.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from codedna.test_mapping.results import TestRunResult

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS commits (
    sha TEXT PRIMARY KEY,
    seq INTEGER NOT NULL UNIQUE,      -- 0 = oldest commit mined
    parent TEXT,
    committed_at INTEGER NOT NULL      -- Unix time (committer date)
);
CREATE TABLE IF NOT EXISTS changed_files (
    sha TEXT NOT NULL REFERENCES commits(sha),
    path TEXT NOT NULL,
    added INTEGER,                     -- NULL for binary files
    deleted INTEGER,
    PRIMARY KEY (sha, path)
);
CREATE TABLE IF NOT EXISTS test_results (
    sha TEXT NOT NULL,
    test_id TEXT NOT NULL,
    status TEXT NOT NULL,              -- passed | failed | error | skipped
    time REAL NOT NULL,
    source TEXT NOT NULL,              -- where the result came from
    PRIMARY KEY (sha, test_id, source)
);
CREATE INDEX IF NOT EXISTS idx_results_sha ON test_results(sha);
"""


@dataclass(frozen=True)
class CommitRecord:
    sha: str
    seq: int
    parent: str | None
    committed_at: int


@dataclass(frozen=True)
class FileChange:
    path: str
    added: int | None
    deleted: int | None


@dataclass(frozen=True)
class ResultRecord:
    test_id: str
    status: str
    time: float

    @property
    def failed(self) -> bool:
        return self.status in ("failed", "error")


class HistoryStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.executescript(_SCHEMA)
        self.db.execute("INSERT OR IGNORE INTO meta VALUES ('schema_version', ?)",
                        (str(SCHEMA_VERSION),))
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> HistoryStore:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # --- metadata ----------------------------------------------------------------

    def set_meta(self, key: str, value: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO meta VALUES (?, ?)", (key, value))
        self.db.commit()

    def get_meta(self, key: str) -> str | None:
        row = self.db.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    # --- commits -------------------------------------------------------------------

    def replace_commits(self, commits: list[tuple[CommitRecord, list[FileChange]]]) -> None:
        """Store mined history; ``seq`` must already be chronological from 0."""
        with self.db:
            self.db.execute("DELETE FROM changed_files")
            self.db.execute("DELETE FROM commits")
            for commit, files in commits:
                self.db.execute("INSERT INTO commits VALUES (?, ?, ?, ?)",
                                (commit.sha, commit.seq, commit.parent, commit.committed_at))
                self.db.executemany(
                    "INSERT OR REPLACE INTO changed_files VALUES (?, ?, ?, ?)",
                    [(commit.sha, f.path, f.added, f.deleted) for f in files])

    def commits(self) -> list[CommitRecord]:
        rows = self.db.execute("SELECT sha, seq, parent, committed_at FROM commits ORDER BY seq")
        return [CommitRecord(*row) for row in rows]

    def changed_files(self, sha: str) -> list[FileChange]:
        rows = self.db.execute(
            "SELECT path, added, deleted FROM changed_files WHERE sha = ? ORDER BY path", (sha,))
        return [FileChange(*row) for row in rows]

    # --- test results ---------------------------------------------------------------

    def add_run(self, run: TestRunResult, source: str) -> int:
        """Store every test-class result of ``run``; returns the number of rows."""
        rows = [(run.commit, test_id, result.status, result.time, source)
                for test_id, result in run.tests.items()]
        with self.db:
            self.db.executemany("INSERT OR REPLACE INTO test_results VALUES (?, ?, ?, ?, ?)", rows)
        return len(rows)

    def add_result(self, sha: str, test_id: str, status: str, time: float, source: str) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO test_results VALUES (?, ?, ?, ?, ?)",
                            (sha, test_id, status, time, source))

    def results(self, sha: str) -> list[ResultRecord]:
        """Results of one commit; with several sources, a failure in any source wins."""
        rows = self.db.execute(
            "SELECT test_id, status, time FROM test_results WHERE sha = ? ORDER BY test_id, source",
            (sha,))
        merged: dict[str, ResultRecord] = {}
        for test_id, status, time in rows:
            current = merged.get(test_id)
            candidate = ResultRecord(test_id, status, time)
            if current is None or (candidate.failed and not current.failed):
                merged[test_id] = candidate
        return list(merged.values())

    def commits_with_results(self) -> set[str]:
        return {row[0] for row in self.db.execute("SELECT DISTINCT sha FROM test_results")}

    def summary(self) -> dict:
        commits = self.db.execute("SELECT COUNT(*) FROM commits").fetchone()[0]
        with_results = len(self.commits_with_results())
        failing = self.db.execute(
            "SELECT COUNT(DISTINCT sha) FROM test_results WHERE status IN ('failed', 'error')"
        ).fetchone()[0]
        tests = self.db.execute("SELECT COUNT(DISTINCT test_id) FROM test_results").fetchone()[0]
        return {"database": str(self.path), "commits": commits,
                "commits_with_results": with_results, "commits_with_failures": failing,
                "test_classes": tests, "repository": self.get_meta("repository")}
