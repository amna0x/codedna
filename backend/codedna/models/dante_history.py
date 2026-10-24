"""DANTE-H: independent history-score adaptation of the authors' artifact.

Reale et al., ICST 2026, doi:10.1109/ICST69053.2026.00080;
artifact https://zenodo.org/records/18900675, src/run_selection.py.
Implements a history-only adaptation of the historical rate + inverse-lag
conditional-stickiness component and CCH density. No source code is copied.
Omitted: commit relevance, LRTS preprocessing, method granularity and full DANTE
selection. Last n observed class runs replace unavailable build-lag alignment.
"""
from collections import defaultdict,deque
from codedna.selection.risk import _estimated_costs

WINDOWS=tuple(range(1,11))
MIN_STICKY_EVENTS=20


def historical_scores(dataset):
    """Per-test rolling histories, pooled conditional counts; predict then update.

    Score = (prior failure rate + sum(P(fail|sticky_n)/n for failed lag n))
            * max(prior failure count,0.1).
    The caller divides by historical estimated duration (CCH). Conditional
    probabilities are zero before 20 conditioning events; no target tuning.
    These values can exceed one and MUST NOT be used as skip probabilities.
    """
    history=defaultdict(lambda:deque(maxlen=10))
    runs=defaultdict(int);failures=defaultdict(int)
    events={n:0 for n in WINDOWS};failed_events={n:0 for n in WINDOWS}
    groups=dataset.rows_by_commit();scores={}
    for sha in dataset.commits:
        rows=groups[sha]
        for r in rows:
            past=list(history[r.test_id])
            rate=failures[r.test_id]/runs[r.test_id] if runs[r.test_id] else 0.
            sticky=sum((failed_events[n]/events[n])/n
                       for n in WINDOWS if len(past)>=n and past[-n]
                       and events[n]>=MIN_STICKY_EVENTS)
            scores[(sha,r.test_id)]=(rate+sticky)*max(failures[r.test_id],.1)
        # All predictions in the commit precede ALL current-outcome updates.
        for r in rows:
            past=list(history[r.test_id])
            for n in WINDOWS:
                if any(past[-n:]):
                    events[n]+=1;failed_events[n]+=r.label
            runs[r.test_id]+=1;failures[r.test_id]+=r.label
            history[r.test_id].append(r.label)
    return scores


def order_history(rows,scores):
    costs=_estimated_costs(rows)
    return [r.test_id for r in sorted(rows,key=lambda r:(
        -scores[(r.commit,r.test_id)]/costs[r.test_id],r.test_id))]
