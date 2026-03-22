"""Report generation utilities for workout data.

This module provides functionality to generate workout summary reports from processed
workout data. It includes functions to summarize workout data by week and generate
formatted markdown reports.

The module handles both cardio and strength training exercises, calculating various
metrics like total volume, distance, duration, and week-over-week changes.
"""

import json
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo

import tzlocal
import yaml

from ..utils.converters import convert_units, seconds_to_time


class PeriodType(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HALF_YEARLY = "half-yearly"
    YEARLY = "yearly"
    FOUR_WEEKS = "4-weeks"
    EIGHT_WEEKS = "8-weeks"
    TWELVE_WEEKS = "12-weeks"
    TWENTY_FOUR_WEEKS = "24-weeks"


def _get_timezone_groups():
    """Get timezone groups mapping primary zones to their aliases.

    Returns:
        dict: Region -> {primary_zone: [alias_zones]} mapping
    """
    return {
        "Europe": {
            # UTC+1 (CET)
            "Europe/Paris": [
                "Europe/Amsterdam",
                "Europe/Berlin",
                "Europe/Brussels",
                "Europe/Copenhagen",
                "Europe/Madrid",
                "Europe/Oslo",
                "Europe/Rome",
                "Europe/Stockholm",
                "Europe/Vienna",
                "Europe/Warsaw",
                "Europe/Zurich",
            ],
            # UTC+0 (GMT/WET)
            "Europe/London": ["Europe/Dublin", "Europe/Lisbon"],
            # UTC+2 (EET)
            "Europe/Helsinki": ["Europe/Athens", "Europe/Bucharest", "Europe/Sofia"],
            # UTC+3
            "Europe/Moscow": ["Europe/Istanbul", "Europe/Minsk"],
        },
        "Americas": {
            # UTC-5 (EST)
            "America/New_York": ["America/Toronto", "America/Detroit", "America/Montreal"],
            # UTC-6 (CST)
            "America/Chicago": ["America/Mexico_City", "America/Winnipeg"],
            # UTC-7 (MST)
            "America/Denver": ["America/Phoenix", "America/Edmonton"],
            # UTC-8 (PST)
            "America/Los_Angeles": ["America/Vancouver", "America/Tijuana"],
            "America/Sao_Paulo": ["America/Buenos_Aires", "America/Santiago"],
        },
        "Asia": {
            "Asia/Dubai": ["Asia/Muscat", "Asia/Baku"],
            "Asia/Kolkata": ["Asia/Colombo"],
            "Asia/Bangkok": ["Asia/Jakarta", "Asia/Hanoi"],
            "Asia/Shanghai": [
                "Asia/Hong_Kong",
                "Asia/Taipei",
                "Asia/Manila",
                "Asia/Singapore",
                "Asia/Kuala_Lumpur",
            ],
            "Asia/Tokyo": ["Asia/Seoul"],
        },
        "Pacific": {
            "Australia/Sydney": ["Australia/Melbourne", "Australia/Hobart"],
            "Australia/Adelaide": [],
            "Australia/Perth": [],
            "Pacific/Auckland": [],
        },
    }


def _build_alias_map():
    """Build alias -> primary timezone mapping from timezone groups.

    Returns:
        dict: Maps alias timezone names to their primary zone (e.g. Europe/Amsterdam -> Europe/Paris)
    """
    alias_map = {}
    for _region, zones in _get_timezone_groups().items():
        for primary, aliases in zones.items():
            for alias in aliases:
                alias_map[alias] = primary
    return alias_map


def get_available_timezones():
    """Get list of common timezones with consolidated regions.

    Returns:
        list: List of 25 primary timezone names organized by region
    """
    organized_zones = []
    for _region, zones in _get_timezone_groups().items():
        for primary_zone in zones:
            organized_zones.append(primary_zone)
    organized_zones.append("UTC")
    return organized_zones


def detect_timezone(available_timezones, candidate=None):
    """Detect the user's timezone and find the closest match in available timezones.

    Args:
        available_timezones (list): List of available timezone names
        candidate (str, optional): Pre-detected timezone name (e.g. from browser).
            If None, detects via tzlocal.

    Returns:
        str: Best matching timezone name from available_timezones
    """
    if candidate is None:
        try:
            candidate = str(tzlocal.get_localzone())
        except Exception:
            return available_timezones[0]

    # Direct match
    if candidate in available_timezones:
        return candidate

    # Try alias mapping (e.g., Europe/Amsterdam -> Europe/Paris)
    alias_map = _build_alias_map()
    if candidate in alias_map:
        return alias_map[candidate]

    # Region fallback (e.g., America/Toronto -> first America/* in list)
    if "/" in candidate:
        region = candidate.split("/")[0]
        for tz in available_timezones:
            if tz.startswith(region + "/"):
                return tz

    return available_timezones[0]


def format_timezone_display(tz):
    """Format timezone for display in UI with offset.

    Args:
        tz (str): Timezone name

    Returns:
        str: Formatted timezone name for display
    """
    try:
        tz_obj = ZoneInfo(tz)
        offset = datetime.now(tz_obj).strftime("%z")
        offset_str = f"{offset[:3]}:{offset[3:]}"

        if "/" in tz:
            region, city = tz.split("/", 1)
            return f"{region} - {city.replace('_', ' ')} (UTC{offset_str})"
        return f"{tz} (UTC{offset_str})"
    except Exception:
        # Fallback if timezone operations fail
        if "/" in tz:
            region, city = tz.split("/", 1)
            return f"{region} - {city.replace('_', ' ')}"
        return tz


def summarize_workouts(processed_data, use_metric=True, tz_name="UTC", group_by="week"):
    """Summarize processed workout data into period-based summaries.

    Processes workout data and generates summaries grouped by day or week, including:
    - Exercise volumes and distances
    - Total workout durations (cardio and strength)
    - Exercise details and progression
    - Period-over-period changes in key metrics

    Args:
        processed_data (list): List of workout entries with exercise details
        use_metric (bool): Whether to use metric units (True) or imperial units (False)
        tz_name (str): Timezone name for date calculations (e.g. 'UTC', 'Europe/Amsterdam')
        group_by (str): Grouping level - 'week' for weekly summaries, 'day' for daily

    Returns:
        dict: Summaries keyed by date ('YYYY-MM-DD') or week range ('YYYY-MM-DD to YYYY-MM-DD')
    """
    summaries = {}
    tz = ZoneInfo(tz_name)

    # First, organize and clean data by date
    workouts_by_date = {}
    for entry in processed_data:
        # Parse date - handle both datetime objects (DataFrame path) and strings (CLI path)
        date_value = entry["Date"]
        if isinstance(date_value, datetime):
            date_utc = date_value
        else:
            date_str = str(date_value)
            if "+" in date_str:
                date_str = date_str.split("+")[0].strip()
            try:
                date_utc = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    date_utc = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    date_utc = datetime.strptime(date_str, "%Y-%m-%d")

        # Convert to local timezone for consistent date handling
        local_date = date_utc.replace(tzinfo=UTC).astimezone(tz)
        workout_date = local_date.strftime("%Y-%m-%d")
        if group_by == "day":
            summary_key = workout_date
        else:
            week_start = local_date - timedelta(days=local_date.weekday())
            summary_key = week_start.strftime("%Y-%m-%d") + " to " + (week_start + timedelta(days=6)).strftime("%Y-%m-%d")

        # Extract exercise metrics - store original weight
        weight = float(entry["Weight(kg)"])  # Keep original weight
        reps = int(float(entry["Reps"]))
        distance_m = float(entry["Distance(m)"])
        try:
            duration = float(entry["Duration(s)"]) if entry["Duration(s)"] else 0.0
        except (ValueError, TypeError):
            duration = 0.0

        # Convert weight if using imperial
        if not use_metric:
            weight, _ = convert_units(weight, "weight", to_metric=False)
            # Store the rounded weight for volume calculations
            rounded_weight = weight
        else:
            rounded_weight = weight

        # Classify exercise type based on metrics
        is_cardio = (
            (duration > 0 and distance_m > 0)  # Running, Walking etc
            or (reps == 0 and distance_m == 0 and duration > 300)  # Elliptical, Rowing etc
        )

        # Strength exercises are anything not cardio meeting specific criteria
        is_strength = not is_cardio and (
            (reps == 0 and weight > 0)  # Kettlebell Single Arm Farmer Walk, Sled Push etc
            or (reps > 0 and weight == 0 and duration == 0)  # Air Squats, Bench Dip etc
            or (reps > 0 and weight > 0)  # Deadlift, Cable Face Pull etc
            or (reps > 0 and distance_m == 0)  # Bent Over Barbell Row etc
            or (reps == 0 and distance_m == 0)  # Dead Hang, Plank etc
        )

        # Create cleaned entry with additional metadata
        cleaned_entry = {
            **entry,
            "local_datetime": local_date,
            "is_cardio": is_cardio,
            "is_strength": is_strength,
            "duration": duration,
            "weight": rounded_weight,  # Use rounded weight
            "weight_unit": "lbs" if not use_metric else "kg",
            "reps": reps,
            "distance_m": distance_m,
        }

        # Initialize workout data structure if needed
        if workout_date not in workouts_by_date:
            workouts_by_date[workout_date] = {
                "exercises": [],
                "summary_key": summary_key,
            }

        workout_data = workouts_by_date[workout_date]
        workout_data["exercises"].append(cleaned_entry)

    # Build strength sessions from timestamp-sorted exercises (order-independent)
    for workout_data in workouts_by_date.values():
        strength_exercises = sorted(
            (ex for ex in workout_data["exercises"] if ex["is_strength"]),
            key=lambda ex: ex["local_datetime"],
        )
        sessions = []
        for ex in strength_exercises:
            assigned = False
            for session in sessions:
                if abs((ex["local_datetime"] - session[-1]["local_datetime"]).total_seconds()) <= 1800:
                    session.append(ex)
                    assigned = True
                    break
            if not assigned:
                sessions.append([ex])
        workout_data["strength_sessions"] = sessions

    # Process workouts: initialize summaries, calculate durations, accumulate stats
    for _, workout_data in workouts_by_date.items():
        summary_key = workout_data["summary_key"]
        if summary_key not in summaries:
            summaries[summary_key] = {
                "cardio_duration": 0,
                "strength_duration": 0,
                "Distance": 0,
                "Reps": 0,
                "Volume": 0,
                "Distance_by_exercise": {},
                "Volume_by_exercise": {},
                "Exercise_details": {},
                "Workouts": {},
            }

        # Calculate strength duration from sessions
        for session in workout_data["strength_sessions"]:
            if len(session) > 0:
                unique_timestamps = len(set(ex["local_datetime"] for ex in session))

                if unique_timestamps > 1:
                    timestamps = sorted(ex["local_datetime"] for ex in session)
                    session_duration = (timestamps[-1] - timestamps[0]).total_seconds()
                    session_duration = max(session_duration, 0)
                else:
                    # Estimate: 2 min per working set, 1 min per warmup set
                    session_duration = sum(120 if ex["isWarmup"].lower() != "true" else 60 for ex in session)

                summaries[summary_key]["strength_duration"] += session_duration

        # Process exercises for statistics
        for exercise in workout_data["exercises"]:
            # Add to workouts timeline
            workout_time = exercise["local_datetime"].strftime("%Y-%m-%d %H:%M")
            if workout_time not in summaries[summary_key]["Workouts"]:
                summaries[summary_key]["Workouts"][workout_time] = []

            # Weight is already in the target unit system (converted at line 244)
            exercise_detail = {
                "exercise": exercise["Exercise"],
                "weight": exercise["weight"],
                "weight_unit": exercise["weight_unit"],
                "reps": exercise["reps"],
                "is_warmup": exercise["isWarmup"].lower() == "true",
                "time": exercise["local_datetime"].strftime("%H:%M"),
                "duration": exercise["duration"],
                "is_cardio": exercise["is_cardio"],
            }

            summaries[summary_key]["Workouts"][workout_time].append(exercise_detail)

            # Update summary statistics
            summaries[summary_key]["Reps"] += exercise["reps"]

            if exercise["is_cardio"]:
                summaries[summary_key]["cardio_duration"] += exercise["duration"]

            # Update exercise details
            if exercise["Exercise"] not in summaries[summary_key]["Exercise_details"]:
                summaries[summary_key]["Exercise_details"][exercise["Exercise"]] = {
                    "sets": [],
                    "total_volume": 0,
                    "max_weight": 0,
                    "total_reps": 0,
                    "total_duration": 0,
                    "working_sets": 0,
                    "warmup_sets": 0,
                    "is_cardio": exercise["is_cardio"],
                }

            details = summaries[summary_key]["Exercise_details"][exercise["Exercise"]]
            details["sets"].append(
                {
                    "weight": exercise["weight"],  # Already rounded
                    "reps": exercise["reps"],
                    "is_warmup": exercise["isWarmup"].lower() == "true",
                    "duration": exercise["duration"],
                    "is_cardio": exercise["is_cardio"],
                }
            )
            # Calculate volume using rounded weight
            volume = exercise["weight"] * exercise["reps"]
            details["total_volume"] += volume
            details["max_weight"] = max(details["max_weight"], exercise["weight"])
            details["total_reps"] += exercise["reps"]
            details["total_duration"] += exercise["duration"]

            if exercise["isWarmup"].lower() == "true":
                details["warmup_sets"] += 1
            else:
                details["working_sets"] += 1

            # Accumulate distance in target unit (source is always meters)
            distance_km = exercise["distance_m"] / 1000
            if use_metric:
                distance = distance_km
            else:
                distance = distance_km * 0.621371  # km -> miles
            summaries[summary_key]["Distance"] += distance

            # Add to distance by exercise if applicable
            if distance > 0:
                if exercise["Exercise"] not in summaries[summary_key]["Distance_by_exercise"]:
                    summaries[summary_key]["Distance_by_exercise"][exercise["Exercise"]] = 0
                summaries[summary_key]["Distance_by_exercise"][exercise["Exercise"]] += distance

            # Add to volume by exercise if applicable
            summaries[summary_key]["Volume"] += volume
            if volume > 0:
                if exercise["Exercise"] not in summaries[summary_key]["Volume_by_exercise"]:
                    summaries[summary_key]["Volume_by_exercise"][exercise["Exercise"]] = 0
                summaries[summary_key]["Volume_by_exercise"][exercise["Exercise"]] += volume

    return summaries


# Backward-compatible alias
summarize_by_week = summarize_workouts


def _parse_summary_key(key):
    """Parse a summary key to extract start and end dates.

    Handles both daily keys ('YYYY-MM-DD') and weekly keys ('YYYY-MM-DD to YYYY-MM-DD').

    Returns:
        tuple: (start_date_str, end_date_str)
    """
    if " to " in key:
        parts = key.split(" to ")
        return parts[0], parts[1]
    return key, key


def _period_key_to_date(key):
    """Convert any period key format to a datetime for sorting.

    Handles: YYYY-MM-DD, YYYY-MM-DD to YYYY-MM-DD, YYYY-MM, YYYY-QN, YYYY-HN, YYYY.
    """
    if " to " in key:
        return datetime.strptime(key.split(" to ")[0], "%Y-%m-%d")
    if "-Q" in key:
        year, q = key.split("-Q")
        month = (int(q) - 1) * 3 + 1
        return datetime(int(year), month, 1)
    if "-H" in key:
        year, h = key.split("-H")
        month = 1 if h == "1" else 7
        return datetime(int(year), month, 1)
    if len(key) == 4 and key.isdigit():
        return datetime(int(key), 1, 1)
    if len(key) == 7 and key[4] == "-":
        return datetime.strptime(key, "%Y-%m")
    return datetime.strptime(key, "%Y-%m-%d")


_ROLLING_WEEKS = {
    PeriodType.MONTHLY: 4,
    PeriodType.QUARTERLY: 13,
    PeriodType.HALF_YEARLY: 26,
    PeriodType.YEARLY: 52,
}


def aggregate_summaries(summaries, period_type, calendar_aligned=False):
    """Aggregate weekly summaries into larger periods.

    Args:
        summaries (dict): Weekly summaries from summarize_workouts()
        period_type (str): Period type ('monthly', 'quarterly', 'half-yearly', 'yearly', '4-weeks', etc.)
        calendar_aligned (bool): If True, use calendar boundaries (Q1=Jan-Mar).
            If False (default), use rolling N-week windows from first data point.

    Returns:
        dict: Aggregated summaries by period
    """
    sorted_weeks = sorted(summaries.keys(), key=lambda x: datetime.strptime(_parse_summary_key(x)[0], "%Y-%m-%d"))

    if not sorted_weeks:
        return {}

    aggregated = {}

    # Get the first week's start date
    first_week_start = datetime.strptime(_parse_summary_key(sorted_weeks[0])[0], "%Y-%m-%d")

    use_calendar = calendar_aligned and period_type in _ROLLING_WEEKS

    for week in sorted_weeks:
        week_start = datetime.strptime(_parse_summary_key(week)[0], "%Y-%m-%d")
        week_summary = summaries[week]

        if use_calendar and period_type == PeriodType.MONTHLY:
            period_key = week_start.strftime("%Y-%m")
            period_name = week_start.strftime("%B %Y")
        elif use_calendar and period_type == PeriodType.QUARTERLY:
            quarter = (week_start.month - 1) // 3 + 1
            period_key = f"{week_start.year}-Q{quarter}"
            month_names = {1: "Jan-Mar", 2: "Apr-Jun", 3: "Jul-Sep", 4: "Oct-Dec"}
            period_name = f"Q{quarter} {week_start.year} ({month_names[quarter]})"
        elif use_calendar and period_type == PeriodType.HALF_YEARLY:
            half = 1 if week_start.month <= 6 else 2
            period_key = f"{week_start.year}-H{half}"
            month_names = {1: "Jan-Jun", 2: "Jul-Dec"}
            period_name = f"H{half} {week_start.year} ({month_names[half]})"
        elif use_calendar and period_type == PeriodType.YEARLY:
            period_key = str(week_start.year)
            period_name = str(week_start.year)
        else:
            # Rolling N-week windows from first data point
            weeks_number = _ROLLING_WEEKS.get(period_type) or int(period_type.split("-")[0])
            period_number = (week_start - first_week_start).days // (7 * weeks_number)
            period_start = first_week_start + timedelta(days=period_number * 7 * weeks_number)
            period_end = period_start + timedelta(days=7 * weeks_number - 1)
            period_key = period_start.strftime("%Y-%m-%d")
            period_name = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"

        if period_key not in aggregated:
            aggregated[period_key] = {
                "period_name": period_name,
                "cardio_duration": 0,
                "strength_duration": 0,
                "Distance": 0,
                "Reps": 0,
                "Volume": 0,
                "Distance_by_exercise": {},
                "Volume_by_exercise": {},
                "Exercise_details": {},
                "Workouts": {},
                "weeks": [],
            }

        period_summary = aggregated[period_key]
        period_summary["weeks"].append(week)

        # Aggregate numeric metrics
        period_summary["cardio_duration"] += week_summary.get("cardio_duration", 0)
        period_summary["strength_duration"] += week_summary.get("strength_duration", 0)
        period_summary["Distance"] += week_summary.get("Distance", 0)
        period_summary["Reps"] += week_summary.get("Reps", 0)
        period_summary["Volume"] += week_summary.get("Volume", 0)

        # Aggregate exercise-specific metrics
        for exercise, distance in week_summary.get("Distance_by_exercise", {}).items():
            if exercise not in period_summary["Distance_by_exercise"]:
                period_summary["Distance_by_exercise"][exercise] = 0
            period_summary["Distance_by_exercise"][exercise] += distance

        for exercise, volume in week_summary.get("Volume_by_exercise", {}).items():
            if exercise not in period_summary["Volume_by_exercise"]:
                period_summary["Volume_by_exercise"][exercise] = 0
            period_summary["Volume_by_exercise"][exercise] += volume

        # Aggregate detailed workout information
        for workout_time, exercises in week_summary.get("Workouts", {}).items():
            period_summary["Workouts"][workout_time] = exercises

        # Aggregate exercise details
        for exercise, details in week_summary.get("Exercise_details", {}).items():
            if exercise not in period_summary["Exercise_details"]:
                period_summary["Exercise_details"][exercise] = {
                    "sets": [],
                    "total_volume": 0,
                    "max_weight": 0,
                    "total_reps": 0,
                    "total_duration": 0,
                    "working_sets": 0,
                    "warmup_sets": 0,
                    "is_cardio": details["is_cardio"],
                }

            ex_details = period_summary["Exercise_details"][exercise]
            ex_details["sets"].extend(details["sets"])
            ex_details["total_volume"] += details["total_volume"]
            ex_details["max_weight"] = max(ex_details["max_weight"], details["max_weight"])
            ex_details["total_reps"] += details["total_reps"]
            ex_details["total_duration"] += details.get("total_duration", 0)
            ex_details["working_sets"] += details["working_sets"]
            ex_details["warmup_sets"] += details["warmup_sets"]

    return aggregated


def _format_summary_stats(summary, distance_unit, weight_unit, previous_summary=None, label_prefix=""):
    """Format summary statistics lines for markdown output.

    Args:
        summary (dict): Summary data with cardio_duration, strength_duration, Distance, etc.
        distance_unit (str): Unit for distance display
        weight_unit (str): Unit for weight display
        previous_summary (dict, optional): Previous period's summary for change calculations
        label_prefix (str): Prefix for labels (e.g. "Total " for overall summary)

    Returns:
        list: Lines of markdown text for summary statistics
    """
    lines = []
    cardio = summary.get("cardio_duration", 0)
    strength = summary.get("strength_duration", 0)

    lines.append(f"- Total Workout Time: {seconds_to_time(cardio + strength)}")
    lines.append(f"- {label_prefix}Strength Training Time: {seconds_to_time(strength)}")
    lines.append(f"- {label_prefix}Cardio Time: {seconds_to_time(cardio)}")
    lines.append(f"- Total Distance: {summary.get('Distance', 0):.2f} {distance_unit}")
    lines.append(f"- Total Reps: {summary.get('Reps', 0)}")
    lines.append(f"- Total Volume: {summary.get('Volume', 0):.2f} {weight_unit}*reps")

    if previous_summary:
        prev_dist = previous_summary.get("Distance", 0)
        prev_vol = previous_summary.get("Volume", 0)
        if prev_dist != 0:
            pct = (summary.get("Distance", 0) - prev_dist) / prev_dist * 100
            lines.append(f"- Distance Change: {pct:.2f}%")
        if prev_vol != 0:
            pct = (summary.get("Volume", 0) - prev_vol) / prev_vol * 100
            lines.append(f"- Volume Change: {pct:.2f}%")

    return lines


def _render_detailed_exercises(report, period_key, exercise_data, weight_unit, show_date_headers=False):
    """Render detailed exercise tables and details for a period.

    Args:
        report (list): Lines list to append to
        period_key (str): Key into exercise_data (date or week range)
        exercise_data (dict): Pre-processed exercise data
        weight_unit (str): Weight unit for display
        show_date_headers (bool): Whether to show date subheadings (True for weekly)
    """
    report.append("### Daily Workouts\n" if show_date_headers else "### Workouts\n")

    for workout_date in sorted(exercise_data[period_key]["by_date"].keys()):
        if show_date_headers:
            report.append(f"#### {workout_date}\n")

        for exercise_name in sorted(exercise_data[period_key]["by_date"][workout_date].keys()):
            exercise_sets = exercise_data[period_key]["by_date"][workout_date][exercise_name]
            report.append(f"**{exercise_name}** ({len(exercise_sets)} sets)")
            report.append("| Set | Reps | Weight | Type |")
            report.append("|-----|------|---------|------|")

            for i, set_info in enumerate(exercise_sets, 1):
                report.append(
                    f"| {i} | {set_info['reps']} | "
                    f"{set_info['weight']:.1f} {set_info['weight_unit']} | "
                    f"{'Warmup' if set_info['is_warmup'] else 'Working'} |"
                )
            report.append("")

    report.append("### Exercise Details\n")
    for exercise_name in sorted(exercise_data[period_key]["details"].keys()):
        details = exercise_data[period_key]["details"][exercise_name]
        report.append(f"#### {exercise_name}")
        report.append(f"- Working Sets: {details['working_sets']}")
        report.append(f"- Warmup Sets: {details['warmup_sets']}")
        report.append(f"- Total Reps: {details['total_reps']}")
        if details["is_cardio"]:
            report.append(f"- Total Duration: {seconds_to_time(details['total_duration'])}")
        report.append(f"- Max Weight: {details['max_weight']:.1f} {weight_unit}")
        report.append(f"- Total Volume: {details['total_volume']:.1f} {weight_unit}*reps")

        report.append("\nSet Progression:")
        report.append("| Set | Weight | Reps | Type |")
        report.append("|-----|---------|------|------|")

        for i, set_info in enumerate(details["sets"], 1):
            report.append(
                f"| {i} | {set_info['weight']:.1f} {weight_unit} | "
                f"{set_info['reps']} | "
                f"{'Warmup' if set_info['is_warmup'] else 'Working'} |"
            )
        report.append("")


def generate_period_summary(period_name, period_summary, use_metric, previous_period_summary=None, report_format="summary"):
    """Generate markdown summary for a specific period.

    Args:
        period_name (str): Name of the period
        period_summary (dict): Summary data for the period
        use_metric (bool): Whether to use metric units
        previous_period_summary (dict): Previous period's summary for comparison
        report_format (str): Type of report to generate ('summary' or 'detailed')

    Returns:
        list: Lines of markdown text for the period summary
    """
    distance_unit = "km" if use_metric else "miles"
    weight_unit = "kg" if use_metric else "lbs"

    lines = []
    lines.append(f"## {period_name}\n")

    if report_format == "detailed":
        # Daily Workouts
        lines.append("### Daily Workouts\n")
        for workout_time in sorted(period_summary["Workouts"].keys()):
            date = workout_time.split()[0]
            lines.append(f"#### {date}\n")

            # Group exercises by name
            exercises_by_name = {}
            for exercise in period_summary["Workouts"][workout_time]:
                if exercise["exercise"] not in exercises_by_name:
                    exercises_by_name[exercise["exercise"]] = []
                exercises_by_name[exercise["exercise"]].append(exercise)

            # Show exercises grouped
            for exercise_name in sorted(exercises_by_name.keys()):
                exercise_sets = exercises_by_name[exercise_name]
                lines.append(f"**{exercise_name}** ({len(exercise_sets)} sets)")
                lines.append("| Set | Reps | Weight | Type |")
                lines.append("|-----|------|---------|------|")

                for i, set_info in enumerate(exercise_sets, 1):
                    lines.append(
                        f"| {i} | {set_info['reps']} | "
                        f"{set_info['weight']:.1f} {set_info['weight_unit']} | "
                        f"{'Warmup' if set_info['is_warmup'] else 'Working'} |"
                    )
                lines.append("")

        # Exercise Details
        lines.append("### Exercise Details\n")
        for exercise_name in sorted(period_summary["Exercise_details"].keys()):
            details = period_summary["Exercise_details"][exercise_name]
            lines.append(f"#### {exercise_name}")
            lines.append(f"- Working Sets: {details['working_sets']}")
            lines.append(f"- Warmup Sets: {details['warmup_sets']}")
            lines.append(f"- Total Reps: {details['total_reps']}")
            if details["is_cardio"]:
                lines.append(f"- Total Duration: {seconds_to_time(details['total_duration'])}")
            lines.append(f"- Max Weight: {details['max_weight']:.1f} {weight_unit}")
            lines.append(f"- Total Volume: {details['total_volume']:.1f} {weight_unit}*reps")

            # Show set progression
            lines.append("\nSet Progression:")
            lines.append("| Set | Weight | Reps | Type |")
            lines.append("|-----|---------|------|------|")

            # Sort sets by date and time
            sorted_sets = sorted(details["sets"], key=lambda x: (x["is_warmup"], -x["weight"]))
            for i, set_info in enumerate(sorted_sets, 1):
                lines.append(
                    f"| {i} | {set_info['weight']:.1f} {weight_unit} | "
                    f"{set_info['reps']} | "
                    f"{'Warmup' if set_info['is_warmup'] else 'Working'} |"
                )
            lines.append("")
    else:
        # Summary report with just the key metrics
        if period_summary["Distance_by_exercise"]:
            lines.append("### Distance by Exercise")
            for exercise, distance in sorted(period_summary["Distance_by_exercise"].items()):
                lines.append(f"- {exercise}: {distance:.2f} {distance_unit}")
            lines.append("")

        if period_summary["Volume_by_exercise"]:
            lines.append("### Volume by Exercise")
            for exercise, volume in sorted(period_summary["Volume_by_exercise"].items()):
                lines.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
            lines.append("")

    # Summary Statistics (included in both formats)
    lines.append("### Summary Statistics")
    lines.extend(_format_summary_stats(period_summary, distance_unit, weight_unit, previous_period_summary))
    lines.append("\n---\n")
    return lines


def generate_markdown_report(summaries, use_metric=True, report_format="summary", period_type=None, calendar_aligned=False):
    """Generate markdown report from workout summaries.

    Args:
        summaries (dict): Weekly workout summaries from summarize_workouts()
        use_metric (bool): Whether to use metric units (True) or imperial units (False)
        report_format (str): Type of report to generate ('summary' or 'detailed')
        period_type (str): Type of period to aggregate into (None, 'monthly', '4-weeks', etc.)
        calendar_aligned (bool): Use calendar boundaries vs rolling windows

    Returns:
        str: Markdown formatted report containing workout statistics and analysis
    """
    report = ["# Workout Summary Report\n"]

    # Define units once for use throughout the report
    distance_unit = "km" if use_metric else "miles"
    weight_unit = "kg" if use_metric else "lbs"

    # Pre-process exercise data for detailed reports to avoid repeated operations
    exercise_data = {}
    if report_format == "detailed" and period_type in (PeriodType.DAILY, PeriodType.WEEKLY):
        for week, summary in summaries.items():
            exercise_data[week] = {"by_date": {}, "details": {}}
            # Group exercises by date
            for workout_time, exercises in summary.get("Workouts", {}).items():
                date = workout_time.split()[0]
                if date not in exercise_data[week]["by_date"]:
                    exercise_data[week]["by_date"][date] = {}

                for exercise in exercises:
                    exercise_name = exercise["exercise"]
                    if exercise_name not in exercise_data[week]["by_date"][date]:
                        exercise_data[week]["by_date"][date][exercise_name] = []
                    exercise_data[week]["by_date"][date][exercise_name].append(exercise)

            # Pre-process exercise details
            for exercise, details in summary.get("Exercise_details", {}).items():
                exercise_data[week]["details"][exercise] = {
                    "working_sets": details["working_sets"],
                    "warmup_sets": details["warmup_sets"],
                    "total_reps": details["total_reps"],
                    "is_cardio": details["is_cardio"],
                    "total_duration": details.get("total_duration", 0),
                    "max_weight": details["max_weight"],
                    "total_volume": details["total_volume"],
                    "sets": sorted(details["sets"], key=lambda x: (x["is_warmup"], -x["weight"])),
                }

    # Calculate overall totals
    overall_summary = {
        "cardio_duration": 0,
        "strength_duration": 0,
        "Distance": 0,
        "Reps": 0,
        "Volume": 0,
        "Distance_by_exercise": {},
        "Volume_by_exercise": {},
        "start_date": None,
        "end_date": None,
    }

    # Get all periods sorted by date
    sorted_weeks = sorted(summaries.keys(), key=lambda x: datetime.strptime(_parse_summary_key(x)[0], "%Y-%m-%d"))

    if sorted_weeks:
        # Set date range
        overall_summary["start_date"] = _parse_summary_key(sorted_weeks[0])[0]
        overall_summary["end_date"] = _parse_summary_key(sorted_weeks[-1])[1]

        # Aggregate all metrics
        for week in sorted_weeks:
            summary = summaries[week]
            overall_summary["cardio_duration"] += summary.get("cardio_duration", 0)
            overall_summary["strength_duration"] += summary.get("strength_duration", 0)
            overall_summary["Distance"] += summary.get("Distance", 0)
            overall_summary["Reps"] += summary.get("Reps", 0)
            overall_summary["Volume"] += summary.get("Volume", 0)

            # Aggregate exercise-specific metrics
            for exercise, distance in summary.get("Distance_by_exercise", {}).items():
                if exercise not in overall_summary["Distance_by_exercise"]:
                    overall_summary["Distance_by_exercise"][exercise] = 0
                overall_summary["Distance_by_exercise"][exercise] += distance

            for exercise, volume in summary.get("Volume_by_exercise", {}).items():
                if exercise not in overall_summary["Volume_by_exercise"]:
                    overall_summary["Volume_by_exercise"][exercise] = 0
                overall_summary["Volume_by_exercise"][exercise] += volume

    # Generate period summaries if requested and not weekly/daily
    if period_type and period_type not in (PeriodType.WEEKLY, PeriodType.DAILY):
        period_summaries = aggregate_summaries(summaries, period_type, calendar_aligned)
        sorted_periods = sorted(period_summaries.keys())

        report.append(f"# {period_type.title()} Summary\n")
        previous_period_summary = None
        for period_key in sorted_periods:
            period_summary = period_summaries[period_key]
            period_lines = generate_period_summary(
                period_summary["period_name"], period_summary, use_metric, previous_period_summary, report_format
            )
            report.extend(period_lines)
            previous_period_summary = period_summary

    # Generate daily summaries if period_type is daily
    if period_type == PeriodType.DAILY:
        previous_day_summary = None
        for day_key in sorted_weeks:
            summary = summaries[day_key]
            day_of_week = datetime.strptime(day_key, "%Y-%m-%d").strftime("%A")
            report.append(f"## {day_key} ({day_of_week})\n")

            if report_format == "detailed":
                _render_detailed_exercises(report, day_key, exercise_data, weight_unit)
            else:
                # Summary report with just the key metrics
                if summary["Distance_by_exercise"]:
                    report.append("### Distance by Exercise")
                    for exercise, distance in sorted(summary["Distance_by_exercise"].items()):
                        report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
                    report.append("")

                if summary["Volume_by_exercise"]:
                    report.append("### Volume by Exercise")
                    for exercise, volume in sorted(summary["Volume_by_exercise"].items()):
                        report.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
                    report.append("")

            # Summary statistics (included in both formats)
            report.append("### Summary Statistics")
            report.extend(_format_summary_stats(summary, distance_unit, weight_unit, previous_day_summary))
            report.append("\n---\n")
            previous_day_summary = summary

    # Generate weekly summaries if period_type is weekly
    if period_type == PeriodType.WEEKLY:
        previous_week_summary = None
        for week in sorted_weeks:
            summary = summaries[week]
            report.append(f"## Week: {week}\n")

            if report_format == "detailed":
                _render_detailed_exercises(report, week, exercise_data, weight_unit, show_date_headers=True)
            else:
                # Summary report with just the key metrics
                if summary["Distance_by_exercise"]:
                    report.append("### Distance by Exercise")
                    for exercise, distance in sorted(summary["Distance_by_exercise"].items()):
                        report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
                    report.append("")

                if summary["Volume_by_exercise"]:
                    report.append("### Volume by Exercise")
                    for exercise, volume in sorted(summary["Volume_by_exercise"].items()):
                        report.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
                    report.append("")

            # Summary statistics (included in both formats)
            report.append("### Summary Statistics")
            report.extend(_format_summary_stats(summary, distance_unit, weight_unit, previous_week_summary))
            report.append("\n---\n")
            previous_week_summary = summary

    # Add overall summary at the end with clear separation
    report.append(f"\n# Overall Summary for {overall_summary['start_date']} to {overall_summary['end_date']}\n")

    # Distance by Exercise
    if overall_summary["Distance_by_exercise"]:
        report.append("### Total Distance by Exercise")
        for exercise, distance in sorted(overall_summary["Distance_by_exercise"].items()):
            report.append(f"- {exercise}: {distance:.2f} {distance_unit}")
        report.append("")

    # Volume by Exercise
    if overall_summary["Volume_by_exercise"]:
        report.append("### Total Volume by Exercise")
        for exercise, volume in sorted(overall_summary["Volume_by_exercise"].items()):
            report.append(f"- {exercise}: {volume:.2f} {weight_unit}*reps")
        report.append("")

    # Overall Summary Statistics
    report.append("### Overall Summary Statistics")
    report.extend(_format_summary_stats(overall_summary, distance_unit, weight_unit, label_prefix="Total "))

    # Calculate averages per period
    num_periods = len(sorted_weeks)
    if num_periods > 0:
        total_cardio = overall_summary["cardio_duration"]
        total_strength = overall_summary["strength_duration"]
        avg_label = str(period_type).replace("-", " ").title() if period_type else "Weekly"
        report.append(f"\n### {avg_label} Averages")
        report.append(f"- Average Workout Time: {seconds_to_time((total_cardio + total_strength) / num_periods)}")
        report.append(f"- Average Strength Training Time: {seconds_to_time(total_strength / num_periods)}")
        report.append(f"- Average Cardio Time: {seconds_to_time(total_cardio / num_periods)}")
        report.append(f"- Average Distance: {(overall_summary['Distance'] / num_periods):.2f} {distance_unit}")
        report.append(f"- Average Reps: {int(overall_summary['Reps'] / num_periods)}")
        report.append(f"- Average Volume: {(overall_summary['Volume'] / num_periods):.2f} {weight_unit}*reps")

    return "\n".join(report)


def _build_structured_report(summaries, use_metric=True, report_format="summary", period_type=None, calendar_aligned=False):
    """Build a structured dict suitable for JSON/YAML serialization.

    Args:
        summaries (dict): Summaries from summarize_workouts()
        use_metric (bool): Whether to use metric units
        report_format (str): 'summary' or 'detailed'
        period_type (str): Period grouping type
        calendar_aligned (bool): Use calendar boundaries vs rolling windows

    Returns:
        dict: Structured report data
    """
    distance_unit = "km" if use_metric else "miles"
    weight_unit = "kg" if use_metric else "lbs"

    # Use aggregated summaries for non-daily/weekly periods
    if period_type and period_type not in (PeriodType.DAILY, PeriodType.WEEKLY):
        aggregated = aggregate_summaries(summaries, period_type, calendar_aligned)
        effective_summaries = aggregated  # Keys are YYYY-MM or YYYY-MM-DD
    else:
        effective_summaries = summaries

    def _sort_key(x):
        return _period_key_to_date(x)

    sorted_keys = sorted(effective_summaries.keys(), key=_sort_key)

    periods = []
    for key in sorted_keys:
        summary = effective_summaries[key]
        period_name = summary.get("period_name")

        # Parse dates from key or period_name
        if period_name and " to " in period_name:
            start_date, end_date = _parse_summary_key(period_name)
        else:
            d = _period_key_to_date(key)
            start_date = d.strftime("%Y-%m-%d")
            end_date = start_date

        parsed_start = datetime.strptime(start_date, "%Y-%m-%d")

        period_entry = {
            "date": start_date,
            "day_of_week": parsed_start.strftime("%A"),
        }
        if period_name:
            period_entry["period"] = period_name
        if start_date != end_date:
            period_entry["end_date"] = end_date

        # Exercise breakdown
        exercises = []
        for exercise_name in sorted(summary.get("Exercise_details", {}).keys()):
            details = summary["Exercise_details"][exercise_name]
            ex_entry = {
                "name": exercise_name,
                "working_sets": details["working_sets"],
                "warmup_sets": details["warmup_sets"],
                "total_reps": details["total_reps"],
                "max_weight": round(details["max_weight"], 1),
                "weight_unit": weight_unit,
                "total_volume": round(details["total_volume"], 1),
                "is_cardio": details["is_cardio"],
            }
            if details["is_cardio"] and details.get("total_duration", 0) > 0:
                ex_entry["total_duration_seconds"] = round(details["total_duration"], 1)
                ex_entry["total_duration"] = seconds_to_time(details["total_duration"])

            if report_format == "detailed":
                ex_entry["sets"] = [
                    {
                        "weight": round(s["weight"], 1),
                        "weight_unit": weight_unit,
                        "reps": s["reps"],
                        "type": "warmup" if s["is_warmup"] else "working",
                    }
                    for s in details["sets"]
                ]
            exercises.append(ex_entry)

        period_entry["exercises"] = exercises

        # Stats
        cardio_dur = summary.get("cardio_duration", 0)
        strength_dur = summary.get("strength_duration", 0)
        period_entry["stats"] = {
            "total_workout_time": seconds_to_time(cardio_dur + strength_dur),
            "total_workout_seconds": round(cardio_dur + strength_dur, 1),
            "strength_time": seconds_to_time(strength_dur),
            "cardio_time": seconds_to_time(cardio_dur),
            "total_distance": round(summary.get("Distance", 0), 2),
            "distance_unit": distance_unit,
            "total_reps": summary.get("Reps", 0),
            "total_volume": round(summary.get("Volume", 0), 2),
            "volume_unit": f"{weight_unit}*reps",
        }

        periods.append(period_entry)

    # Overall summary (always from original summaries for accurate totals)
    raw_sorted = sorted(summaries.keys(), key=lambda x: datetime.strptime(_parse_summary_key(x)[0], "%Y-%m-%d"))
    overall_start = _parse_summary_key(raw_sorted[0])[0] if raw_sorted else None
    overall_end = _parse_summary_key(raw_sorted[-1])[1] if raw_sorted else None

    total_cardio = sum(s.get("cardio_duration", 0) for s in summaries.values())
    total_strength = sum(s.get("strength_duration", 0) for s in summaries.values())
    total_distance = sum(s.get("Distance", 0) for s in summaries.values())
    total_reps = sum(s.get("Reps", 0) for s in summaries.values())
    total_volume = sum(s.get("Volume", 0) for s in summaries.values())

    overall = {
        "date_range": {"start": overall_start, "end": overall_end},
        "total_workout_time": seconds_to_time(total_cardio + total_strength),
        "total_strength_time": seconds_to_time(total_strength),
        "total_cardio_time": seconds_to_time(total_cardio),
        "total_distance": round(total_distance, 2),
        "distance_unit": distance_unit,
        "total_reps": total_reps,
        "total_volume": round(total_volume, 2),
        "volume_unit": f"{weight_unit}*reps",
    }

    num_periods = len(sorted_keys)
    if num_periods > 0:
        avg_label = str(period_type) if period_type else "weekly"
        overall["averages"] = {
            "period": avg_label,
            "avg_workout_time": seconds_to_time((total_cardio + total_strength) / num_periods),
            "avg_distance": round(total_distance / num_periods, 2),
            "avg_reps": int(total_reps / num_periods),
            "avg_volume": round(total_volume / num_periods, 2),
        }

    return {
        "report_type": str(period_type) if period_type else "weekly",
        "grouping_mode": "calendar" if calendar_aligned else "rolling",
        "unit_system": "metric" if use_metric else "imperial",
        "format": report_format,
        "periods": periods,
        "overall": overall,
    }


def generate_json_report(summaries, use_metric=True, report_format="summary", period_type=None, calendar_aligned=False):
    """Generate a JSON report from workout summaries.

    Args:
        summaries (dict): Summaries from summarize_workouts()
        use_metric (bool): Whether to use metric units
        report_format (str): 'summary' or 'detailed'
        period_type (str): Period grouping type
        calendar_aligned (bool): Use calendar boundaries vs rolling windows

    Returns:
        str: JSON formatted report
    """
    data = _build_structured_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    return json.dumps(data, indent=2, ensure_ascii=False)


def generate_yaml_report(summaries, use_metric=True, report_format="summary", period_type=None, calendar_aligned=False):
    """Generate a YAML report from workout summaries.

    Args:
        summaries (dict): Summaries from summarize_workouts()
        use_metric (bool): Whether to use metric units
        report_format (str): 'summary' or 'detailed'
        period_type (str): Period grouping type
        calendar_aligned (bool): Use calendar boundaries vs rolling windows

    Returns:
        str: YAML formatted report
    """
    data = _build_structured_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    return yaml.safe_dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def generate_gpt_report(summaries, use_metric=True, report_format="summary", period_type=None, calendar_aligned=False):
    """Generate a GPT-optimized compact report for FitbodGPT consumption.

    Outputs a token-efficient TSV format with pre-computed analytics.
    Working sets only (warmups excluded). Includes muscle group volume
    analysis and exercise trend data.

    Args:
        summaries (dict): Summaries from summarize_workouts()
        use_metric (bool): Whether to use metric units
        report_format (str): 'summary' or 'detailed' (detailed adds recent sessions)
        period_type (str): Period grouping type
        calendar_aligned (bool): Use calendar boundaries vs rolling windows

    Returns:
        str: GPT-optimized compact report
    """
    from ..data.exercise_db import clear_unknown_exercises, get_exercise_muscles, get_unknown_exercises

    clear_unknown_exercises()

    weight_unit = "kg" if use_metric else "lbs"
    distance_unit = "km" if use_metric else "miles"

    # Build structured data first (reuse existing logic)
    data = _build_structured_report(summaries, use_metric, report_format, period_type, calendar_aligned)
    periods = data["periods"]
    overall = data["overall"]

    # --- Header ---
    date_range = overall.get("date_range", {})
    start = date_range.get("start", "unknown")
    end = date_range.get("end", "unknown")

    # Count weeks and unique exercises
    num_weeks = len(periods) if periods else 0
    all_exercises = set()
    total_sessions = 0
    for p in periods:
        for ex in p.get("exercises", []):
            all_exercises.add(ex["name"])
        # Estimate sessions from the period (use stats if available)
        total_sessions += 1  # Each period is at least one session block

    # Better session count: count from original summaries
    total_sessions = len(summaries)

    lines = [
        f"date_range: {start} to {end}",
        f"weeks: {num_weeks}",
        f"sessions: {total_sessions}",
        f"unit: {'metric' if use_metric else 'imperial'}",
        f"exercises: {len(all_exercises)}",
        "",
    ]

    # --- Weekly Summary ---
    lines.append("## weekly_summary")
    lines.append(f"week\tsessions\tstrength_min\tcardio_min\tvolume_{weight_unit}\treps\tdistance_{distance_unit}")

    for p in periods:
        stats = p.get("stats", {})
        week_label = p.get("date", "")
        # Count exercises as a proxy for sessions within the period
        strength_sec = 0
        cardio_sec = 0
        if "strength_time" in stats:
            strength_sec = stats.get("total_workout_seconds", 0) - _time_to_seconds(stats.get("cardio_time", "0:00:00"))
        cardio_sec = _time_to_seconds(stats.get("cardio_time", "0:00:00"))

        volume = stats.get("total_volume", 0)
        reps = stats.get("total_reps", 0)
        distance = stats.get("total_distance", 0)

        lines.append(
            f"{week_label}\t1\t{int(strength_sec // 60)}\t{int(cardio_sec // 60)}"
            f"\t{round(volume, 1)}\t{reps}\t{round(distance, 2)}"
        )

    lines.append("")

    # --- Exercise Stats ---
    # Aggregate per-exercise data across all periods
    exercise_data = {}
    exercise_first_period = {}
    exercise_last_period = {}

    for i, p in enumerate(periods):
        for ex in p.get("exercises", []):
            name = ex["name"]
            if ex.get("is_cardio", False):
                continue  # Skip cardio for exercise_stats (tracked in weekly_summary)
            if name not in exercise_data:
                exercise_data[name] = {
                    "sessions": 0,
                    "working_sets": 0,
                    "total_reps": 0,
                    "max_weight": 0,
                    "total_volume": 0,
                    "weight_sum": 0,
                    "weight_count": 0,
                }
                exercise_first_period[name] = i
            exercise_last_period[name] = i

            d = exercise_data[name]
            d["sessions"] += 1
            d["working_sets"] += ex.get("working_sets", 0)
            d["total_reps"] += ex.get("total_reps", 0)
            d["max_weight"] = max(d["max_weight"], ex.get("max_weight", 0))
            d["total_volume"] += ex.get("total_volume", 0)
            if ex.get("max_weight", 0) > 0:
                d["weight_sum"] += ex.get("max_weight", 0)
                d["weight_count"] += 1

    # Calculate per-exercise trends (first half avg vs second half avg of max_weight)
    exercise_trends = {}
    for name in exercise_data:
        first_half_weights = []
        second_half_weights = []
        midpoint = len(periods) // 2
        for i, p in enumerate(periods):
            for ex in p.get("exercises", []):
                if ex["name"] == name and not ex.get("is_cardio", False) and ex.get("max_weight", 0) > 0:
                    if i < midpoint:
                        first_half_weights.append(ex["max_weight"])
                    else:
                        second_half_weights.append(ex["max_weight"])

        if first_half_weights and second_half_weights:
            first_avg = sum(first_half_weights) / len(first_half_weights)
            second_avg = sum(second_half_weights) / len(second_half_weights)
            if first_avg > 0:
                trend = ((second_avg - first_avg) / first_avg) * 100
                exercise_trends[name] = f"{trend:+.1f}%"
            else:
                exercise_trends[name] = "N/A"
        else:
            exercise_trends[name] = "N/A"

    lines.append("## exercise_stats")
    lines.append(f"exercise\tsessions\tworking_sets\ttotal_reps\tmax_{weight_unit}\tavg_{weight_unit}\ttotal_volume\ttrend")

    for name in sorted(exercise_data.keys()):
        d = exercise_data[name]
        avg_weight = round(d["weight_sum"] / d["weight_count"], 1) if d["weight_count"] > 0 else 0
        lines.append(
            f"{name}\t{d['sessions']}\t{d['working_sets']}\t{d['total_reps']}"
            f"\t{round(d['max_weight'], 1)}\t{avg_weight}\t{round(d['total_volume'], 1)}"
            f"\t{exercise_trends.get(name, 'N/A')}"
        )

    lines.append("")

    # --- Muscle Volume ---
    # Aggregate weekly muscle group sets using exercise_db
    muscle_weekly_sets = {}  # muscle -> list of weekly set counts
    for p in periods:
        period_muscles = {}
        for ex in p.get("exercises", []):
            if ex.get("is_cardio", False):
                continue
            muscles = get_exercise_muscles(ex["name"])
            working = ex.get("working_sets", 0)
            for m in muscles:
                period_muscles[m] = period_muscles.get(m, 0) + working
        for m, sets in period_muscles.items():
            if m not in muscle_weekly_sets:
                muscle_weekly_sets[m] = []
            muscle_weekly_sets[m].append(sets)

    # Calculate muscle trends (first half avg vs second half avg)
    lines.append("## muscle_volume")
    lines.append("muscle\tweekly_avg_sets\ttrend")

    for muscle in sorted(muscle_weekly_sets.keys()):
        if muscle == "unknown":
            continue  # Skip unknown muscle group in summary
        weekly = muscle_weekly_sets[muscle]
        avg = round(sum(weekly) / len(weekly), 1) if weekly else 0
        midpoint = len(weekly) // 2
        if midpoint > 0 and len(weekly) > midpoint:
            first_avg = sum(weekly[:midpoint]) / midpoint
            second_avg = sum(weekly[midpoint:]) / (len(weekly) - midpoint)
            if first_avg > 0:
                trend = ((second_avg - first_avg) / first_avg) * 100
                trend_str = f"{trend:+.1f}%"
            else:
                trend_str = "N/A"
        else:
            trend_str = "N/A"
        lines.append(f"{muscle}\t{avg}\t{trend_str}")

    lines.append("")

    # --- Recent Sessions (last 14) ---
    lines.append("## recent_sessions")
    lines.append("date\texercises")

    # Get the last 14 periods with compact exercise notation
    recent = periods[-14:] if len(periods) > 14 else periods
    for p in reversed(recent):  # Most recent first
        date = p.get("date", "")
        exercises_compact = []
        for ex in p.get("exercises", []):
            name = ex["name"]
            ws = ex.get("working_sets", 0)
            reps = ex.get("total_reps", 0)
            max_w = ex.get("max_weight", 0)
            if ex.get("is_cardio", False):
                dur_s = ex.get("total_duration_seconds", 0)
                if dur_s > 0:
                    dur_min = int(dur_s // 60)
                    exercises_compact.append(f"{name}:{dur_min}min")
                else:
                    exercises_compact.append(name)
            elif ws > 0 and reps > 0:
                reps_per_set = reps // ws if ws > 0 else reps
                if max_w > 0:
                    exercises_compact.append(f"{name}:{ws}x{reps_per_set}@{round(max_w, 1)}{weight_unit}")
                else:
                    exercises_compact.append(f"{name}:{ws}x{reps_per_set}")
            else:
                exercises_compact.append(name)
        lines.append(f"{date}\t{','.join(exercises_compact)}")

    # --- Unknown Exercises ---
    unknown = get_unknown_exercises()
    if unknown:
        lines.append("")
        lines.append("## unknown_exercises")
        for name in sorted(unknown):
            lines.append(name)

    lines.append("")
    return "\n".join(lines)


def _time_to_seconds(time_str):
    """Convert a time string like '1:30:00' or '0:29:37' to seconds."""
    if not time_str or time_str == "0":
        return 0
    parts = time_str.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    return 0
