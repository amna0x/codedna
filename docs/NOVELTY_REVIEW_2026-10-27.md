# CodeDNA novelty review and feature recommendations

Research date: 27 October 2026. Reviewed local main `45821b4908bf3c17ff60cea28fd934c0dd55d8f1`.

## Recommendation

Keep CodeDNA. Strengthen its evaluation and the decisions it explains before adding another model. The strongest proposed research question is:

> Under incomplete test feedback, what extra protection and cost come from combining a structural must-run floor with target-project-validated stopping that limits omitted failures?

This is a proposed empirical contribution, not an established result or a claim of being first. Its components have prior art. A negative result would still answer a useful question.

The immediate next build should be a deployment-faithful replay harness and a loss-definition report. Then evaluate the already implemented structural/risk union. New product features should reuse that evidence.

## Scope and evidence

This is a focused literature and source review, not an exhaustive systematic review. Sources were selected around predictive test selection, conformal stopping, coding-agent test selection, deployment feedback, and risk control.

Local navigation used the existing Graphify graph (3,199 nodes), then checked source. Relevant files: `backend/codedna/selection/{conformal,tuned,validation}.py`, `backend/codedna/models/{experiment,uncertainty}.py`, `backend/codedna/test_history/features.py`, `backend/codedna/agent/brake.py`, `scripts/run_rolling_evidence.py`, roadmap, handoff, related-work table, and saved B12f/B13f findings. No experiment was rerun. No code or saved results changed.

Public GitHub sources were retrieved through GitHub's API when browser retrieval failed. Versions inspected:

- FaithfulCut: `3e48eb578cfe11a876c7134d0e765147f073845a`.
- Westermo predictive test selection: `bc56aa304e1624e66225e85ae385a3862a557d56`.

The source repositories' claims were inspected, not independently reproduced. DANTE full paper remains unavailable in this review; do not infer absent features from its abstract.

## Closest work and implications

| Work and source | Evidence inspected | Implication for CodeDNA |
|---|---|---|
| [Predictive Test Selection, Machalica et al., ICSE-SEIP 2019](https://arxiv.org/abs/1810.05286) | Paper record; existing project full-text comparison | Learned selection with aggregate recall targets is established. Treat B11 as an adaptation, not a reproduction of Facebook's system. |
| [DANTE, ICST 2026](https://doi.org/10.1109/ICST69053.2026.00080), [author artifact](https://zenodo.org/records/18900675) | Publisher abstract and artifact record | Training-free historical and change-aware scoring is a serious baseline. CodeDNA's existing history adaptation does not establish superiority over full DANTE. |
| [Context-Aware Sequential Ranking, 2026](https://www.mdpi.com/2227-7390/14/18/3276) | Publisher search record and existing full-text comparison; direct retrieval rate-limited | Conformal candidate filtering and deterministic history/content ranking overlap with uncertainty-aware selection. Adding conformal prediction alone is not novel. |
| [MOX, 2026](https://www.mdpi.com/2079-9292/15/17/3854) | Publisher method/abstract material | Cost, detection, coverage and traceability tradeoffs are prior art. Its inferred change events limit direct comparison with real changed code. |
| [Westermo CRC source](https://github.com/l-k-1-2/Predictive-test-selection) | README, source structure, pinned revision | Already selects tests using conformal risk control, including rolling/adaptive variants. It controls a fraction of missed failing tests. Do not claim first CRC test selector. |
| [FaithfulCut](https://github.com/TheDeadcoder/FaithfulCut) | README, preregistration, replay source and control definitions | Already combines censored/delayed feedback, random full-suite audits, risk controllers and monitoring. The author describes it as under review, not accepted. Audit/drift features alone cannot establish novelty. Its build-escape loss differs from CodeDNA's any-omitted-failure loss. |
| [TDAD, March 2026 preprint](https://arxiv.org/html/2603.17973v2) | Architecture, impact-analysis method and evaluation material | Graph-guided test context for coding agents is prior art. An MCP interface or dependency map alone is insufficient as a research claim. |
| [TestPrune, FSE 2026](https://arxiv.org/html/2510.18270v2) | Method and evaluation material | Already combines issue-based localization, coverage and greedy regression-suite reduction for repair workflows. Agent test minimization is not a new category. |
| [Conformal Risk Control, ICLR 2024](https://research.google/pubs/conformal-risk-control/) | Author paper and research record | Controls expected bounded monotone loss under stated assumptions. This differs from a high-probability claim about one fitted policy and from certainty on the next commit. |
| [Learn then Test](https://arxiv.org/html/2110.01052v3) | Risk-control theorem, valid p-values and fixed-sequence sections | Fixed-sequence scanning needs valid individual tests. Calling a Wilson evidence screen LTT does not automatically establish an exact finite-sample guarantee. |
| [Non-Exchangeable CRC, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/de04896f011beff76c91e094f72727f4-Abstract-Conference.html) | Conference record and author PDF introduction/theorem description | Recency weighting has statistical precedents. Bounds involve assumptions and shift terms; weighting recent commits does not solve arbitrary drift. |
| [Anytime-Valid CRC, February 2026 preprint](https://arxiv.org/html/2602.04364v1) | Problem formulation and assumptions | Repeated certification has prior art. The basic formulation uses independent identically distributed calibration points; its shift extension assumes known importance weights. It is not a ready-made guarantee for arbitrary CI streams. |

## Important distinction: three different meanings of safety

Let F be the set of failing tests for a commit, and S the selected tests.

1. **Build escape:** F is nonempty and S catches none of F. A selector that catches one of ten failing tests avoids an escape.
2. **Any omitted failure:** at least one member of F is outside S. Catching nine of ten still counts as a miss.
3. **Missed-test fraction:** the proportion of failing tests outside S. Catching nine of ten gives loss 0.1.

CodeDNA's `metrics().safety` is the share of failing commits with **zero omitted failing tests**. Its CRC loss is `missed > 0`, evaluated among failing audit commits. FaithfulCut's primary escape criterion is weaker: no failing test caught. The Westermo project uses a missed-test fraction. These are distinct objectives, not interchangeable percentages.

Also distinguish the denominator. A 5% miss rate over all commits can conceal a much larger miss rate among failing commits. B10's current empirical gate and B12f do not use the same denominator.

Proposed feature: show the selected objective explicitly, with numerator, denominator, sample size, observation window and method. Avoid a bare '95% safe' badge. A comparison must score every method under the same losses, even when methods were originally designed for different objectives.

## What the existing results support

- The original nine-project B10 confirmation found no meaningful safety difference from a matched recent-failure budget; failing-test recall was lower. This does not support claiming a universally better selector.
- B12f saves 16.20 percentage points of recorded test time against the gated product, but safety falls 1.79 points. Cloudify reaches 87.84% safety, below 95%.
- Exploratory B13f saves 3.61 points of recorded test time. Its safety difference is +0.54 points, with interval [-0.25, +1.42]; improvement is unproven. Cloudify again misses 95%.
- The nine-project PTS budget match failed. Its comparison cannot establish an equal-cost winner.
- Historical test-execution cost excludes build, feature extraction and startup overhead. It is not measured CI wall time.

Sources: tracked findings under `experiments/results/*confirmatory-perf-2026-10-26/` and `docs/REPORT_DRAFT.md` sections 4.11/4.12. Preserve original studies and their hashes. New experiments need new output folders.

## The main evaluation gap

The feature builder correctly uses earlier commits rather than current/future labels. However, it updates state with all stored prior results. The saved replay consumes these precomputed feature rows. It does not rebuild each policy's history using only results that policy chose to observe.

That is a full-history retrospective simulation, not automatically a simulation of long-term partial selection. It remains useful when full outcomes really become available later. It does not establish performance when skipped outcomes remain unknown. This is a feedback-availability limitation, distinct from ordinary future-label leakage.

For a new replay:

- Keep full labels in an evaluator-only store for measuring misses.
- Give each policy a separate observation store. Release only its executed results and completed audit results.
- Rebuild history-derived features from that store, including training/calibration inputs when models update. Masking final labels while keeping full-history features is insufficient.
- Use completion times if reliable timestamps exist. Otherwise disclose a simplified sequential-completion assumption; do not invent timing data.
- Treat skipped tests as unknown, never passed. A passing subset does not tell us whether the entire commit would fail.
- Count full audits, mandatory tests, repeated runs and selector overhead in total cost.

## Ranked feature proposals

| Priority | Feature | User value | Research value and limit |
|---|---|---|---|
| 1 | **Unchecked-tests view** | Shows skipped tests, last observed result, evidence age, and why each remains unchecked. | Makes incomplete feedback measurable. UI alone is not novelty; pair it with the new replay. |
| 1 | **Full-suite audit mode** | Occasionally checks skipped tests and refreshes evidence. Exposes audit cost and required consent. | Necessary for estimating hidden misses. Random audit selection must be independent of unseen outcomes. Already prior art; evaluate its value for the structural/risk combination. |
| 1 | **Cost–safety comparison** | Shows 'run all', structure only, history budget, and audited stopping using comparable costs. | Repairs the PTS fairness gap; report common attainable budgets and matched-safety frontiers. No claimed winner when matching fails. |
| 2 | **Decision evidence export** | Saves snapshot IDs, plugin/model/policy versions, mandatory tests, risk objective, audit counts, missing results and final execution status. | Helps reproduce an actual brake decision. An evidence record is not proof that a patch is bug-free. Reuse existing snapshot and result machinery. |
| 2 | **New-failure protection and report** | Highlights changed/new tests and tests that have not failed before; shows what history-only ranking can miss. | Evaluate the existing structural floor on first failures separately from recurring/flaky failures. Do not classify a failure using future information. |
| 2 | **Risk–coverage screen** | Shows how often CodeDNA permits reduced testing versus requesting the full suite. | Measures useful abstention instead of praising a method that achieves safety by always running everything. Distinguish uncertainty coverage from code coverage. |
| 3 | **Evidence-expiry and shift warning** | Turns reduced selection off when evidence becomes unsuitable. | Useful engineering; not new by itself. Predefine triggers and test false alarms, missed changes and recovery cost. |
| 3 | **Failure explanation and comparison** | Connects a failed test to changed code and labels confirmed/heuristic/unresolved paths. | Useful inspection, but not a proven root cause. Human evaluation is needed before claiming explanations improve developer decisions. |
| Later | **Per-test coverage refinement** | Helps reduce over-broad structural selections. | Validate source/snapshot alignment and stale-coverage fallback. Coverage-based selection already exists; extra collection cost may erase savings. |
| Later | **JS/TS plugin** | Broadens the product to web projects. | Language breadth is product value; Java's risk evidence does not transfer automatically. |

Features already implemented must not be rebuilt: CRC opt-in, the structural-plan union, Python/mixed full-suite fallback, must-run policy, project history, history replay, plugin manager and basic execution evidence.

## Recommended research design

**RQ1:** How much do partial observations change each method's apparent safety and savings?

**RQ2:** Does adding the structural must-run floor improve protection for first failures at comparable total cost?

**RQ3:** Can the combined brake preserve the chosen failure-conditional target while offering useful reduced-suite coverage after audit costs?

**RQ4:** How often does it refuse reduced testing, and how quickly does evidence recover after code or test changes?

Baselines: full suite; existing dependency selection; recent-failure fixed budgets; DANTE adaptation clearly labelled; B10; B12f; exploratory B13f. Include a FaithfulCut-style controller if faithfully implementable. Reuse published author code only with license/provenance checks. Do not describe an adaptation as a complete reproduction.

Ablations: statistical stop only; structural floor only; their union; union with audits; union with evidence-expiry. Compare different audit schedules at the same total cost. Do not tune a separate favorable budget on evaluation outcomes.

Report all three losses, first-failure performance, failing-test recall, reduced-suite coverage, audit cost, selector time, total executed test cost, incomplete builds and per-project results. Compare base selections and final executed selections separately: a later audit must not conceal that the base selector missed a failure.

Start with two development projects, one with abundant failures and one difficult case. Previously inspected Cloudify is a diagnostic development case, not fresh confirmation. Write and timestamp the protocol before choosing a new untouched evaluation period/project. Existing nine-project data can support development/sensitivity checks, not a second claim of independent confirmation after redesign.

Use paired temporal blocks or whole-PR resampling where reliable grouping exists. Predefine block length, primary contrasts and multiplicity handling. Do not change intervals merely to obtain significance. If evidence is scarce, report uncertainty and full-suite fallback.

Keep a laptop-friendly pipeline: cache prediction-independent data, cap processes, use incremental checkpoints and smoke runs before expensive evaluations. No paid agent calls are required for the first study. Replaying existing patches tests brake decisions; it cannot establish that agents write better patches.

## Statistical improvement worth considering

B13/B13f's fixed-sequence logic is promising, but the existing Wilson screen is approximate. If a finite-sample claim is wanted, first specify the exact loss, independent sampling unit, valid test and multiplicity procedure. Exact binomial testing can be appropriate for independent Bernoulli loss on representative failing audit commits; it does not fix temporal dependence or biased observation.

For illustration, zero misses in 19 independent failing commits still gives a one-sided exact 95% upper bound of about 14.59%. Zero in 59 gives about 4.95%. The bound is `1 - 0.05**(1/n)`. Nineteen commits can satisfy CRC's `(misses+1)/(n+1) <= .05` correction, but that is a different statement from 95%-confidence certification. Also account for threshold selection and repeated certification.

Do not deploy online CRC updates based only on observed subset results: hidden failures and the unknown failing-commit denominator can bias the update. Start from complete full-run audit observations. Any inverse-propensity method needs its own assumptions and validation.

## Product status and language/distribution plan

Milestone 5 is reached in implementation, but not fully closed: report completion and supervisor review remain. The roadmap's old 'no fresh verdict' and pending-publication text is stale. The confirmation finished, and PR #22 merged as `45821b4`. The installed graph/source review confirms D-068/D-070 should not be implemented again.

Remaining delivery work: refresh the installer with current code; complete Python/mixed IDE acceptance and Java diagnostics; test on clean Windows without an existing Python setup; finish the GitHub PR demo, human graph spot-check and report/defence materials. Existing 554-test Maven-inclusive validation is recorded; this research review did not rerun it.

Recommended language order: **JavaScript/TypeScript next**, then consider **Go**. Keep Kotlin for a specific JVM demand; Java interop and symbol resolution need real validation. Start each new plugin with discovery, labelled graph edges, execution and conservative fallback. Validate risk separately.

Jest already offers related-test selection and structured results, so include it as a native baseline rather than selling that capability as new. Vitest's related command has static-import limits. Go offers structured test output. See [Jest CLI](https://jestjs.io/docs/cli), [Vitest CLI](https://vitest.dev/guide/cli.html), and [Go command docs](https://pkg.go.dev/cmd/go#hdr-Test_packages).

Use both the website and the IDE's **Language plugins** view with one official catalogue and installation path. Keep Java/Python bundled initially; offer optional engine plugins as pinned, checksum-verified downloads once hosting and release packages exist. CodeDNA engine plugins are separate from editor extensions/VSIX packages. The current catalogue has no downloadable Java/Python URLs; the existing website is not a finished distribution service.

## Concrete next sequence

1. Agree the loss definitions; preserve prior findings and label the full-history limitation.
2. Build the small policy-specific replay harness with tests that hidden outcomes cannot alter decisions.
3. Evaluate the current structural/risk union, first failures, audit overhead and attainable cost matching on development data.
4. Freeze a new protocol; evaluate untouched data only after the design is fixed.
5. Expose unchecked tests and export decision evidence using existing core results.
6. Complete installer/manual/report work, then add the JS/TS plugin and publish the shared catalogue.

The project can be a strong FYP through a clear question, a complete working brake, fair comparisons and honest failure cases. More languages and a polished website improve the product. They do not by themselves establish research novelty.
