"""Isolated Workout Intelligence analytics engine (Phase 7B).

This package is intentionally independent from ``app.domain`` (Health Index /
Daily Intelligence). It must not import from, or be imported by, the daily
scoring engine. All computations here are deterministic and explainable.
"""

from app.analytics.workout_load import (
    CALCULATION_VERSION,
    LoadEngineResult,
    SessionExerciseInput,
    SessionLoadInput,
    SetInput,
    compute_session_load,
)

__all__ = [
    "CALCULATION_VERSION",
    "LoadEngineResult",
    "SessionExerciseInput",
    "SessionLoadInput",
    "SetInput",
    "compute_session_load",
]
