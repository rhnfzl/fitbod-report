"""Behaviour on multi-year exports, where every renderer used to fall over."""

from datetime import datetime, timedelta

from src.pdf.generator import _split_sections, convert_to_pdf_bytes
from src.report.generator import PeriodType, generate_gpt_report, summarize_workouts


def _long_history(weeks=120):
    """Enough history to produce a report no browser wants to syntax-highlight."""
    entries = []
    start = datetime(2023, 1, 2, 18, 0)
    for week in range(weeks):
        at = start + timedelta(weeks=week)
        for exercise in ("Deadlift", "Barbell Bench Press", "Back Squat"):
            for warmup, weight, reps in ((True, 60.0, 5), (False, 120.0, 4), (False, 120.0, 4)):
                entries.append(
                    {
                        "Date": at,
                        "Exercise": exercise,
                        "Weight(kg)": weight,
                        "Reps": reps,
                        "Distance(m)": 0.0,
                        "Duration(s)": 0.0,
                        "isWarmup": "true" if warmup else "false",
                    }
                )
    return entries


def _session_row(report, date):
    """The recent_sessions row for one date (not the period_summary row)."""
    lines = report.split("\n")
    start = lines.index("## recent_sessions")
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith(f"{date}\t"):
            return line
    raise AssertionError(f"no recent_sessions row for {date}")


class TestPdfSectioning:
    def test_large_markdown_is_split_into_sections(self):
        """One oversized section renders superlinearly and effectively hangs."""
        md = "# Report\n\n" + "".join(f"## Week {i}\n\n" + ("filler line\n" * 400) for i in range(20))

        sections = _split_sections(md)

        assert len(sections) > 1
        assert "".join(sections) == md, "splitting must not lose or reorder content"

    def test_sections_start_at_headings(self):
        md = "# Report\n\n" + "".join(f"## Week {i}\n\ncontent {i}\n\n" for i in range(50))

        for section in _split_sections(md, max_chars=200)[1:]:
            assert section.startswith("## "), "a section must not begin mid-table"

    def test_small_markdown_stays_one_section(self):
        assert len(_split_sections("# Title\n\n## One\n\nshort\n")) == 1

    def test_large_report_renders_to_pdf(self):
        """Previously this did not finish; it should now be quick."""
        from src.report.generator import generate_markdown_report

        summaries = summarize_workouts(_long_history(), True, "UTC", "week")
        md = generate_markdown_report(summaries, True, "detailed", PeriodType.WEEKLY, False, True)
        assert len(md) > 150_000, "fixture should be big enough to matter"

        data = convert_to_pdf_bytes(md)

        assert data.startswith(b"%PDF-")


class TestGptDetailedFormat:
    def test_detailed_differs_from_summary(self):
        """The GPT export ignored report_format, so 'detailed' silently did nothing."""
        summaries = summarize_workouts(_long_history(weeks=4), True, "UTC", "week")

        summary = generate_gpt_report(summaries, True, "summary", PeriodType.WEEKLY, False, True)
        detailed = generate_gpt_report(summaries, True, "detailed", PeriodType.WEEKLY, False, True)

        assert summary != detailed

    def test_detailed_lists_individual_sets_and_marks_warmups(self):
        summaries = summarize_workouts(_long_history(weeks=4), True, "UTC", "week")

        detailed = generate_gpt_report(summaries, True, "detailed", PeriodType.WEEKLY, False, True)
        row = _session_row(detailed, "2023-01-02")

        # one warmup at 60 then two working sets at 120
        assert "Deadlift:5@60.0w,4@120.0,4@120.0" in row

    def test_summary_collapses_to_sets_by_reps(self):
        summaries = summarize_workouts(_long_history(weeks=4), True, "UTC", "week")

        summary = generate_gpt_report(summaries, True, "summary", PeriodType.WEEKLY, False, True)
        row = _session_row(summary, "2023-01-02")

        assert "Deadlift:2x4@120.0kg" in row
