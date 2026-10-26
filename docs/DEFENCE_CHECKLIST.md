# Defence and offline demo checklist

## Ten-minute demonstration

1. Explain the problem: reduced testing saves work but can hide failures.
2. Open the demo in CodeDNA. Show Changes and a labelled impact path.
3. Show the full-suite recommendation when project evidence is insufficient.
4. Explain that Python/mixed projects currently have no validated risk model.
5. Show a saved history replay without rerunning completed studies.
6. Run the synthetic validated-history brake demo: partial selection, real
   failing test blocks, corrected implementation passes. Say the history is
   synthetic; it demonstrates integration, not research performance.
7. Show confirmatory results: B10 did not outperform the matched rule; the
   gated product saves modest recorded test time. CRC has a real tradeoff and
   Cloudify fails the target. Keep B10 default.
8. Explain that catching one failing test differs from retaining all failing
   tests, and that recorded test time is not CI wall time.
9. Show the plugin manager and distinguish analysis plugins from editor tools.
10. Close with limitations and planned improvements, not a universal guarantee.

## Before the demonstration

- Freeze a source revision and record installer checksum, bundle manifest and
  actual full-suite validation. Keep the previous working installer backup.
- Prepare all demo Git snapshots and cache Maven dependencies beforehand.
- Test the demo offline. Python execution needs a working project interpreter
  with pytest/dependencies; Java needs a JDK and the relevant build tool.
- Keep saved study reports, figures, screenshots and a copy of the guide local.
- Rehearse once and record a video. A prepared script is not a recorded video.
- Have the student complete docs/graph-human-review/sample-40.csv independently.
- Obtain supervisor feedback on the precise thesis claim and final report.

## Questions to rehearse

- Why use a model if history rules rank better? The model supplies a checked
  stopping estimate; superior ranking is not claimed.
- Does a passed brake prove the patch correct? No. It reports required test
  execution for an immutable snapshot, with explicit evidence limits.
- Why sometimes run everything? Unsupported or inadequate evidence must not be
  converted into an invented risk probability.
- Is this the first conformal test selector? No; related methods and tools exist.
- Is 95% safety guaranteed on the next change? No. Statistical assumptions,
  changing code, incomplete feedback and sampling uncertainty limit the claim.
