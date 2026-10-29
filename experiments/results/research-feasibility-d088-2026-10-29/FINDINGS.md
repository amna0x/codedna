# D088 independent-study preparation and feasibility

This is not an effectiveness evaluation and contains no new success claim.

## Moonshot

Downloaded the pinned GitBug-Java metadata: 55 files, 85,611,832 bytes. Recorded
file hashes and deterministic repository-level selection in
`experiments/moonshot-real-bug-selection-d088.json`: six development repositories,
twelve held-out repositories. Held-out source/test outcomes have not been audited.

All six development cases contain published failing-to-passing test evidence.
The source-contract audit found zero changed, same-identity method candidates
meeting the current public static numeric-method contract. All selected changed
Java files were read successfully; zero source acquisition errors in the corrected
audit. An initial adapter passed strings to the byte-based parser; that diagnostic
is retained locally and is not an unsupported-program result.

This establishes a support-coverage bottleneck on this development sample, not
zero bug-detection accuracy across all Java software. No project code was executed,
no witness searches were run, and no fixed-version outputs were invented as oracles.
Signature eligibility alone would not have proved dependencies compile or that a
changed method causes the documented failure. Broader real-program support needs
development work before an honest held-out effectiveness test can be useful.

## AI brake

Inspected the public 3,016,466,104-byte LRTS ZIP by bounded HTTP byte ranges.
Downloaded only its metadata CSV: 20,592,181 bytes; selected member CRC and local
SHA256 verified. A total of 68,692,243 range bytes was needed in the metadata-fetch
invocation, mostly ZIP central-directory data. This is not whole-archive checksum
verification. The original 2.8 GiB archive was not downloaded in full.

ActiveMQ has 446 metadata suite-run rows, 391 distinct build-head SHAs: 426 rows
target main and 20 target release branches. This cannot fill the predefined 1,500
distinct-build window. Rows are PR builds; a common target branch does not prove
ancestry. No outcome-based project substitution, trained model, risk replay, or
measured speedup was performed. The candidate is infeasible for this protocol.

A later revised protocol must disclose this feasibility result and select its
cohort using outcome-blind availability/ancestry rules before reading policy
outcomes. It must not reduce safety gates to manufacture skipping opportunities.

## Validation gate

The existing D087 full Maven-inclusive suite is still running and has reported a
failure. Its position corresponds to the old test that required rejecting long
return values, now intentionally supported. The fixture was changed to an actually
unsupported double return; all five unsupported-signature checks then passed
(35 deselected, 10.19 seconds). Wait for the full traceback and final totals before
concluding this is the sole failure. Application source a30ce70 is unchanged.
Do not call the original invocation a clean pass. No new installer/push/merge.
