# AGENTS.md — rules for AI coding agents and contributors

CodeDNA is a university Final Year Project (Path A: software engineering only).
It analyses Java code changes, estimates their impact, and selects regression
tests while estimating the risk of skipping the rest.

Full brief: [CODEDNA_STARTER.md](CODEDNA_STARTER.md). Current plan:
[docs/ROADMAP.md](docs/ROADMAP.md).

## Before you start

- Read `docs/PROJECT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md` and
  `docs/DECISIONS.md` before implementing anything.
- Work on **one milestone at a time**. Check the roadmap for the active one.
- Before a large change, summarise the intended implementation first.

## While working

- Explain assumptions and limitations in plain English.
- Write tests for every new feature. Tests must create temporary Git
  repositories and must not need internet access.
- Never claim a heuristic relationship is a guaranteed dependency. Graph edges
  must be labelled confirmed / heuristic / unresolved.
- Record unknown or unresolved analysis results instead of guessing.
- Do not silently add major dependencies. Add them to `pyproject.toml` only
  when a milestone needs them, and record why in `docs/DECISIONS.md`.
- Avoid cybersecurity scope (vulnerability detection, pentesting, security
  scoring).
- Do not implement advanced ML or frontend work before their milestones.
- Keep the project runnable on ordinary student laptops (no Kubernetes,
  microservices, or GPU requirements).
- Do not change unrelated modules.
- Call Git with argument lists through `codedna.git_analysis.git.run_git`;
  never use `shell=True`, and never run scripts from analysed repositories.

## Before claiming completion

- Run the test suite: `python -m pytest`.
- Report the actual commands and results. **Never fabricate test results,
  accuracy, runtime, or research numbers.**
- Update documentation after architectural changes (`docs/ARCHITECTURE.md`,
  `docs/DECISIONS.md`, README commands).

## Safety and hygiene

- Do not expose credentials. Never commit `.env` files, tokens, private
  datasets, or downloaded dependency caches.
- Ask before destructive repository operations (force push, history rewrite,
  deleting branches or data).
- Keep research experiments reproducible: fixed seeds, chronological splits,
  recorded dataset versions, no leakage from future commits.

## Layout

| Path | Purpose |
|------|---------|
| `backend/codedna/` | Python package (CLI + analysis modules) |
| `backend/tests/` | pytest suite |
| `examples/sample-java-project/` | Tiny Maven + JUnit 5 project for demos/tests |
| `scripts/` | Developer helper scripts |
| `docs/` | Specification, architecture, research and decision records |

New top-level directories (`adapters/`, `experiments/`, `frontend/`) and new
packages under `backend/codedna/` are created only when their first real
implementation lands.
