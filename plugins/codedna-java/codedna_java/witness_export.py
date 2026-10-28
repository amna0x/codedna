"""Export deliberately selected source and a standalone JDK-only reproducer."""
from hashlib import sha256
import json

REPRODUCER = r'''import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import javax.tools.ToolProvider;

/** Reproduces an observation. Neither version is asserted to be correct. */
public final class ReproduceDifference {
  static final String TYPE = @@TYPE@@, METHOD = @@METHOD@@, FILE = @@FILE@@;
  static final int INPUT = @@INPUT@@, EXPECTED_BASE = @@BASE@@, EXPECTED_HEAD = @@HEAD@@;
  static void verify(Path file, String expected) throws Exception {
    String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    if (!actual.equals(expected)) throw new IllegalStateException("Source fingerprint differs: " + file);
  }
  static int run(Path classes, Path cwd) throws Exception {
    String suffix = System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("win") ? ".exe" : "";
    String token = "CODEDNA_REPRO_" + UUID.randomUUID() + ":";
    Process p = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin", "java"+suffix).toString(),
        "-Xmx64m", "-Xss256k", "-cp", classes.toString(), "CodeDNABehaviorProbe", TYPE, METHOD,
        Integer.toString(INPUT), token).directory(cwd.toFile()).redirectErrorStream(true).start();
    ExecutorService reader = Executors.newSingleThreadExecutor();
    Future<byte[]> bytes = reader.submit(() -> p.getInputStream().readNBytes(65537));
    try {
      if (!p.waitFor(5, TimeUnit.SECONDS)) throw new IllegalStateException("Reproduction timed out");
      byte[] output = bytes.get(1, TimeUnit.SECONDS);
      if (p.exitValue()!=0 || output.length>65536) throw new IllegalStateException("Incomplete reproduction output");
      List<String> values = new String(output, StandardCharsets.UTF_8).lines()
          .filter(line -> line.startsWith(token+"value:")).toList();
      if (values.size()!=1) throw new IllegalStateException("No unique normal int observation");
      return Integer.parseInt(values.get(0).substring((token+"value:").length()));
    } finally {
      p.toHandle().descendants().forEach(child -> child.destroyForcibly());
      p.destroyForcibly(); p.getInputStream().close(); reader.shutdownNow();
    }
  }
  public static void main(String[] args) throws Exception {
    var compiler = ToolProvider.getSystemJavaCompiler();
    if (compiler==null) throw new IllegalStateException("Use JDK 17+, not a standalone JRE");
    Path root = Path.of("").toAbsolutePath();
    Path harness = root.resolve("CodeDNABehaviorProbe.java");
    verify(root.resolve("base").resolve(FILE), @@BASE_SHA@@);
    verify(root.resolve("head").resolve(FILE), @@HEAD_SHA@@);
    verify(harness, @@HARNESS_SHA@@);
    Path work = Files.createTempDirectory("codedna-reproduce-");
    Path empty = Files.createDirectory(work.resolve("empty"));
    int[] observed = new int[2];
    String[] versions = {"base", "head"};
    for (int i=0; i<versions.length; i++) {
      Path classes = Files.createDirectory(work.resolve(versions[i]));
      int code = compiler.run(null, null, null, "-proc:none", "-classpath", empty.toString(),
          "-sourcepath", empty.toString(), "-d", classes.toString(),
          root.resolve(versions[i]).resolve(FILE).toString(), harness.toString());
      if (code!=0) throw new IllegalStateException("Cannot compile the self-contained version " + versions[i]);
      observed[i] = run(classes, work);
    }
    System.out.printf("input=%d base=%d head=%d%n", INPUT, observed[0], observed[1]);
    if (observed[0]!=EXPECTED_BASE || observed[1]!=EXPECTED_HEAD || observed[0]==observed[1])
      throw new IllegalStateException("The recorded difference was not reproduced");
    System.out.println("Recorded behavioral difference reproduced. Base is not an oracle.");
    System.out.println("Temporary compiled files: " + work);
  }
}
'''


def export_reproducer(output, basename, sources, symbol, witness, hashes, harness):
    class_name, method = symbol.split('#')
    method = method[:-5]  # validated '(int)' suffix
    if witness['base']['kind'] != 'value' or witness['head']['kind'] != 'value':
        raise ValueError('a normal int-return witness is required for this reproducer')
    files = {}

    def write(name, raw):
        with (output/name).open('xb') as stream:
            stream.write(raw)
        files[name] = sha256(raw).hexdigest()

    for label, source in zip(('base', 'head'), sources):
        (output/label).mkdir()
        write(label+'/'+basename, source)
    write('CodeDNABehaviorProbe.java', harness.encode('utf-8'))
    values = {'TYPE': json.dumps(class_name), 'METHOD': json.dumps(method),
              'FILE': json.dumps(basename), 'INPUT': str(witness['input']),
              'BASE': str(witness['base']['value']), 'HEAD': str(witness['head']['value']),
              'BASE_SHA': json.dumps(hashes['base']), 'HEAD_SHA': json.dumps(hashes['head']),
              'HARNESS_SHA': json.dumps(files['CodeDNABehaviorProbe.java'])}
    program = REPRODUCER
    for key, value in values.items():
        program = program.replace('@@'+key+'@@', value)
    if '@@' in program:
        raise ValueError('unresolved reproducer template field')
    write('ReproduceDifference.java', program.encode('utf-8'))
    readme = f'''# Observed Java behavioral difference

Symbol: `{symbol}`. Input: `{witness['input']}`.
Observed base result: `{witness['base']['value']}`.
Observed head result: `{witness['head']['value']}`.

This records unequal normal return values. Base is not an oracle. An applicable
expectation is needed to classify this difference as a regression. It does not
validate skip risk, prove equivalence or remove any existing required test.

This folder contains the ENTIRE deliberately selected Java source file from
each version, including other code in that file. Review source and report before
sharing. No original checkout is modified by compilation here. Execute only
trusted project code. The generated reproducer is ordinary Java, not a sandbox.

From this folder with JDK 17+ (no CodeDNA, Python, Maven or external libraries):

```text
javac -proc:none ReproduceDifference.java
java -cp . ReproduceDifference
```

The program verifies source/harness fingerprints, compiles self-contained
versions with annotation processing disabled, and runs a fresh JVM for each.
It requires the recorded pair exactly; a changed, failed or timed-out observation
does not pass reproduction. Compiled class files are left in the reported OS
temporary directory. This one reproduction run does not prove general determinism.
'''
    write('README.md', readme.encode('utf-8'))
    return {'files_sha256': files, 'entrypoint': 'ReproduceDifference.java',
            'requires': 'JDK 17+; explicitly trusted selected source',
            'disclosure': 'Includes the entire chosen base/head source file. Review before sharing.'}
