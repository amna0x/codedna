# Graph precision check (M2), 2026-10-25

**Question.** When CodeDNA's dependency graph draws an edge, is it right? And
which references to repository types does it miss?

## Projects and versions

| Project | Commit | Date |
|---|---|---|
| HikariCP (github.com/brettwooldridge/HikariCP) | a4d93f4f85517f90e632b795486d7102e933d7ff | 2026-06-15 |
| LittleProxy (github.com/adamfisk/LittleProxy) | 70edbe1c502d79449fb5ceb9d00cca6a0759d56f | 2017-09-25 |

Both are in the RTPTorrent study set. Graphs were built at type level
(`include_members=False`) by the code in this commit, after the fixes below.

## Method

1. `scripts/sample_graph_edges.py REPO --per-label 40 --seed 0` drew 40
   confirmed and 40 heuristic non-`contains` edges per project, each with one
   evidence `file:line` chosen at random, so 160 edges in total.
2. Each edge was labelled `correct` if the evidence line in the source type
   refers to the target type under Java's name rules (imports, same package,
   member types, inherited member types, `java.lang` shadowing), `incorrect`
   if it refers to something else, or `unclear` otherwise. The labeller read
   the evidence line and, where needed, the target's declaration and the
   file's imports in the source.
3. `scripts/score_graph_sample.py` computes precision with a two-sided 95 %
   Wilson interval.
4. Missed references (a recall check): every unresolved reference was put
   into one of four groups: `var`, a `java.lang` type (the JDK 21 list), a
   simple name declared as a type somewhere in the repository, or not in the
   repository. The third group was checked by hand. A plain-text search for
   `class|interface|enum|record NAME` in the sources caught types the graph
   does not model.

**Who labelled.** The labels were made by Claude, the AI assistant that
wrote this code, while reading the source. They should be spot-checked by a
student, for example 20 random rows per file, before the report relies on
them. The CSVs keep every row so that check is possible.

## Results

Precision (`combined-score.json`, `*-score.json`):

| Label | Correct / judged | Precision | 95 % Wilson |
|---|---|---|---|
| confirmed | 80 / 80 | 1.00 | [0.954, 1.00] |
| heuristic | 80 / 80 | 1.00 | [0.954, 1.00] |
| all | 160 / 160 | 1.00 | [0.977, 1.00] |

There were no incorrect or unclear rows. One HikariCP row (`HikariPool.this`)
is labelled `static_access`, but it is really a qualified `this`. The target
type is still right, so it counts as correct, with a note.

Heuristic edges are 56 of 676 dependency edges on HikariCP and 94 of 502 on
LittleProxy. Their sample covers most of HikariCP's heuristic edges.

**Missed references, before the fix** (HikariCP, 147 unresolved entries,
546 references):

| Group | Entries | References | Verdict |
|---|---|---|---|
| `var` (local type inference) | 27 | 260 | bug: not a type name |
| `java.lang` type missing from CodeDNA's short list | 26 | 32 | bug: JDK type counted as unknown |
| declared in the repository | 6 | 7 | missed edges: 3 via `import static T.*`, 3 inherited from a superclass |
| not in the repository | 88 | 247 | correct (library or JDK) |

Three more names are local classes declared inside test methods
(`BadConnection`, `Foo`, `Bar`). D-009 attributes local classes to the
enclosing member, so they are not graph types and stay unresolved.

The check also found one silent wrong resolution. In HikariCP's
`TestConnections.OverrideHandler`, `Override` means the enum inherited from
`SQLExceptionOverride`, not `java.lang.Override`; the code writes
`@java.lang.Override` for the annotation for that reason. Before the fix,
CodeDNA treated it as the JDK annotation.

**After the fix** (`graph-stats-*.json`):

| Project | Unresolved rate | Unresolved references | Dependency edges |
|---|---|---|---|
| HikariCP | 0.264 → 0.139 | 546 → 247 | 668 → 676 |
| LittleProxy | 0.103 → 0.070 | 112 → 76 | 479 → 502 |

After the fix, no unresolved name on either project is a type the graph
models. LittleProxy gained edges from member types inherited through generic
superclasses (`ProxyConnection<HttpRequest>`) and test base classes.

## Limits

- 160 edges from two projects; the intervals describe these projects only.
- The recall check sees only references the extractor records; a name the
  extractor never collects would be invisible to it. Method-level calls are
  not modelled (D-010).
- AI labels, not yet checked by a person (see above).
