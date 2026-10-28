# CodeDNA Moonshot: an evidence engine for software change

**Proposal date:** 27 October 2026  
**Horizon:** twelve months after an explicitly approved start  
**Assumption:** unlimited development resources; ordinary developer hardware remains a supported runtime  
**Status:** proposal only. No implementation is authorized by this document.

## The ambition

Make CodeDNA the system a developer or coding agent consults before trusting a software change.

Today the central question is: “Which regression tests should I run, and what is the estimated risk of skipping the others?” The moonshot expands it:

> “What evidence would make this particular change acceptable, what is the cheapest next action that could materially improve that evidence, and what do we still not know?”

CodeDNA should maintain a living, versioned account of a change: the behavior it intends to alter, the code and contracts it might affect, the tests and observations that support it, the assumptions those observations depend on, and the reasons acceptance is still withheld. It should use that account to recommend and execute authorized validation, recover from interruption, and produce a replayable decision record.

The decisive product experience is a developer changing a shared Java component and seeing, within an interactive workflow:

1. The relevant changed declarations and likely downstream effects, with inspectable source evidence.
2. The tests that must run, tests selected for additional information, and tests currently omitted.
3. The exact limits of the analysis: unresolved dispatch, stale coverage, unseen failures, configuration changes, incomplete history, or unsupported boundaries.
4. A concrete next action: run this test, refresh this mapping, inspect this contract, or run the full suite.
5. A result that says precisely what was established for this snapshot and environment.

For coding agents, that becomes an evidence contract: an agent cannot satisfy a required check merely by asserting that its patch is correct. CodeDNA evaluates recorded observations against the contract. For humans, it becomes an understandable account of why a change is ready, blocked, or insufficiently checked.

This is a much more ambitious destination than a richer graph panel or a better ranker. The main improvement is a trustworthy loop from change to evidence to decision to new observation.

## What this proposal preserves

The current Java research work remains the first priority. The existing FYP must retain a bounded, defensible contribution even if every experimental moonshot hypothesis fails. The twelve-month program is an expansion plan, not a retrospective rewrite of the thesis or a promise about its submission date.

Do not interrupt the active D-076 pilot, change its fingerprinted source, retune its protocol, or relabel reused data as fresh confirmation. Complete and review that checkpoint before beginning a phase that changes affected implementation. D-077 explanation/export work is an existing foundation, not an unbuilt moonshot deliverable.

Keep the current conservative defaults until a separately evaluated replacement earns promotion. Preserve B10 as the recorded default and CRC as the existing opt-in unless a new decision explicitly changes that. Keep Java-specific risk evidence separate from Python and any later language. Existing Python/mixed fallback is a correct behavior to preserve, not a deficiency to hide.

The owner has deferred installation refresh, public catalogue delivery, and clean-PC acceptance to the end of the current engineering sequence. This plan respects that order. New language work also remains gated behind completion of the Java workflow and explicit approval of that expansion.

The core stays language-neutral, local-first, and usable without a GPU, accounts, a cluster, or a hosted service. Optional large-scale experiment infrastructure does not become a requirement for opening a repository. Builds require the existing explicit execution authorization; analysis must never silently execute repository scripts. No cybersecurity scoring, vulnerability research, or pentesting enters scope.

Nothing here authorizes a commit, push, merge, release, public upload, external message, or new study run. Each phase is reviewed before the next begins. This file does not supersede AGENTS.md, MEMORY.md, existing research protocols, or the active roadmap.

## Starting position: extend what already exists

This proposal is grounded in the checkout's AGENTS.md, MEMORY.md, PROJECT_SPEC, ARCHITECTURE, ROADMAP, DECISIONS through D-077, BLUEPRINT_COMPLETION, and DEFERRED_FEATURES, together with its local Graphify graph. Documentation contains historical status sections; the newest overrides take precedence. Status below is documented capability, not a claim that every acceptance gate was revalidated during proposal writing.

| Existing foundation | Moonshot extension |
|---|---|
| Git change extraction and declaration mapping | Snapshot-bound change identity across edits, runs, and recovery |
| Shared graph with confirmed/heuristic edges and unresolved references | Temporal evidence graph with explicit coverage gaps and validity conditions |
| Dependency/coverage selection and structural-plan union | Mandatory evidence floor plus observation-aware adaptive scheduling |
| History, calibrated risk selection, audit gates, B10 and opt-in CRC | Decisions that account for their own partial feedback and evidence expiry |
| Saved runs, research replay, decision export | One reusable evidence lineage across human, IDE, CLI, and agent workflows |
| Java and Python plugins | Capability-aware contracts; later languages only with separate evidence |
| Agent brake and MCP interface | Versioned validation contracts and externally checkable completion records |
| Theia IDE and local API | A change-centered workspace with truthful operations and recovery |
| Frozen desktop plugin installation | Final distribution acceptance and reproducible release evidence |
| D-076 observation-isolated pilot | Starting feasibility evidence for a larger, separately registered program |

The code-navigation Graphify graph is not the application's dependency graph. Keep those roles distinct. Use local Graphify to navigate implementation and verify relevant source; do not replace CodeDNA's graph schema or decision logic with navigation-tool inference.

## The product: a change evidence workspace

The primary screen should be organized around a change, not a collection of unrelated commands. Its persistent identity includes repository identity, base/head or working-tree digest, plugin and policy versions, and the relevant execution environment.

The screen answers five questions in plain language:

- **What changed?** Declarations, resources, build files, configuration, and intended behavioral scope.
- **What might be affected?** Evidence-backed paths with uncertainty visible at each step.
- **What have we actually checked?** Observed passes, failures, skips, interruptions, and their precise snapshot.
- **What remains unchecked?** Omitted tests, unknown boundaries, stale mappings, and assumptions.
- **What should happen next?** A specific validation action with estimated cost and its rationale.

An estimate of skip risk must not visually dominate the screen when its prerequisites are absent. “Risk unvalidated” is a useful result. It should explain the missing condition and whether an authorized action can repair it. An estimated duration should never masquerade as measured progress. Test names can describe static declarations; generated descriptions of intent must remain identified as suggestions.

The graph is an investigation tool: click an explanation to inspect the underlying declarations and evidence. A large force-directed graph is not the default answer to every question. Start with the changed component and relevant paths, then let the user expand them.

Support counterfactual exploration: “What changes if I require this test?”, “What if I have ten more minutes?”, “What if this coverage is stale?”, “What if I refuse all heuristic edges?” These are previews of alternative plans. They must not rewrite the actual decision record or claim outcomes for tests that were never run.

## The technical center: a temporal evidence graph

The graph should represent more than code relationships. It should connect immutable snapshots, declarations, tests, executions, policies, coverage observations, model artifacts, audits, unresolved references, and decision records.

Every important claim needs a subject, a predicate, provenance, an observation time, a validity scope, and a reason it might stop applying. For example, “test T covered method M” is an observation under a particular revision, input, runner, instrumentation, and environment. It is not a timeless proof that T detects every fault in M.

Separate at least three layers:

1. **Structural facts:** parsed declarations and references, preserving confirmed/heuristic/unresolved semantics.
2. **Execution observations:** actual outcomes, coverage, durations, collection completeness, and environment identity.
3. **Decision claims:** a policy's selected set, prerequisites, estimated quantities, refusals, and acceptance result.

A relationship can be structurally confirmed yet incomplete as an account of runtime behavior. A dynamic observation can be exact for its run yet irrelevant to a later snapshot. Provenance and completeness must therefore remain separate dimensions. Do not collapse them into a single confidence percentage.

Build an incremental engine over content-addressed artifacts. Cache immutable parsing by content; cache derived results only with complete dependency fingerprints. Invalidation must include plugin, schema, configuration, classpath, instrumentation, and policy changes where relevant. Working-tree snapshots must account for added, removed, renamed, and untracked inputs. Results from an older snapshot remain inspectable but cannot silently satisfy a newer contract.

For ordinary projects, use an embedded store and bounded caches. Export portable evidence bundles rather than introducing mandatory distributed databases. Define storage retention and compaction explicitly: old blobs may be pruned according to policy, but retained decision records must disclose when their full replay dependencies are no longer available.

## Semantic depth where it changes decisions

The Java graph should become substantially more useful through method-level reference resolution, explicit dispatch alternatives, and better treatment of inheritance, interfaces, generated code, resource loading, configuration, annotation-driven behavior, and build topology.

Do not promise a sound whole-program analysis for arbitrary Java. Instead define supported semantic slices and publish their failure modes. A compiler-backed resolver can provide stronger evidence where the environment is available, while the existing parser remains a lightweight baseline. Resolution that requires builds stays behind the execution boundary. Unavailable dependencies produce explicit unknowns.

Model non-code inputs because a build file or configuration change can invalidate a narrow plan even when method bodies are untouched. Broad fallback is the correct default until a particular input class has an evaluated treatment.

Expand coverage mapping deliberately across Maven/Gradle modules and parameterized tests. Separate test discovery, executability, instrumentation success, mapping completeness, and outcome completeness. A test appearing in discovery does not establish that it ran; a missing coverage entry does not establish non-dependence.

Cross-language relationships come later as explicit boundary contracts: subprocess entry points, API schemas, generated clients, shared files, and message formats. Do not invent direct edges merely because Java and Python coexist in a repository.

## The hard research problem: learning from selective observation

The largest scientific opportunity is to make test selection honest about the data it creates.

After a selector omits a test, its outcome is unknown. That outcome must not be recorded as a pass, imputed as a fact, or supplied to the next decision as if production had observed it. Full-information retrospective results can be useful, but they answer a different question from a policy deployed under partial feedback.

The proposed scheduler maintains an observation ledger. At each decision it can see only evidence available at that time. It constructs a mandatory set from supported structural requirements and policy rules, then recommends additional tests under an explicit budget. Candidate actions can include ordinary tests, broader runs, and scheduled audits. A test may be valuable because it is likely to find a failure, because it covers a mandatory obligation, or because it repairs an important evidence gap; these rationales should be distinguishable.

Use a simple accounting identity rather than an impressive but unjustified score:

`proposed work = mandatory obligations + evaluated policy choices + scheduled audit obligations`

The actual set is a deduplicated union. Budget exhaustion cannot erase mandatory obligations. If required work exceeds the budget, report the conflict and return an incomplete/broader plan. If the policy lacks validated prerequisites, retain fallback.

Audits are central. Predefine their schedule or sampling policy, what they observe, how they enter later training, and what they cost. Audit full-suite runs that replace selected runs must not be double-counted. Audits added on top must be charged. Include fitting, calibration, graph extraction, instrumentation, retries, and setup in cost accounting; report developer latency and aggregate compute separately.

Research candidates include conservative adaptive scheduling, evidence-expiry rules, drift detection, and selection-bias correction. Logged action probabilities may support some estimators only if the sampling policy provides the needed support and assumptions hold. Deterministic omission cannot be repaired by pretending to know propensities. Statistical stopping procedures must address repeated decisions and dependence before receiving stronger language than empirical validation.

No theorem should be implied by a calibrated probability. Define the target explicitly: per-test miss, failure-containing-commit miss, recall, and release acceptance are different endpoints. A nominal five-percent target on one endpoint does not establish a five-percent guarantee on another.

The research may conclude that broad audits consume most savings, or that simple rules dominate a more elaborate scheduler. That is a valid outcome. The evidence engine, operations, and agent contracts remain valuable without a positive ML result.

## Agent contracts: an evidence brake that survives the agent changing the code

Extend the existing brake/MCP workflow rather than building a second agent backend.

A proposed validation contract binds a change snapshot to required checks, applicable policy versions, execution permissions, and acceptance rules. The agent can request a plan, inspect why obligations exist, run authorized checks, and submit observations. CodeDNA evaluates those observations; agent-written summaries are explanatory text, not execution evidence.

A suggested lifecycle is `draft -> planned -> executing -> evaluated`, with terminal or recoverable states such as `blocked`, `incomplete`, `cancelled`, and `stale`. Exact names are design work, not an implemented API. A code edit after execution invalidates affected acceptance evidence. A skipped required class, interrupted runner, missing report, or mismatch between requested and executed tests cannot result in a successful contract.

Completion means “the recorded obligations for this snapshot were satisfied under these conditions.” It does not mean “this patch contains no defects,” “safe to deploy everywhere,” or “approved to merge.” Acceptance authority remains separate from evidence collection.

Make the contract usable by multiple agents and tools without requiring shared conversational memory. Independent consumers should be able to verify artifact hashes, versions, required/observed test sets, and the verdict. Hashes establish identity and detect changes; they do not prove the runner was truthful. The trust boundary and report origin must remain explicit.

The most ambitious demonstration is an agent attempting a large refactor, being stopped because one required check was skipped, repairing the gap, then becoming stale when it changes code again. CodeDNA should enforce this through its data model, not through a prompt telling the agent to behave.

## Tests that strengthen the evidence, with an explicit oracle problem

Add a later assistant for proposing focused tests at uncovered change boundaries. It can suggest boundary cases, invariants, metamorphic relations, or property-based checks, with a clear distinction between a proposed oracle and a validated requirement.

Generated tests can encode the same mistaken assumption as generated code. Passing them cannot automatically justify skipping existing tests or certify the patch. Require review of the intended behavior and execute only with authorization. Keep generated test evidence identifiable.

Use mutation testing and historical fault replay to investigate whether proposed tests detect meaningful changes. Mutants are proxies, not representative production defects by default. Track invalid, equivalent, uncompilable, and timed-out mutants separately, and report instrumentation cost. Never use a mutation score as the sole acceptance criterion.

This work earns inclusion only if it improves measured fault detection or diagnosis beyond equal-cost ordinary validation. Otherwise keep it an optional investigation aid.

## Operations that make the ambition usable

Every expensive operation needs an identity, truthful state, resumable checkpoint where feasible, and a bounded cancellation path. Reuse existing progress and cancellation capabilities where present; complete missing core behavior instead of layering another spinner over it.

An operation record should distinguish queued, running, cancellation requested, cancelled, failed, completed, and stale. Progress can be counts when the total is known and named stages when it is not. A cancellation request is not completion. Child runners must be supervised; interruption must preserve completed observations and identify incomplete reports.

Checkpoint recovery validates source/input fingerprints before resuming. Changed inputs produce a new operation or an explicit invalidation, never a quiet resume against different code. Writes are atomic; duplicate import and replay are idempotent. Concurrent runs cannot overwrite another snapshot's results.

Portable diagnostic exports should remain bounded and intentional. Extend the existing allowlisted evidence export, separating a shareable summary from optional source-bearing artifacts. Local repository names and paths may still be sensitive; show what will be exported. No default telemetry or external upload is necessary.

## A research laboratory inside the product's development process

Build one evaluation system that can replay chronological histories while enforcing information visibility. Each competing policy receives only its own observations. A separate evaluator may inspect complete reference outcomes for scoring, but those outcomes must never cross into policy state before their allowed observation time.

Version datasets, feature generation, source mapping, splits, policies, environment, and protocols. Freeze confirmatory protocols before outcomes are inspected. Use development cohorts for iteration and independent held-out projects or prospective windows for confirmation. More seeds do not create more independent projects.

Compare against full-suite execution, recent-failure ordering, shortest-first, dependency/coverage selection, and the current product policy. Compare at attainable matched costs, including audits and overhead. Report when a competitor cannot meet the intended cost match. Report all projects, refusals, and unsupported cases, not just those on which the new method succeeds.

Primary outcomes should include failure-containing-commit misses, first/new-failure behavior, total validation cost, time to first actionable failure, risk-valid coverage, fallback rate, and evidence recovery time. Secondary predictive scores are diagnostic. A favorable calibration plot is not sufficient to promote a stopping policy.

Report project-level uncertainty and sensitivity to dependence. A sample with zero observed misses can still be too small to support a stringent risk claim. Rare failures set a real limit on what twelve months can establish, even with unlimited engineers.

Do not make future independent human graph labels an owner task; that request was declined. Use reproducible automated reference checks and attribute AI reviews honestly. Any genuinely independent collaboration is optional and requires separate agreement and provenance.

## Twelve sequential phases

Months are planning allocations from approval, not promises or permission to start several phases simultaneously. Each phase ends with a concrete artifact, evidence review, and an explicit decision to continue, revise, or stop. Existing authorized work can supply deliverables; do not reimplement it to fit this outline.

### Phase 0 — Month 1: establish the baseline and freeze the contract

Finish the active pilot and current engineering checkpoint without disturbing their protocols. Reconcile existing contracts, current defects, deferred work, and actual acceptance evidence. Identify which historical documents are superseded. Produce a capability matrix and a versioned proposal for change identity, evidence validity, operation state, and acceptance semantics.

Create a representative local benchmark portfolio spanning small and medium Java projects, multi-module builds, unsupported inputs, cold history, and deliberate runner interruptions. Set the baseline on actual hardware. Preserve original experiments; new measurements go into new folders.

**Exit:** a reviewed scope, baseline report, compatibility plan, and phase-1 acceptance cases. No hidden dependency on unfinished public hosting or additional languages. The current FYP completion path remains viable on its own.

### Phase 1 — Month 2: make operations recoverable

Complete truthful progress, cancellation, operation identity, and checkpoint recovery in the existing core/API/IDE contracts. Make stale results impossible to confuse with current results. Preserve partial observations without treating them as completed validation.

**Exit:** tested cancellation during extraction, instrumentation, and execution; restart/resume with matching fingerprints; refusal on changed inputs; atomic recovery after an interrupted write; concurrent runs with no result cross-contamination. Record actual cancellation latency and any uninterruptible runner sections.

### Phase 2 — Month 3: establish the evidence ledger

Implement the minimum temporal provenance and observation model. Extend saved history and exports rather than creating another competing source of truth. Build a compatibility adapter for existing records, marking absent fields as unknown rather than inventing them.

**Exit:** a decision can be traced to its snapshot, policy, plugin, selected/required tests, and actual observations. Imports are idempotent. Schema migration preserves old outcomes. A changed environment or snapshot invalidates applicable claims. A portable bundle can be independently inspected without the IDE.

### Phase 3 — Month 4: deepen Java semantics

Add a bounded method-resolution capability and improve configuration/build-input treatment. Use capability flags and explicit unresolved reasons. Prototype stronger resolver integrations behind optional dependencies and execution permissions, recording architectural decisions before adding them.

**Exit:** published supported cases and limitations; measured extraction precision/completeness on an explicitly described reference set; regression cases for overloads, inheritance, interfaces, generated inputs, and missing classpaths; no unknown relationship silently converted into a confirmed dependency.

### Phase 4 — Month 5: make test observation dependable

Improve multi-module execution and mapping, including Gradle coverage where feasible. Track requested, discovered, executed, skipped, and reported tests separately. Add evidence-age and mapping-completeness explanations.

**Exit:** real Maven and Gradle integration fixtures establish exact test-set accounting; selected execution and full-suite audit paths produce comparable records; failed instrumentation and partial reports force incomplete/unknown states; overhead is measured rather than omitted.

### Phase 5 — Month 6: build observation-faithful evaluation

Extend the D-076 kernel and replay infrastructure into the shared evaluation harness. Add fixed-budget audit policies, evaluator/policy separation, complete cost ledgers, and a locked development/confirmation split. Keep existing saved findings immutable.

**Exit:** adversarial tests show policies cannot read withheld outcomes, future commits, or another policy's state. Repeat execution reproduces decisions and scores from identical inputs. A pilot can finish with a negative finding and still produce a complete report.

### Phase 6 — Month 7: investigate adaptive evidence acquisition

Evaluate a small, preregistered family of observation-aware schedulers against the frozen baselines. Start simple: mandatory floor, recency rules, evidence expiry, and a fixed audit budget. Add a more complex learner only when a simpler policy leaves a measured opportunity.

**Exit:** a go/no-go research report with per-project results, first-failure analysis, matched total costs, uncertainty, and refusal coverage. Promotion is conditional on evidence. A failed hypothesis leaves the current default in place.

### Phase 7 — Month 8: implement agent evidence contracts

Extend existing brake/MCP behavior to snapshot-bound obligations, structured evidence submission, and reproducible verdicts. Integrate one actual agent workflow through the same core used by humans. Do not create an agent-specific selection implementation.

**Exit:** an agent cannot satisfy a contract with missing/skipped checks, fabricated summaries, mismatched snapshots, or results from a prior edit. A real passing/failing/stale workflow is recorded. Contract success does not trigger publication or deployment.

### Phase 8 — Month 9: deliver the change evidence workspace

Unify explanations, unchecked tests, evidence health, operation recovery, and counterfactual planning around the existing IDE workflow. Add purpose-built navigation from a decision to a test, source location, or missing prerequisite. Ensure basic tasks also remain available through CLI/API.

**Exit:** end-to-end open/analyze/plan/run/record/reopen scenarios pass, including failure, cancellation, stale response, empty history, and unsupported input. A developer can distinguish a static test declaration from an observed result and an unvalidated risk estimate from an accepted check record.

### Phase 9 — Month 10: probe missing behavior with focused test proposals

Prototype optional test suggestions and mutation/historical-fault evaluation. Start with a narrow Java use case. Treat generated oracles as reviewable proposals. If the research cannot show added value, ship only the investigation capability or omit it.

**Exit:** equal-cost evaluation separates historical faults from mutation proxies, discloses invalid mutants and overhead, and demonstrates whether the proposals add detection value. No generated-test pass automatically broadens acceptance or relaxes existing obligations.

### Phase 10 — Month 11: test generality and prospective behavior

Use a locked prospective shadow evaluation on consented projects where feasible: recommendations are recorded while ordinary full validation remains authoritative. Ensure collected evaluation outcomes do not leak into decisions prematurely. Report unsuccessful adoption and setup friction as evidence.

Only after the Java gate and explicit language-expansion approval, assess the next plugin, likely JavaScript/TypeScript before Go as already proposed in the backlog. A plugin may provide structural capability without a validated stopping policy. Python remains a separate validation domain.

**Exit:** prospective or explicitly limited substitute evidence, a domain/capability matrix, drift/refusal results, and a stated conclusion about generalization. If independent data access is unavailable, narrow the claim; do not silently reuse development projects as confirmation.

### Phase 11 — Month 12: harden, distribute, and defend the result

Complete final packaging, real hosting destinations, official catalogue checks, upgrade/recovery exercises, and clean-machine acceptance after the current sequence's other work. Reuse the completed frozen-plugin architecture. Validate the exact artifacts that will be delivered.

Publish only with separate owner authorization. Assemble a reproducible research package, a local demonstration, an honest capability matrix, operator documentation, and a final account of which hypotheses survived.

**Exit:** exact release hashes and provenance; tested clean-machine installation and rollback; Maven-inclusive full suite and applicable real Gradle/IDE checks; verified download destinations; no claim stronger than the evidence. Keep a local-only usable product if public distribution remains unavailable.

## The scorecard and promotion rules

The following are proposed engineering ambitions and research decision rules. They are not achieved results, literature claims, or formal statistical guarantees. Phase 0 must freeze benchmark sizes, hardware, tolerances, and evaluation populations before they are used for promotion.

| Dimension | Proposed twelve-month ambition | How to evaluate it |
|---|---|---|
| Provenance | Every accepted check record has complete required identity fields and traceable observations | Schema validation plus deliberate snapshot/environment mismatch cases |
| Unknowns | Every supported analysis failure produces a structured unknown, refusal, or fallback | Fault injection and unsupported-input matrix |
| Incrementality | Small cached changes feel interactive; investigate a p95 under 2 seconds on a frozen medium-project workload | Separate warm analysis from cold extraction, execution, and UI time |
| Cancellation | Cancellation acknowledged promptly; investigate under 1 second for acknowledgement and under 5 seconds to stop cooperative workers | Measure actual child process termination and document exceptions |
| Recovery | Interrupted resumable operations recover without double imports or stale acceptance | Process termination and changed-input recovery exercises |
| Reproducibility | Offline replay produces identical decisions for fixed artifacts | Repeated runs and artifact identity checks; runtime variation reported separately |
| Efficiency | Stretch goal: at least 30% lower total validation cost on the frozen eligible cohort | Include audits, setup, analysis, fitting, retries, and instrumentation; show all projects |
| Miss control | No promotion on average savings alone; require the prespecified endpoint and uncertainty criteria to pass | Project-level and pooled reporting, dependence sensitivity, first-failure analysis |
| Evidence reach | Report what fraction of changes actually qualifies for validated estimates | Count refusals, fallbacks, unsupported projects, and expired evidence |
| Agent integrity | No successful contract with an omitted required check or changed snapshot in the acceptance suite | Adversarial contract fixtures plus actual runner demonstrations |
| Usability | A developer can explain why a check is required and what remains unknown | Observable task outcomes; any external participant work separately agreed |

The 30% figure is a stretch objective, not a reason to change the population or risk threshold after seeing results. If it is unattainable, publish the cost frontier and keep the simpler policy. An upper confidence bound can be wide even with no observed failures; “not enough evidence” must remain an allowed conclusion.

Promotion has separate gates: implementation correctness, retrospective evidence, observation-faithful evaluation, and prospective/domain validation where the claim requires it. Passing a UI test cannot promote a statistical policy. Passing a benchmark cannot prove a clean-machine installer works. A research-only candidate can remain useful without becoming a product default.

## Architecture and team organization under unlimited resources

Unlimited staffing should buy depth of evidence, adversarial review, better integration fixtures, and faster iteration within a phase. It should not buy unnecessary service boundaries.

Keep one coherent language-neutral analysis core, one shared graph/evidence schema, existing plugin boundaries, and a single set of decision semantics consumed by CLI, local API, IDE, and MCP. Separate pure planning from permissioned execution. Use optional workers for expensive tasks, with a supervised local default and the same result contract.

A future staffed program could have owners for Java semantics, execution/coverage, evidence storage, statistical evaluation, agent contracts, IDE interaction, and release engineering. Give protocol review and outcome analysis independence from the people tuning candidate policies when feasible. This describes a hypothetical organization, not authorization to launch agents or parallel work now.

Before any large implementation, write a design note with compatibility impact, alternatives, data migrations, expected failure modes, resource budget, and acceptance cases. Major dependencies enter only when a phase needs them, with a decision record. Refresh local Graphify after code changes; verify graph-derived relationships against current source.

Test new features with temporary repositories and offline fixtures. Run the required full Maven-inclusive suite before claiming implementation completion; also exercise real runners and IDE boundaries appropriate to the change. Synthetic histories verify information isolation, not empirical accuracy. Real datasets evaluate accuracy, not every failure mode of operation recovery. Both are necessary for their respective claims.

## What could invalidate the plan

**The feedback loop may be too expensive to repair.** Audits can erase apparent selection savings. Response: report total cost, reduce ambition, retain broad validation, and keep the evidence/agent product independently useful.

**Faults may be too rare for the desired risk claim.** Unlimited developers cannot manufacture representative independent failures. Response: extend observation where possible, disclose uncertainty, and restrict the domain or claim. Do not substitute more seeds or mutants for independent production evidence.

**Semantic analysis may hit diminishing returns.** Reflection, generated code, and framework behavior can remain unresolved. Response: measure whether stronger resolution changes decisions, retain capability-specific fallback, and stop investing where cost exceeds benefit.

**A rich evidence store may become a maintenance burden.** Response: start with a minimum versioned record, reuse existing history/export contracts, and demand a concrete consumer before adding a new entity or relation.

**The agent workflow may encourage metric gaming.** An agent might narrow declared obligations, edit tests, or present old observations. Response: bind obligations to policy and snapshot, preserve changed-test visibility, and keep authority outside the agent's free-text account. These are software-validation semantics, not an expansion into security scope.

**The IDE could consume the project.** Response: maintain CLI/API parity for essential workflows and keep analysis out of TypeScript. Build the workspace only after evidence contracts exist.

**The program could overtake the FYP.** Response: keep the current report defensible as its own deliverable, separate new experiments, and require explicit phase approval. A twelve-month platform vision does not justify delaying existing research closure.

## Three acceptable end states

**Minimum worthwhile result:** CodeDNA becomes a robust local evidence workbench with dependable recovery, traceable decisions, stronger Java mappings, honest unchecked-test visibility, and agent contracts. Statistical selection stays conservative. This is still a substantial improvement.

**Strong result:** observation-aware policies demonstrate useful total-cost savings within a clearly bounded Java domain, with independent or prospective confirmation appropriate to the claim. Developers can inspect and replay why a plan was accepted or refused.

**Moonshot result:** a developer or agent can make a substantial change and CodeDNA continuously assembles the smallest empirically justified validation plan, adapts as real observations arrive, repairs its own evidence gaps through costed audits, and emits a portable, verifiable acceptance record. It becomes the common evidence layer across editing, CI, and agent workflows.

Even in the moonshot state, passing tests is not proof of universal correctness. The breakthrough is making the boundary between observation, estimate, assumption, and unknown operationally useful.

## The proposed next review

Review the destination first: should CodeDNA become this evidence engine, and should observation-aware validation be its main research expansion? Then review Phase 0 and its boundaries against the current D-076/D-077 checkpoint.

Once a phase is approved, implement only that phase, produce its artifacts and actual validation results, update the completion record, and review the next gate. If new evidence changes the plan, version the proposal and explain the change. Do not silently convert this document into permission to execute all twelve months.

**Implementation status at writing: none of the proposed moonshot work was implemented by creating this file.**

---

## Revision 2 — Behavioral change laboratory: the revised moonshot

**Added:** 27 October 2026. **Status:** planning only; no implementation begun.

### Why this revision exists

The owner correctly challenged the original proposal: much of its vision is already CodeDNA's purpose, and several proposed foundations already exist or are under active development. Change-impact analysis, dependency explanations, regression-test selection, calibrated risk and fallback, recorded execution, replay, evidence export, and the agent brake are existing capabilities. Observation-isolated evaluation is already part of the D-076 work. Improving their integration, provenance, semantics, and recovery is valuable, but presenting that as a wholly new moonshot overstated the difference.

The entire original proposal above is preserved unchanged as the **Version 1 maturation plan**. It remains useful as a menu of engineering improvements. This appended revision replaces its headline destination for the moonshot discussion; it does not replace the active roadmap or authorize either plan's implementation. The two twelve-month schedules are alternatives, not twenty-four months of cumulative commitments.

The revised destination is:

> **CodeDNA becomes a behavioral change laboratory: it discovers how two versions of a system behave differently, constructs concrete examples of unintended differences, and helps produce and validate a repair.**

The central leap is from choosing existing validation to discovering missing behavioral evidence. Instead of stopping at “these tests are relevant,” CodeDNA should be able to say: “Here is an input and execution scenario where the old and new versions differ; here is the smallest reproducer we found; here is the evidence connecting that difference to the change; and here is whether a candidate repair resolves it without violating the other checked obligations.”

This is a proposed product and research direction. It is not a claim of worldwide novelty or that its individual techniques are new. Any eventual novelty claim needs a dedicated literature and prior-system review before research commitments are frozen.

### What changes from Version 1

| Dimension | Version 1 emphasis | Revised moonshot |
|---|---|---|
| Main question | Which validation evidence should we collect next? | What behavior did this change alter that existing validation fails to expose? |
| Main output | An explainable validation plan and acceptance record | A reproducible behavioral difference, its classification, and checked repair evidence |
| Existing tests | Primarily select, schedule, execute, and audit them | Reuse them as seeds and obligations while generating distinguishing scenarios |
| Code graph | Explain impact and support selection | Focus behavioral exploration and connect observed differences to changed components |
| Generated tests | Optional late-stage assistance | A core output: minimized executable reproducers with explicit oracle provenance |
| Agent brake | Enforce snapshot-bound check obligations | Also require agents to address discovered counterexamples and revalidate after repairs |
| Main scientific risk | Selection bias and partial feedback | Discovering meaningful differences despite weak oracles, nondeterminism, and enormous search spaces |
| Role of the old plan | The proposed destination | Supporting infrastructure, adopted only where the revised experiment needs it |

Observation-aware selection remains important and continues under its existing protocol. It is no longer presented as a newly invented moonshot. The revised program can use conservative full-suite validation while its behavioral exploration remains experimental.

### The flagship experience

A developer or agent changes synchronization in a Java connection pool. All existing tests pass. CodeDNA uses the changed declarations and relevant state transitions to choose a bounded exploration region. It executes base and changed revisions under controlled inputs and schedules.

The aspirational result is a schedule where the base version completes but the changed version leaves one caller unable to acquire a connection after another caller returns it. The laboratory stores the schedule, operation sequence, relevant environment, and observations. It reruns the scenario to distinguish a repeatable divergence from a one-off timeout, then minimizes the operation sequence and participating threads while preserving the observed difference.

The developer receives a small regression test or replay fixture, the event traces, and a ranked explanation of where the executions diverged. An agent proposes a repair in an isolated branch or disposable workspace only after that work is authorized. CodeDNA reruns the counterexample, nearby variants, and the existing regression obligations. Any further code edit makes affected evidence stale.

This example is a target demonstration, not an existing capability or a promised result. General deterministic replay of arbitrary JVM concurrency is outside the initial supported scope. Begin with a controlled fixture and supported scheduling hooks; disclose uninstrumented native code, unsupported synchronization, and environment behavior.

### Capability 1: candidate behavioral contracts

Construct reviewable hypotheses about intended behavior from existing assertions, API declarations, documentation, explicit requirements, and observed execution. Examples include order preservation, idempotence, transaction boundaries, resource release, exception compatibility, and permitted state transitions.

Every contract needs provenance and status. Distinguish an explicit requirement from a test-encoded expectation, an invariant observed only on sampled runs, and a model-generated suggestion. Contradictory sources should appear as a disagreement to resolve, rather than being silently merged into a confident oracle.

The base revision is a reference, not absolute truth. A change may intentionally fix its behavior. Differential execution therefore first establishes a difference; calling that difference a regression requires an applicable requirement or reviewed expectation. Record classifications such as intended difference, likely regression pending review, confirmed obligation violation, environmental mismatch, and unresolved.

Changes to existing tests and contracts must remain visible. A repair cannot make its counterexample disappear simply by deleting the obligation or weakening an assertion without explicit review.

### Capability 2: matched execution of base and changed versions

Build paired execution capsules containing revision identity, toolchain, dependencies, configuration, fixtures, randomness controls, and permitted environmental interactions. Execute the same scenario against each revision and compare declared observations: return values, exception categories, observable event sequences, persisted state, and selected external interactions.

Comparison needs typed normalization rules. Temporary paths, timestamps, ordering, and generated identifiers can create noise, but erasing them indiscriminately can erase a real regression. Version every normalizer, state its rationale, retain raw local observations where permitted, and measure its false-positive and missed-difference behavior.

Use recorded or simulated dependencies where appropriate, with their limits disclosed. A recording cannot establish correctness for live services or unseen responses. Where a faithful paired environment cannot be constructed, return an unsupported or inconclusive result rather than interpreting mismatched executions as a code defect.

All execution remains behind the project's explicit build authorization. The proposal grants no permission to run arbitrary repositories, access production systems, copy private datasets, or record user traffic.

### Capability 3: generate distinguishing scenarios

Use change-impact information to direct a bounded search over inputs, operation sequences, configuration combinations, and later supported thread schedules. Start with deterministic, inspectable generators: boundary values, sequences derived from existing tests, state-machine transitions, and property-based exploration. Consider constraint-based methods or model-assisted proposals only where simpler methods leave a measured gap.

The search objective is an observable divergence or obligation violation with a reproducible witness. It is not maximum coverage alone. Coverage is a steering signal; touching changed code does not establish that the change was meaningfully checked.

Treat all budgets as explicit: CPU time, wall time, executions, instrumentation overhead, memory, and replay storage. Keep a local bounded mode on ordinary laptops. Larger optional experiment workers may accelerate exploration, but they do not become a dependency of ordinary CodeDNA analysis.

Distinguish outcomes: a witness was found; an obligation was violated; a difference needs classification; no witness was found within the budget; the environment prevented comparison. “No witness found” must never become “the versions are equivalent.”

### Capability 4: minimize and explain a counterexample

Reduce inputs, operation sequences, configuration, schedules, and fixtures while preserving a specified divergence predicate. The output should include the original witness, minimized witness, reduction steps, reproduction results, and any required environmental assumptions.

Minimization should preserve the kind of difference being investigated. Reducing a wrong-result example into a crash does not necessarily preserve the original defect. For flaky observations, use a declared repeated-run rule and report reproduction frequency. Avoid claiming a globally smallest example; report the reduction method and the local minimum reached.

Connect the witness to source through observed trace alignment and the existing impact graph. Rank candidate explanations, clearly separating observed divergence from inferred causation. A nearby changed line is not automatically the cause. Controlled candidate reversions can strengthen an explanation where feasible, but interactions among changes can prevent a unique attribution.

The useful deliverable is a small executable reproducer a developer can inspect and rerun outside the IDE, plus enough evidence to understand why CodeDNA raised it.

### Capability 5: explore and validate repairs

Offer repair proposals after a concrete obligation violation or reviewed unintended difference exists. Keep proposal generation separate from evaluation. A proposed patch must satisfy the minimized reproducer, the original scenario, held-out related scenarios, and the existing required regression checks for the changed snapshot.

Reserve evaluation scenarios that the repair generator cannot inspect while proposing candidates. Otherwise the system can overfit the exact visible witness. Disclose the candidate budget and count unsuccessful repair attempts in cost. Test deletion, broad exception suppression, constant returns, and other ways to satisfy a narrow witness must be checked against broader obligations.

Call the result a **validated candidate repair within recorded checks**, not a proven-correct repair. Human approval remains separate from execution evidence; no automatic merge, release, or deployment is implied.

### Capability 6: reusable behavioral models and change previews

Accumulate versioned, bounded models of component behavior from reviewed contracts and execution observations. Models might describe API state transitions, permitted event orderings, output relationships, or resource-lifecycle obligations. Maintain their applicability domain, counterexamples, and invalidation conditions.

The long-term experience is a developer exploring a proposed API or refactor and asking which previously observed behaviors or contracts it could violate. Static predictions guide experiments; actual execution supplies the witness. A learned model is an approximation and must not silently replace execution evidence.

This is the most speculative layer. It should earn its place by finding useful witnesses faster or identifying obligations that simpler search misses. If it adds explanation without measurable discovery value, keep it an optional aid rather than a product gate.

### An architecture that extends CodeDNA

Reuse the current change extractor, language plugins, graph, history, execution boundaries, evidence export, and brake. Introduce only the minimum additional contracts required by a concrete experiment:

- **Scenario:** inputs, operation sequence, fixtures, environmental controls, and applicable contract references.
- **Paired observation:** base/head identities, environment fingerprints, actual results, normalization rules, and comparison completeness.
- **Behavioral witness:** a reproducible difference or obligation violation, classification status, and supporting observations.
- **Reduction record:** the preserved divergence predicate, candidate reductions, and resulting reproducer.
- **Repair evaluation:** patch identity, visible and held-out checks, candidate costs, outcomes, and remaining unknowns.

These are proposed data concepts, not approved packages or APIs. Keep language-specific instrumentation behind plugins and decision semantics in the Python core. The IDE presents the same records consumed by CLI and MCP. Do not build another history database or agent-specific analysis engine merely to accommodate the new vocabulary.

Use Version 1's recovery, provenance, and operation ideas when needed by these experiments. Defer unrelated workspace redesign and platform expansion. A successful first behavioral witness is more valuable than a year of infrastructure built in anticipation of it.

### Revised twelve-month sequence

This schedule replaces the original moonshot schedule for planning discussion. Each month is a proposed allocation after explicit program approval. Work proceeds one phase at a time, with review before advancing; the current Java/FYP checkpoint remains first.

| Phase | Allocation | Concrete deliverable and exit gate |
|---|---|---|
| R0: baseline and problem definition | Month 1 | Complete/review the active checkpoint; inspect prior approaches; choose one bounded Java behavior domain; freeze benchmark provenance, comparison semantics, execution permissions, and baseline methods. |
| R1: paired execution | Month 2 | Reproduce known behavioral differences between base/head in offline fixtures; detect environment mismatch; record exact scenarios and observations without claiming defect classification. |
| R2: contract and oracle handling | Month 3 | Represent explicit, inferred, and suggested contracts separately; demonstrate intended-change and ambiguous-difference cases; require a justified oracle before confirming regression. |
| R3: directed scenario search | Month 4 | Find previously hidden witnesses within a fixed budget on a development cohort; compare against existing tests, untargeted generation, and simple change-directed methods. |
| R4: counterexample reduction | Month 5 | Export inspectable reproducers; preserve the original divergence predicate; measure size reduction, reproduction reliability, and total reduction cost. |
| R5: trace-based diagnosis | Month 6 | Link observations to changed components; evaluate ranked attribution separately from witness discovery; preserve uncertain and multi-cause explanations. |
| R6: controlled concurrency | Month 7 | Demonstrate bounded schedule exploration/replay on explicitly supported Java fixtures; report nondeterministic and unsupported cases; do not promise arbitrary JVM replay. |
| R7: repair proposals | Month 8 | Evaluate authorized candidate patches against original witnesses, related cases, hidden checks, and current regression obligations; expose overfitting and unsuccessful candidates. |
| R8: behavioral model reuse | Month 9 | Test whether retained state/contract models reduce time to a useful witness on later held-out changes; retain simpler search if models do not help. |
| R9: developer and agent workflow | Month 10 | End-to-end inspect difference, classify intent, export reproducer, propose repair, revalidate, and invalidate after another edit through the existing IDE/API/MCP paths. |
| R10: independent evaluation | Month 11 | Run the frozen confirmatory evaluation on held-out projects or prospective changes; report all exclusions, costs, ambiguous cases, and failed hypotheses. |
| R11: hardening and final demonstration | Month 12 | Deliver a bounded local laboratory, exact reproduction artifacts, final research claims, and later distribution/clean-machine evidence where authorized; keep speculative layers experimental. |

The concurrency and behavioral-model phases are stretch branches. If deterministic paired execution, oracle handling, or reproduction reliability is inadequate, spend those allocations fixing the earlier layer. Do not hide a failed prerequisite by moving to a more impressive demonstration.

### Evaluation that could justify the ambition

Freeze the definition of a useful discovery: an executable witness of an adjudicated unintended difference, or a violation of an explicit obligation, that the existing test baseline failed to expose under the stated conditions. Report raw differences separately from confirmed regressions.

Measure discovery rate, time and compute to first useful witness, false alarms per investigated change, ambiguous-result rate, reproducibility, reduction quality, diagnosis accuracy, and developer effort. For repair, measure candidates that generalize to held-out checks, not merely those that pass the shown reproducer. Include environment setup, failed builds, instrumentation, exploration, minimization, and human classification effort in cost.

Use real historical regression/fix pairs when usable, checking chronology and dataset construction. The regression fix or associated test must not leak into discovery or repair generation when it is reserved as evaluation truth. Synthetic faults and mutants can stress mechanisms, but remain a separate population. Do not present them as equivalent to independent production regressions.

Compare with existing tests alone, simple untargeted generation, simple diff-directed generation, and applicable reproducible specialist methods selected during the prior-work review. Hold budgets comparable and disclose unavailable baselines. Ablate graph guidance, inferred contracts, minimization, and retained behavioral models to identify which additions actually matter.

Freeze numeric success thresholds after Phase R0 establishes baseline feasibility and before confirmatory outcomes are examined. Suitable stretch targets to investigate include finding useful new witnesses on a substantial minority of eligible missed-regression cases and materially reducing time to a reproducible example. Neither target is an achieved result. Publish the denominator: supported, buildable, reproducible cases may be a narrow fraction of the original candidate population.

Claims must remain distinct: “found a difference,” “found a regression,” “localized the cause,” and “validated a repair” require different evidence. A passing bounded search cannot establish behavioral equivalence. Statistical test-selection risk estimates also cannot be transplanted onto behavioral-search completeness.

### Failure modes and deliberate limits

**The oracle may be missing.** Old and new behavior differ, but intention is unclear. Preserve the witness and ask for classification when necessary; do not invent requirements from the old implementation.

**The environment may dominate the observation.** Time, databases, services, randomness, and native behavior can overwhelm paired execution. Bound the supported environment, retain mismatch diagnostics, and narrow the claim.

**Exploration may not scale.** Inputs, state transitions, and schedules grow combinatorially. Measure marginal discovery value per cost, focus on changed boundaries, and report budget exhaustion honestly.

**Generated repair and generated tests may share the same mistake.** Use independent obligations and held-out scenarios; retain the original regression suite. More generated assertions do not automatically provide independent evidence.

**The system may find noisy differences developers do not care about.** Evaluate usefulness and classification burden, rather than optimizing the count of differences alone.

**The vision may distract from finishing CodeDNA.** Keep the existing FYP contribution and current engineering obligations independent. No implementation starts merely because this revision is written. New dependencies, experiments, execution, and publication still follow the existing rules.

### The revised success picture

The minimum worthwhile result is a reliable Java paired-execution laboratory that discovers and minimizes useful behavioral differences in a clearly bounded domain. A strong result adds change-directed discovery, defensible regression classification, and substantially faster diagnosis. The full moonshot closes the loop: discover a hidden behavioral regression, produce a small reproducer, help create a repair, and validate that candidate against independent obligations through CodeDNA's existing agent brake.

The next review should choose the first bounded behavioral domain and assess R0. The original document remains intact above so both proposals, the owner's criticism, and the reason for this change remain visible.

**Revision status: documentation appended only. No behavioral laboratory, new search engine, repair system, experiment, or implementation phase was started.**
