"""Tests for summarize_workouts - unit conversion, session grouping, distance."""

from conftest import make_entry as _make_entry

from src.report.generator import summarize_workouts


class TestUnitConversion:
    def test_metric_weight_not_double_converted(self):
        entries = [_make_entry(weight_kg=50.0, reps=10)]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # Volume should be 50 * 10 = 500, not 50*0.453592*10
        assert summaries[key]["Volume"] == 500.0
        # Workout detail weight should be 50kg, not converted
        workouts = list(summaries[key]["Workouts"].values())[0]
        assert workouts[0]["weight"] == 50.0
        assert workouts[0]["weight_unit"] == "kg"

    def test_imperial_weight_converted_once(self):
        entries = [_make_entry(weight_kg=50.0, reps=10)]
        summaries = summarize_workouts(entries, use_metric=False, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        workouts = list(summaries[key]["Workouts"].values())[0]
        # 50kg -> ~110 lbs (gym-rounded)
        assert workouts[0]["weight_unit"] == "lbs"
        assert workouts[0]["weight"] == 110.0  # 50 * 2.20462 = 110.23, gym-rounded to 110

    def test_metric_distance_not_inflated(self):
        entries = [_make_entry(exercise="Running", distance_m=5000.0, duration_s=1800.0, reps=0)]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # 5000m = 5.0km, should NOT be multiplied by 1.60934
        assert abs(summaries[key]["Distance"] - 5.0) < 0.01

    def test_imperial_distance_converted(self):
        entries = [_make_entry(exercise="Running", distance_m=5000.0, duration_s=1800.0, reps=0)]
        summaries = summarize_workouts(entries, use_metric=False, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # 5km * 0.621371 = 3.107 miles
        assert abs(summaries[key]["Distance"] - 3.107) < 0.01

    def test_distance_ratio_metric_imperial(self):
        entries = [_make_entry(exercise="Running", distance_m=10000.0, duration_s=3600.0, reps=0)]
        m = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        i = summarize_workouts(entries, use_metric=False, tz_name="UTC", group_by="day")
        km = list(m.values())[0]["Distance"]
        mi = list(i.values())[0]["Distance"]
        assert abs(km / mi - 1.60934) < 0.001


class TestSessionGrouping:
    def test_ascending_timestamps(self):
        entries = [
            _make_entry(date_str="2024-01-15 10:00:00"),
            _make_entry(date_str="2024-01-15 10:10:00"),
            _make_entry(date_str="2024-01-15 10:20:00"),
        ]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # Session duration: 10:20 - 10:00 = 1200s
        assert summaries[key]["strength_duration"] == 1200.0

    def test_descending_timestamps_same_duration(self):
        entries = [
            _make_entry(date_str="2024-01-15 10:20:00"),
            _make_entry(date_str="2024-01-15 10:10:00"),
            _make_entry(date_str="2024-01-15 10:00:00"),
        ]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # Should produce same duration as ascending (sorted internally)
        assert summaries[key]["strength_duration"] == 1200.0

    def test_same_timestamp_uses_estimate(self):
        entries = [
            _make_entry(date_str="2024-01-15 10:00:00"),
            _make_entry(date_str="2024-01-15 10:00:00"),
        ]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # Estimate: 2min per working set = 240s
        assert summaries[key]["strength_duration"] == 240.0

    def test_large_gap_splits_sessions(self):
        entries = [
            _make_entry(date_str="2024-01-15 10:00:00"),
            _make_entry(date_str="2024-01-15 10:10:00"),
            _make_entry(date_str="2024-01-15 14:00:00"),  # >30min gap
            _make_entry(date_str="2024-01-15 14:10:00"),
        ]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        # Two sessions: 600s + 600s = 1200s
        assert summaries[key]["strength_duration"] == 1200.0

    def test_duration_never_negative(self):
        entries = [
            _make_entry(date_str="2024-01-15 10:30:00"),
            _make_entry(date_str="2024-01-15 10:00:00"),
        ]
        summaries = summarize_workouts(entries, use_metric=True, tz_name="UTC", group_by="day")
        key = list(summaries.keys())[0]
        assert summaries[key]["strength_duration"] >= 0

    def test_shuffled_input_same_duration(self):
        """Session duration must not depend on input row order."""
        chronological = [
            _make_entry(date_str="2024-01-15 10:00:00"),
            _make_entry(date_str="2024-01-15 10:10:00"),
            _make_entry(date_str="2024-01-15 14:00:00"),
            _make_entry(date_str="2024-01-15 14:10:00"),
        ]
        shuffled = [chronological[2], chronological[0], chronological[3], chronological[1]]

        s1 = summarize_workouts(chronological, use_metric=True, tz_name="UTC", group_by="day")
        s2 = summarize_workouts(shuffled, use_metric=True, tz_name="UTC", group_by="day")
        key = list(s1.keys())[0]
        assert s1[key]["strength_duration"] == s2[key]["strength_duration"]
