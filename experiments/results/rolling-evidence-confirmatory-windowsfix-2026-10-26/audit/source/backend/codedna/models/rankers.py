"""Test-ordering strategies: simple historical baselines and ML models.

Every ranker turns the rows of one commit into an ordering (first = run
first). Baselines (docs/RESEARCH_PLAN.md):

* ``random``            B1 — fixed seed per commit, for reference.
* ``shortest_first``    B2 — ascending historical mean duration.
* ``recent_failures``   B3 — most failures in the last runs first, then shortest.
* ``failure_history``   B5 — highest historical failure rate first.

ML rankers (``logistic_regression``, ``gradient_boosting``) are trained on
earlier commits and order tests by predicted failure probability. They need
scikit-learn (``pip install -e ".[ml]"``).
"""

from __future__ import annotations

import hashlib
import random

from codedna.test_history.features import Row

BASELINES = ("random", "shortest_first", "recent_failures", "failure_history")
ML_MODELS = ("logistic_regression", "gradient_boosting")


def order_by_baseline(name: str, rows: list[Row]) -> list[str]:
    if name == "random":
        seed = int(hashlib.sha256(rows[0].commit.encode()).hexdigest()[:8], 16) if rows else 0
        tests = sorted(r.test_id for r in rows)
        random.Random(seed).shuffle(tests)
        return tests
    if name == "shortest_first":
        key = lambda r: (r.features["mean_duration"], r.test_id)  # noqa: E731
    elif name == "recent_failures":
        key = lambda r: (-r.features["recent_failures"], r.features["mean_duration"], r.test_id)  # noqa: E731
    elif name == "failure_history":
        key = lambda r: (-r.features["failure_rate"], -r.features["past_failures"], r.test_id)  # noqa: E731
    else:
        raise ValueError(f"unknown baseline {name!r}")
    return [r.test_id for r in sorted(rows, key=key)]


class MLRanker:
    """A probabilistic classifier wrapped as a ranker.

    ``class_weight="balanced"`` (the default) up-weights the rare failing rows,
    which helps ranking but inflates raw probabilities; ``None`` trains on the
    natural failure rate (used as the stricter uncalibrated baseline, D-037).
    """

    def __init__(self, name: str, feature_names: list[str], seed: int = 0,
                 class_weight: str | None = "balanced"):
        try:
            from sklearn.ensemble import HistGradientBoostingClassifier
            from sklearn.linear_model import LogisticRegression
            from sklearn.pipeline import make_pipeline
            from sklearn.preprocessing import StandardScaler
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError('scikit-learn is required: pip install -e ".[ml]"') from exc
        self.name = name
        self.feature_names = feature_names
        if name == "logistic_regression":
            self.model = make_pipeline(
                StandardScaler(),
                LogisticRegression(class_weight=class_weight, max_iter=1000, random_state=seed))
        elif name == "gradient_boosting":
            self.model = HistGradientBoostingClassifier(
                class_weight=class_weight, random_state=seed, max_iter=200)
        else:
            raise ValueError(f"unknown model {name!r}")

    def _matrix(self, rows: list[Row]) -> list[list[float]]:
        return [[row.features[name] for name in self.feature_names] for row in rows]

    def fit(self, rows: list[Row]) -> None:
        labels = [row.label for row in rows]
        if len(set(labels)) < 2:
            raise ValueError("training data needs both failing and passing examples")
        self.model.fit(self._matrix(rows), labels)

    def predict_proba(self, rows: list[Row]) -> list[float]:
        if not rows:
            return []
        return [float(p[1]) for p in self.model.predict_proba(self._matrix(rows))]

    def order(self, rows: list[Row]) -> list[str]:
        scores = self.predict_proba(rows)
        ranked = sorted(zip(rows, scores), key=lambda pair: (-pair[1], pair[0].test_id))
        return [row.test_id for row, _ in ranked]
