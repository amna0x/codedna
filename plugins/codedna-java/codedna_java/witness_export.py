"""Export deliberately selected source and a standalone JDK-only reproducer."""
from hashlib import sha256
import json
import re
from codedna_java.witness_inputs import parameter_types, encode, java_arguments
from codedna_java.witness_values import canonical

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
        "-Xmx64m", "-Xss256k", "-Dfile.encoding=UTF-8", "-cp", classes.toString(), "CodeDNABehaviorProbe", TYPE, METHOD,
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
      int code = compiler.run(null, null, null, "-encoding", "UTF-8", "-proc:none", "-classpath", empty.toString(),
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


def export_reproducer(output, basename, sources, symbol, witness, hashes, harness, *, expectation=None, support=None, instance=False):
    class_name, method = symbol.split('#')
    method = method.split('(', 1)[0]
    types = parameter_types(symbol)
    if witness['base']['kind'] != 'value' or witness['head']['kind'] != 'value':
        raise ValueError('a normal int/long-return witness is required for this reproducer')
    files = {}

    def write(name, raw):
        with (output/name).open('xb') as stream:
            stream.write(raw)
        files[name] = sha256(raw).hexdigest()

    for label, source in zip(('base', 'head'), sources):
        (output/label).mkdir()
        write(label+'/'+basename, source)
    write('CodeDNABehaviorProbe.java', harness.encode('utf-8'))
    helper_names = []
    for label in ('base', 'head'):
        for file, raw in (support or {}).get(label, []):
            name = label+'/support/'+file
            (output/name).parent.mkdir(parents=True, exist_ok=True)
            write(name, raw)
            if label == 'base': helper_names.append('support/'+file)
    values = {'TYPE': json.dumps(class_name), 'METHOD': json.dumps(method),
              'FILE': json.dumps(basename), 'INPUT': str(witness['input']),
              'BASE': str(witness['base']['value'])+'L', 'HEAD': str(witness['head']['value'])+'L',
              'BASE_SHA': json.dumps(hashes['base']), 'HEAD_SHA': json.dumps(hashes['head']),
              'HARNESS_SHA': json.dumps(files['CodeDNABehaviorProbe.java'])}
    program = REPRODUCER
    if helper_names:
        checks = '\n'.join('    verify(root.resolve('+json.dumps(name)+'), '+json.dumps(digest)+');'
                            for name, digest in files.items() if '/support/' in name)
        program = program.replace('Path work = Files.createTempDirectory', checks+'\n    Path work = Files.createTempDirectory')
        additions = '\n'.join('      compile.add(root.resolve(versions[i]).resolve('+json.dumps(name)+').toString());'
                              for name in helper_names)
        program = program.replace('int code = compiler.run(null, null, null,',
                                  'var compile = new ArrayList<String>(List.of(')
        program = program.replace('harness.toString());\n      if (code!=0)',
            'harness.toString()));\n'+additions+'\n      int code = compiler.run(null, null, null, compile.toArray(String[]::new));\n      if (code!=0)')
    if types != ['int']:
        values['INPUT'] = json.dumps(encode(types, witness['input']))
        values['INPUT_TYPES'] = json.dumps(','.join(types))
        values['DISPLAY_INPUT'] = json.dumps(json.dumps(witness['input'], ensure_ascii=True))
        program = program.replace('static final int INPUT = @@INPUT@@, EXPECTED_BASE = @@BASE@@, EXPECTED_HEAD = @@HEAD@@;',
            'static final String INPUT = @@INPUT@@, INPUT_TYPES = @@INPUT_TYPES@@;\n'
            '  static final String DISPLAY_INPUT = @@DISPLAY_INPUT@@;\n'
            '  static final int EXPECTED_BASE = @@BASE@@, EXPECTED_HEAD = @@HEAD@@;')
        program = program.replace('Integer.toString(INPUT), token)', 'INPUT, token, INPUT_TYPES)')
        program = program.replace('"input=%d base=%d head=%d%n", INPUT', '"input=%s base=%d head=%d%n", DISPLAY_INPUT')
    def substitute(match):
        if match[1] not in values:
            raise ValueError('unresolved reproducer template field')
        return values[match[1]]
    program = program.replace('static final int INPUT = @@INPUT@@, EXPECTED_BASE = @@BASE@@, EXPECTED_HEAD = @@HEAD@@;',
        'static final int INPUT = @@INPUT@@;\n  static final long EXPECTED_BASE = @@BASE@@, EXPECTED_HEAD = @@HEAD@@;')
    program = program.replace('static final int EXPECTED_BASE =', 'static final long EXPECTED_BASE =')
    program = program.replace('static int run(', 'static long run(').replace('return Integer.parseInt(values.get(0)', 'return Long.parseLong(values.get(0)')
    program = program.replace('int[] observed = new int[2]', 'long[] observed = new long[2]')
    if any(isinstance(witness[label]['value'], list) for label in ('base', 'head')):
        values['BASE'] = json.dumps(canonical(witness['base']['value']))
        values['HEAD'] = json.dumps(canonical(witness['head']['value']))
        program = program.replace('static final long EXPECTED_BASE =', 'static final String EXPECTED_BASE =')
        program = program.replace('static long run(', 'static String run(')
        program = program.replace('return Long.parseLong(values.get(0).substring((token+"value:").length()));',
                                  'return values.get(0).substring((token+"value:").length());')
        program = program.replace('long[] observed = new long[2]', 'String[] observed = new String[2]')
        program = program.replace('base=%d head=%d', 'base=%s head=%s')
        program = program.replace('observed[0]!=EXPECTED_BASE || observed[1]!=EXPECTED_HEAD || observed[0]==observed[1]',
            '!observed[0].equals(EXPECTED_BASE) || !observed[1].equals(EXPECTED_HEAD) || observed[0].equals(observed[1])')
    # Substitute once: literal user inputs may themselves contain template markers.
    program = re.sub(r'@@([A-Z_]+)@@', substitute, program)
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
'''
    if expectation is not None:
        expected = expectation['expected']
        readme += '''
## Supplied expectation and JUnit draft

SUPPLIED_EXPECTATION.json records a caller-supplied requirement; CodeDNA has not
independently verified that requirement. CodeDNAWitnessTest.java asserts that
supplied input/output, not the base result. Review it before copying it to a
trusted JUnit 5 project. It is not installed or executed automatically.
The supplied input counts toward the search budget in both generation modes.
The reduced witness may use another input; see report.json for whether the
supplied input had confirmed observations. This draft is separate from the
JDK-only difference reproducer and does not change required tests or skip risk.
'''
    write('README.md', readme.encode('utf-8'))
    if expectation is not None:
        # The assertion comes from a supplied requirement, never the old output.
        draft = '''import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

// Review the supplied requirement before adding this draft to the project.
// Run only with trusted project code and its JUnit 5 dependencies.
public final class CodeDNAWitnessTest {
  @Test void suppliedRequirement() throws Exception {
    assertEquals(EXPECTED, TYPE.METHOD(INPUT), REQUIREMENT);
  }
}
'''
        if isinstance(expected, list):
            draft = draft.replace('assertEquals', 'assertArrayEquals')
            expected_java = 'new int[]{'+','.join(map(str, expected))+'}'
        else:
            expected_java = str(expected)+('L' if not -(2**31)<=expected<2**31 else '')
        replacements = {'EXPECTED': expected_java, 'TYPE': 'new '+class_name+'()' if instance else class_name,
                        'METHOD': method, 'INPUT': java_arguments(types, expectation['input']),
                        'REQUIREMENT': json.dumps(expectation['requirement'], ensure_ascii=True)}
        # Substitute the message last so its contents cannot become template code.
        draft = re.sub(r'\b(EXPECTED|TYPE|METHOD|INPUT|REQUIREMENT)\b',
                       lambda match: replacements[match.group()], draft)
        write('CodeDNAWitnessTest.java', draft.encode('utf-8'))
        write('SUPPLIED_EXPECTATION.json', (json.dumps(expectation, indent=2)+'\n').encode('utf-8'))
    return {'files_sha256': files, 'entrypoint': 'ReproduceDifference.java',
            'requires': 'JDK 17+; explicitly trusted selected source',
            'disclosure': 'Includes the entire chosen base/head source file. Review before sharing.'}
