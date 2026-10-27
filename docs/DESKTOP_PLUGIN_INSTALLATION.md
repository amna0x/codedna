# Packaged desktop plugin installation (D-074)

The Windows desktop installs approved optional language wheels without a
separate Python interpreter, pip, administrator access or modifying its bundled
application files. The source/developer installation continues to use its own
Python environment. Both routes retain the official catalogue, pinned version,
explicit confirmation, API compatibility and SHA-256 checks.

## Storage and activation

The default store is `%LOCALAPPDATA%/CodeDNA/plugins`. `active.json` selects
immutable version directories. Installation validates wheel identity, RECORD
hashes, interpreter/platform tags, Python requirements and existing dependency
versions. The bundled PyPA installer writes into a staging directory. A fresh
core subprocess checks the actual language factory and API before activation.
An atomic manifest replacement makes the change effective after restart.
Failed checks or activation preserve the previous manifest. Concurrent changes
are refused with a retry message. No package index is contacted for dependencies.

An explicit absolute `CODEDNA_PLUGIN_HOME` can select a portable/test store.
Normal analysed project folders do not select or configure the plugin store.
The core snapshots active paths once at startup; installation and removal both
request a restart rather than replacing live imported code.

Removing an optional override restores a bundled language on restart if one
exists. Bundled Java/Python cannot be uninstalled through the optional manager.
Inactive versions remain a rollback cache, avoiding deletion of loaded native
files on Windows. This cache is not an active plugin. A damaged optional copy
is reported while a working bundled copy is used when available.

## Release constraints

- Only catalogue-approved wheels are accepted. The catalogue is still not
  publicly hosted; this fix does not resolve that separate HTTP 404.
- Wheel code must live under its distribution's normalized module namespace.
  It cannot replace the core, standard library or installer runtime.
- Python startup hooks, symbolic links, unsafe paths, duplicate names and
  Python CLI/GUI script launchers are rejected. Language entry points are the
  supported extension contract, rather than unrelated command-line programs.
- Wheels must match the packaged Python/platform and have their dependencies
  already available. Missing/incompatible dependencies cause a clear refusal;
  the working version remains active. Publishers must provide compatible
  releases, not rely on automatic downloads of arbitrary dependency packages.
- A successful isolated load is not a guarantee against every future plugin
  bug. Installed plugin code runs with the user's permissions after consent.

## Verification

Tests use synthetic, checksum-pinned wheels and temporary stores, without
network access. They cover install/update, dependency refusal, broken factories,
unsafe wheels, concurrent mutation, atomic-write failure, cold restart,
removal/restoration and damaged-copy fallback. Existing source-pip behavior and
language registry tests remain covered. IDE build and 19 Node tests pass.

The actual frozen core is additionally exercised with PATH restricted to
Windows system tools and a synthetic bootstrap language plugin in an isolated
store. That fixture calls the real manager inside the frozen process. It is
not a production bypass for arbitrary wheel paths or URLs. Production CLI/API
installation still fetches the official catalogue. Frozen and final-installer
results are recorded separately after those checks complete; a local smoke
does not constitute a clean-PC installation.

The bundled wheel library is [PyPA installer](https://installer.pypa.io/en/stable/),
pinned to 0.7.0 in the desktop/build test extras. Packaging supplies wheel-tag,
version, requirement and marker validation. No risk-model behavior changed.


### Actual frozen candidate result

All seven executable-level checks passed with Python/pip absent from PATH:
installation and cold restart, damaged-override fallback, broken update,
missing dependency, checksum refusal, removal/restoration and bundled removal
protection. All 1,451 core hashes match. The full Maven-inclusive suite and
final NSIS installer verification are still running; this is not their result.
Evidence: FROZEN_PLUGIN_VALIDATION_D074_2026-10-27.json.


D-074 final full-suite and installer validation is complete. The authoritative
dated counts, checksum, signature status and friend kit are recorded in
RELEASE_VALIDATION_D074_2026-10-27.json. Clean-PC acceptance and public catalogue
delivery remain separate; previous in-progress notes above are historical.
