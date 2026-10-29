# Observed Java behavioral difference

Symbol: `java_programs.LEVENSHTEIN#levenshtein(String,String)`. Input: `['electron', 'neutron']`.
Observed base result: `8`.
Observed head result: `3`.

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

## Supplied expectation and JUnit draft

SUPPLIED_EXPECTATION.json records a caller-supplied requirement; CodeDNA has not
independently verified that requirement. CodeDNAWitnessTest.java asserts that
supplied input/output, not the base result. Review it before copying it to a
trusted JUnit 5 project. It is not installed or executed automatically.
The supplied input counts toward the search budget in both generation modes.
The reduced witness may use another input; see report.json for whether the
supplied input had confirmed observations. This draft is separate from the
JDK-only difference reproducer and does not change required tests or skip risk.
