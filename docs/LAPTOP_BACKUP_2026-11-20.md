# Laptop backup — 2026-11-20

Before the owner deleted the laptop checkout, everything CodeDNA needs that
existed only on the laptop was either uploaded or confirmed rebuildable.
All code, docs, committed results and `graphify-out/` were already on GitHub.

## What was uploaded

One GitHub Release asset: **`codedna-laptop-data-2026-11-20.zip`** on the
release tagged `laptop-data-2026-11-20`.

- Size: 364,851,641 bytes
- SHA-256: `566571d8200151d48f8b5f835c5def9e3092579fef96bea1fbc3a79031189cfe`
- 634 files, 439,578,583 bytes unpacked. Per-file sizes and SHA-256 hashes are
  in [`LAPTOP_BACKUP_2026-11-20_MANIFEST.json`](LAPTOP_BACKUP_2026-11-20_MANIFEST.json)
  (also inside the zip as `MANIFEST.json`).

Paths inside the zip are repository-relative, so unzip at the repository root.

| Contents | Why kept |
|----------|----------|
| `experiments/datasets/raw/` (RTPTorrent v1.1 four-project subset) | Slow Zenodo download |
| `experiments/datasets/derived/*.db`, `*.json` | History DBs for study11 |
| `experiments/results/study11-2026-10-21/*/dataset.csv` | Up to 2 h per project to rebuild |
| `experiments/datasets/confirmatory*/` top-level JSON, logs, patch | Provenance of the confirmatory run (status, frozen code, equivalence proof) |
| `experiments/results/moonshot-engineering-pilot-d085-2026-10-28/**/*.class` | Exact pilot witnesses |
| `build/*.json`, `*.log`, `*.py` and `build/desktop-*/` top-level files | Validation/acceptance evidence logs |
| `build/supervisor-review/`, `build/plugin-release/`, `build/website-handoff/` | Review packs, plugin wheels, website handoff zip |
| `build/desktop-D085-2026-10-28/CodeDNA-D085-Friend-Kit.zip` | Delivered friend kit |
| `build/moonshot-fixtures-*/` | Pilot fixtures |
| `graphify-snapshot-97c3be7/` | Old graphify output from the local-only commit `97c3be7`, exported as files only |

## What was not uploaded, and why

| Item | Size (approx.) | How to get it back |
|------|---------------|--------------------|
| `experiments/datasets/confirmatory/raw/` | 5.5 GB | Public RTPTorrent data and public Git repositories; `scripts/prepare_confirmatory.py` re-downloads and checks every SHA-256 recorded in `preparation.json` |
| `experiments/datasets/confirmatory-windowsfix-2026-10-26/{db,datasets}/` | 3.6 GB | Rebuilt from the raw data by `scripts/continue_confirmatory.py`. Its results and verdict are committed in `experiments/results/rolling-evidence-confirmatory-windowsfix-2026-10-26/` |
| `experiments/datasets/confirmatory-live-2026-10-25/{db,datasets,raw}/` | 3.1 GB | Superseded failed run (see `MEMORY.md`) |
| `experiments/datasets/confirmatory/dl4j-pack-part-backup.bin`, `confirmatory/db/` | 1.4 GB | Partial download leftover / first producer output |
| `build/desktop-*/` installer builds, `build/desktop-core/` | 3.6 GB | Rebuilt by the desktop packaging scripts |
| `.venv/`, `node_modules/`, `ide/` build output, `*.egg-info`, `__pycache__`, `.pytest_cache` | ~1–2 GB | Reinstalled by the setup steps below |

Deliberately left behind (not uploaded on purpose):

- `git stash` entries, including "GPT laptop edits" (buggy project-history
  rewrite / D-052 reuse). Never commit or restore them.
- Local branch `keep/private-email-backup-20261028-399d9c3`: its content is
  identical to pushed commit `840d297`; only its commit identities differ and
  contain private email addresses. Never push it.
- Local branches `keep/graphify-97c3be7` and `keep/local-main-before-pr21-20261026`:
  pre-PR-21 history with a private email address. Their only unique content
  (the graphify snapshot) is in the zip.

## Restore

```powershell
git clone https://github.com/amna0x/codedna.git
cd codedna
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pip install -e plugins/codedna-java -e plugins/codedna-python
```

Download the data zip from the release and unpack it at the repository root:

```powershell
gh release download laptop-data-2026-11-20 -R amna0x/codedna
(Get-FileHash codedna-laptop-data-2026-11-20.zip -Algorithm SHA256).Hash
Expand-Archive codedna-laptop-data-2026-11-20.zip -DestinationPath .
```

The hash must equal the SHA-256 above. Then:

- Tests: `python -m pytest --run-maven` (needs JDK and Maven).
- IDE: double-click `start.bat` (installs and builds the IDE on first run).
- Website: the React website lives on the pushed, unmerged branch
  `codex/website-react-gsap`; there, `cd website; npm install; npm run build`
  (`website/.render.mjs` is local build output).
- Graph: `graphify update .` refreshes `graphify-out/`.
- Confirmatory data (only to reproduce from scratch): see
  `docs/CONFIRMATORY_PREPARATION_2026-10-25.md`.
