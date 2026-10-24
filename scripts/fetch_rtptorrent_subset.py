"""Fetch selected RTPTorrent v1.1 logs and bare repos using HTTP byte ranges.

Only requested projects, their main result CSVs, and the shared job/commit map
are written. No third-party project code is executed. ZIP CRCs and local
SHA-256 hashes verify the selected entries; the whole-archive MD5 cannot be
verified without downloading the entire archive.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import io
import json
import shutil
import stat
import time
import urllib.error
import urllib.request
import zipfile
from collections import OrderedDict
from pathlib import Path, PurePosixPath

URL = "https://zenodo.org/records/4046180/files/rtp-torrent-v11.zip?download=1"
ARCHIVE_MD5 = "1f7fa822b0cf155bd007a94d1a24a336"
DEFAULT_PROJECTS = ["brettwooldridge@HikariCP", "adamfisk@LittleProxy",
                    "neuland@jade4j", "l0rdn1kk0n@wicket-bootstrap"]


class RemoteZip(io.RawIOBase):
    """A seekable, bounded-cache view of a range-capable public ZIP file."""

    def __init__(self):
        self.position = 0
        self.cache = OrderedDict()
        self.downloaded = 0
        self.length = None
        with self._fetch(0, 0) as response:
            self.length = int(response.headers["Content-Range"].split("/")[-1])
            response.read()

    def _fetch(self, start, end):
        for attempt in range(4):
            request = urllib.request.Request(URL, headers={
                "User-Agent": "CodeDNA-research-data/1.0", "Range": f"bytes={start}-{end}"})
            try:
                response = urllib.request.urlopen(request, timeout=90)
            except urllib.error.HTTPError as exc:
                if exc.code not in (429, 500, 502, 503, 504) or attempt == 3:
                    raise
                time.sleep(min(30, 2 ** (attempt + 1)))
                continue
            actual = response.headers.get("Content-Range", "")
            expected = f"bytes {start}-{end}/"
            if response.status != 206 or not actual.startswith(expected):
                response.close()
                raise RuntimeError(f"Server did not honor byte range {start}-{end}")
            if self.length is not None and int(actual.split("/")[-1]) != self.length:
                response.close()
                raise RuntimeError("Remote archive length changed during download")
            return response
        raise RuntimeError("Range download retries exhausted")

    def seekable(self):
        return True

    def _range_bytes(self, start, end):
        for attempt in range(4):
            try:
                with self._fetch(start, end) as response:
                    data = response.read()
                if len(data) != end - start + 1:
                    raise OSError("Short HTTP range response")
                return data
            except (http.client.IncompleteRead, TimeoutError, OSError):
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Range read retries exhausted")

    def readable(self):
        return True

    def tell(self):
        return self.position

    def seek(self, offset, whence=0):
        position = offset if whence == 0 else self.position + offset if whence == 1 else self.length + offset
        if position < 0:
            raise ValueError("Negative archive position")
        self.position = position
        return position

    def read(self, n=-1):
        n = min(self.length - self.position, n if n >= 0 else self.length - self.position)
        if n <= 0:
            return b""
        start, end = self.position, self.position + n - 1
        block = 4 * 1024 * 1024
        key = start // block
        if n <= block and key == end // block:
            if key not in self.cache:
                first, last = key * block, min(self.length - 1, (key + 1) * block - 1)
                self.cache[key] = self._range_bytes(first, last)
                self.downloaded += len(self.cache[key])
                while len(self.cache) > 2:
                    self.cache.popitem(last=False)
            data = self.cache[key][start - key * block:end - key * block + 1]
        else:
            data = self._range_bytes(start, end)
            self.downloaded += len(data)
        if len(data) != n:
            raise RuntimeError("Short remote read")
        self.position += n
        return data


def selected_entry(name: str, projects: list[str]) -> bool:
    if name in ("rtp-torrent/readme.md", "rtp-torrent/tr_all_built_commits.csv"):
        return True
    for project in projects:
        if name == f"rtp-torrent/{project}/{project}.csv":
            return True
        prefix = f"rtp-torrent/repo/{project}/"
        if name.startswith(prefix) and not name[len(prefix):].startswith("hooks/"):
            return True
    return False


def safe_target(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if relative.is_absolute() or ".." in relative.parts or "\\" in name or ":" in name:
        raise ValueError(f"Unsafe ZIP path: {name!r}")
    target = root.joinpath(*relative.parts).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"ZIP path escapes output directory: {name!r}")
    return target


def fetch(out: Path, projects: list[str]) -> dict:
    if not projects or any("/" in p or "\\" in p or "@" not in p or ":" in p for p in projects):
        raise ValueError("Expected qualified RTPTorrent project names such as adamfisk@LittleProxy")
    out.mkdir(parents=True, exist_ok=True)
    manifest_path = out / "rtptorrent-subset-manifest.json"
    existing = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    if existing and set(existing.get("projects", [])) != set(projects):
        raise ValueError("Existing subset has different projects; use a different output directory")
    entries = dict(existing.get("entries", {}))
    remote = RemoteZip()
    with zipfile.ZipFile(remote) as archive:
        # Git recognizes a bare repository only if its empty refs directory
        # exists, even when every reference is stored in packed-refs.
        for entry in archive.infolist():
            if entry.is_dir() and selected_entry(entry.filename, projects):
                safe_target(out, entry.filename).mkdir(parents=True, exist_ok=True)
        chosen = [e for e in archive.infolist() if not e.is_dir() and selected_entry(e.filename, projects)]
        for project in projects:
            if not any(e.filename == f"rtp-torrent/{project}/{project}.csv" for e in chosen):
                raise ValueError(f"Project is not present in archive: {project}")
        # The shared 282 MiB map contains all 20 projects. The importer only
        # needs rows for the selected projects' job IDs; filter while streaming.
        shared = "rtp-torrent/tr_all_built_commits.csv"
        chosen.sort(key=lambda e: e.filename == shared)
        missing_bytes = sum((10 * 1024**2 if e.filename == shared else e.file_size)
                            for e in chosen if not safe_target(out, e.filename).exists())
        free = shutil.disk_usage(out).free
        reserve = 600 * 1024 * 1024
        if missing_bytes + reserve > free:
            raise RuntimeError(f"Need {missing_bytes:,} bytes plus a 600 MiB reserve; {free:,} bytes free")
        print(f"Selected {len(chosen)} files; {missing_bytes / 1024**2:.1f} MiB to extract", flush=True)
        for entry in chosen:
            if stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError(f"Refusing symlink entry: {entry.filename}")
            target = safe_target(out, entry.filename)
            recorded = entries.get(entry.filename)
            if target.exists():
                if not recorded or hashlib.sha256(target.read_bytes()).hexdigest() != recorded["sha256"]:
                    raise RuntimeError(f"Existing file is not verified by subset manifest: {target}")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".part")
            digest = hashlib.sha256()
            transformation = None
            source_digest = None
            if entry.filename == shared:
                jobs = set()
                for project in projects:
                    results = safe_target(out, f"rtp-torrent/{project}/{project}.csv")
                    with results.open(encoding="utf-8", newline="") as handle:
                        jobs.update(int(row["travisJobId"]) for row in csv.DictReader(handle))
                source_digest = hashlib.sha256()

                class HashingReader(io.RawIOBase):
                    def readable(self):
                        return True

                    def readinto(self, buffer):
                        chunk = source.read(len(buffer))
                        source_digest.update(chunk)
                        buffer[:len(chunk)] = chunk
                        return len(chunk)

                kept = 0
                with archive.open(entry) as source, temporary.open("w", encoding="utf-8", newline="") as handle:
                    text = io.TextIOWrapper(io.BufferedReader(HashingReader()), encoding="utf-8", newline="")
                    rows = csv.DictReader(text)
                    if rows.fieldnames != ["tr_job_id", "git_commit_id"]:
                        raise ValueError(f"Unexpected shared-map columns: {rows.fieldnames}")
                    writer = csv.DictWriter(handle, fieldnames=rows.fieldnames)
                    writer.writeheader()
                    for row in rows:
                        if int(row["tr_job_id"]) in jobs:
                            writer.writerow(row)
                            kept += 1
                digest.update(temporary.read_bytes())
                transformation = {"kind": "filter job IDs to selected projects", "jobs": len(jobs),
                                  "rows_kept": kept, "source_sha256": source_digest.hexdigest()}
            else:
                with archive.open(entry) as source, temporary.open("wb") as handle:
                    while chunk := source.read(1024 * 1024):
                        handle.write(chunk)
                        digest.update(chunk)
            # ZipExtFile verifies the entry's CRC at EOF before the final rename.
            temporary.replace(target)
            entries[entry.filename] = {"bytes": target.stat().st_size, "archive_entry_bytes": entry.file_size,
                                       "crc32": f"{entry.CRC:08x}", "sha256": digest.hexdigest(),
                                       "transformation": transformation}
            manifest = {"url": URL, "archive_bytes": remote.length,
                        "published_archive_md5": ARCHIVE_MD5, "whole_archive_md5_verified": False,
                        "verification": "ZIP entry CRC32 and extracted-file SHA-256; selective download",
                        "projects": projects, "entries": entries, "license": "CC BY 4.0",
                        "citation": "Mattis et al., MSR 2020, doi:10.1145/3379597.3387458"}
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            if entry.file_size > 1024 * 1024:
                print(f"Extracted {entry.filename} ({target.stat().st_size / 1024**2:.1f} MiB)", flush=True)
    print(f"Downloaded {remote.downloaded / 1024**2:.1f} MiB via byte ranges", flush=True)
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=Path("experiments/datasets/raw"))
    parser.add_argument("--projects", nargs="+", default=DEFAULT_PROJECTS)
    args = parser.parse_args(argv)
    fetch(args.out, args.projects)


if __name__ == "__main__":
    main()
