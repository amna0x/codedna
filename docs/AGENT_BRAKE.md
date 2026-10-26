# Test brake for AI coding agents — setup guide

`codedna mcp` lets a coding agent ask CodeDNA, before it says a change is
done, which tests the change must run, and run them for one verdict (D-059).
It is a Model Context Protocol server on stdin/stdout, so any MCP-capable
agent can use it. Install CodeDNA first (`pip install -e .` in this
repository) so the `codedna` command is on the agent's PATH.

## Tools

| Tool | Runs project code? | Answer |
|------|--------------------|--------|
| `codedna_plan_tests` | no | test classes that must run, a reason for each, the skip risk |
| `codedna_impact` | no | code the change can affect: confirmed and heuristic links apart, files not analysed |
| `codedna_check` | **yes** (the build) | `passed`, `blocked`, `incomplete`, `nothing_to_run` or `no_tests`, plus the results |

All tools default to `base=HEAD` and `head=WORKTREE`, which means the
agent's uncommitted edits. Without validated project history (D-041) the plan is
the whole suite. Partial plans appear only once the project's own recorded
runs pass the audit (D-053).

`codedna_plan_tests` and `codedna_check` take an optional `method`:
`"b10"` (default: calibrated stop behind the audit gate, D-041) or `"crc"`
(failure-conditional conformal stop, D-068). With `crc` the plan's `risk`
has a `conformal` block: the stopping value, the number of failing audit
commits (at least 19 are needed, otherwise the whole suite runs) and the
corrected bound. The bound assumes past failing commits are exchangeable
with future ones; it is not a guarantee.

## Structural feedback and language support

Every plan includes structural_plan, the dependency plan labelled
`structural only, no probability`. It is the structural selection measured
by the SWE-bench brake study. It can be used for early feedback, but the
agent must still run all must_run tests before finishing. Structural tests
and policy pins can only broaden the required risk selection. Both plans
refer to the same immutable revisions, including a WORKTREE snapshot.
If structural tests broaden a partial validated selection, risk carries
`estimate_is_conservative: true`: the retained value bounds the original
model estimate, not real-world safety. If no tests remain skipped, skip
risk is zero.

The brake detects Java/Python test suites. Python has no validated risk
selector yet, so Python and mixed-language repositories get an explicit
unvalidated full-suite plan, not a risk-selection error or guessed score.
check uses the installed language plugins to run the required tests and
combine their results. Build consent is still required. For MCP Python checks,
select the project's interpreter at server startup, for example
`codedna mcp --repo PROJECT --allow-build --python PROJECT/.venv/Scripts/python.exe`.
The interpreter must already have pytest and the project's dependencies;
CodeDNA does not install them or let tool arguments override this choice. Install the Java
and Python packages alongside the core when working from source:

```powershell
.venv/Scripts/python -m pip install -e ".[ml,api,dev]" -e plugins/codedna-java -e plugins/codedna-python
```

## Connect an agent

Read-only (plan and impact only):

- **Claude Code**: `claude mcp add codedna -- codedna mcp --repo /path/to/project`
- **Cursor**: in `.cursor/mcp.json` of the project:

  ```json
  {"mcpServers": {"codedna": {"command": "codedna", "args": ["mcp", "--repo", "."]}}}
  ```

- **Codex CLI**: in `~/.codex/config.toml`:

  ```toml
  [mcp_servers.codedna]
  command = "codedna"
  args = ["mcp", "--repo", "/path/to/project"]
  ```

To also offer `codedna_check`, add `--allow-build` (and `--mvn PATH` or
`--gradle PATH` if the build tool is not on PATH). Do this only for projects you trust: the agent can
then start the project's build, which runs its code and build plugins. The
server then serves that one repository only, whatever path the agent sends.

## Tell the agent to use it

Add to the project's `AGENTS.md` or `CLAUDE.md`:

```markdown
Before you report a code change as done, call `codedna_plan_tests`. If
`codedna_check` is available, call it and report the change as done only
when the verdict is `passed` (or `nothing_to_run`); on `blocked` fix the
failing tests, on `incomplete` fix the build first.
```

## Demo

```bash
python scripts/demo_agent_brake.py /tmp/brake-demo           # plan + impact, no build
python scripts/demo_agent_brake.py /tmp/brake-demo2 --check   # also runs Maven: verdict "blocked"
```

The demo copies `examples/sample-java-project`, makes a wrong discount edit
the way an agent might, and talks to `codedna mcp` over stdio. With
`--check` the verdict is `blocked`, because `PriceCalculatorTest` fails.
That demo has no project history, so the plan is the whole suite.

```bash
python scripts/demo_brake_end_to_end.py /tmp/brake-e2e            # plans only
python scripts/demo_brake_end_to_end.py /tmp/brake-e2e2 --check    # also runs Maven
```

This one adds 240 earlier commits and a **synthetic** recorded history, so
the plan with `method: "crc"` is validated and partial (1 of 2 classes).
With `--check` the wrong formula is `blocked` and a harmless comment is
`passed`. The invented history proves the mechanism, not any time saving.

## Limits

- The verdict covers the listed test classes only. `passed` means those
  tests passed, not that the change is correct.
- Java only for now (through the language plugin). Maven and Gradle
  layouts are read; other builds may show no tests.
- The offline study on public agent patches is described in
  [AGENT_BRAKE_STUDY_PROTOCOL.md](AGENT_BRAKE_STUDY_PROTOCOL.md), with
  results in [REPORT_AGENT_BRAKE.md](REPORT_AGENT_BRAKE.md): on public
  SWE-bench Java patches the plan held a failing test whenever the full suite
  did. Whether agents finish with fewer broken changes when they use the
  brake has not been measured.

The validated-history demo now adds IndependentTest for a separate shipping-fee
component, unrelated to discount calculation. The
breaking edit keeps both affected dependency tests and still skips the
independent test. Its recorded history is explicitly synthetic; this is
an end-to-end mechanism demonstration, not additional research evidence.
