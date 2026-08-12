"""Shared test fixtures and helpers."""

from datetime import datetime

import pytest

from src.data.exercise_db import clear_unknown_exercises


@pytest.fixture(autouse=True)
def _reset_unknown_exercises():
    """Keep the module-level unknown-exercise tracker from leaking between tests.

    It is process-global, so without this any test asserting on unknown
    exercises depends on which tests ran before it.
    """
    clear_unknown_exercises()
    yield
    clear_unknown_exercises()


def make_entry(
    exercise="Bench Press",
    weight_kg=50.0,
    reps=10,
    distance_m=0.0,
    duration_s=0.0,
    date_str="2024-01-15 10:00:00",
    is_warmup="false",
):
    """Create a minimal processed record for testing."""
    return {
        "Date": datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S"),
        "Exercise": exercise,
        "Weight(kg)": weight_kg,
        "Reps": reps,
        "Distance(m)": distance_m,
        "Duration(s)": duration_s,
        "isWarmup": is_warmup,
    }
