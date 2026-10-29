# Observed Java behavioral difference

Symbol: `leetcode.medium.OnlineStockSpan#calculateSpans(int[])`. Input: `[0, 0]`.
Observed base result: `[1, 2]`.
Observed head result: `[1, 1]`.

This records unequal normal return values. Base is not an oracle. An applicable
expectation is needed to classify this difference as a regression. It does not
validate skip risk, prove equivalence or remove any existing required test.

This folder contains the ENTIRE deliberately selected Java source file from
each version, including other code in that file. Review source and report before
sharing. No original checkout is modified by compilation here. Execute only
trusted project code. The generated reproducer is ordinary Java, not a sandbox.

From this folder with JDK 17+ (no CodeDNA, Python, Maven or external libraries):

```text
javac -encoding UTF-8 -proc:none ReproduceDifference.java
java -Dfile.encoding=UTF-8 -cp . ReproduceDifference
```

The program verifies source/harness fingerprints, compiles self-contained
versions as UTF-8 with annotation processing disabled, and runs a fresh JVM for
each with startup file.encoding=UTF-8. This controlled encoding may differ from
the original project runtime; observations apply to this explicit scenario.
It requires the recorded pair exactly; a changed, failed or timed-out observation
does not pass reproduction. Compiled class files are left in the reported OS
temporary directory. This one reproduction run does not prove general determinism.
