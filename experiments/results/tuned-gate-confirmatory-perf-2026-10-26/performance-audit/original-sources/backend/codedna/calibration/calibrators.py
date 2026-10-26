"""Probability calibration (Milestone 5, D-025).

A model's raw scores are often badly calibrated: a test given "0.3" may fail
far more or less than 30 % of the time. A calibrator is a one-dimensional
map fitted on held-out data (the chronological validation split) that turns
raw scores into probabilities that match observed failure frequencies.

* ``none``     — identity.
* ``platt``    — logistic regression on the log-odds of the raw score
  (Platt scaling); smooth, needs few failures.
* ``isotonic`` — isotonic regression; monotone, flexible, needs more data.
"""

from __future__ import annotations

import math

METHODS = ("none", "platt", "isotonic")
_EPS = 1e-6


class Calibrator:
    def __init__(self, method: str = "isotonic"):
        if method not in METHODS:
            raise ValueError(f"unknown calibration method {method!r}; choose from {METHODS}")
        self.method = method
        self._model = None

    def fit(self, scores: list[float], labels: list[int]) -> Calibrator:
        if self.method == "none":
            return self
        if len(set(labels)) < 2:
            raise ValueError("calibration data needs both failing and passing examples")
        if self.method == "platt":
            from sklearn.linear_model import LogisticRegression
            self._model = LogisticRegression(C=1e6, max_iter=1000)  # ~unregularised
            self._model.fit([[_logit(s)] for s in scores], labels)
        else:
            from sklearn.isotonic import IsotonicRegression
            self._model = IsotonicRegression(y_min=0.0, y_max=1.0, out_of_bounds="clip")
            self._model.fit(scores, labels)
        return self

    def transform(self, scores: list[float]) -> list[float]:
        if not scores:
            return []
        if self.method == "none":
            return [float(s) for s in scores]
        if self._model is None:
            raise RuntimeError("calibrator is not fitted")
        if self.method == "platt":
            return [float(p[1]) for p in self._model.predict_proba([[_logit(s)] for s in scores])]
        return [float(p) for p in self._model.predict(scores)]


def _logit(p: float) -> float:
    p = min(max(p, _EPS), 1 - _EPS)
    return math.log(p / (1 - p))
