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

## Limits

- The verdict covers the listed test classes only. `passed` means those
  tests passed, not that the change is correct.
- Java only for now (through the language plugin). Maven and Gradle
  layouts are read; other builds may show no tests.
- The offline study on public agent patches is described in
  [AGENT_BRAKE_STUDY_PROTOCOL.md](AGENT_BRAKE_STUDY_PROTOCOL.md). Whether
  agents finish with fewer broken changes when they use the brake has not
  been measured.
