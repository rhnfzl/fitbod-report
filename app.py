"""Streamlit web application for Fitbod workout report generation."""

import json
import os
import tempfile
import time
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.data.processor import process_data_from_df
from src.data.validator import validate_data_structure
from src.pdf.generator import convert_to_pdf
from src.report.generator import (
    PeriodType,
    detect_timezone,
    format_timezone_display,
    generate_gpt_report,
    generate_json_report,
    generate_markdown_report,
    generate_yaml_report,
    get_available_timezones,
    summarize_workouts,
)
from src.utils.converters import seconds_to_time

# Period types that support calendar-aligned grouping (vs rolling windows)
_CALENDAR_TYPES = frozenset({PeriodType.MONTHLY, PeriodType.QUARTERLY, PeriodType.HALF_YEARLY, PeriodType.YEARLY})


def monitor_performance(operation_name):
    """Monitor performance of operations."""
    start_time = time.time()
    return lambda: time.time() - start_time


@st.cache_data
def load_and_validate_data(file_data):
    """Cache the data loading and validation process."""
    df = pd.read_csv(file_data)
    is_valid, missing_cols = validate_data_structure(df, is_dataframe=True)
    if not is_valid:
        raise ValueError(f"Invalid CSV structure. Missing columns: {', '.join(missing_cols)}")
    return df


@st.cache_data
def prepare_date_filtered_data(df, start_date, end_date):
    """Cache the date filtering process."""
    date_series = pd.to_datetime(df["Date"])
    mask = (date_series.dt.date >= start_date) & (date_series.dt.date <= end_date)
    filtered_df = df[mask].copy()

    filtered_df["Date"] = pd.to_datetime(filtered_df["Date"])
    if filtered_df["Date"].dt.tz is None:
        filtered_df["Date"] = filtered_df["Date"].dt.tz_localize("UTC")

    return filtered_df


@st.cache_data(ttl=3600)
def get_timezone_options():
    """Cache timezone list and formatted display names (refreshed hourly for DST changes)."""
    available = get_available_timezones()
    formatted = [format_timezone_display(tz) for tz in available]
    return available, formatted


@st.cache_data
def _process_data(filtered_df):
    """Cache the DataFrame-to-records conversion (independent of report settings)."""
    return process_data_from_df(filtered_df)


@st.cache_data
def process_and_summarize(filtered_df, unit_system, tz_name, period_type, calendar_aligned=False):
    """Process data and generate summaries with caching."""
    processed_data = _process_data(filtered_df)

    # Use daily granularity for calendar-aligned periods to prevent cross-boundary bleed
    if period_type == PeriodType.DAILY:
        group_by = "day"
    elif calendar_aligned and period_type in _CALENDAR_TYPES:
        group_by = "day"
    else:
        group_by = "week"
    return summarize_workouts(processed_data, use_metric=(unit_system == "metric"), tz_name=tz_name, group_by=group_by)


def generate_report_content(summaries, unit_system, report_format, output_format, period_type, calendar_aligned=False):
    """Generate report in the requested output format."""
    use_metric = unit_system == "metric"

    if output_format == "json":
        return generate_json_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    elif output_format == "yaml":
        return generate_yaml_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    elif output_format == "gpt":
        return generate_gpt_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    else:
        return generate_markdown_report(summaries, use_metric, report_format, period_type, calendar_aligned)


def get_download_config(output_format):
    """Get file extension and MIME type for download."""
    configs = {
        "markdown": ("md", "text/markdown"),
        "json": ("json", "application/json"),
        "yaml": ("yaml", "text/yaml"),
        "gpt": ("txt", "text/plain"),
        "pdf": ("pdf", "application/pdf"),
    }
    return configs.get(output_format, ("md", "text/markdown"))


def render_copy_for_fitbod_gpt(report_content):  # noqa: E501
    """Render a lightweight clipboard button for GPT exports."""
    btn_style = "background:#111827;color:#fff;border:none;border-radius:8px;padding:10px 14px;cursor:pointer;font-size:14px;"
    escaped = json.dumps(report_content)
    components.html(
        f"""
        <div style="display:flex;align-items:center;gap:12px;
                    font-family:system-ui,sans-serif;">
          <button id="copy-fitbod-gpt" style="{btn_style}"
            onclick='navigator.clipboard.writeText({escaped})
              .then(()=>{{
                document.getElementById("copy-fitbod-gpt-status")
                  .textContent="Copied to clipboard.";
              }})
              .catch(()=>{{
                document.getElementById("copy-fitbod-gpt-status")
                  .textContent="Copy failed. Use the preview below.";
              }});'>
            Copy for FitbodGPT
          </button>
          <span id="copy-fitbod-gpt-status"
                style="font-size:13px;color:#374151;"></span>
        </div>
        """,
        height=54,
    )


def handle_file_processing(uploaded_file):
    """Process uploaded file with error handling."""
    try:
        with st.spinner("Processing file..."):
            return load_and_validate_data(uploaded_file), None
    except pd.errors.EmptyDataError:
        return None, "The uploaded file is empty"
    except pd.errors.ParserError:
        return None, "Invalid CSV format"
    except ValueError as ve:
        return None, str(ve)
    except Exception as e:
        return None, f"Error processing file: {e!s}"


def detect_browser_timezone(available_timezones):
    """Detect timezone using st.context (browser) with alias mapping and tzlocal fallback."""
    browser_tz = getattr(st.context, "timezone", None)
    detected = detect_timezone(available_timezones, candidate=browser_tz)
    return available_timezones.index(detected)


# Page config
st.set_page_config(
    page_title="Fitbod Report Generator",
    page_icon=":material/fitness_center:",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/rhnfzl/fitbod-report/issues",
        "Report a bug": "https://github.com/rhnfzl/fitbod-report/issues/new",
        "About": "Fitbod Workout Analysis Tool v0.2.0",
    },
)

st.logo("assets/fitbod-logo.svg", link="https://fitbod.me")
st.title(":material/fitness_center: Workout Report Generator")
st.markdown("""
Analyze your [Fitbod](https://fitbod.me) workout data and generate structured reports,
optimized for AI assistants (ChatGPT, Claude, Gemini) or your own review.
Upload your exported workout data to get started!

**Export formats**: Markdown, JSON, YAML (structured for AI tools), PDF (for printing).
Supports metric and imperial units, daily/weekly/monthly/quarterly/yearly grouping,
and detailed set-by-set or summary views.
""")

# File uploader
uploaded_file = st.file_uploader(
    "Upload your Fitbod export (CSV file)",
    type=["csv"],
    key="fitbod_upload",
    help="Upload the CSV file exported from your Fitbod app. "
    "To export: Open Fitbod app > Log > Settings > Export Workout Data",
)

if uploaded_file is not None:
    df, error = handle_file_processing(uploaded_file)
    if error:
        st.error(error)
        st.stop()

    try:
        date_series = pd.to_datetime(df["Date"])
        min_date = date_series.min()
        max_date = date_series.max()

        # Tabs for Report Generator and Data Preview
        tab_report, tab_data = st.tabs(["Report Generator", "Data Preview"])

        with tab_data:
            st.subheader("Raw Workout Data")
            st.dataframe(df, width="stretch")

        with tab_report:
            # Date range selector
            st.subheader("Select Date Range")

            # Quick-select presets
            preset = st.radio(
                "Quick Select",
                [
                    "Last 3 Months",
                    "Last 6 Months",
                    "This Quarter",
                    "This Year",
                    "Last Year",
                    "All Data",
                    "Custom",
                ],
                horizontal=True,
                key="date_preset",
                help="Rolling presets count back from your latest workout. Calendar presets align to boundaries.",
            )

            data_start = min_date.date()
            data_end = max_date.date()

            if preset == "Custom":
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input(
                        "Start Date",
                        data_start,
                        min_value=data_start,
                        max_value=data_end,
                        help="Select the start date for your workout analysis",
                    )
                with col2:
                    end_date = st.date_input(
                        "End Date",
                        data_end,
                        min_value=data_start,
                        max_value=data_end,
                        help="Select the end date for your workout analysis",
                    )
            else:
                if preset == "Last 3 Months":
                    start_date = max(data_end - timedelta(days=90), data_start)
                    end_date = data_end
                elif preset == "Last 6 Months":
                    start_date = max(data_end - timedelta(days=182), data_start)
                    end_date = data_end
                elif preset == "This Quarter":
                    q_month = ((data_end.month - 1) // 3) * 3 + 1
                    start_date = max(data_end.replace(month=q_month, day=1), data_start)
                    end_date = data_end
                elif preset == "This Year":
                    start_date = max(data_end.replace(month=1, day=1), data_start)
                    end_date = data_end
                elif preset == "Last Year":
                    start_date = max(data_end.replace(year=data_end.year - 1, month=1, day=1), data_start)
                    end_date = min(data_end.replace(year=data_end.year - 1, month=12, day=31), data_end)
                else:  # All Data
                    start_date = data_start
                    end_date = data_end
                st.caption(f"{start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")

            # Filter data
            filtered_df = prepare_date_filtered_data(df, start_date, end_date)

            if filtered_df.empty:
                st.warning("No data available for the selected date range.")
                st.stop()

            # Report settings
            st.subheader("Report Settings")
            col3, col4, col5, col6 = st.columns(4)
            with col3:
                unit_system = st.selectbox(
                    "Unit System",
                    ["metric", "imperial"],
                    index=0,
                    key="unit_system",
                    help="Choose metric (kg, km) or imperial (lbs, miles) units for your report",
                )
            with col4:
                report_format = st.selectbox(
                    "Report Format",
                    ["summary", "detailed"],
                    index=0,
                    key="report_format",
                    help="Summary: Key metrics only. Detailed: Includes set-by-set breakdown",
                )
            with col5:
                output_format = st.selectbox(
                    "Output Format",
                    ["gpt", "markdown", "json", "yaml", "pdf"],
                    index=0,
                    key="output_format",
                    help="GPT: Token-efficient for FitbodGPT. Markdown/JSON/YAML: Text. PDF: Formatted document",
                )
            with col6:
                available_timezones, formatted_timezones = get_timezone_options()

                if "detected_timezone_index" not in st.session_state:
                    st.session_state.detected_timezone_index = detect_browser_timezone(available_timezones)

                timezone_display = st.selectbox(
                    "Timezone",
                    formatted_timezones,
                    index=st.session_state.detected_timezone_index,
                    key="timezone_select",
                    help="Select your timezone for accurate date and time handling in the report",
                )
                selected_timezone = available_timezones[formatted_timezones.index(timezone_display)]

            # Summary period
            st.subheader("Summary Options")
            col_period, col_grouping = st.columns([3, 2])
            with col_period:
                period_type = st.selectbox(
                    "Summary Period",
                    [pt.value for pt in PeriodType],
                    index=1,
                    key="period_type",
                    help="Daily: day-by-day. Weekly: week-by-week. Others: broader trends",
                )
                period_type = PeriodType(period_type)
            with col_grouping:
                if period_type in _CALENDAR_TYPES:
                    calendar_aligned = st.toggle(
                        "Calendar-aligned",
                        value=False,
                        key="calendar_aligned",
                        help="Off: rolling windows from your first workout (e.g. quarterly = 13 weeks). "
                        "On: aligned to calendar boundaries (e.g. Q1 = Jan-Mar).",
                    )
                else:
                    calendar_aligned = False

            effective_period_type = period_type
            effective_calendar_aligned = calendar_aligned
            if output_format == "gpt":
                effective_period_type = PeriodType.WEEKLY
                effective_calendar_aligned = False
                st.info("GPT export is weekly-only for FitbodGPT. Non-weekly summary selections are ignored for this format.")

            # Performance warning
            if report_format == "detailed":
                days_count = (end_date - start_date).days
                if period_type == PeriodType.DAILY and days_count > 60:
                    st.warning(
                        "Detailed daily reports for periods longer than 60 days may be slow."
                        " Consider using summary format or reducing the date range."
                    )
                elif days_count // 7 > 12:
                    st.warning(
                        "Detailed reports for long periods may be slow."
                        " Consider using summary format or reducing the date range."
                    )

            # Generate button
            if st.button("Generate Report", key="generate_btn", help="Click to generate your workout report"):
                with st.spinner("Generating report..."):
                    try:
                        timer = monitor_performance("Report Generation")

                        # Process and summarize
                        summaries = process_and_summarize(
                            filtered_df, unit_system, selected_timezone, effective_period_type, effective_calendar_aligned
                        )

                        # Store summaries and precomputed totals
                        st.session_state.summaries = summaries
                        st.session_state.summary_totals = {
                            "cardio": sum(s.get("cardio_duration", 0) for s in summaries.values()),
                            "strength": sum(s.get("strength_duration", 0) for s in summaries.values()),
                            "reps": sum(s.get("Reps", 0) for s in summaries.values()),
                            "volume": sum(s.get("Volume", 0) for s in summaries.values()),
                        }

                        # Generate report content (PDF uses markdown as intermediate)
                        effective_format = "markdown" if output_format == "pdf" else output_format
                        st.session_state.report_content = generate_report_content(
                            summaries,
                            unit_system,
                            report_format,
                            effective_format,
                            effective_period_type,
                            effective_calendar_aligned,
                        )
                        # Store generation settings to detect stale reports
                        st.session_state.report_settings = {
                            "output_format": output_format,
                            "unit_system": unit_system,
                            "report_format": report_format,
                            "period_type": effective_period_type,
                            "calendar_aligned": effective_calendar_aligned,
                        }

                        duration = timer()
                        if duration > 5:
                            st.warning(
                                f"Report generation took {duration:.2f}s. Consider summary format or a shorter date range."
                            )

                    except Exception as e:
                        st.error(f"Error generating report: {e!s}")
                        st.stop()

            # Display results after generation
            if st.session_state.get("report_content") is not None:
                # Check if settings changed since generation
                gen_settings = st.session_state.get("report_settings", {})
                current_settings = {
                    "output_format": output_format,
                    "unit_system": unit_system,
                    "report_format": report_format,
                    "period_type": effective_period_type,
                    "calendar_aligned": effective_calendar_aligned,
                }
                if gen_settings != current_settings:
                    st.warning("Report settings have changed since last generation. Click 'Generate Report' to update.")

                st.markdown("---")

                # Summary metrics (use precomputed totals with stored unit system)
                totals = st.session_state.get("summary_totals")
                gen_unit = gen_settings.get("unit_system", unit_system)
                if totals:
                    weight_unit = "kg" if gen_unit == "metric" else "lbs"
                    num_periods = len(st.session_state.get("summaries", {}))
                    gen_period = gen_settings.get("period_type", period_type)

                    m1, m2, m3, m4 = st.columns(4)
                    gen_cal = gen_settings.get("calendar_aligned", False)
                    if gen_period == PeriodType.DAILY or (gen_cal and gen_period in _CALENDAR_TYPES):
                        period_label = f"{num_periods} days"
                    else:
                        period_label = f"{num_periods} weeks"
                    m1.metric("Workout Periods", period_label)
                    m2.metric("Total Time", seconds_to_time(totals["cardio"] + totals["strength"]))
                    m3.metric("Total Reps", f"{totals['reps']:,}")
                    m4.metric("Total Volume", f"{totals['volume']:,.0f} {weight_unit}")

                # Download button (use stored format to match content)
                report_content = st.session_state.report_content
                gen_format = gen_settings.get("output_format", output_format)
                ext, mime = get_download_config(gen_format)

                if gen_format == "pdf":
                    pdf_path = os.path.join(tempfile.gettempdir(), f"workout_report_{datetime.now().strftime('%Y%m%d')}.pdf")
                    convert_to_pdf(report_content, pdf_path)
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            "Download Report",
                            f.read(),
                            file_name=f"workout_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                            mime="application/pdf",
                        )
                    os.unlink(pdf_path)
                else:
                    st.download_button(
                        "Download Report",
                        report_content,
                        file_name=f"workout_report_{datetime.now().strftime('%Y%m%d')}.{ext}",
                        mime=mime,
                    )
                    if gen_format == "gpt":
                        render_copy_for_fitbod_gpt(report_content)

                # Report preview
                st.subheader("Report Preview")
                if gen_format == "gpt":
                    st.info("Copy the report below and paste it into FitbodGPT in ChatGPT.")
                preview_lang = {"json": "json", "yaml": "yaml", "gpt": None}.get(gen_format, "markdown")
                st.code(report_content, language=preview_lang, line_numbers=True)

    except Exception as e:
        st.error(f"Error processing file: {e!s}")
