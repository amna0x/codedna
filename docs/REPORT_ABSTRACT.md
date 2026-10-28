# Abstract

CodeDNA investigates how developers can reduce regression testing while making
the limits of test selection explicit. It combines change-impact analysis,
language plugins, historical failure prediction and calibrated stopping with a
target-project audit and full-suite fallback. A desktop IDE, local API and MCP
interface expose the same core analysis. An agent-facing brake combines the
statistical recommendation with dependency-based required tests and project
policy. Java and Python analysis are implemented; validated risk selection is
currently limited to Java.

A nine-project rolling-origin confirmation found no meaningful safety difference
between the B10 stopping rule and recent-failure selection at matched recorded
test time, and lower failing-test recall. The audit gate permits reduced testing
only in a minority of blocks. Failure-conditional conformal stopping, available
as an opt-in method, reaches 95% commit safety on eight of nine follow-up
projects but decreases average safety relative to the conservative gated
product. Cloudify misses the target. Exploratory threshold tuning is promising
but does not establish a superior default. A public agent-patch study evaluates
structural selection, rather than claiming improvements to agents themselves.

The contribution is an implemented, inspectable decision pipeline and a
reproducible evaluation of its tradeoffs. Results do not establish universal
model transfer, future safety guarantees or CI wall-clock speedup. Limitations
include temporal dependence, incomplete CI records, unobserved skipped outcomes,
restricted build support and statistical assumptions under distribution shift.
