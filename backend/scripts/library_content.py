"""Curated starter-library content definitions and a static consistency check.

This module is pure data plus a validator. It defines system Exercises, Templates,
and Programs by stable keys. The seeder (``seed_library``) resolves references by
slug/name and creates the content through the normal application services, so it
passes exactly the same validation as coach-created content.

Content principles:
- Every Exercise uses one of the five supported tracking modes.
- Instructions and cues are general and practical, never medical claims.
- Set fields match the exercise's tracking mode (validated at seed time).
"""

from typing import Any

from app.models import ExerciseTrackingMode as Mode

# Fields on disclaimer-sensitive text that must never contain medical/absolute claims.
BANNED_PHRASES: tuple[str, ...] = (
    "prevents injury",
    "injury-free",
    "fixes posture",
    "cures",
    "cure ",
    "treats",
    "safe for everyone",
    "medically approved",
    "guaranteed",
    "during pregnancy",
    "rehabilitation",
    "rehab ",
    "diagnos",
    "weight loss guarantee",
)


# --------------------------------------------------------------------------- exercises


def _ex(
    key: str,
    slug: str,
    name: str,
    mode: Mode,
    category: str,
    pattern: str,
    equipment: list[str],
    primary: list[str],
    instructions: str,
    cues: list[str],
    *,
    secondary: list[str] | None = None,
    unilateral: bool = False,
) -> dict[str, Any]:
    return {
        "key": key,
        "slug": slug,
        "name": name,
        "tracking_mode": mode,
        "category": category,
        "movement_pattern": pattern,
        "equipment": equipment,
        "primary_muscle_groups": primary,
        "secondary_muscle_groups": secondary or [],
        "unilateral": unilateral,
        "instructions": instructions,
        "safety_cues": cues,
    }


LIBRARY_EXERCISES: tuple[dict[str, Any], ...] = (
    # repetitions_and_load
    _ex("starter.goblet_squat", "starter-goblet-squat", "Goblet squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["dumbbell"], ["quadriceps", "glutes"],
        "Hold one weight at the chest and squat to a comfortable depth with control.",
        ["Keep the chest tall and stop at a depth you can control."], secondary=["core"]),
    _ex("starter.rdl", "starter-dumbbell-rdl", "Dumbbell Romanian deadlift", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["dumbbell"], ["hamstrings", "glutes"],
        "Hinge at the hips with a long spine, lowering the weights along the legs, then stand tall.",
        ["Move through a range that keeps your back comfortable and controlled."], secondary=["back"]),
    _ex("starter.db_bench", "starter-dumbbell-bench-press", "Dumbbell bench press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["dumbbell", "bench"], ["chest", "triceps"],
        "Press the weights up over the chest and lower them under control.",
        ["Choose a load that lets you complete controlled repetitions."], secondary=["shoulders"]),
    _ex("starter.one_arm_row", "starter-one-arm-dumbbell-row", "One-arm dumbbell row", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal pull", ["dumbbell", "bench"], ["back"],
        "With one hand supported, row the weight toward the hip and lower it with control.",
        ["Keep the spine long and avoid twisting the trunk."], secondary=["biceps"], unilateral=True),
    _ex("starter.db_shoulder_press", "starter-dumbbell-shoulder-press", "Dumbbell shoulder press", Mode.REPETITIONS_AND_LOAD,
        "strength", "vertical push", ["dumbbell"], ["shoulders", "triceps"],
        "Press the weights overhead and lower them to shoulder height under control.",
        ["Stop the set if overhead pressing becomes uncomfortable."], secondary=["core"]),
    _ex("starter.walking_lunge", "starter-dumbbell-walking-lunge", "Dumbbell walking lunge", Mode.REPETITIONS_AND_LOAD,
        "strength", "lunge", ["dumbbell"], ["quadriceps", "glutes"],
        "Step forward into a controlled lunge and continue, alternating legs.",
        ["Use a stride you can control and hold support nearby if needed."], secondary=["core"], unilateral=True),
    _ex("starter.back_squat", "starter-barbell-back-squat", "Barbell back squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["barbell", "squat rack"], ["quadriceps", "glutes"],
        "With the bar on the upper back, squat to a controlled depth and stand tall.",
        ["Use safety supports and a depth you can control."], secondary=["core"]),
    _ex("starter.hip_thrust", "starter-dumbbell-hip-thrust", "Dumbbell hip thrust", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["dumbbell", "bench"], ["glutes", "hamstrings"],
        "With shoulders on a bench, drive the hips up under a weight and lower with control.",
        ["Keep the ribcage down and move through a comfortable range."], secondary=["core"]),
    # repetitions_only
    _ex("starter.bodyweight_squat", "starter-bodyweight-squat", "Bodyweight squat", Mode.REPETITIONS_ONLY,
        "strength", "squat", [], ["quadriceps", "glutes"],
        "Squat to a comfortable depth and stand tall, keeping the movement controlled.",
        ["Choose a depth that feels controlled for you."], secondary=["core"]),
    _ex("starter.push_up", "starter-push-up", "Push-up", Mode.REPETITIONS_ONLY,
        "strength", "horizontal push", [], ["chest", "triceps"],
        "Lower the chest toward the floor with a braced body and press back up.",
        ["Drop to the knees if full push-ups cannot stay controlled."], secondary=["shoulders", "core"]),
    _ex("starter.incline_push_up", "starter-incline-push-up", "Incline push-up", Mode.REPETITIONS_ONLY,
        "strength", "horizontal push", ["bench"], ["chest", "triceps"],
        "With hands on a raised surface, lower the chest and press back up under control.",
        ["Raise the surface higher to make the movement easier."], secondary=["shoulders"]),
    _ex("starter.glute_bridge", "starter-glute-bridge", "Glute bridge", Mode.REPETITIONS_ONLY,
        "strength", "hinge", [], ["glutes"],
        "Lying on your back, drive the hips up and lower under control.",
        ["Move through a range that keeps the lower back comfortable."], secondary=["hamstrings"]),
    _ex("starter.reverse_lunge", "starter-reverse-lunge", "Reverse lunge", Mode.REPETITIONS_ONLY,
        "strength", "lunge", [], ["quadriceps", "glutes"],
        "Step back into a controlled lunge and return, alternating legs.",
        ["Hold a stable support if balance is uncertain."], secondary=["core"], unilateral=True),
    _ex("starter.dead_bug", "starter-dead-bug", "Alternating dead bug", Mode.REPETITIONS_ONLY,
        "core", "anti-extension", ["exercise mat"], ["core"],
        "Lower opposite arm and leg while keeping the trunk still, then alternate.",
        ["Use a range that lets the lower back stay controlled."], unilateral=True),
    _ex("starter.bird_dog", "starter-bird-dog", "Bird dog", Mode.REPETITIONS_ONLY,
        "core", "anti-rotation", ["exercise mat"], ["core"],
        "On hands and knees, extend opposite arm and leg, then return and alternate.",
        ["Move slowly and keep the hips level."], secondary=["glutes"], unilateral=True),
    # duration
    _ex("starter.front_plank", "starter-front-plank", "Forearm plank", Mode.DURATION,
        "core", "isometric", ["exercise mat"], ["core"],
        "Hold a straight, braced position on the forearms for the planned time.",
        ["End the hold when the position can no longer be kept."], secondary=["shoulders"]),
    _ex("starter.side_plank", "starter-side-plank", "Side plank", Mode.DURATION,
        "core", "isometric", ["exercise mat"], ["core"],
        "Hold a braced side position supported by one forearm for the planned time.",
        ["Drop the bottom knee to reduce difficulty."], unilateral=True),
    _ex("starter.wall_sit", "starter-wall-sit", "Wall sit", Mode.DURATION,
        "strength", "isometric", [], ["quadriceps"],
        "Hold a seated position against a wall with thighs parallel to the floor.",
        ["Raise the hips higher to make the hold easier."], secondary=["glutes"]),
    _ex("starter.dead_hang", "starter-dead-hang", "Dead hang", Mode.DURATION,
        "strength", "hang", ["pull-up station"], ["forearms"],
        "Hang from a bar with a relaxed, controlled grip for the planned time.",
        ["Step off under control and stop before grip fully fails."], secondary=["back"]),
    _ex("starter.cat_cow", "starter-cat-cow", "Cat-cow flow", Mode.DURATION,
        "mobility", "spinal flow", ["exercise mat"], ["spine"],
        "On hands and knees, slowly alternate rounding and arching the spine for the planned time.",
        ["Move gently within a comfortable range."], secondary=["core"]),
    _ex("starter.hip_flexor_stretch", "starter-hip-flexor-stretch", "Half-kneeling hip flexor stretch", Mode.DURATION,
        "mobility", "static stretch", ["exercise mat"], ["hip flexors"],
        "In a half-kneeling position, gently shift forward to feel a light stretch and hold.",
        ["Ease off if the stretch feels sharp rather than gentle."], unilateral=True),
    # distance_and_duration
    _ex("starter.treadmill_walk", "starter-treadmill-walk", "Steady treadmill walk", Mode.DISTANCE_AND_DURATION,
        "cardio", "walking", ["treadmill"], ["lower body"],
        "Walk at a steady, comfortable pace for the planned distance and time.",
        ["Use the safety stop and step off if balance feels uncertain."]),
    _ex("starter.easy_jog", "starter-easy-jog", "Easy jog", Mode.DISTANCE_AND_DURATION,
        "cardio", "running", [], ["lower body"],
        "Jog at a conversational pace for the planned distance and time.",
        ["Slow to a walk if the effort stops feeling easy."]),
    _ex("starter.stationary_bike", "starter-stationary-bike", "Stationary bike", Mode.DISTANCE_AND_DURATION,
        "cardio", "cycling", ["stationary bike"], ["lower body"],
        "Cycle at a steady effort for the planned distance and time.",
        ["Set a resistance you can sustain comfortably."]),
    _ex("starter.rowing_machine", "starter-rowing-machine", "Rowing machine", Mode.DISTANCE_AND_DURATION,
        "cardio", "rowing", ["rowing machine"], ["back", "legs"],
        "Row at a steady rhythm for the planned distance and time.",
        ["Keep the movement smooth and controlled."], secondary=["core"]),
    # bodyweight_or_assisted_repetitions
    _ex("starter.assisted_pull_up", "starter-assisted-pull-up", "Band-assisted pull-up", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical pull", ["pull-up station"], ["back"],
        "Pull up with optional assistance and lower under control.",
        ["Avoid dropping quickly into the bottom position."], secondary=["biceps"]),
    _ex("starter.assisted_dip", "starter-assisted-dip", "Assisted dip", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical push", ["dip station"], ["chest", "triceps"],
        "Lower into a controlled dip with optional assistance and press back up.",
        ["Use a range where the shoulders stay comfortable."], secondary=["shoulders"]),
    _ex("starter.inverted_row", "starter-inverted-row", "Inverted row", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "horizontal pull", ["barbell", "squat rack"], ["back"],
        "Lying under a bar, pull the chest toward it and lower under control.",
        ["Raise the bar height to make the row easier."], secondary=["biceps"]),
    _ex("starter.negative_pull_up", "starter-negative-pull-up", "Negative pull-up", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical pull", ["pull-up station"], ["back"],
        "Start at the top of a pull-up and lower slowly under control.",
        ["Step down and reset rather than dropping quickly."], secondary=["biceps"]),
)


EXERCISE_SLUG_BY_KEY: dict[str, str] = {
    item["key"]: item["slug"] for item in LIBRARY_EXERCISES
}


# --------------------------------------------------------------------------- set builders


def _load(number: int, lo: int, hi: int, load: float, unit: str = "kg", *,
          rpe: float | None = None, rest: int = 90, tempo: str | None = None,
          set_type: str = "working") -> dict[str, Any]:
    item: dict[str, Any] = {
        "set_number": number, "set_type": set_type,
        "repetitions_min": lo, "repetitions_max": hi,
        "target_load_original_value": load, "target_load_original_unit": unit,
        "rest_seconds": rest,
    }
    if rpe is not None:
        item["target_rpe"] = rpe
    if tempo is not None:
        item["tempo"] = tempo
    return item


def _reps(number: int, lo: int, hi: int, *, rir: int | None = None, rpe: float | None = None,
          rest: int = 60, tempo: str | None = None, set_type: str = "working") -> dict[str, Any]:
    item: dict[str, Any] = {
        "set_number": number, "set_type": set_type,
        "repetitions_min": lo, "repetitions_max": hi, "rest_seconds": rest,
    }
    if rir is not None:
        item["target_rir"] = rir
    if rpe is not None:
        item["target_rpe"] = rpe
    if tempo is not None:
        item["tempo"] = tempo
    return item


def _dur(number: int, seconds: int, *, rpe: float | None = None, rest: int = 45,
         set_type: str = "working") -> dict[str, Any]:
    item: dict[str, Any] = {
        "set_number": number, "set_type": set_type,
        "target_duration_seconds": seconds, "rest_seconds": rest,
    }
    if rpe is not None:
        item["target_rpe"] = rpe
    return item


def _dist(number: int, seconds: int, distance: float, unit: str = "kilometers", *,
          rpe: float | None = None, rest: int = 0, set_type: str = "working") -> dict[str, Any]:
    item: dict[str, Any] = {
        "set_number": number, "set_type": set_type,
        "target_duration_seconds": seconds,
        "target_distance_value": distance, "target_distance_unit": unit,
        "rest_seconds": rest,
    }
    if rpe is not None:
        item["target_rpe"] = rpe
    return item


def _assist(number: int, lo: int, hi: int, *, assist: float | None = None, aunit: str = "kg",
            rir: int | None = None, rpe: float | None = None, rest: int = 75,
            tempo: str | None = None, set_type: str = "working") -> dict[str, Any]:
    item: dict[str, Any] = {
        "set_number": number, "set_type": set_type,
        "repetitions_min": lo, "repetitions_max": hi, "rest_seconds": rest,
    }
    if assist is not None:
        item["target_assistance_original_value"] = assist
        item["target_assistance_original_unit"] = aunit
    if rir is not None:
        item["target_rir"] = rir
    if rpe is not None:
        item["target_rpe"] = rpe
    if tempo is not None:
        item["tempo"] = tempo
    return item


def _slot(exercise_key: str, section: str, order: int, sets: list[dict[str, Any]], *,
          coach_notes: str | None = None, trainee_instructions: str | None = None) -> dict[str, Any]:
    return {
        "exercise_key": exercise_key, "section": section, "display_order": order,
        "coach_notes": coach_notes, "trainee_instructions": trainee_instructions, "sets": sets,
    }


def _template(key: str, name: str, description: str, goal_tags: list[str],
              minutes: int, rpe: float | None, slots: list[dict[str, Any]], *,
              trainee_instructions: str | None = None) -> dict[str, Any]:
    return {
        "key": key, "name": name, "description": description, "goal_tags": goal_tags,
        "estimated_duration_minutes": minutes, "target_session_rpe": rpe,
        "coach_notes": None,
        "trainee_instructions": trainee_instructions
        or "Move with control and stop any movement that causes pain.",
        "exercises": slots,
    }


LIBRARY_TEMPLATES: tuple[dict[str, Any], ...] = (
    _template("starter.tmpl.lower_a", "Lower Body Strength A",
        "General lower-body strength session with squat and hinge patterns.",
        ["strength", "beginner"], 45, 7, [
            _slot("starter.dead_bug", "warm_up", 1, [_reps(1, 8, 10, rir=3, set_type="warm_up")]),
            _slot("starter.goblet_squat", "main", 1, [_load(n, 8, 10, 12, rpe=7) for n in range(1, 4)]),
            _slot("starter.rdl", "main", 2, [_load(n, 8, 10, 14, rpe=7) for n in range(1, 4)]),
            _slot("starter.hip_thrust", "main", 3, [_load(n, 10, 12, 16, rpe=7) for n in range(1, 3)]),
            _slot("starter.front_plank", "cool_down", 1, [_dur(1, 30, rpe=4, set_type="back_off")]),
        ]),
    _template("starter.tmpl.upper_a", "Upper Body Strength A",
        "General upper-body strength session with push and pull patterns.",
        ["strength", "beginner"], 45, 7, [
            _slot("starter.push_up", "warm_up", 1, [_reps(1, 6, 8, rir=3, set_type="warm_up")]),
            _slot("starter.db_bench", "main", 1, [_load(n, 8, 10, 12, rpe=7) for n in range(1, 4)]),
            _slot("starter.one_arm_row", "main", 2, [_load(n, 8, 10, 12, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_shoulder_press", "main", 3, [_load(n, 10, 12, 8, rpe=7) for n in range(1, 3)]),
            _slot("starter.assisted_pull_up", "cool_down", 1, [_assist(1, 5, 6, assist=15, rir=3, set_type="back_off")]),
        ]),
    _template("starter.tmpl.full_body_beginner", "Full Body Foundation",
        "Simple full-body session using approachable movements.",
        ["general_health", "beginner"], 35, 6, [
            _slot("starter.bodyweight_squat", "main", 1, [_reps(n, 10, 12) for n in range(1, 3)]),
            _slot("starter.incline_push_up", "main", 2, [_reps(n, 8, 12) for n in range(1, 3)]),
            _slot("starter.glute_bridge", "main", 3, [_reps(n, 10, 12) for n in range(1, 3)]),
            _slot("starter.front_plank", "cool_down", 1, [_dur(1, 25, rpe=4, set_type="back_off")]),
        ]),
    _template("starter.tmpl.bodyweight_a", "Bodyweight Home A",
        "No-equipment session suitable for home training.",
        ["general_health", "beginner"], 30, 6, [
            _slot("starter.bodyweight_squat", "main", 1, [_reps(n, 10, 15) for n in range(1, 3)]),
            _slot("starter.push_up", "main", 2, [_reps(n, 6, 10) for n in range(1, 3)]),
            _slot("starter.reverse_lunge", "main", 3, [_reps(n, 8, 10) for n in range(1, 3)]),
            _slot("starter.side_plank", "cool_down", 1, [_dur(1, 20, set_type="back_off")]),
        ]),
    _template("starter.tmpl.bodyweight_b", "Bodyweight Home B",
        "Second no-equipment home session with core focus.",
        ["general_health", "beginner"], 30, 6, [
            _slot("starter.glute_bridge", "main", 1, [_reps(n, 10, 15) for n in range(1, 3)]),
            _slot("starter.incline_push_up", "main", 2, [_reps(n, 8, 12) for n in range(1, 3)]),
            _slot("starter.bird_dog", "main", 3, [_reps(n, 8, 10) for n in range(1, 3)]),
            _slot("starter.wall_sit", "cool_down", 1, [_dur(1, 30, set_type="back_off")]),
        ]),
    _template("starter.tmpl.lower_b", "Lower Body Strength B",
        "Second lower-body strength session with squat and lunge patterns.",
        ["strength", "intermediate"], 50, 7, [
            _slot("starter.back_squat", "main", 1, [_load(n, 5, 8, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.walking_lunge", "main", 2, [_reps(n, 8, 10) for n in range(1, 3)]),
            _slot("starter.hip_thrust", "main", 3, [_load(n, 8, 10, 20, rpe=7) for n in range(1, 3)]),
            _slot("starter.side_plank", "cool_down", 1, [_dur(1, 30, set_type="back_off")]),
        ]),
    _template("starter.tmpl.upper_b", "Upper Body Strength B",
        "Second upper-body strength session emphasizing pulling.",
        ["strength", "intermediate"], 50, 7, [
            _slot("starter.db_shoulder_press", "main", 1, [_load(n, 8, 10, 10, rpe=7) for n in range(1, 4)]),
            _slot("starter.inverted_row", "main", 2, [_assist(n, 8, 10) for n in range(1, 4)]),
            _slot("starter.assisted_dip", "main", 3, [_assist(n, 6, 8, assist=10) for n in range(1, 3)]),
            _slot("starter.dead_hang", "cool_down", 1, [_dur(1, 20, set_type="back_off")]),
        ]),
    _template("starter.tmpl.conditioning", "Strength and Conditioning Mix",
        "Light conditioning session combining cardio and simple strength.",
        ["general_health", "endurance"], 35, 6, [
            _slot("starter.easy_jog", "warm_up", 1, [_dist(1, 300, 0.6, rpe=4, set_type="warm_up")]),
            _slot("starter.stationary_bike", "main", 1, [_dist(1, 600, 3.0, rpe=6)]),
            _slot("starter.rowing_machine", "main", 2, [_dist(1, 300, 0.75, rpe=6)]),
        ]),
    _template("starter.tmpl.mobility", "Mobility and Flexibility Flow",
        "Gentle mobility session for general movement quality.",
        ["recovery", "general_health"], 25, 4, [
            _slot("starter.cat_cow", "warm_up", 1, [_dur(1, 60, rpe=3, set_type="warm_up")]),
            _slot("starter.hip_flexor_stretch", "main", 1, [_dur(1, 40, rpe=3)]),
            _slot("starter.wall_sit", "main", 2, [_dur(1, 30, rpe=4)]),
            _slot("starter.dead_hang", "cool_down", 1, [_dur(1, 20, set_type="back_off")]),
        ]),
    _template("starter.tmpl.recovery_walk", "Recovery Walk and Core",
        "Easy recovery session pairing a walk with light core work.",
        ["recovery", "general_health"], 30, 4, [
            _slot("starter.treadmill_walk", "main", 1, [_dist(1, 1200, 1.5, rpe=4)]),
            _slot("starter.front_plank", "main", 2, [_dur(1, 30, rpe=4)]),
            _slot("starter.glute_bridge", "cool_down", 1, [_reps(1, 10, 12, set_type="back_off")]),
        ]),
)


# --------------------------------------------------------------------------- programs


def _session(template_key: str, weekday: str, order: int, *, required: bool = True,
             instructions: str | None = None) -> dict[str, Any]:
    return {
        "template_key": template_key, "weekday": weekday, "display_order": order,
        "required": required, "planned_duration_override_minutes": None,
        "target_session_rpe_override": None, "coach_notes": None,
        "trainee_instructions": instructions,
    }


def _week(number: int, sessions: list[dict[str, Any]], *, label: str | None = None,
          is_deload: bool = False) -> dict[str, Any]:
    return {
        "week_number": number, "label": label, "coach_notes": None,
        "is_deload": is_deload, "sessions": sessions,
    }


def _repeat_weeks(count: int, sessions: list[dict[str, Any]], *, deload_last: bool = False,
                  ) -> list[dict[str, Any]]:
    weeks = []
    for number in range(1, count + 1):
        is_deload = deload_last and number == count
        label = "Lighter week" if is_deload else f"Week {number}"
        weeks.append(_week(number, sessions, label=label, is_deload=is_deload))
    return weeks


LIBRARY_PROGRAMS: tuple[dict[str, Any], ...] = (
    {
        "key": "starter.prog.beginner_full_body",
        "name": "Beginner Full-Body Strength",
        "description": "A four-week, three-day full-body starting point for newer trainees.",
        "goal_tags": ["strength", "beginner"],
        "duration_weeks": 4,
        "coach_notes": "General starting structure; review and adjust before assigning.",
        "trainee_instructions": "Complete the three sessions on non-consecutive days when possible.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.full_body_beginner", "monday", 1),
            _session("starter.tmpl.lower_a", "wednesday", 1),
            _session("starter.tmpl.upper_a", "friday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.bodyweight_foundation",
        "name": "Beginner Bodyweight Foundation",
        "description": "A four-week, three-day plan using minimal or no equipment for home training.",
        "goal_tags": ["general_health", "beginner"],
        "duration_weeks": 4,
        "coach_notes": "Home-friendly; substitute movements as appropriate for the trainee.",
        "trainee_instructions": "Rest at least a day between sessions.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.bodyweight_a", "monday", 1),
            _session("starter.tmpl.full_body_beginner", "wednesday", 1),
            _session("starter.tmpl.bodyweight_b", "friday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.upper_lower",
        "name": "General Gym Strength - Upper/Lower",
        "description": "A four-week, four-day upper/lower split for a general gym context.",
        "goal_tags": ["strength", "intermediate"],
        "duration_weeks": 4,
        "coach_notes": "General intermediate structure without advanced claims.",
        "trainee_instructions": "Pair each upper day with the following lower day.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.upper_a", "monday", 1),
            _session("starter.tmpl.lower_a", "tuesday", 1),
            _session("starter.tmpl.upper_b", "thursday", 1),
            _session("starter.tmpl.lower_b", "friday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.strength_conditioning",
        "name": "General Fitness - Strength and Conditioning",
        "description": "A three-week, three-day mix of simple strength and light conditioning.",
        "goal_tags": ["general_health", "endurance"],
        "duration_weeks": 3,
        "coach_notes": "Balances strength and easy conditioning; no weight-loss guarantees.",
        "trainee_instructions": "Keep conditioning efforts comfortable and controlled.",
        "weeks": _repeat_weeks(3, [
            _session("starter.tmpl.full_body_beginner", "monday", 1),
            _session("starter.tmpl.conditioning", "wednesday", 1),
            _session("starter.tmpl.recovery_walk", "saturday", 1, required=False),
        ]),
    },
    {
        "key": "starter.prog.mobility_recovery",
        "name": "Mobility and Recovery Sessions",
        "description": "A two-week, three-day set of gentle mobility and easy recovery sessions.",
        "goal_tags": ["recovery", "general_health"],
        "duration_weeks": 2,
        "coach_notes": "General mobility and recovery movement, not injury treatment.",
        "trainee_instructions": "Move gently and stop anything that feels sharp.",
        "weeks": _repeat_weeks(2, [
            _session("starter.tmpl.mobility", "monday", 1),
            _session("starter.tmpl.recovery_walk", "wednesday", 1),
            _session("starter.tmpl.mobility", "friday", 1, required=False),
        ]),
    },
)


# --------------------------------------------------------------------------- verification


def verify_library_content() -> list[str]:
    """Return a list of consistency problems in the curated content (empty when valid).

    Static checks only; the seeder additionally runs full domain validation.
    """
    problems: list[str] = []
    supported_modes = set(Mode)

    exercise_keys = [item["key"] for item in LIBRARY_EXERCISES]
    exercise_slugs = [item["slug"] for item in LIBRARY_EXERCISES]
    if len(set(exercise_keys)) != len(exercise_keys):
        problems.append("Duplicate exercise keys")
    if len(set(exercise_slugs)) != len(exercise_slugs):
        problems.append("Duplicate exercise slugs")
    key_set = set(exercise_keys)

    def _check_text(where: str, text: str | None) -> None:
        if not text:
            return
        lowered = text.lower()
        for phrase in BANNED_PHRASES:
            if phrase in lowered:
                problems.append(f"Disallowed phrase '{phrase.strip()}' in {where}")

    for item in LIBRARY_EXERCISES:
        if item["tracking_mode"] not in supported_modes:
            problems.append(f"Unsupported tracking mode in {item['key']}")
        _check_text(f"exercise {item['key']} instructions", item["instructions"])
        for cue in item["safety_cues"]:
            _check_text(f"exercise {item['key']} cue", cue)

    template_keys = [item["key"] for item in LIBRARY_TEMPLATES]
    template_names = [item["name"] for item in LIBRARY_TEMPLATES]
    if len(set(template_keys)) != len(template_keys):
        problems.append("Duplicate template keys")
    if len(set(template_names)) != len(template_names):
        problems.append("Duplicate template names")
    template_key_set = set(template_keys)

    for template in LIBRARY_TEMPLATES:
        _check_text(f"template {template['key']} description", template["description"])
        _check_text(f"template {template['key']} instructions", template["trainee_instructions"])
        if not template["exercises"]:
            problems.append(f"Template {template['key']} has no exercises")
        section_orders: dict[str, list[int]] = {}
        for slot in template["exercises"]:
            if slot["exercise_key"] not in key_set:
                problems.append(
                    f"Template {template['key']} references unknown exercise {slot['exercise_key']}"
                )
            section_orders.setdefault(slot["section"], []).append(slot["display_order"])
            set_numbers = [s["set_number"] for s in slot["sets"]]
            if sorted(set_numbers) != list(range(1, len(set_numbers) + 1)):
                problems.append(f"Template {template['key']} has non-contiguous set numbers")
        for section, orders in section_orders.items():
            if sorted(orders) != list(range(1, len(orders) + 1)):
                problems.append(
                    f"Template {template['key']} section {section} has non-contiguous order"
                )

    program_keys = [item["key"] for item in LIBRARY_PROGRAMS]
    program_names = [item["name"] for item in LIBRARY_PROGRAMS]
    if len(set(program_keys)) != len(program_keys):
        problems.append("Duplicate program keys")
    if len(set(program_names)) != len(program_names):
        problems.append("Duplicate program names")

    for program in LIBRARY_PROGRAMS:
        _check_text(f"program {program['key']} description", program["description"])
        _check_text(f"program {program['key']} instructions", program["trainee_instructions"])
        if not 1 <= program["duration_weeks"] <= 12:
            problems.append(f"Program {program['key']} has an unsupported duration")
        if len(program["weeks"]) != program["duration_weeks"]:
            problems.append(f"Program {program['key']} week count != duration_weeks")
        for week in program["weeks"]:
            if not week["sessions"]:
                problems.append(f"Program {program['key']} week {week['week_number']} has no sessions")
            slot_keys = [(s["weekday"], s["display_order"]) for s in week["sessions"]]
            if len(set(slot_keys)) != len(slot_keys):
                problems.append(
                    f"Program {program['key']} week {week['week_number']} has duplicate slots"
                )
            for session in week["sessions"]:
                if session["template_key"] not in template_key_set:
                    problems.append(
                        f"Program {program['key']} references unknown template {session['template_key']}"
                    )
    return problems
