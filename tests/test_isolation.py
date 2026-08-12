"""Report generation must not carry state between calls.

The Streamlit deployment serves every user from one process, so any module-level
mutable state is shared across sessions. These tests pin the boundary.
"""

from datetime import datetime, timedelta

from src.report.generator import PeriodType, generate_gpt_report, summarize_workouts


def _entries(exercise_name, weeks=4):
    """Four weekly sessions of one exercise."""
    out = []
    for week in range(weeks):
        date = datetime(2025, 1, 6, 18, 0) + timedelta(weeks=week)
        for _ in range(5):
            out.append(
                {
                    "Date": date,
                    "Exercise": exercise_name,
                    "Weight(kg)": 100.0,
                    "Reps": 5,
                    "Distance(m)": 0.0,
                    "Duration(s)": 0.0,
                    "isWarmup": "false",
                }
            )
    return out


def _report(exercise_name, include_analysis):
    summaries = summarize_workouts(_entries(exercise_name), True, "UTC", "week")
    return generate_gpt_report(summaries, True, "summary", PeriodType.WEEKLY, False, include_analysis)


def test_unknown_exercises_do_not_leak_between_reports():
    """One caller's custom exercise names must never appear in another's report.

    Regression test: the unknown-exercise tracker used to be module-level state
    cleared only when analysis was enabled, so with the analysis toggle off a
    report listed every unrecognised name seen since the process started.
    """
    first = _report("Alice Private Rehab Lift", include_analysis=False)
    second = _report("Bob Custom Press", include_analysis=False)

    assert "Alice Private Rehab Lift" in first
    assert "Bob Custom Press" in second
    assert "Alice Private Rehab Lift" not in second


def test_unknown_exercises_do_not_leak_with_analysis_enabled():
    first = _report("Alice Private Rehab Lift", include_analysis=True)
    second = _report("Bob Custom Press", include_analysis=True)

    assert "Alice Private Rehab Lift" in first
    assert "Alice Private Rehab Lift" not in second


def test_unknown_count_reflects_only_the_current_report():
    _report("Alice Private Rehab Lift", include_analysis=True)
    second = _report("Bob Custom Press", include_analysis=True)

    assert "unknown_exercise_count\t1" in second


def test_known_exercises_report_no_unknowns():
    report = _report("Back Squat", include_analysis=True)

    assert "## unknown_exercises" not in report
    assert "unknown_exercise_count\t0" in report
