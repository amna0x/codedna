# Moonshot version — approved bounded scope

Owner approval: 2026-10-28. This selects the narrow recommendation, not the full
untracked MOONSHOT.md proposal. Finish current validation/performance work first.

Keep CodeDNA's existing purpose: validating a software change. Add one optional
Java capability which runs a deterministic scenario against base/head, records
an observable difference, and exports a reduced reproducer. A difference becomes
a regression only when an explicit applicable expectation justifies that label.
The base implementation is not automatically the oracle. No witness within a
budget does not establish equivalence. Use existing execution consent and brake.

Begin with one supported Java input/output domain and bounded inputs. Prefer
deterministic generators and existing tooling before paid AI calls or new major
dependencies. Evaluate change-guided against simple generation at equal budgets;
measure useful witnesses, false alarms, reproduction and reduction cost. Keep
historical/synthetic evidence separate. Verify prior systems before novelty claims.

No new IDE, database, language plugin, automatic repair, general concurrency
replay or learned behavioral model is approved by this scope. Keep it experimental
and separate from current statistical stopping claims. Existing FYP remains usable
if the pilot does not add measured value. Design the first pilot before coding it.
