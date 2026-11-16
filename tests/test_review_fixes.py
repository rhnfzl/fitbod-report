"""Regression tests for defects found while verifying the correctness PR against a real export."""

import json
import re
from datetime import datetime, timedelta
from unittest import mock

from src.pdf.generator import _chunk_tables, convert_to_pdf_bytes
from src.report.generator import (
    PeriodType,
    generate_gpt_report,
    generate_json_report,
    generate_markdown_report,
    summarize_workouts,
)


def _entry(exercise, at, weight=100.0, reps=5, warmup=False):
    return {
        "Date": at,
        "Exercise": exercise,
        "Weight(kg)": weight,
        "Reps": reps,
        "Distance(m)": 0.0,
        "Duration(s)": 0.0,
        "isWarmup": "true" if warmup else "false",
    }


def _analysis(entries, period_type, group_by):
    summaries = summarize_workouts(entries, True, "UTC", group_by)
    return json.loads(generate_json_report(summaries, True, "summary", period_type, False, True))["analysis"]


START = datetime(2025, 1, 6, 18, 0)  # a Monday


def test_per_workout_trend_shows_a_frequency_change():
    """One shared weeks-per-period factor made both halves equal the overall rate."""
    once = [_entry("Back Squat", START + timedelta(weeks=w)) for w in range(10)]
    twice = [_entry("Back Squat", START + timedelta(weeks=w, days=d)) for w in range(10, 20) for d in (0, 3)]

    for period_type, group_by in ((PeriodType.WEEKLY, "week"), (PeriodType.PER_WORKOUT, "session"), (PeriodType.DAILY, "day")):
        analysis = _analysis(once + twice, period_type, group_by)
        assert analysis["second_half_sessions_pw"] > analysis["first_half_sessions_pw"] * 1.3, (period_type, analysis)


def test_rotating_weekday_trainee_has_no_false_gaps():
    """Once a week on a different weekday each week is not a missed week."""
    entries = [_entry("Back Squat", START + timedelta(weeks=w, days=w % 5)) for w in range(16)]
    for period_type, group_by in ((PeriodType.WEEKLY, "week"), (PeriodType.DAILY, "day"), (PeriodType.PER_WORKOUT, "session")):
        assert _analysis(entries, period_type, group_by)["gap_weeks"] == "none", period_type


def test_sporadic_trainee_still_gets_gaps():
    """Inferring the cadence switched detection off for whoever trained least."""
    entries = [_entry("Back Squat", START + timedelta(weeks=w)) for w in range(0, 18, 3)]
    gaps = _analysis(entries, PeriodType.WEEKLY, "week")["gap_weeks"]
    assert gaps not in ("none", "n/a") and "2025-01-13" in gaps


def test_monthly_report_does_not_claim_no_gaps():
    entries = [_entry("Back Squat", START + timedelta(weeks=w)) for w in range(0, 26, 3)]
    analysis = _analysis(entries, PeriodType.MONTHLY, "week")
    assert analysis["gap_weeks"] == "n/a"
    assert analysis["gap_window_weeks"] is None


def test_sets_keep_the_order_performed_and_sessions_run_oldest_first():
    """Set Progression sorted warm-ups last and heaviest first, reversing a ramp."""
    newest_first = [
        _entry("Romanian Deadlift", START + timedelta(hours=10), 60.0, 8, warmup=True),
        _entry("Romanian Deadlift", START + timedelta(hours=10), 70.0, 8),
        _entry("Romanian Deadlift", START + timedelta(hours=10), 75.0, 8),
        _entry("Back Squat", START, 100.0, 5),
    ]
    summaries = summarize_workouts(newest_first, True, "UTC", "session")
    report = generate_markdown_report(summaries, True, "detailed", PeriodType.PER_WORKOUT, False, False)

    weights = re.findall(r"^\| \d+ \| ([\d.]+) kg \|", report.split("#### Romanian Deadlift")[1], flags=re.M)
    assert weights[:3] == ["60.0", "70.0", "75.0"]
    assert report.index("Back Squat") < report.index("Romanian Deadlift"), "same-day workouts must run oldest first"


def test_gpt_lists_uneven_working_sets_and_ignores_warmups():
    sets = [(60.0, 5, True), (100.0, 10, False), (100.0, 8, False), (100.0, 8, False)]
    entries = [_entry("Back Squat", START, w, r, warmup=wu) for w, r, wu in sets]
    report = generate_gpt_report(summarize_workouts(entries, True, "UTC", "week"), True, "summary", PeriodType.WEEKLY)
    assert "Back Squat:10/8/8@100.0kg" in report
    assert "\tworking_reps\t" in report and "\tworking_volume\t" in report


def test_muscle_sets_are_per_week_for_any_period_type():
    entries = [_entry("Back Squat", START + timedelta(weeks=w)) for w in range(52) for _ in range(3)]

    def quads(period_type, group_by):
        report = generate_gpt_report(summarize_workouts(entries, True, "UTC", group_by), True, "summary", period_type)
        return float(re.search(r"^quads\t([\d.]+)", report, flags=re.M).group(1))

    assert quads(PeriodType.WEEKLY, "week") == quads(PeriodType.YEARLY, "week") == 3.0


def test_markdown_survives_a_failing_analysis():
    entries = [_entry("Back Squat", START + timedelta(weeks=w)) for w in range(4)]
    summaries = summarize_workouts(entries, True, "UTC", "week")
    with mock.patch("src.report.generator._compute_analysis", side_effect=ValueError("boom")):
        report = generate_markdown_report(summaries, True, "summary", PeriodType.WEEKLY, False, True)
    assert "Analysis could not be computed: boom" in report
    assert "# Overall Summary" in report


def test_tables_taller_than_a_page_are_chunked_and_render():
    """MuPDF overflows a table taller than a page and can then loop forever."""
    rows = "\n".join(f"| {i} | 100.0 kg | 5 | Working |" for i in range(200))
    md = f"# Report\n\n| Set | Weight | Reps | Type |\n|-----|---------|------|------|\n{rows}\n"

    chunked = _chunk_tables(md, max_rows=30)
    assert chunked.count("| Set | Weight | Reps | Type |") == 7
    assert convert_to_pdf_bytes(md).startswith(b"%PDF")
