"""Regression test selection strategies (baselines now; risk-aware selection in Milestone 5)."""

from codedna.selection.baselines import (
    STRATEGIES,
    SelectedTest,
    SelectionError,
    SelectionReport,
    compare_strategies,
    select_tests,
)

__all__ = [
    "STRATEGIES",
    "SelectedTest",
    "SelectionError",
    "SelectionReport",
    "compare_strategies",
    "select_tests",
]
