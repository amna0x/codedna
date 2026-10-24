"""An existing feature CSV must not prevent rebuilding a missing history DB."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

from codedna.git_analysis import git
from codedna.models.experiment import _reproducibility
from codedna.test_history import features, rtptorrent
from codedna.test_history.features import Dataset, Row
from codedna.test_history.store import HistoryStore


def test_preparation_recovers_database_when_feature_csv_is_cached(repo, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "prepare_features", Path(__file__).resolve().parents[2] / "scripts/prepare_transfer_features.py")
    prepare = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(prepare)
    folder = repo.path / "experiments/results/study11-2026-10-21/hikaricp"
    folder.mkdir(parents=True)
    path = folder / "dataset.csv"
    Dataset([Row("a", 0, "TestA", 0, 1., {"mean_duration": 1.})],
            ["mean_duration"], ["a"]).to_csv(path)
    original = path.read_bytes()
    expected = _reproducibility(Dataset.from_csv(path), 0)
    (folder / "experiment-seed0.json").write_text(json.dumps({"reproducibility": expected}))
    monkeypatch.setattr(git, "resolve_repository", lambda path: Path(path).resolve())
    monkeypatch.setattr(git, "run_git", lambda *args: "true")
    monkeypatch.setattr(prepare.shutil, "disk_usage", lambda path: SimpleNamespace(free=2 * 1024**3))
    calls = []

    def import_recorded(dataset_dir, project, store):
        calls.append(project)
        store.set_meta("rtptorrent_project", project)
        return SimpleNamespace(to_dict=lambda: {"project": project})

    def must_not_rebuild(*args, **kwargs):
        raise AssertionError("Verified feature CSV should be reused")

    monkeypatch.setattr(rtptorrent, "import_rtptorrent", import_recorded)
    monkeypatch.setattr(features, "build_dataset", must_not_rebuild)
    result = prepare.prepare("hikaricp", str(repo.path))
    assert result["matches_original_study"] is True
    assert (repo.path / result["database"]).exists()
    with HistoryStore(repo.path / result["database"]) as store:
        assert store.get_meta("rtptorrent_project") == prepare.PROJECTS["hikaricp"]
    assert path.read_bytes() == original
    prepare.prepare("hikaricp", str(repo.path))
    assert calls == [prepare.PROJECTS["hikaricp"]]
