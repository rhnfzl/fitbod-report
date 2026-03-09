"""Shared test fixtures and helpers."""

from datetime import datetime


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
