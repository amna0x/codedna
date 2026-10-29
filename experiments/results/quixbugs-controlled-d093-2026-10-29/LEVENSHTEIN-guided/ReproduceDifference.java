import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import javax.tools.ToolProvider;

/** Reproduces an observation. Neither version is asserted to be correct. */
public final class ReproduceDifference {
  static final String TYPE = "java_programs.LEVENSHTEIN", METHOD = "levenshtein", FILE = "LEVENSHTEIN.java";
  static final String INPUT = "YQ==:YQ==", INPUT_TYPES = "String,String";
  static final String DISPLAY_INPUT = "[\"a\", \"a\"]";
  static final long EXPECTED_BASE = 1L, EXPECTED_HEAD = 0L;
  static void verify(Path file, String expected) throws Exception {
    String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    if (!actual.equals(expected)) throw new IllegalStateException("Source fingerprint differs: " + file);
  }
  static long run(Path classes, Path cwd) throws Exception {
    String suffix = System.getProperty("os.name").toLowerCase(Locale.ROOT).contains("win") ? ".exe" : "";
    String token = "CODEDNA_REPRO_" + UUID.randomUUID() + ":";
    Process p = new ProcessBuilder(Path.of(System.getProperty("java.home"), "bin", "java"+suffix).toString(),
        "-Xmx64m", "-Xss256k", "-Dfile.encoding=UTF-8", "-cp", classes.toString(), "CodeDNABehaviorProbe", TYPE, METHOD,
        INPUT, token, INPUT_TYPES).directory(cwd.toFile()).redirectErrorStream(true).start();
    ExecutorService reader = Executors.newSingleThreadExecutor();
    Future<byte[]> bytes = reader.submit(() -> p.getInputStream().readNBytes(65537));
    try {
      if (!p.waitFor(5, TimeUnit.SECONDS)) throw new IllegalStateException("Reproduction timed out");
      byte[] output = bytes.get(1, TimeUnit.SECONDS);
      if (p.exitValue()!=0 || output.length>65536) throw new IllegalStateException("Incomplete reproduction output");
      List<String> values = new String(output, StandardCharsets.UTF_8).lines()
          .filter(line -> line.startsWith(token+"value:")).toList();
      if (values.size()!=1) throw new IllegalStateException("No unique normal int observation");
      return Long.parseLong(values.get(0).substring((token+"value:").length()));
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
    verify(root.resolve("base").resolve(FILE), "ee1b7bc544156fbd475ea03e3b5e6b3e6edecae3f7de31e6ee0c647308f04ea0");
    verify(root.resolve("head").resolve(FILE), "694a68e7633c784d74871b5b9032b6bc093db285994a7df895474567b4b6175b");
    verify(harness, "aa85bf98eb72455f946d6b6b7d8bc024d2752481c37a099248b60068c84e03e7");
        verify(root.resolve("base/support/Node.java"), "f6c623fd51166f7a65f9691716e2f576b246a7b846415e3234e62904bf5b0c67");
    verify(root.resolve("base/support/WeightedEdge.java"), "eef70c3a26f05fbee735183154f41f751313155eb16d4980ba7589acacbcbb04");
    verify(root.resolve("head/support/Node.java"), "f6c623fd51166f7a65f9691716e2f576b246a7b846415e3234e62904bf5b0c67");
    verify(root.resolve("head/support/WeightedEdge.java"), "eef70c3a26f05fbee735183154f41f751313155eb16d4980ba7589acacbcbb04");
    Path work = Files.createTempDirectory("codedna-reproduce-");
    Path empty = Files.createDirectory(work.resolve("empty"));
    long[] observed = new long[2];
    String[] versions = {"base", "head"};
    for (int i=0; i<versions.length; i++) {
      Path classes = Files.createDirectory(work.resolve(versions[i]));
      var compile = new ArrayList<String>(List.of( "-encoding", "UTF-8", "-proc:none", "-classpath", empty.toString(),
          "-sourcepath", empty.toString(), "-d", classes.toString(),
          root.resolve(versions[i]).resolve(FILE).toString(), harness.toString()));
      compile.add(root.resolve(versions[i]).resolve("support/Node.java").toString());
      compile.add(root.resolve(versions[i]).resolve("support/WeightedEdge.java").toString());
      int code = compiler.run(null, null, null, compile.toArray(String[]::new));
      if (code!=0) throw new IllegalStateException("Cannot compile the self-contained version " + versions[i]);
      observed[i] = run(classes, work);
    }
    System.out.printf("input=%s base=%d head=%d%n", DISPLAY_INPUT, observed[0], observed[1]);
    if (observed[0]!=EXPECTED_BASE || observed[1]!=EXPECTED_HEAD || observed[0]==observed[1])
      throw new IllegalStateException("The recorded difference was not reproduced");
    System.out.println("Recorded behavioral difference reproduced. Base is not an oracle.");
    System.out.println("Temporary compiled files: " + work);
  }
}
