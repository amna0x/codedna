# CodeDNA IDE

A desktop IDE built on [Eclipse Theia](https://theia-ide.org) 1.76.0
(Electron 42) with CodeDNA views. Theia provides the editor, file explorer,
terminal and preferences; the `codedna-extension` package adds:

- **Changed code** (left panel, `Ctrl+Alt+D`): changed classes and methods
  between two commits, and the classes that may be affected, each with the
  dependency path explaining why (heuristic links are labelled as such).
  Click a row to open the file at that line.
- **Recommended tests** (right panel, `Ctrl+Alt+T`): test classes to run for
  a change (static dependency selection or all), with the reasons per test.
  Failure-risk scores are not shown until a model has been trained on the
  repository's history — the view says so instead of inventing numbers.

```
Theia frontend (views, React)  ── JSON-RPC ──▶  Theia backend (Node)
                                                  │ starts `codedna serve`
                                                  │ (127.0.0.1, random token in env)
                                                  ▼
                                    CodeDNA local API (Python core)
```

The session token stays in the backend process; the views never see it. The
views only analyse — they never run project code.

## Prerequisites

| Tool | Version | Why |
|------|---------|-----|
| Node.js | 22 (tested 22.21); Theia recommends 24 | build and run |
| npm | 10+ | install |
| Python | 3.11+ with CodeDNA installed: `pip install -e "..[api]"` | the analysis core (`codedna` on PATH, or set `CODEDNA_EXECUTABLE`) |
| Windows | Visual Studio Build Tools with "Desktop development with C++" | native modules (node-pty, keytar, drivelist, ffmpeg) |

## Build and run

```bash
cd ide
npm install
npm run build
npm start
```

Open a folder that is a Git repository with Java code (e.g. a repository made
by `python scripts/make_demo_repo.py ../codedna-demo`), then open
**View → Changed code** / **Recommended tests**.

### Troubleshooting

- `UNABLE_TO_GET_ISSUER_CERT` while rebuilding native modules on Windows:
  if `NODE_USE_SYSTEM_CA=1` is set and the Windows store lacks
  ISRG Root X2, Node cannot verify `artifacts.electronjs.org`. Run the build
  with that variable unset for the build only (PowerShell:
  `$env:NODE_USE_SYSTEM_CA=$null; npm run build`).
- `could not start "codedna"`: install the core into the Python on your PATH
  or set `CODEDNA_EXECUTABLE` to the full path of `codedna(.exe)`.

## Not yet

Java language support in the editor (Theia's VS Code extension host + a Java
extension), the graph view, run-selected-tests from the IDE, risk scores in
the Tests view, uncommitted-change analysis, packaging/installers.
