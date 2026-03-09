"""Tests for unit conversion functions."""

from src.utils.converters import convert_units, round_to_gym_weight, seconds_to_time


class TestSecondsToTime:
    def test_zero(self):
        assert seconds_to_time(0) == "0h 0m 0s"

    def test_minutes_only(self):
        assert seconds_to_time(150) == "0h 2m 30s"

    def test_hours_minutes_seconds(self):
        assert seconds_to_time(3661) == "1h 1m 1s"

    def test_negative_clamps_to_zero(self):
        assert seconds_to_time(-100) == "0h 0m 0s"

    def test_invalid_returns_zero(self):
        assert seconds_to_time("abc") == "0h 0m 0s"


class TestConvertUnits:
    def test_weight_kg_to_lbs(self):
        value, unit = convert_units(10, "weight", to_metric=False)
        assert unit == "lbs"
        assert value == 20  # 10 * 2.20462 = 22.05, gym-rounded to 20

    def test_weight_lbs_to_kg(self):
        value, unit = convert_units(100, "weight", to_metric=True)
        assert unit == "kg"
        assert abs(value - 45.3592) < 0.01

    def test_distance_km_to_miles(self):
        value, unit = convert_units(10, "distance", to_metric=False)
        assert unit == "miles"
        assert abs(value - 6.21371) < 0.01

    def test_distance_miles_to_km(self):
        value, unit = convert_units(10, "distance", to_metric=True)
        assert unit == "km"
        assert abs(value - 16.0934) < 0.01


class TestRoundToGymWeight:
    def test_very_light_rounds_to_1lb(self):
        assert round_to_gym_weight(2.7) == 3

    def test_light_rounds_to_2_5lbs(self):
        assert round_to_gym_weight(11.3) == 11.5

    def test_heavy_rounds_to_5lbs(self):
        assert round_to_gym_weight(47) == 45
        assert round_to_gym_weight(53) == 55

    def test_exact_5lb_increment(self):
        assert round_to_gym_weight(50) == 50
