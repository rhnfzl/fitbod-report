"""The precomputed analysis block that gets fed to a coaching model."""

import json
from datetime import datetime, timedelta

from src.report.generator import (
    GAP_WINDOW_WEEKS,
    PeriodType,
    generate_json_report,
    summarize_workouts,
)


def _entry(exercise, at, weight=100.0, reps=5):
    return {
        "Date": at,
        "Exercise": exercise,
        "Weight(kg)": weight,
        "Reps": reps,
        "Distance(m)": 0.0,
        "Duration(s)": 0.0,
        "isWarmup": "false",
    }


def _analysis(entries, period_type=PeriodType.WEEKLY, group_by="week", calendar_aligned=False):
    summaries = summarize_workouts(entries, True, "UTC", group_by)
    report = generate_json_report(summaries, True, "summary", period_type, calendar_aligned, True)
    return json.loads(report)["analysis"]


def _weekly_program(weeks, skip=(), exercises=("Back Squat",), sets=3, start=datetime(2025, 1, 6, 18, 0)):
    entries = []
    for week in range(weeks):
        if week in skip:
            continue
        at = start + timedelta(weeks=week)
        for exercise in exercises:
            entries.extend(_entry(exercise, at) for _ in range(sets))
    return entries


class TestVolumeTrend:
    def test_growth_is_reported_as_a_positive_change_not_a_drop(self):
        """The old key name asserted a direction the value does not carry."""
        light = [_entry("Back Squat", datetime(2025, 1, 6, 18, 0) + timedelta(weeks=w), 50.0) for w in range(4)]
        heavy = [_entry("Back Squat", datetime(2025, 1, 6, 18, 0) + timedelta(weeks=w), 100.0) for w in range(4, 8)]

        analysis = _analysis(light + heavy)

        assert "volume_drop_pct" not in analysis
        assert analysis["volume_change_pct"] > 0
        assert analysis["second_half_vol_pw"] > analysis["first_half_vol_pw"]


class TestPerWeekNormalisation:
    def test_monthly_report_states_sessions_per_week_not_per_month(self):
        """A monthly report once claimed 8.47 sessions per week."""
        entries = _weekly_program(26)  # one session a week for half a year

        weekly = _analysis(entries)
        monthly = _analysis(entries, PeriodType.MONTHLY, group_by="day", calendar_aligned=True)

        for analysis in (weekly, monthly):
            assert 0.5 <= analysis["second_half_sessions_pw"] <= 1.5, analysis["second_half_sessions_pw"]


class TestGapDetection:
    def test_gap_is_found_even_when_it_falls_early(self):
        """Cadence came from the mean of the first five intervals, so an early
        gap inflated that mean past the cutoff and disabled detection."""
        analysis = _analysis(_weekly_program(16, skip={4, 5}))

        assert analysis["gap_weeks"] != "none"
        assert "2025-02-03" in analysis["gap_weeks"]

    def test_gap_is_found_when_it_falls_late(self):
        analysis = _analysis(_weekly_program(16, skip={10, 11}))

        assert "2025-03-17" in analysis["gap_weeks"]

    def test_no_gaps_reported_for_uninterrupted_training(self):
        assert _analysis(_weekly_program(16))["gap_weeks"] == "none"

    def test_only_recent_gaps_are_listed(self):
        """An unbounded list reached back years and dominated the export."""
        analysis = _analysis(_weekly_program(80, skip={2, 3}))

        assert analysis["gap_window_weeks"] == GAP_WINDOW_WEEKS
        assert analysis["gap_weeks"] == "none", "a gap 78 weeks back is not actionable"


class TestMuscleBalance:
    def test_core_work_is_counted_rather_than_dropped(self):
        """abs/obliques/lower_back/neck fell through both halves and vanished."""
        entries = _weekly_program(8, exercises=("Back Squat", "Barbell Bench Press", "Ab Crunch Machine"))

        analysis = _analysis(entries)

        assert analysis["core_share_pct"] > 0

    def test_averages_divide_by_every_period_not_only_trained_ones(self):
        """A muscle trained once in eight weeks must not read as a weekly staple."""
        squats = _weekly_program(8, exercises=("Barbell Bench Press",))
        one_leg_day = [_entry("Back Squat", datetime(2025, 1, 6, 18, 0)) for _ in range(3)]

        analysis = _analysis(squats + one_leg_day)

        # Bench every week vs squats once: upper must dominate decisively.
        assert analysis["upper_lower_ratio"] > 3, analysis["upper_lower_ratio"]
