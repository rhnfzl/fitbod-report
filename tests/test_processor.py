"""Tests for data processor - rounding order and multiplier handling."""

import pandas as pd

from src.data.processor import process_data_from_df


def _make_df(**overrides):
    """Create a minimal valid DataFrame with one row."""
    defaults = {
        "Date": ["2024-01-15 10:00:00+00:00"],
        "Exercise": ["Bench Press"],
        "Reps": [10],
        "Weight(kg)": [50.0],
        "Duration(s)": [0.0],
        "Distance(m)": [0.0],
        "Incline": [0],
        "Resistance": [0],
        "isWarmup": [False],
        "Note": [""],
        "multiplier": [1.0],
    }
    defaults.update(overrides)
    return pd.DataFrame(defaults)


class TestWeightRounding:
    def test_rounds_to_nearest_half_kg(self):
        df = _make_df(**{"Weight(kg)": [37.3]})
        records = process_data_from_df(df)
        assert records[0]["Weight(kg)"] == 37.5

    def test_multiplier_applied_before_rounding(self):
        # 25.0 * 0.75 = 18.75, rounded to 19.0 (nearest 0.5)
        df = _make_df(**{"Weight(kg)": [25.0], "multiplier": [0.75]})
        records = process_data_from_df(df)
        assert records[0]["Weight(kg)"] == 19.0

    def test_multiplier_1_preserves_rounding(self):
        df = _make_df(**{"Weight(kg)": [37.3], "multiplier": [1.0]})
        records = process_data_from_df(df)
        assert records[0]["Weight(kg)"] == 37.5

    def test_multiplier_2_then_round(self):
        # 12.3 * 2 = 24.6, rounded to 24.5
        df = _make_df(**{"Weight(kg)": [12.3], "multiplier": [2.0]})
        records = process_data_from_df(df)
        assert records[0]["Weight(kg)"] == 24.5

    def test_no_multiplier_column(self):
        df = _make_df(**{"Weight(kg)": [37.3]})
        df = df.drop(columns=["multiplier"])
        records = process_data_from_df(df)
        assert records[0]["Weight(kg)"] == 37.5
