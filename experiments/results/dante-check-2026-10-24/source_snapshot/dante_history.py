"""Independent DANTE-inspired history-only baseline; NOT a DANTE reproduction.

No commit relevance component, LRTS preprocessing or author implementation is
reproduced. A smoothed two-state transition model represents failure persistence
and recurrence. Scores order tests; they are not calibrated skip probabilities.
"""
from collections import defaultdict
from codedna.selection.risk import _estimated_costs


def historical_scores(dataset):
    """Predict before observing each commit; absent tests keep their last state."""
    counts = defaultdict(lambda: [[0, 0], [0, 0]])
    previous = {}
    global_counts = [[0, 0], [0, 0]]
    scores = {}
    grouped = dataset.rows_by_commit()
    for sha in dataset.commits:
        rows = grouped[sha]
        for row in rows:
            state = previous.get(row.test_id, 0)
            # Beta(1,1) smoothing globally; two equivalent prior observations
            # shrink a sparse per-test transition estimate to the project rate.
            global_rate = (global_counts[state][1] + 1) / (sum(global_counts[state]) + 2)
            local = counts[row.test_id][state]
            scores[(sha, row.test_id)] = (local[1] + 2 * global_rate) / (sum(local) + 2)
        for row in rows:
            state = previous.get(row.test_id, 0)
            label = int(row.label)
            counts[row.test_id][state][label] += 1
            global_counts[state][label] += 1
            previous[row.test_id] = label
    return scores


def order_history(rows, scores):
    costs = _estimated_costs(rows)
    return [r.test_id for r in sorted(rows, key=lambda r: (
        -scores[(r.commit, r.test_id)] / costs[r.test_id], r.test_id))]
