"""End-to-end golden-file tests: CSV bytes in, report text out.

These run the same pipeline the Streamlit app does and compare the result
against checked-in files under tests/golden/. They exist to make every change
to the reported numbers visible and deliberate.

The goldens record current behaviour, bugs included. When a fix legitimately
changes the output, regenerate and read the diff before committing it:

    REGEN_GOLDEN=1 uv run pytest tests/test_golden.py
"""

import os
from pathlib import Path

import pandas as pd
import pytest

from src.data.processor import process_data_from_df
from src.data.validator import validate_data_structure
from src.report.generator import (
    PeriodType,
    generate_gpt_report,
    generate_json_report,
    generate_markdown_report,
    generate_yaml_report,
    summarize_workouts,
)

FIXTURE = Path(__file__).parent / "fixtures" / "sample_fitbod.csv"
GOLDEN_DIR = Path(__file__).parent / "golden"


def _load_summaries(tz_name="UTC", group_by="week"):
    """Reproduce app.py's load path exactly."""
    df = pd.read_csv(FIXTURE)
    is_valid, missing = validate_data_structure(df, is_dataframe=True)
    assert is_valid, f"fixture is missing columns: {missing}"

    df["Date"] = pd.to_datetime(df["Date"])
    if df["Date"].dt.tz is None:
        df["Date"] = df["Date"].dt.tz_localize("UTC")

    return summarize_workouts(process_data_from_df(df), use_metric=True, tz_name=tz_name, group_by=group_by)


def _check(name, actual):
    """Compare against the golden file, or rewrite it when regenerating."""
    path = GOLDEN_DIR / name
    if os.environ.get("REGEN_GOLDEN"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(actual)
        pytest.skip(f"regenerated {name}")
    assert path.exists(), f"missing golden {path}; run REGEN_GOLDEN=1 pytest to create it"
    expected = path.read_text()
    assert actual == expected, (
        f"{name} changed.\n"
        f"If the change is intended, regenerate with REGEN_GOLDEN=1 and review the diff."
    )


@pytest.mark.parametrize(
    ("name", "fmt", "report_format"),
    [
        ("weekly_summary.md", generate_markdown_report, "summary"),
        ("weekly_detailed.md", generate_markdown_report, "detailed"),
        ("weekly_summary.json", generate_json_report, "summary"),
        ("weekly_summary.yaml", generate_yaml_report, "summary"),
        ("weekly_summary.gpt.txt", generate_gpt_report, "summary"),
        ("weekly_detailed.gpt.txt", generate_gpt_report, "detailed"),
    ],
)
def test_weekly_golden(name, fmt, report_format):
    summaries = _load_summaries()
    _check(name, fmt(summaries, True, report_format, PeriodType.WEEKLY, False, True))


@pytest.mark.parametrize(
    ("name", "period_type", "calendar_aligned"),
    [
        ("monthly_calendar.json", PeriodType.MONTHLY, True),
        ("monthly_rolling.json", PeriodType.MONTHLY, False),
        ("quarterly_calendar.json", PeriodType.QUARTERLY, True),
    ],
)
def test_aggregated_golden(name, period_type, calendar_aligned):
    # Calendar-aligned periods use daily granularity, as app.py does.
    group_by = "day" if calendar_aligned else "week"
    summaries = _load_summaries(group_by=group_by)
    _check(name, generate_json_report(summaries, True, "summary", period_type, calendar_aligned, True))


def test_imperial_golden():
    summaries = _load_summaries()
    _check("weekly_imperial.gpt.txt", generate_gpt_report(summaries, False, "summary", PeriodType.WEEKLY, False, True))


def test_timezone_shifts_day_buckets():
    """A non-UTC zone must move sessions into different day buckets.

    Weekly grouping is deliberately not used here: the fixture's 18:30 UTC
    sessions shift by a day under Pacific/Auckland but stay inside the same
    Monday-Sunday week, so a weekly report is identical and would prove nothing.
    """
    utc = _load_summaries(tz_name="UTC", group_by="day")
    auckland = _load_summaries(tz_name="Pacific/Auckland", group_by="day")
    assert sorted(utc)[0] == "2025-01-06"
    assert sorted(auckland)[0] == "2025-01-07", "UTC+13 must push an 18:30 session to the next day"

    _check("daily_auckland.gpt.txt", generate_gpt_report(auckland, True, "summary", PeriodType.DAILY, False, True))


def test_analysis_can_be_disabled():
    summaries = _load_summaries()
    _check("weekly_no_analysis.gpt.txt", generate_gpt_report(summaries, True, "summary", PeriodType.WEEKLY, False, False))
