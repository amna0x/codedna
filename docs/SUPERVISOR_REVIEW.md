# Supervisor review pack

Status: prepared for review; no approval is claimed.
Read REPORT_ABSTRACT.md, REPORT_ASSEMBLED.md, RELATED_WORK_COMPARISON.md,
NOVELTY_REVIEW_2026-10-27.md and BLUEPRINT_COMPLETION.md.

## Proposed thesis claim

CodeDNA implements and evaluates an inspectable regression-testing brake that
combines change-impact analysis, target-project-audited stopping and conservative
fallback. The contribution concerns the decision pipeline and its measured
tradeoffs, not superior ML ranking or a universal safety guarantee.

## Findings that must remain visible

- Nine-project B10 confirmation: no meaningful safety advantage over the
  matched history rule; failing-test recall is lower.
- B12f: 95% safety on eight of nine projects, but a safety/time tradeoff against
  the conservative product; Cloudify misses the target.
- B13f exploratory; attempted PTS equal-cost match unsuccessful.
- The existing retrospective replay sees stored prior outcomes. Closed-loop
  partial-feedback performance remains unvalidated.
- Structural agent-patch results do not establish that agents write better code.
- Graph labels are AI-made until an independent student completes the review.

## Questions for the supervisor

1. Is this incremental method/system contribution sufficient for the FYP?
2. Is the primary outcome omitted-failure safety, build escape, or both?
3. Are the stated negative results and statistical limitations presented fairly?
4. Is a new partial-feedback study required, or better left as future work?
5. Does the product demonstration adequately show the original project scope?
6. Is multi-language expansion appropriate after current acceptance checks?
7. What university template, submission date and demonstration evidence apply?

Record reviewer, date, decisions and requested changes below after a real review.
No automated message has been sent to the supervisor.
