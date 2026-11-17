"""Warm-up separation and exercise ordering in the exported report."""

from datetime import datetime

import pytest

from src.report.generator import PeriodType, generate_gpt_report, summarize_workouts


def _set(exercise, weight, reps, warmup, at="2025-01-06 18:30:00"):
    return {
        "Date": datetime.strptime(at, "%Y-%m-%d %H:%M:%S"),
        "Exercise": exercise,
        "Weight(kg)": weight,
        "Reps": reps,
        "Distance(m)": 0.0,
        "Duration(s)": 0.0,
        "isWarmup": "true" if warmup else "false",
    }


def _session(at="2025-01-06 18:30:00"):
    """Deadlift then bench, each warmed up first - as Fitbod exports them."""
    return [
        _set("Deadlift", 60.0, 5, True, at),
        _set("Deadlift", 90.0, 3, True, at),
        _set("Deadlift", 120.0, 4, False, at),
        _set("Deadlift", 120.0, 4, False, at),
        _set("Deadlift", 120.0, 4, False, at),
        _set("Barbell Bench Press", 40.0, 10, True, at),
        _set("Barbell Bench Press", 80.0, 6, False, at),
        _set("Barbell Bench Press", 80.0, 6, False, at),
    ]


def _summaries(entries):
    return summarize_workouts(entries, True, "UTC", "week")


def _session_exercises(report, date):
    """Exercise names for one row of the report's recent_sessions section."""
    lines = report.split("\n")
    start = lines.index("## recent_sessions")
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith(f"{date}\t"):
            return [part.split(":")[0] for part in line.split("\t")[1].split(",")]
    raise AssertionError(f"no recent_sessions row for {date}")


class TestWarmupSeparation:
    def test_working_figures_exclude_warmups(self):
        details = _summaries(_session())["2025-01-06 to 2025-01-12"]["Exercise_details"]["Deadlift"]

        assert details["working_sets"] == 3
        assert details["warmup_sets"] == 2
        # Totals keep every set; working figures are tracked alongside them.
        assert details["total_reps"] == 20
        assert details["working_reps"] == 12
        assert details["total_volume"] == pytest.approx(60 * 5 + 90 * 3 + 120 * 12)
        assert details["working_volume"] == pytest.approx(120 * 12)
        assert details["working_max_weight"] == 120.0

    def test_recent_sessions_reports_working_reps_per_working_set(self):
        """3x4 must not be reported as 3x8 because warmup reps were folded in."""
        report = generate_gpt_report(_summaries(_session()), True, "summary", PeriodType.WEEKLY, False, True)

        assert "Deadlift:3x4@120.0kg" in report
        assert "Deadlift:3x8" not in report
        assert "Barbell Bench Press:2x6@80.0kg" in report

    def test_exercise_stats_volume_excludes_warmups(self):
        report = generate_gpt_report(_summaries(_session()), True, "summary", PeriodType.WEEKLY, False, True)
        row = next(line for line in report.split("\n") if line.startswith("Deadlift\t"))

        # exercise, sessions, working_sets, reps, max, avg, volume, trend
        assert row.split("\t")[3] == "12"
        assert row.split("\t")[6] == "1440.0"


class TestExerciseOrdering:
    def test_order_within_a_session_is_preserved(self):
        """Fitbod shares one timestamp per session, so row order is the sequence."""
        report = generate_gpt_report(_summaries(_session()), True, "summary", PeriodType.WEEKLY, False, True)

        assert _session_exercises(report, "2025-01-06") == ["Deadlift", "Barbell Bench Press"]

    def test_each_session_is_its_own_row(self):
        """A weekly report must still list one row per workout, not one per week.

        Merging a week's sessions averaged their rep schemes together: a heavy
        2-rep day and a 4-rep day were reported as a single set of doubles.
        """
        monday = _session("2025-01-06 18:30:00")
        thursday = [_set("Back Squat", 100.0, 5, False, "2025-01-09 18:30:00")]
        # Newest first, exactly as Fitbod writes the file.
        report = generate_gpt_report(_summaries(thursday + monday), True, "summary", PeriodType.WEEKLY, False, True)

        assert _session_exercises(report, "2025-01-06") == ["Deadlift", "Barbell Bench Press"]
        assert _session_exercises(report, "2025-01-09") == ["Back Squat"]

    def test_sessions_are_listed_newest_first(self):
        monday = _session("2025-01-06 18:30:00")
        thursday = [_set("Back Squat", 100.0, 5, False, "2025-01-09 18:30:00")]
        report = generate_gpt_report(_summaries(thursday + monday), True, "summary", PeriodType.WEEKLY, False, True)

        lines = report.split("\n")
        start = lines.index("## recent_sessions")
        dates = [ln.split("\t")[0] for ln in lines[start + 2 :] if ln and not ln.startswith("## ")]

        assert dates == ["2025-01-09", "2025-01-06"]

    def test_order_is_not_alphabetical(self):
        report = generate_gpt_report(_summaries(_session()), True, "summary", PeriodType.WEEKLY, False, True)
        names = _session_exercises(report, "2025-01-06")

        assert names != sorted(names)
