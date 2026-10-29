import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import javax.tools.ToolProvider;

/** Reproduces an observation. Neither version is asserted to be correct. */
public final class ReproduceDifference {
  static final String TYPE = "leetcode.medium.OnlineStockSpan", METHOD = "calculateSpans", FILE = "OnlineStockSpan.java";
  static final String INPUT = "0,0", INPUT_TYPES = "int[]";
  static final String DISPLAY_INPUT = "[0, 0]";
  static final String EXPECTED_BASE = "[1,2]", EXPECTED_HEAD = "[1,1]";
  static void verify(Path file, String expected) throws Exception {
    String actual = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
    if (!actual.equals(expected)) throw new IllegalStateException("Source fingerprint differs: " + file);
  }
  static String run(Path classes, Path cwd) throws Exception {
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
      return values.get(0).substring((token+"value:").length());
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
    verify(root.resolve("base").resolve(FILE), "8804a64e378661e9a4735ed15765dd907af9d20adad3bec95546d754e5bdc388");
    verify(root.resolve("head").resolve(FILE), "9caf29080886dd2eafd8c5043fa2b41acf0c4f62d79e20528a0035297242bf39");
    verify(harness, "aa85bf98eb72455f946d6b6b7d8bc024d2752481c37a099248b60068c84e03e7");
    Path work = Files.createTempDirectory("codedna-reproduce-");
    Path empty = Files.createDirectory(work.resolve("empty"));
    String[] observed = new String[2];
    String[] versions = {"base", "head"};
    for (int i=0; i<versions.length; i++) {
      Path classes = Files.createDirectory(work.resolve(versions[i]));
      int code = compiler.run(null, null, null, "-encoding", "UTF-8", "-proc:none", "-classpath", empty.toString(),
          "-sourcepath", empty.toString(), "-d", classes.toString(),
          root.resolve(versions[i]).resolve(FILE).toString(), harness.toString());
      if (code!=0) throw new IllegalStateException("Cannot compile the self-contained version " + versions[i]);
      observed[i] = run(classes, work);
    }
    System.out.printf("input=%s base=%s head=%s%n", DISPLAY_INPUT, observed[0], observed[1]);
    if (!observed[0].equals(EXPECTED_BASE) || !observed[1].equals(EXPECTED_HEAD) || observed[0].equals(observed[1]))
      throw new IllegalStateException("The recorded difference was not reproduced");
    System.out.println("Recorded behavioral difference reproduced. Base is not an oracle.");
    System.out.println("Temporary compiled files: " + work);
  }
}
