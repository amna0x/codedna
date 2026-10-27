# Clean Windows acceptance - not yet performed

Use a new Windows VM or a separate PC without a preinstalled CodeDNA/Python
setup. This laptop has no Windows Sandbox executable. Do not call a PATH-only
smoke a clean-PC test.

1. Record Windows version, whether Git/Python/JDK/build tools are present, and
   that this is a separate clean environment. A Python Store alias does not
   establish a usable Python installation.
2. Copy the final installer and release validation JSON. Compare SHA-256 before
   opening the installer; use the hash matching that exact build.
3. Install as the current user. Record chosen directory and any installer error.
4. Run scripts/verify_desktop_install.ps1 with -AppDirectory pointing to the
   installed app. It verifies the bundled payload and plugins, runs no project
   build, installs nothing and writes a local JSON report. No report is sent.
5. Launch the IDE. Verify Extensions is visible and Language plugins lists Java
   and Python even when the online catalogue is unavailable.
6. Install Git if absent, then open a throwaway project and verify Changes,
   Impact and full-suite fallback without installing system Python for analysis.
7. For Java execution, separately provide a JDK/Maven or Gradle. For Python
   execution, provide the project's interpreter with pytest/dependencies. Give
   explicit build consent and check an actual pass and failure.
8. Confirm errors are actionable when a prerequisite is missing. A missing
   interpreter or skipped required test must never produce a passed brake.
9. Restart, verify the plugin tab persists, then test uninstallation. Record
   observations/screenshots and preserve logs locally.

Return the smoke JSON plus manual observations to the project. Until then the
clean-PC requirement remains open. The local packaged-core smoke has already
passed, but it answers a different question.
