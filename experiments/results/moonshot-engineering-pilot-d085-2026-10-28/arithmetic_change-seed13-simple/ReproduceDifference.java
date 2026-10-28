import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import javax.tools.ToolProvider;

/** Reproduces an observation. Neither version is asserted to be correct. */
public final class ReproduceDifference {
  static final String TYPE = "example.Fee", METHOD = "fee", FILE = "Fee.java";
  static final int INPUT = 0, EXPECTED_BASE = 1, EXPECTED_HEAD = 2;
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
    verify(root.resolve("base").resolve(FILE), "146b5842c26ae214f3bbdda4193fbe3fd05dc0deaf6020755d84df06a2557856");
    verify(root.resolve("head").resolve(FILE), "7ec1f3b0b8e244e9c021834079dcaca1076ba7845479b147e955a6f17cc5ed22");
    verify(harness, "a78f4a777b74a96dacc936f45c7df648fd333355274a535df8466271d91410f0");
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
