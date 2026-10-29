# D091: larger independent-history screening and evaluation

Owner authorized larger-scale evaluation after the negative D090 evidence-floor
result. Keep D090/ActiveMQ findings immutable. Application stays a02d20f; no new
features or changed thresholds. The 780-test Maven-inclusive pass remains tied
to that application. Do not rerun it for research-only preparation scripts.

Before opening outcome labels, fix four LRTS targets and branches:
Hadoop/trunk, Hive/master, Jackrabbit Oak/trunk and Kafka/trunk. Repositories are
apache/hadoop, apache/hive, apache/jackrabbit-oak and apache/kafka. Metadata file
SHA256 must match the existing downloaded LRTS provenance. Project choice is
based on metadata availability, not policy success. Keep every project's result,
including unavailable, insufficient-history and failed preparations.

For each target, group exact heads and retain the earliest build and its jobs
as in D089. Sort by first build timestamp then SHA. Take the first 2,000 distinct
heads, or all if fewer. Below 500, record insufficient availability. Use 60/20/20
train/audit/evaluation, with floors on the first two. Do not extend windows after
observing misses. Do not replace any project with a favorable alternative.

Screen source ancestry with blobless depth-256 Git fetches (48 heads per batch).
Record unresolved shallow ancestry; count only proven, strictly earlier ancestors.
Use all selected heads to verify ancestry, without interpreting labels. Retain
download/identity errors. Fetch only matching raw compressed inventories using
HTTP ranges with a 256 MiB/project budget; no whole 3 GB archive download. Verify
member CRC, local SHA256, nested size bounds, class uniqueness and durations.
Keep raw failures and discrepancies. Do not claim no original skipped tests from
executed-class counts alone. No downloaded scripts are executed.

Freeze cohort manifests before inventory outcomes or model predictions are read.
Apply the live historical 50/25/25 split to each target's available prior ancestors
from the outer training/audit cohort. Before fitting, assess existing B10/CRC
minimum evidence at alpha 0.05. Insufficient evidence means full suites; never
lower thresholds or substitute guessed features. Cases that may pass these
necessary checks need actual frozen-model features/structural selection and audit
predictions; a feasible count is not approval to skip.

For eligible comparisons preserve B0 full suite, structural-only, existing simple
history ordering, B10 and CRC. Report every project's sample/failure denominators,
refusals, observed misses, selection ratio and historical duration estimates.
Prespecify any actual matched-execution subset before seeing its timings. New CI
builds require verified source/toolchain/build feasibility; do not run multi-hour
suites simply to decorate a result. Historical durations cannot establish elapsed
CI savings. Measure analysis/startup/audit cost when actually executed and disclose
unperformed comparisons. No favorable-result claim before evidence supports it.
