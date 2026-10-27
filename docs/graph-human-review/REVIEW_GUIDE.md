# How to label the graph edges yourself

You or your teammate can be the human reviewer. Work independently of the old
AI correctness labels. Ideally label separately before discussing disagreements.
Record reviewer initials/date privately in your submitted notes; report the
procedure honestly rather than calling it expert validation.

1. Make a working copy of sample-40.csv and open it in Excel or a text editor.
2. Use SOURCE_LINKS.md to open the matching project/original_row. Links pin the
   exact commit, not today's branch. Read the evidence line, imports, enclosing
   class and target definition. Follow other source files when needed.
3. Interpret source as the type that has a dependency, target as the referenced
   type, and kind as the claimed relationship. You are checking a source-level
   relationship, not proving that a changed method will break a test.
4. Fill human_label with exactly correct, incorrect or unclear. Fill human_note
   with a short reason and any supporting file/line. Do not edit the original
   row number, project, edge or evidence fields.
5. correct: the claimed target and relationship are supported by the source and
   Java name rules. An import/reference must resolve to that target; matching
   words alone is insufficient.
6. incorrect: the target is wrong, the relationship is absent, or the reference
   resolves to another type. Explain what the code actually shows.
7. unclear: context is insufficient, resolution is ambiguous, a link cannot be
   inspected, or you cannot judge confidently. Explain why. Never guess to
   produce a perfect score.
8. The confidence column is CodeDNA's claim, not the answer. Check confirmed
   edges as carefully as heuristic ones. A valid heuristic edge is still not a
   guarantee of runtime influence.
9. Finish all 40 without viewing the previous AI labels. Keep your original
   completed copy. Then provide it for scoring against the frozen original rows.

For example, a literal extends clause supports an inheritance edge only if its
base name resolves to the reported target. A class with the same simple name in
another package does not establish that edge. This is an illustration, not an
answer to a sampled row.

Afterwards we can compute human agreement, count unclear/disputed edges and
write up disagreements. Cohen's kappa may be undefined when every label from
both reviewers is identical. Do not fabricate a number in that case. Human
labels supplement the existing study; they do not change its original outputs.
