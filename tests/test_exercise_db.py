"""Regression tests for Fitbod exercise classifications."""

from src.data.exercise_db import get_exercise_equipment, get_exercise_muscles


def test_leg_curl_variants_map_to_hamstrings():
    assert get_exercise_muscles("Leg Curl") == ["hamstrings"]
    assert get_exercise_muscles("Lying Hamstrings Curl") == ["hamstrings"]
    assert get_exercise_muscles("Seated Leg Curl") == ["hamstrings"]


def test_glute_kickback_variants_map_to_glutes():
    assert get_exercise_muscles("Glute Kickback Machine") == ["glutes"]
    assert get_exercise_muscles("Single Leg Cable Kickback") == ["glutes"]


def test_bench_dip_stays_triceps_first():
    assert get_exercise_muscles("Bench Dip") == ["triceps"]


def test_equipment_regressions_stay_specific():
    assert get_exercise_equipment("Cross Body Hammer Curls") == "dumbbell"
    assert get_exercise_equipment("Hammer Curls") == "dumbbell"
    assert get_exercise_equipment("Single Arm Landmine Press") == "barbell"
    assert get_exercise_equipment("T-Bar Row") == "barbell"
