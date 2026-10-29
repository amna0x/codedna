import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

// Review the supplied requirement before adding this draft to the project.
// Run only with trusted project code and its JUnit 5 dependencies.
public final class CodeDNAWitnessTest {
  @Test void suppliedRequirement() throws Exception {
    assertEquals(3, java_programs.LEVENSHTEIN.levenshtein("electron", "neutron"), "Published QuixBugs testcase expectation");
  }
}
