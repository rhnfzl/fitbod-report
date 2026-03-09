"""Tests for report output - aggregation semantics and format consistency."""

import json

import yaml
from conftest import make_entry as _make_entry

from src.report.generator import (
    PeriodType,
    aggregate_summaries,
    generate_json_report,
    generate_markdown_report,
    generate_yaml_report,
    summarize_workouts,
)


def _make_multi_week_entries():
    """Create entries spanning multiple weeks for aggregation testing."""
    entries = []
    # Week 1: Jan 15 (Mon)
    entries.append(_make_entry(date_str="2024-01-15 10:00:00", reps=10, weight_kg=50))
    # Week 2: Jan 22 (Mon)
    entries.append(_make_entry(date_str="2024-01-22 10:00:00", reps=12, weight_kg=55))
    # Week 3: Feb 5 (Mon)
    entries.append(_make_entry(date_str="2024-02-05 10:00:00", reps=8, weight_kg=60))
    # Week 4: Feb 12 (Mon)
    entries.append(_make_entry(date_str="2024-02-12 10:00:00", reps=10, weight_kg=65))
    return entries


class TestAggregation:
    def test_monthly_calendar_groups_by_calendar_month(self):
        entries = _make_multi_week_entries()
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        monthly = aggregate_summaries(daily, PeriodType.MONTHLY, calendar_aligned=True)

        # Should have 2 months: January and February
        assert len(monthly) == 2
        keys = sorted(monthly.keys())
        assert keys[0] == "2024-01"
        assert keys[1] == "2024-02"

    def test_monthly_rolling_uses_4week_windows(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        monthly = aggregate_summaries(weekly, PeriodType.MONTHLY)  # default: rolling

        # Rolling keys are YYYY-MM-DD (start date), period_name has " to " range
        for key in monthly:
            assert len(key) == 10 and key[4] == "-"  # YYYY-MM-DD, not YYYY-MM
            assert " to " in monthly[key]["period_name"]

    def test_monthly_totals_match_input(self):
        entries = _make_multi_week_entries()
        input_reps = sum(e["Reps"] for e in entries)

        # Calendar mode: daily summaries for accurate month boundaries
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        monthly_cal = aggregate_summaries(daily, PeriodType.MONTHLY, calendar_aligned=True)
        assert input_reps == sum(s["Reps"] for s in monthly_cal.values())

        # Rolling mode: weekly summaries
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        monthly_roll = aggregate_summaries(weekly, PeriodType.MONTHLY, calendar_aligned=False)
        assert input_reps == sum(s["Reps"] for s in monthly_roll.values())

    def test_4week_aggregation(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        agg = aggregate_summaries(weekly, PeriodType.FOUR_WEEKS)

        # 4 weeks span ~1 4-week period
        assert len(agg) >= 1

        weekly_volume = sum(s["Volume"] for s in weekly.values())
        agg_volume = sum(s["Volume"] for s in agg.values())
        assert weekly_volume == agg_volume


def _make_multi_month_entries():
    """Create entries spanning multiple months for quarterly/half-yearly/yearly testing."""
    entries = []
    dates = [
        "2024-01-15 10:00:00",
        "2024-03-10 10:00:00",
        "2024-05-20 10:00:00",
        "2024-07-08 10:00:00",
        "2024-09-15 10:00:00",
        "2024-11-10 10:00:00",
    ]
    for i, d in enumerate(dates):
        entries.append(_make_entry(date_str=d, reps=10 + i, weight_kg=50 + i * 5))
    return entries


class TestCalendarAggregation:
    def test_quarterly_calendar_groups_by_quarter(self):
        entries = _make_multi_month_entries()
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        quarterly = aggregate_summaries(daily, PeriodType.QUARTERLY, calendar_aligned=True)

        keys = sorted(quarterly.keys())
        assert "2024-Q1" in keys
        assert "2024-Q2" in keys
        assert quarterly["2024-Q1"]["period_name"] == "Q1 2024 (Jan-Mar)"

    def test_quarterly_rolling_uses_13week_windows(self):
        entries = _make_multi_month_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        quarterly = aggregate_summaries(weekly, PeriodType.QUARTERLY)  # default: rolling

        # Rolling keys are YYYY-MM-DD, not YYYY-QN
        for key in quarterly:
            assert len(key) == 10 and key[4] == "-"
            assert " to " in quarterly[key]["period_name"]

    def test_half_yearly_calendar_groups_by_half(self):
        entries = _make_multi_month_entries()
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        half_yearly = aggregate_summaries(daily, PeriodType.HALF_YEARLY, calendar_aligned=True)

        keys = sorted(half_yearly.keys())
        assert "2024-H1" in keys
        assert "2024-H2" in keys
        assert half_yearly["2024-H1"]["period_name"] == "H1 2024 (Jan-Jun)"

    def test_yearly_calendar_groups_by_year(self):
        entries = _make_multi_month_entries()
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        yearly = aggregate_summaries(daily, PeriodType.YEARLY, calendar_aligned=True)

        assert len(yearly) == 1
        assert "2024" in yearly
        assert yearly["2024"]["period_name"] == "2024"

    def test_totals_match_input_both_modes(self):
        entries = _make_multi_month_entries()
        input_reps = sum(e["Reps"] for e in entries)

        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")

        for pt in [PeriodType.QUARTERLY, PeriodType.HALF_YEARLY, PeriodType.YEARLY]:
            # Calendar mode uses daily summaries
            agg_cal = aggregate_summaries(daily, pt, calendar_aligned=True)
            assert input_reps == sum(s["Reps"] for s in agg_cal.values()), f"{pt} cal=True"

            # Rolling mode uses weekly summaries
            agg_roll = aggregate_summaries(weekly, pt, calendar_aligned=False)
            assert input_reps == sum(s["Reps"] for s in agg_roll.values()), f"{pt} cal=False"

    def test_json_quarterly_report(self):
        entries = _make_multi_month_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_json_report(weekly, True, "summary", PeriodType.QUARTERLY)
        data = json.loads(report)

        assert data["report_type"] == "quarterly"
        assert data["grouping_mode"] == "rolling"
        assert len(data["periods"]) <= len(weekly)

    def test_json_quarterly_calendar_report(self):
        entries = _make_multi_month_entries()
        daily = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        report = generate_json_report(daily, True, "summary", PeriodType.QUARTERLY, calendar_aligned=True)
        data = json.loads(report)

        assert data["report_type"] == "quarterly"
        assert data["grouping_mode"] == "calendar"
        assert len(data["periods"]) < len(daily)

    def test_json_yearly_report(self):
        entries = _make_multi_month_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_json_report(weekly, True, "summary", PeriodType.YEARLY)
        data = json.loads(report)

        assert data["report_type"] == "yearly"
        assert len(data["periods"]) == 1


class TestJsonYamlAggregation:
    def test_json_monthly_uses_aggregated_periods(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")

        report = generate_json_report(weekly, True, "summary", PeriodType.MONTHLY)
        data = json.loads(report)

        # Should have fewer periods than raw weeks
        assert len(data["periods"]) < len(weekly)
        assert data["report_type"] == "monthly"

    def test_json_weekly_matches_raw_count(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")

        report = generate_json_report(weekly, True, "summary", PeriodType.WEEKLY)
        data = json.loads(report)

        assert len(data["periods"]) == len(weekly)

    def test_yaml_monthly_roundtrip(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")

        report = generate_yaml_report(weekly, True, "summary", PeriodType.MONTHLY)
        data = yaml.safe_load(report)

        assert data["report_type"] == "monthly"
        assert len(data["periods"]) < len(weekly)

    def test_overall_totals_consistent(self):
        entries = _make_multi_week_entries()
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")

        report = generate_json_report(weekly, True, "summary", PeriodType.MONTHLY)
        data = json.loads(report)

        # Overall reps should match sum of period reps
        period_reps = sum(p["stats"]["total_reps"] for p in data["periods"])
        assert data["overall"]["total_reps"] == period_reps


class TestStringPeriodType:
    def test_markdown_accepts_string_period_type(self):
        """Ensure generate_markdown_report works with string period_type (from selectbox)."""
        entries = [_make_entry()]
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_markdown_report(weekly, True, "summary", "weekly")
        assert "Workout Summary Report" in report

    def test_json_accepts_string_period_type(self):
        entries = [_make_entry()]
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_json_report(weekly, True, "summary", "weekly")
        data = json.loads(report)
        assert data["report_type"] == "weekly"


class TestMarkdownReport:
    def test_markdown_not_empty(self):
        entries = [_make_entry()]
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_markdown_report(weekly, True, "summary", PeriodType.WEEKLY)
        assert "Workout Summary Report" in report

    def test_detailed_contains_set_table(self):
        entries = [_make_entry()]
        weekly = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="week")
        report = generate_markdown_report(weekly, True, "detailed", PeriodType.WEEKLY)
        assert "| Set |" in report
