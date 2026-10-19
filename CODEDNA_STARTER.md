# CodeDNA — Software Engineering FYP Starter

## MASTER INSTRUCTIONS FOR CODEX

You are the lead software engineer and technical mentor for CodeDNA,
a research-oriented university Final Year Project (FYP).

Read this entire document before making changes.

Your task is to turn this empty repository into a clean, testable,
reproducible development environment for CodeDNA Path A.

Do not attempt to implement the entire FYP at once.

---

# 1. PROJECT IDENTITY

Name:
CodeDNA

Working title:
CodeDNA: Risk-Calibrated Change-Impact Analysis and Intelligent
Regression Test Selection for Continuous Integration

Project type:
Software Engineering Final Year Project

Team:
2–3 BSCS students

Expected duration:
6–9 months

Target language for analysis:
Java

Implementation language:
Python

Primary purpose:
Analyze software changes, understand their possible impact on a
codebase, and recommend regression tests while estimating the risk
of skipping other tests.

This is PATH A — SOFTWARE ENGINEERING ONLY.

Do not implement vulnerability detection, penetration testing,
security scoring, or cybersecurity modules.

---

# 2. WHAT CODEDNA SHOULD EVENTUALLY DO

A developer supplies:

- A Git repository
- A base commit
- A target commit or pull request
- An optional test execution budget

CodeDNA should:

1. Detect changed files, classes, and methods.
2. Construct a code dependency graph.
3. Identify potentially affected components.
4. Connect code components to regression tests.
5. Analyze historical test outcomes and durations.
6. Estimate the probability that individual tests will fail.
7. Rank and select tests under a configurable budget.
8. Calibrate estimated probabilities.
9. Expand the test selection or run all tests when confidence
   is insufficient.
10. Explain every selection decision.
11. Visualize the repository through an interactive code graph.
12. Evaluate performance against established baselines.

Important:
The graph is a useful application feature.
The scientific contribution must come from measurable improvements
in test-selection decisions, risk estimation, or both.

Do not claim novelty without evidence.

---

# 3. DEVELOPMENT PHILOSOPHY

Follow these principles:

- Build a working vertical slice before adding complexity.
- Implement one milestone at a time.
- Prefer correctness over visual polish.
- Write automated tests for important behavior.
- Never invent dependency relationships or test outcomes.
- Record unknown or unresolved analysis results.
- Keep experimental data separate from training code.
- Do not fabricate accuracy, runtime, or research results.
- Do not use an LLM as the core regression-test predictor.
- Do not add microservices, Kubernetes, authentication,
  or unnecessary infrastructure.
- Avoid premature abstractions.
- Keep the system understandable to undergraduate students.
- Explain design decisions in plain English.
- Preserve a modular architecture for later extensions.

Before large changes, summarize the intended implementation.
After changes, run tests and report actual results.

---

# 4. INITIAL TECHNOLOGY STACK

Backend:
- Python 3.11+
- FastAPI
- Pydantic
- pytest

Git analysis:
- Git CLI through safe subprocess calls
- PyDriller only if it provides a clear advantage

Graph analysis:
- NetworkX

Java parsing:
- Tree-sitter Java for initial syntax extraction
- Evaluate JavaParser or Eclipse JDT later for stronger
  symbol and call resolution

Java testing:
- Java 17
- Maven
- JUnit 5
- JaCoCo for coverage mapping

Storage:
- SQLite for the prototype
- PostgreSQL only if later justified

Machine learning (later):
- scikit-learn
- XGBoost or LightGBM
- Probability calibration methods

Frontend (later):
- React
- TypeScript
- Vite
- Cytoscape.js for the code graph

Development:
- Git
- GitHub
- VS Code
- Codex desktop app
- GitHub Actions
- Docker only when needed

Avoid adding dependencies until their purpose is clear.

---

# 5. TARGET REPOSITORY STRUCTURE

Create the following structure progressively:

codedna/
|
|-- AGENTS.md
|-- README.md
|-- CODEDNA_STARTER.md
|-- .gitignore
|-- .env.example
|-- pyproject.toml
|
|-- backend/
|   |-- codedna/
|   |   |-- __init__.py
|   |   |-- cli.py
|   |   |-- api/
|   |   |-- git_analysis/
|   |   |-- java_analysis/
|   |   |-- dependency_graph/
|   |   |-- impact_analysis/
|   |   |-- test_mapping/
|   |   |-- test_history/
|   |   |-- models/
|   |   |-- calibration/
|   |   |-- selection/
|   |   |-- reporting/
|   |
|   |-- tests/
|
|-- adapters/
|   |-- java_maven/
|
|-- frontend/
|   |-- (created in a later milestone)
|
|-- examples/
|   |-- sample-java-project/
|
|-- experiments/
|   |-- baselines/
|   |-- datasets/
|   |-- evaluation/
|   |-- results/
|
|-- docs/
|   |-- PROJECT_SPEC.md
|   |-- ARCHITECTURE.md
|   |-- ROADMAP.md
|   |-- RESEARCH_PLAN.md
|   |-- DATASET_PLAN.md
|   |-- DECISIONS.md
|
|-- scripts/
|
|-- .github/
    |-- workflows/

Do not create empty placeholder modules without a purpose.
Create directories when their first implementation is needed.

---

# 6. SYSTEM ARCHITECTURE

Git repository / pull request
          |
          v
Git change extractor
          |
          v
Java code parser
          |
          v
Dependency graph builder
          |
          v
Change-impact analyzer
          |
          v
Candidate test generator
          |
          v
Historical test data + feature generator
          |
          v
Failure-probability model
          |
          v
Probability calibration
          |
          v
Risk-aware test selector
          |
          v
Confidence acceptable?
       /        \
      YES        NO
       |          |
       v          v
Selected tests   Broaden selection / retest all
       \          /
        v        v
       CI execution + evaluation
                |
                v
       Explanations and graph UI

The visual graph should reuse the same underlying analysis data.

Do not build a separate graph system with unrelated data.

---

# 7. GRAPH VISUALIZATION REQUIREMENTS

The eventual interface should be inspired by interactive codebase
graph exploration tools, including Graphifyy-style visualization.

Do not copy another product's branding or proprietary assets.

Minimum graph features:

- Display repository files and modules as nodes
- Display known dependency relationships as edges
- Zoom and pan
- Search for files and classes
- Select a node to inspect details
- Highlight changed files
- Highlight potentially impacted files
- Show why one component is connected to another
- Highlight related tests when mapping is available
- Filter nodes and edge types

Progressive detail:

Level 1:
Packages and folders

Level 2:
Files and classes

Level 3:
Methods and selected call relationships

Use expandable or clustered views so large repositories remain usable.

Distinguish:

- Confirmed static relationships
- Heuristic relationships
- Unresolved relationships

Never present a heuristic graph edge as a proven runtime call.

Advanced features, only if time permits:

- Before/after commit graph comparison
- Historical co-change edges
- Test coverage overlay
- Test-risk heatmap
- Timeline exploration
- Graph-based explanation paths
- Incremental graph updates

Graph UI development begins only after the underlying analysis
produces trustworthy JSON.

---

# 8. RESEARCH FOUNDATION

CodeDNA must not claim that the following are new:

- Detecting changed Git files
- Building code dependency graphs
- Selecting affected tests
- ML-based test prioritization
- Using historical failures to rank tests

These are established research and industry techniques.

Our candidate research direction:

Can a hybrid structural and historical regression-test selector
reduce execution cost while providing better calibrated estimates
of the risk of skipping tests?

Can an uncertainty-aware fallback policy reduce missed failures
compared with ordinary ML selection?

Potential research questions:

RQ1:
How accurately do structural, change, and historical features
predict regression-test failures?

RQ2:
How much test execution time can be saved at specified
empirical failure-detection targets?

RQ3:
Does probability calibration improve the reliability of
test-risk estimates?

RQ4:
Does uncertainty-aware fallback improve the safety/cost trade-off?

RQ5 (optional):
Do graph-derived features improve prediction or explainability
enough to justify their computation cost?

These are hypotheses to test, not guaranteed outcomes.

---

# 9. EXISTING RESEARCH AND OPEN-SOURCE REFERENCES

Study these projects as prior art, baselines, or benchmarks.

Do not blindly merge their source code into CodeDNA.

1. Predictive RTS
https://github.com/EngineeringSoftware/predictiverts

Purpose:
Study ML-based regression test selection and feature engineering.

2. Ekstazi
https://github.com/gliga/ekstazi

Purpose:
Study dependency-based regression test selection.

3. Fine-Ekstazi
https://github.com/EngineeringSoftware/fine-ekstazi

Purpose:
Study fine-grained change/dependency tracking.

4. RTSTester
https://github.com/JohnsonSYK/RTSTester

Purpose:
Study evaluation and comparison of RTS techniques.

5. Defects4J
https://github.com/rjust/defects4j

Purpose:
Use real Java faults and triggering tests for controlled evaluation.

Also investigate:

- LRTS
- RTPTorrent
- JaCoCo
- Maven Surefire
- JavaParser
- Tree-sitter Java
- Cytoscape.js

Before using code from another repository:

- Verify the current repository URL
- Check its license
- Check supported language/tool versions
- Check whether it is maintained
- Cite the original authors
- Record what was reused and what was implemented independently

Do not assume that public GitHub code is automatically reusable.

---

# 10. EXPERIMENTAL BASELINES

Eventually implement or fairly compare:

B0: Retest all tests
B1: Random ordering
B2: Shortest test first
B3: Recent failures + short duration
B4: Dependency-only selection
B5: Historical-failure-only ranking
B6: Change-only ML
B7: Hybrid ML without calibration
B8: Hybrid ML with calibration
B9: Hybrid ML with calibrated fallback

Do not implement all baselines during the first milestone.

---

# 11. EXPERIMENTAL EVALUATION

Important metrics:

Failure detection:
- Failing-test recall
- Missed failing tests
- Commit-level safety rate

Efficiency:
- Test selection ratio
- Test execution time reduction
- End-to-end CI time reduction
- Analysis and inference overhead

Prioritization:
- APFD
- APFDc
- Time to first failure

Prediction:
- Precision
- Recall
- PR-AUC

Risk calibration:
- Brier score
- Expected Calibration Error
- Reliability diagrams
- Risk-coverage curves

Graph correctness:
- Precision of extracted relationships on manually checked samples
- Unresolved-edge rate
- Graph build time

Use chronological splits, not random commit shuffling.

Suggested starting protocol:
- Oldest 60% commits: training
- Next 20%: validation/calibration
- Latest 20%: final testing

Avoid information leakage from future commits.

Use full-suite test outcomes as ground truth when available.

Never invent performance numbers.

---

# 12. MILESTONE PLAN

MILESTONE 0 — Repository bootstrap

Deliverables:
- Python project initialized
- AGENTS.md
- README.md
- Architecture documentation
- Research plan
- Automated test framework
- GitHub Actions test workflow
- Example Java Maven project
- Clear local setup instructions

MILESTONE 1 — Git and Java change analysis

Input:
Repository path, base commit, target commit

Output:
Structured JSON identifying changed Java files,
classes, methods, and line ranges.

Requirements:
- Added files
- Deleted files
- Modified files
- Renamed files
- Changes outside methods
- Clear unresolved cases
- Automated tests

MILESTONE 2 — Dependency graph

Build package/file/class-level relationships first.

Add method-level relationships only where resolution is reliable.

Requirements:
- Stable node IDs
- Typed edges
- Impact traversal
- Explainable dependency paths
- JSON graph export
- Unit tests

MILESTONE 3 — Test mapping

Requirements:
- Discover JUnit tests
- Integrate Maven test execution
- Import JaCoCo coverage when available
- Map tests to code
- Implement dependency-only baseline
- Compare with retest-all

MILESTONE 4 — History and predictive ranking

Requirements:
- Git history mining
- Historical test results
- Test duration estimates
- Feature engineering
- Simple historical baselines
- Logistic regression baseline
- Gradient-boosted model

MILESTONE 5 — Research contribution

Requirements:
- Probability calibration
- Configurable risk policies
- Fallback to broader/full suite
- Risk/cost experiments
- Ablation studies
- Reproducible results

MILESTONE 6 — Interactive visualization and FYP demo

Requirements:
- React dashboard
- Cytoscape.js repository graph
- Changed/affected code highlighting
- Ranked tests and explanations
- GitHub PR demonstration
- Final experimental report

Milestone 6 may be developed in parallel after the graph
data format stabilizes.

---

# 13. FIRST CODING TASK FOR CODEX

When asked to bootstrap this project, perform ONLY Milestone 0
and the smallest useful part of Milestone 1.

FIRST:

1. Inspect the current workspace.
2. Check available Python, Git, Java, and Maven versions.
3. Report missing prerequisites without pretending they exist.
4. Initialize the Python project.
5. Create the documented repository structure.
6. Write a useful AGENTS.md based on this file.
7. Create the project specification and architecture docs.
8. Create a tiny Java/Maven/JUnit example repository.
9. Implement a Python CLI entry point.
10. Implement Git change extraction.
11. Add automated tests.
12. Add a GitHub Actions workflow.
13. Update README.md with actual commands.

Initial CLI goal:

codedna analyze --repo PATH --base SHA --head SHA

For the first implementation, the command may output
file-level changes before method-level parsing is added.

Example JSON shape:

{
  "repository": "/path/to/repo",
  "base_commit": "BASE_SHA",
  "head_commit": "HEAD_SHA",
  "changed_files": [
    {
      "path": "src/main/java/example/OrderService.java",
      "status": "modified",
      "changed_lines": [[12, 18]]
    }
  ],
  "warnings": []
}

The example is illustrative, not actual analysis output.

The CLI must validate inputs and fail clearly on invalid SHAs,
missing repositories, and Git command errors.

Do not execute untrusted repository scripts automatically.

Do not use shell=True for Git commands.

---

# 14. TEST REQUIREMENTS

At minimum, test:

- Valid Git repository
- Invalid repository
- Valid commit comparison
- Invalid commit SHA
- Modified Java file
- Added Java file
- Deleted Java file
- Renamed Java file
- Changes to non-Java files
- Empty diff
- Filenames containing spaces

For Java method analysis, later add:

- Overloaded methods
- Constructors
- Nested classes
- Multiple methods in one file
- Comments and formatting-only changes
- Changes spanning multiple methods
- Method deletion
- Syntax errors
- Unsupported constructs

Create temporary Git repositories in automated tests.

Do not depend on an external internet connection for unit tests.

---

# 15. AGENTS.MD RULES

Create an AGENTS.md containing these rules:

- Read docs before implementation.
- Work on one milestone at a time.
- Explain assumptions and limitations.
- Write tests for new features.
- Run tests before claiming completion.
- Never fabricate test results.
- Never claim a heuristic is a guaranteed dependency.
- Do not silently add major dependencies.
- Avoid cybersecurity scope.
- Do not implement advanced ML or frontend work early.
- Keep the project runnable on ordinary student laptops.
- Do not expose credentials.
- Never commit .env files, tokens, private datasets,
  or downloaded dependency caches.
- Ask before destructive repository operations.
- Do not change unrelated modules.
- Update documentation after architectural changes.
- Keep research experiments reproducible.

---

# 16. TEAM WORKFLOW

Use GitHub branches:

main
develop
feature/git-analysis
feature/java-parser
feature/dependency-graph
feature/test-mapping
feature/ml-ranking
feature/dashboard

Suggested responsibilities:

Student A:
Git mining, Java parsing, dependency graph

Student B:
Test data, baselines, ML, calibration, evaluation

Student C:
Graph visualization, API, integration, CI, documentation

All students must understand the complete architecture.

Use pull requests and code review.

Do not have multiple Codex sessions edit the same files
simultaneously without coordinating changes.

---

# 17. DEFINITION OF DONE FOR INITIAL BOOTSTRAP

Milestone 0 is complete only if:

[ ] README explains the project clearly
[ ] AGENTS.md exists
[ ] Python environment can be installed
[ ] CLI command can run
[ ] Example Java project builds
[ ] Automated Python tests pass
[ ] Git change extraction has real tests
[ ] GitHub Actions workflow exists
[ ] Architecture documentation exists
[ ] Known limitations are documented
[ ] No fake results are presented
[ ] No secrets are committed

If something cannot be completed, document the blocker.

---

# 18. WHAT CODEX MUST REPORT AFTER IMPLEMENTATION

Provide:

1. Summary of what was created
2. Directory tree
3. Actual commands executed
4. Test results
5. Example CLI command
6. Example real output
7. Known limitations
8. Dependencies installed
9. Any decisions requiring human review
10. Recommended next milestone

Never claim success unless commands actually ran.

---

# 19. FUTURE DEMONSTRATION SCENARIO

The final FYP demonstration should resemble this:

A developer changes a Java method.

CodeDNA:

1. Detects the changed method.
2. Opens the interactive codebase graph.
3. Highlights affected components.
4. Shows connected regression tests.
5. Ranks those tests by predicted failure risk.
6. Estimates test execution cost.
7. Reports uncertainty.
8. Expands testing if confidence is inadequate.
9. Exports an explainable report.

The final presentation should compare CodeDNA against
established test-selection baselines.

Do not claim guaranteed detection of all regressions.

---

# 20. START HERE

CODEX, FOLLOW THESE INSTRUCTIONS:

Read this document completely.

Inspect the workspace and identify installed prerequisites.

Implement Milestone 0 and the minimal file-level Git analysis
CLI described in Section 13.

Do not implement the dashboard, machine learning, risk
calibration, or security extensions yet.

Write clean, testable code.

Run the tests.

Explain every important architectural decision.

When finished, tell me exactly how to run CodeDNA locally
and demonstrate the Git change analyzer.

Begin now.
