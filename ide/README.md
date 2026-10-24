# CodeDNA IDE

A desktop IDE built on [Eclipse Theia](https://theia-ide.org) 1.76.0
(Electron 42) with CodeDNA views. Theia provides the editor, file explorer,
terminal and preferences; the `codedna-extension` package adds:

- **Changes** (left panel, `Ctrl+Alt+D`): what changed in your code
  (New / Changed / Removed) and which other classes might be affected, each
  with a one-line reason ("Direct" or "Likely" link). Click a row to open
  the file at that line.
- **Tests to run** (right panel, `Ctrl+Alt+T`): the test classes your change
  can affect (or all tests), each with the reason in plain words, and which
  ones were not selected. The risk strategy shows calibrated estimates only
  after a separate target-history audit; otherwise it recommends the full suite.

Both views share one **Compare** choice: *My last commit* (default), *My
last 5 commits*, or *Choose commits…* for any two commits or branches.

```
Theia frontend (views, React)  ── JSON-RPC ──▶  Theia backend (Node)
                                                  │ starts `codedna serve`
                                                  │ (127.0.0.1, random token in env)
                                                  ▼
                                    CodeDNA local API (Python core)
```

The session token stays in the backend process; the views never see it. The
views analyse without executing code. Explicit confirmation in **Tests to run**
enables selected Maven execution; analysis never triggers a build.

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
by `python scripts/make_demo_repo.py ../codedna-demo`), then press
`Ctrl+Alt+D` (**Changes**) and `Ctrl+Alt+T` (**Tests to run**).
If panels look narrow from an earlier session, run **View → Reset Workbench
Layout** (command palette).

### Java editing

The app bundles Theia's VS Code extension host with two pinned Open VSX
extensions (`theiaPlugins` in `electron-app/package.json`): the Java grammar
(`vscode.java`) and Red Hat Language Support for Java (`redhat.java`, Windows
x64 build with its own Java runtime). `npm run build` downloads them into
`electron-app/plugins/` (git-ignored). They give completion, errors, go to
definition and Maven project import; CodeDNA's own analysis does not use them.

### Windows installer

```bash
cd ide
npm install
npm run build
npm run package --workspace electron-app   # → electron-app/dist/CodeDNA IDE Setup 0.1.0.exe
```

The installer contains the IDE only. The Python core is installed separately
(`pip install -e "..[api]"`, or set `CODEDNA_EXECUTABLE`). Long CodeDNA
actions show a progress notification with the elapsed time.

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
extension), the graph view, uncommitted-change analysis, packaging/installers.


## Risk and test execution

**Validated risk stopping** is the default recommendation strategy. The core
checks prior target evidence; missing/failed evidence displays **Risk unvalidated**
and recommends the full suite. Accepted history shows the estimated aggregate
skip risk and prior audit counts/upper bound, with no safety guarantee.

**Run recommended test classes** asks before executing project code. The backend
recomputes selection at the displayed immutable revisions, runs the selected
classes in an isolated export and returns actual statuses, warnings and logs.
Changing the comparison clears old recommendations. See
[the Java workflow](../docs/JAVA_WORKFLOW.md) for history preparation and limits.
