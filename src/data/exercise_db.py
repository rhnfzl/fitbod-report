"""Exercise-to-muscle-group and equipment mappings for Fitbod exercises.

Covers 209 known exercises from the Fitbod EXERCISE_MAPPING. Used by the GPT
report generator to compute the ``## muscle_volume`` section.

NOTE: This is NOT a complete list of all Fitbod exercises. Fitbod has hundreds
of exercises and users can create custom ones. When an exercise is not found in
this database, it is classified as "unknown" and reported to the user so they
can contribute it back. To add a new exercise, add an entry to both
EXERCISE_MUSCLES and EXERCISE_EQUIPMENT below, then update the corresponding
exercise-database.json in the fitbod-gpt repo's knowledge/ directory.

Muscle groups used:
    chest, upper_chest, lower_chest, lats, upper_back, lower_back, traps,
    front_delts, side_delts, rear_delts, shoulders, biceps, triceps, forearms,
    quads, hamstrings, glutes, calves, abs, obliques, hip_flexors,
    adductors, neck
"""

from __future__ import annotations

from typing import Final

# ---------------------------------------------------------------------------
# Primary muscle mapping: Fitbod exercise name -> list of primary muscles
# Each exercise maps to 1-3 primary muscle groups.
# ---------------------------------------------------------------------------

EXERCISE_MUSCLES: Final[dict[str, list[str]]] = {
    # ----- Core / Abs -----
    "Ab Crunch Machine": ["abs"],
    "Bicycle Crunch": ["abs"],
    "Cable Crunch": ["abs"],
    "Crunches": ["abs"],
    "Dead Bug": ["abs"],
    "Decline Crunch": ["abs"],
    "Decline Russian Twists": ["obliques", "abs"],
    "Hanging Knee Raise": ["abs", "hip_flexors"],
    "Hanging Leg Raise": ["abs", "hip_flexors"],
    "Knee Up": ["abs", "hip_flexors"],
    "Leg Pull-In": ["abs", "hip_flexors"],
    "Leg Raise": ["abs", "hip_flexors"],
    "Medicine Ball Russian Twist": ["obliques", "abs"],
    "Plank": ["abs", "obliques"],
    "Plank Shoulder Taps": ["abs", "obliques"],
    "Reverse Crunch": ["abs"],
    "Russian Twist": ["obliques", "abs"],
    "Scissor Crossover Kick": ["abs", "hip_flexors"],
    "Scissor Kick": ["abs", "hip_flexors"],
    "Side Bridge": ["obliques", "abs"],
    "Sit Up": ["abs"],
    "Toe Touchers": ["abs"],
    "Vertical Knee Raise": ["abs", "hip_flexors"],

    # ----- Chest -----
    "Barbell Bench Press": ["chest"],
    "Barbell Incline Bench Press": ["upper_chest", "chest"],
    "Cable Crossover Fly": ["chest"],
    "Close-Grip Bench Press": ["triceps", "chest"],
    "Decline Push Up": ["upper_chest", "chest"],
    "Dip": ["triceps", "chest"],
    "Dumbbell Bench Press": ["chest"],
    "Dumbbell Decline Bench Press": ["lower_chest", "chest"],
    "Dumbbell Fly": ["chest"],
    "Dumbbell Incline Bench Press": ["upper_chest", "chest"],
    "Dumbbell Incline Fly": ["upper_chest"],
    "Dumbbell Pullover": ["lats", "chest"],
    "Hammerstrength Chest Press": ["chest"],
    "Hammerstrength Decline Chest Press": ["lower_chest", "chest"],
    "Hammerstrength Incline Chest Press": ["upper_chest", "chest"],
    "Machine Bench Press": ["chest"],
    "Machine Fly": ["chest"],
    "Push Up": ["chest"],
    "Single Arm Landmine Press": ["upper_chest", "front_delts"],
    "Smith Machine Bench Press": ["chest"],
    "Smith Machine Incline Bench Press": ["upper_chest", "chest"],
    "Tricep Push Up": ["triceps", "chest"],
    "Walkout to Push Up": ["chest", "abs"],

    # ----- Back -----
    "Assisted Chin Up": ["lats", "biceps"],
    "Assisted Neutral Grip Pull Up": ["lats", "upper_back"],
    "Assisted Pull Up": ["lats", "upper_back"],
    "Assisted Wide Grip Pull Up": ["lats", "upper_back"],
    "Australian Pull Up": ["lats", "upper_back"],
    "Bent Over Barbell Row": ["lats", "upper_back"],
    "Cable Row": ["lats", "upper_back"],
    "Chin Up": ["lats", "biceps"],
    "Diverging Seated Row": ["lats", "upper_back"],
    "Dumbbell Row": ["lats", "upper_back"],
    "Hammerstrength Iso Row": ["lats", "upper_back"],
    "Incline Dumbbell Row": ["lats", "upper_back"],
    "Inverted Row": ["lats", "upper_back"],
    "Lat Pulldown": ["lats"],
    "Machine Row": ["lats", "upper_back"],
    "Pendlay Row": ["lats", "upper_back"],
    "Pull Up": ["lats", "upper_back"],
    "Scapular Pull Up": ["lats", "upper_back"],
    "Seated Cable Row": ["lats", "upper_back"],
    "T-Bar Row": ["lats", "upper_back"],
    "V-Bar Pulldown": ["lats"],
    "Wide Grip Lat Pulldown": ["lats"],

    # ----- Lower back / posterior chain -----
    "Back Extensions": ["lower_back", "glutes"],
    "Deadlift": ["hamstrings", "glutes", "lower_back"],
    "Deadlift to Calf Raise": ["hamstrings", "glutes", "lower_back"],
    "Dumbbell Romanian Deadlift": ["hamstrings", "glutes", "lower_back"],
    "Dumbbell Superman": ["lower_back", "glutes"],
    "Good Morning": ["hamstrings", "lower_back", "glutes"],
    "Incline Back Extension": ["lower_back", "glutes"],
    "Romanian Deadlift": ["hamstrings", "glutes", "lower_back"],
    "Seated Back Extension": ["lower_back", "glutes"],
    "Stiff-Legged Barbell Good Morning": ["hamstrings", "lower_back", "glutes"],
    "Superman": ["lower_back", "glutes"],
    "Superman Hold": ["lower_back", "glutes"],
    "Superman with Scaption": ["lower_back", "glutes"],

    # ----- Shoulders -----
    "Arnold Dumbbell Press": ["front_delts", "side_delts"],
    "Barbell Shoulder Press": ["front_delts", "side_delts"],
    "Cable Face Pull": ["rear_delts", "upper_back"],
    "Cable Lateral Raise": ["side_delts"],
    "Cable Rear Delt Fly": ["rear_delts"],
    "Dumbbell Back Fly": ["rear_delts"],
    "Dumbbell Front Raise": ["front_delts"],
    "Dumbbell Lateral Raise": ["side_delts"],
    "Dumbbell Rear Delt Raise": ["rear_delts"],
    "Dumbbell Shoulder Press": ["front_delts", "side_delts"],
    "Dumbbell Shoulder Raise": ["side_delts"],
    "Dumbbell Squat To Shoulder Press": ["quads", "glutes", "front_delts"],
    "Dumbbell Upright Row": ["side_delts", "traps"],
    "Hammerstrength Shoulder Press": ["front_delts", "side_delts"],
    "Machine Overhead Press": ["front_delts", "side_delts"],
    "Machine Rear Delt Fly": ["rear_delts"],
    "Machine Reverse Fly": ["rear_delts"],
    "Machine Shoulder Press": ["front_delts", "side_delts"],
    "Push Press": ["front_delts", "side_delts"],
    "Upright Row": ["side_delts", "traps"],

    # ----- Traps / neck -----
    "Barbell Shrug": ["traps"],
    "Dumbbell Shrug": ["traps"],
    "Face Down Plate Neck Resistance": ["neck"],

    # ----- Biceps -----
    "Barbell Curl": ["biceps"],
    "Cable Bicep Curl": ["biceps"],
    "Cross Body Hammer Curls": ["biceps", "forearms"],
    "Dumbbell Bicep Curl": ["biceps"],
    "EZ-Bar Curl": ["biceps"],
    "Hammer Curls": ["biceps", "forearms"],
    "Incline Dumbbell Curl": ["biceps"],
    "Incline EZ-Bar Curl": ["biceps"],
    "Incline Hammer Curl": ["biceps", "forearms"],
    "Machine Bicep Curl": ["biceps"],
    "Machine Preacher Curl": ["biceps"],
    "Preacher Curl": ["biceps"],
    "Reverse Barbell Curl": ["forearms", "biceps"],
    "Reverse Dumbbell Curl": ["forearms", "biceps"],
    "Seated Dumbbell Curl": ["biceps"],
    "Single Arm Cable Bicep Curl": ["biceps"],
    "Spider Curls": ["biceps"],
    "Zottman Curl": ["biceps", "forearms"],
    "Zottman Preacher Curl": ["biceps", "forearms"],
    "EZ-Bar Reverse Grip Curl": ["forearms", "biceps"],

    # ----- Triceps -----
    "Assisted Dip": ["triceps", "chest"],
    "Bench Dip": ["triceps"],
    "Cable One Arm Tricep Side Extension": ["triceps"],
    "Cable One Arm Underhand Tricep Extension": ["triceps"],
    "Cable Rope Overhead Triceps Extension": ["triceps"],
    "Cable Rope Tricep Extension": ["triceps"],
    "Cable Tricep Pushdown": ["triceps"],
    "Cable Underhand Tricep Pushdown": ["triceps"],
    "Dumbbell Kickbacks": ["triceps"],
    "Dumbbell Skullcrusher": ["triceps"],
    "Dumbbell Tricep Extension": ["triceps"],
    "EZ-Bar Overhead Tricep Extension": ["triceps"],
    "Machine Tricep Dip": ["triceps"],
    "Machine Tricep Extension": ["triceps"],
    "Seated Tricep Press": ["triceps"],
    "Single Arm Dumbbell Tricep Extension": ["triceps"],
    "Skullcrusher": ["triceps"],
    "Tricep Extension": ["triceps"],

    # ----- Forearms -----
    "Palms-Down Dumbbell Wrist Curl": ["forearms"],
    "Palms-Up Dumbbell Wrist Curl": ["forearms"],

    # ----- Quads / legs -----
    "Air Squats": ["quads", "glutes"],
    "Back Squat": ["quads", "glutes"],
    "Barbell Lunge": ["quads", "glutes"],
    "Bodyweight Bulgarian Split Squat": ["quads", "glutes"],
    "Dumbbell Goblet Squat": ["quads", "glutes"],
    "Dumbbell Lunge": ["quads", "glutes"],
    "Dumbbell Squat": ["quads", "glutes"],
    "Dumbbell Walking Lunge": ["quads", "glutes"],
    "Forward Lunge with Twist": ["quads", "glutes"],
    "Front Squat": ["quads", "glutes"],
    "Hack Squat": ["quads", "glutes"],
    "Leg Extension": ["quads"],
    "Leg Press": ["quads", "glutes"],
    "Lunge": ["quads", "glutes"],
    "Lunge Twist": ["quads", "glutes"],
    "Machine Leg Press": ["quads", "glutes"],
    "Single Leg Leg Extension": ["quads"],
    "Smith Machine Squat": ["quads", "glutes"],
    "Step Up": ["quads", "glutes"],

    # ----- Hamstrings -----
    "Leg Curl": ["hamstrings"],
    "Lying Hamstrings Curl": ["hamstrings"],
    "Seated Leg Curl": ["hamstrings"],

    # ----- Glutes / hips -----
    "Barbell Hip Thrust": ["glutes", "hamstrings"],
    "Cable Hip Abduction": ["glutes"],
    "Cable Hip Adduction": ["adductors"],
    "Glute Kickback Machine": ["glutes"],
    "Hip Thrust": ["glutes", "hamstrings"],
    "Machine Hip Abductor": ["glutes"],
    "Machine Hip Adductor": ["adductors"],
    "Single Leg Cable Kickback": ["glutes"],
    "Single Leg Glute Bridge": ["glutes", "hamstrings"],
    "Stability Ball Hip Bridge": ["glutes", "hamstrings"],

    # ----- Calves -----
    "Calf Press": ["calves"],
    "Seated Machine Calf Press": ["calves"],
    "Smith Machine Calf Raise": ["calves"],
    "Standing Leg Side Hold": ["calves"],
    "Standing Machine Calf Press": ["calves"],

    # ----- Cardio -----
    "Burpee": ["quads", "chest"],
    "Cycling": ["quads", "hamstrings"],
    "Cycling - Stationary": ["quads", "hamstrings"],
    "Elliptical": ["quads", "hamstrings"],
    "Hiking": ["quads", "glutes"],
    "Rowing": ["lats", "upper_back"],
    "Running": ["quads", "hamstrings"],
    "Running - Treadmill": ["quads", "hamstrings"],
    "Sled Push": ["quads", "glutes"],
    "Stair Stepper": ["quads", "glutes"],
    "Walking": ["quads", "glutes"],

    # ----- Kettlebell -----
    "Kettlebell Single Arm Farmer Walk": ["forearms", "traps"],
    "Kettlebell Swing": ["glutes", "hamstrings"],
    "Kettlebell Swing American": ["glutes", "hamstrings"],

    # ----- Carries -----
    "Farmer's Walk": ["forearms", "traps"],

    # ----- Mobility / flexibility -----
    "Backward Arm Circle": ["shoulders"],
    "Bench T-Spine Stretch": ["upper_back", "shoulders"],
    "Bird Dog": ["abs", "lower_back"],
    "Cat Cow": ["lower_back", "abs"],
    "Chest Expansion": ["chest", "shoulders"],
    "Dead Hang": ["forearms", "lats"],
    "Forward Arm Circle": ["shoulders"],
    "Leg Swing": ["hip_flexors"],
    "PVC Around the World": ["shoulders"],
    "Seated Figure Four": ["glutes", "hip_flexors"],
    "Single Leg Overhead Kettlebell Hold": ["shoulders", "abs"],
    "Single Leg Straight Forward Bend": ["hamstrings"],
    "Tricep Stretch": ["triceps"],
}

# ---------------------------------------------------------------------------
# Equipment mapping: Fitbod exercise name -> equipment type
# ---------------------------------------------------------------------------

EXERCISE_EQUIPMENT: Final[dict[str, str]] = {
    # ----- Barbell -----
    "Back Squat": "barbell",
    "Barbell Bench Press": "barbell",
    "Barbell Curl": "barbell",
    "Barbell Hip Thrust": "barbell",
    "Barbell Incline Bench Press": "barbell",
    "Barbell Lunge": "barbell",
    "Barbell Shoulder Press": "barbell",
    "Barbell Shrug": "barbell",
    "Bent Over Barbell Row": "barbell",
    "Close-Grip Bench Press": "barbell",
    "Deadlift": "barbell",
    "Deadlift to Calf Raise": "barbell",
    "Front Squat": "barbell",
    "Good Morning": "barbell",
    "Hip Thrust": "barbell",
    "Pendlay Row": "barbell",
    "Push Press": "barbell",
    "Reverse Barbell Curl": "barbell",
    "Romanian Deadlift": "barbell",
    "Skullcrusher": "barbell",
    "Stiff-Legged Barbell Good Morning": "barbell",
    "Upright Row": "barbell",

    # ----- Dumbbell -----
    "Arnold Dumbbell Press": "dumbbell",
    "Cross Body Hammer Curls": "dumbbell",
    "Dumbbell Back Fly": "dumbbell",
    "Dumbbell Bench Press": "dumbbell",
    "Dumbbell Bicep Curl": "dumbbell",
    "Dumbbell Decline Bench Press": "dumbbell",
    "Dumbbell Fly": "dumbbell",
    "Dumbbell Front Raise": "dumbbell",
    "Dumbbell Goblet Squat": "dumbbell",
    "Dumbbell Incline Bench Press": "dumbbell",
    "Dumbbell Incline Fly": "dumbbell",
    "Dumbbell Kickbacks": "dumbbell",
    "Dumbbell Lateral Raise": "dumbbell",
    "Dumbbell Lunge": "dumbbell",
    "Dumbbell Pullover": "dumbbell",
    "Dumbbell Rear Delt Raise": "dumbbell",
    "Dumbbell Romanian Deadlift": "dumbbell",
    "Dumbbell Row": "dumbbell",
    "Incline Dumbbell Row": "dumbbell",
    "Dumbbell Shoulder Press": "dumbbell",
    "Dumbbell Shoulder Raise": "dumbbell",
    "Dumbbell Shrug": "dumbbell",
    "Dumbbell Skullcrusher": "dumbbell",
    "Dumbbell Squat": "dumbbell",
    "Dumbbell Squat To Shoulder Press": "dumbbell",
    "Dumbbell Superman": "dumbbell",
    "Dumbbell Tricep Extension": "dumbbell",
    "Dumbbell Upright Row": "dumbbell",
    "Dumbbell Walking Lunge": "dumbbell",
    "Hammer Curls": "dumbbell",
    "Incline Dumbbell Curl": "dumbbell",
    "Incline Hammer Curl": "dumbbell",
    "Palms-Down Dumbbell Wrist Curl": "dumbbell",
    "Palms-Up Dumbbell Wrist Curl": "dumbbell",
    "Reverse Dumbbell Curl": "dumbbell",
    "Seated Dumbbell Curl": "dumbbell",
    "Single Arm Dumbbell Tricep Extension": "dumbbell",
    "Spider Curls": "dumbbell",
    "Tricep Extension": "dumbbell",
    "Zottman Curl": "dumbbell",
    "Zottman Preacher Curl": "dumbbell",

    # ----- Cable -----
    "Cable Bicep Curl": "cable",
    "Cable Crossover Fly": "cable",
    "Cable Crunch": "cable",
    "Cable Face Pull": "cable",
    "Cable Hip Abduction": "cable",
    "Cable Hip Adduction": "cable",
    "Cable Lateral Raise": "cable",
    "Cable One Arm Tricep Side Extension": "cable",
    "Cable One Arm Underhand Tricep Extension": "cable",
    "Cable Rear Delt Fly": "cable",
    "Cable Rope Overhead Triceps Extension": "cable",
    "Cable Rope Tricep Extension": "cable",
    "Cable Row": "cable",
    "Cable Tricep Pushdown": "cable",
    "Cable Underhand Tricep Pushdown": "cable",
    "Seated Cable Row": "cable",
    "Single Arm Cable Bicep Curl": "cable",
    "Single Leg Cable Kickback": "cable",

    # ----- Machine -----
    "Ab Crunch Machine": "machine",
    "Calf Press": "machine",
    "Diverging Seated Row": "machine",
    "Glute Kickback Machine": "machine",
    "Hack Squat": "machine",
    "Hammerstrength Chest Press": "machine",
    "Hammerstrength Decline Chest Press": "machine",
    "Hammerstrength Incline Chest Press": "machine",
    "Hammerstrength Iso Row": "machine",
    "Hammerstrength Shoulder Press": "machine",
    "Lat Pulldown": "machine",
    "Leg Curl": "machine",
    "Leg Extension": "machine",
    "Leg Press": "machine",
    "Lying Hamstrings Curl": "machine",
    "Machine Bench Press": "machine",
    "Machine Bicep Curl": "machine",
    "Machine Fly": "machine",
    "Machine Hip Abductor": "machine",
    "Machine Hip Adductor": "machine",
    "Machine Leg Press": "machine",
    "Machine Overhead Press": "machine",
    "Machine Preacher Curl": "machine",
    "Machine Rear Delt Fly": "machine",
    "Machine Reverse Fly": "machine",
    "Machine Row": "machine",
    "Machine Shoulder Press": "machine",
    "Machine Tricep Dip": "machine",
    "Machine Tricep Extension": "machine",
    "Seated Leg Curl": "machine",
    "Seated Machine Calf Press": "machine",
    "Single Leg Leg Extension": "machine",
    "Standing Machine Calf Press": "machine",
    "V-Bar Pulldown": "machine",
    "Wide Grip Lat Pulldown": "machine",

    # ----- EZ bar -----
    "EZ-Bar Curl": "ez_bar",
    "EZ-Bar Overhead Tricep Extension": "ez_bar",
    "EZ-Bar Reverse Grip Curl": "ez_bar",
    "Incline EZ-Bar Curl": "ez_bar",
    "Preacher Curl": "ez_bar",

    # ----- Smith machine -----
    "Smith Machine Bench Press": "smith_machine",
    "Smith Machine Calf Raise": "smith_machine",
    "Smith Machine Incline Bench Press": "smith_machine",
    "Smith Machine Squat": "smith_machine",

    # ----- Kettlebell -----
    "Kettlebell Single Arm Farmer Walk": "kettlebell",
    "Kettlebell Swing": "kettlebell",
    "Kettlebell Swing American": "kettlebell",
    "Single Leg Overhead Kettlebell Hold": "kettlebell",

    # ----- Other equipment -----
    "Face Down Plate Neck Resistance": "plate",
    "Medicine Ball Russian Twist": "medicine_ball",
    "PVC Around the World": "other",
    "Sled Push": "sled",
    "Stability Ball Hip Bridge": "stability_ball",

    # ----- Bodyweight -----
    "Air Squats": "bodyweight",
    "Assisted Chin Up": "bodyweight",
    "Assisted Dip": "bodyweight",
    "Assisted Neutral Grip Pull Up": "bodyweight",
    "Assisted Pull Up": "bodyweight",
    "Assisted Wide Grip Pull Up": "bodyweight",
    "Australian Pull Up": "bodyweight",
    "Back Extensions": "bodyweight",
    "Backward Arm Circle": "bodyweight",
    "Bench Dip": "bodyweight",
    "Bench T-Spine Stretch": "bodyweight",
    "Bicycle Crunch": "bodyweight",
    "Bird Dog": "bodyweight",
    "Bodyweight Bulgarian Split Squat": "bodyweight",
    "Burpee": "bodyweight",
    "Cat Cow": "bodyweight",
    "Chest Expansion": "bodyweight",
    "Chin Up": "bodyweight",
    "Crunches": "bodyweight",
    "Cycling": "bodyweight",
    "Cycling - Stationary": "bodyweight",
    "Dead Bug": "bodyweight",
    "Dead Hang": "bodyweight",
    "Decline Crunch": "bodyweight",
    "Decline Push Up": "bodyweight",
    "Decline Russian Twists": "bodyweight",
    "Dip": "bodyweight",
    "Elliptical": "bodyweight",
    "Farmer's Walk": "bodyweight",
    "Forward Arm Circle": "bodyweight",
    "Forward Lunge with Twist": "bodyweight",
    "Hanging Knee Raise": "bodyweight",
    "Hanging Leg Raise": "bodyweight",
    "Hiking": "bodyweight",
    "Incline Back Extension": "bodyweight",
    "Inverted Row": "bodyweight",
    "Knee Up": "bodyweight",
    "Leg Pull-In": "bodyweight",
    "Leg Raise": "bodyweight",
    "Leg Swing": "bodyweight",
    "Lunge": "bodyweight",
    "Lunge Twist": "bodyweight",
    "Plank": "bodyweight",
    "Plank Shoulder Taps": "bodyweight",
    "Pull Up": "bodyweight",
    "Push Up": "bodyweight",
    "Reverse Crunch": "bodyweight",
    "Rowing": "bodyweight",
    "Running": "bodyweight",
    "Running - Treadmill": "bodyweight",
    "Russian Twist": "bodyweight",
    "Scapular Pull Up": "bodyweight",
    "Scissor Crossover Kick": "bodyweight",
    "Scissor Kick": "bodyweight",
    "Seated Back Extension": "bodyweight",
    "Seated Figure Four": "bodyweight",
    "Seated Tricep Press": "bodyweight",
    "Side Bridge": "bodyweight",
    "Single Arm Landmine Press": "barbell",
    "Single Leg Glute Bridge": "bodyweight",
    "Single Leg Straight Forward Bend": "bodyweight",
    "Sit Up": "bodyweight",
    "Stair Stepper": "bodyweight",
    "Standing Leg Side Hold": "bodyweight",
    "Step Up": "bodyweight",
    "Superman": "bodyweight",
    "Superman Hold": "bodyweight",
    "Superman with Scaption": "bodyweight",
    "T-Bar Row": "barbell",
    "Toe Touchers": "bodyweight",
    "Tricep Push Up": "bodyweight",
    "Tricep Stretch": "bodyweight",
    "Vertical Knee Raise": "bodyweight",
    "Walking": "bodyweight",
    "Walkout to Push Up": "bodyweight",

    # Note: Barbell Lunge already in barbell section above
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Tracks exercises encountered at runtime that are not in the database.
# Populated by get_exercise_muscles() / get_exercise_equipment().
_unknown_exercises: set[str] = set()


def get_exercise_muscles(exercise_name: str) -> list[str]:
    """Return the primary muscle groups for a Fitbod exercise.

    Args:
        exercise_name: The Fitbod exercise name (case-sensitive).

    Returns:
        A list of primary muscle group strings. Returns ``["unknown"]`` for
        unrecognized exercises (and records them for later reporting).
    """
    muscles = EXERCISE_MUSCLES.get(exercise_name)
    if muscles is None:
        _unknown_exercises.add(exercise_name)
        return ["unknown"]
    return muscles


def get_exercise_equipment(exercise_name: str) -> str:
    """Return the equipment type for a Fitbod exercise.

    Args:
        exercise_name: The Fitbod exercise name (case-sensitive).

    Returns:
        An equipment string, or ``"unknown"`` for unrecognized exercises
        (and records them for later reporting).
    """
    equipment = EXERCISE_EQUIPMENT.get(exercise_name)
    if equipment is None:
        _unknown_exercises.add(exercise_name)
        return "unknown"
    return equipment


def get_unknown_exercises() -> set[str]:
    """Return the set of exercise names encountered that are not in the DB.

    This allows callers (e.g. the GPT report generator) to surface unknown
    exercises to the user so they can be added to the database.
    """
    return _unknown_exercises.copy()


def clear_unknown_exercises() -> None:
    """Reset the unknown exercises tracker."""
    _unknown_exercises.clear()
