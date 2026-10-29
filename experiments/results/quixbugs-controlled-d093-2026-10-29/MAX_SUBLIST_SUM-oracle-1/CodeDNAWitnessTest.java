import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

// Review the supplied requirement before adding this draft to the project.
// Run only with trusted project code and its JUnit 5 dependencies.
public final class CodeDNAWitnessTest {
  @Test void suppliedRequirement() throws Exception {
    assertEquals(5, java_programs.MAX_SUBLIST_SUM.max_sublist_sum(new int[]{4,-5,2,1,-1,3}), "Published QuixBugs testcase expectation");
  }
}
