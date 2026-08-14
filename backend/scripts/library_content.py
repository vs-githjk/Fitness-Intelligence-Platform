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

from app.models import ExerciseDifficulty as Difficulty
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
    difficulty: Difficulty = Difficulty.BEGINNER,
    coaching: list[str] | None = None,
    mistakes: list[str] | None = None,
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
        "difficulty": difficulty,
        "coaching_cues": coaching or [],
        "common_mistakes": mistakes or [],
    }


LIBRARY_EXERCISES: tuple[dict[str, Any], ...] = (
    # repetitions_and_load
    _ex("starter.goblet_squat", "starter-goblet-squat", "Goblet squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["dumbbell"], ["quadriceps", "glutes"],
        "Hold one weight at the chest and squat to a comfortable depth with control.",
        ["Keep the chest tall and stop at a depth you can control."], secondary=["core"],
        difficulty=Difficulty.BEGINNER,
        coaching=["Drive the knees out in line with the toes.", "Keep the elbows tucked under the weight."],
        mistakes=["Letting the heels lift off the floor.", "Rounding the upper back forward."]),
    _ex("starter.rdl", "starter-dumbbell-rdl", "Dumbbell Romanian deadlift", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["dumbbell"], ["hamstrings", "glutes"],
        "Hinge at the hips with a long spine, lowering the weights along the legs, then stand tall.",
        ["Move through a range that keeps your back comfortable and controlled."], secondary=["back"],
        difficulty=Difficulty.INTERMEDIATE,
        coaching=["Push the hips back before bending the knees.", "Keep the weights close to the legs."],
        mistakes=["Rounding the lower back at the bottom.", "Turning it into a squat instead of a hinge."]),
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

    # --- expanded barbell strength (repetitions_and_load) ---
    _ex("starter.barbell_front_squat", "starter-barbell-front-squat", "Barbell front squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["barbell", "squat rack"], ["quadriceps", "glutes"],
        "With the bar racked on the front of the shoulders, squat to a controlled depth and stand tall.",
        ["Use safety supports and a depth you can control."], secondary=["core"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the elbows high so the bar stays on the shoulder shelf.", "Brace the trunk before descending."],
        mistakes=["Letting the elbows drop so the bar rolls forward.", "Rounding the upper back under the bar."]),
    _ex("starter.barbell_deadlift", "starter-barbell-deadlift", "Barbell deadlift", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["barbell"], ["hamstrings", "glutes"],
        "Hinge to grip the bar, then stand tall by driving the floor away and locking the hips.",
        ["Set the back before pulling and stop the set if it rounds."], secondary=["back", "lower back", "forearms"],
        difficulty=Difficulty.INTERMEDIATE,
        coaching=["Take the slack out of the bar before you pull.", "Push the floor away rather than yanking the bar up."],
        mistakes=["Letting the hips shoot up before the bar leaves the floor.", "Rounding the lower back on the pull."]),
    _ex("starter.barbell_bench_press", "starter-barbell-bench-press", "Barbell bench press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["barbell", "bench"], ["chest", "triceps"],
        "Lower the bar to the chest under control and press it back over the shoulders.",
        ["Use a spotter or safeties for working loads."], secondary=["shoulders"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the wrists stacked over the elbows.", "Touch the mid-chest and press in a slight arc back over the shoulders."],
        mistakes=["Flaring the elbows straight out to the sides.", "Bouncing the bar off the chest."]),
    _ex("starter.barbell_overhead_press", "starter-barbell-overhead-press", "Barbell overhead press", Mode.REPETITIONS_AND_LOAD,
        "strength", "vertical push", ["barbell"], ["shoulders", "triceps"],
        "Press the bar from the shoulders to overhead and lower it under control.",
        ["Stop the set if overhead pressing becomes uncomfortable."], secondary=["core"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Squeeze the glutes so the ribcage stays down.", "Move the head back slightly to clear a straight bar path."],
        mistakes=["Leaning back into a bench-press position.", "Pressing the bar forward instead of straight up."]),
    _ex("starter.barbell_row", "starter-barbell-row", "Barbell row", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal pull", ["barbell"], ["back", "lats"],
        "Hinge to a supported torso angle and row the bar to the lower ribs, then lower it under control.",
        ["Keep the spine long and stop if the back rounds."], secondary=["biceps"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Lead with the elbows toward the hips.", "Hold the hinged torso angle steady through the set."],
        mistakes=["Standing up to heave the weight each rep.", "Shrugging the bar with the traps instead of rowing."]),
    _ex("starter.barbell_hip_thrust", "starter-barbell-hip-thrust", "Barbell hip thrust", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["barbell", "bench"], ["glutes", "hamstrings"],
        "With the upper back on a bench, drive the hips up under the bar to a level bridge and lower with control.",
        ["Pad the bar and move through a comfortable range."], secondary=["core"],
        coaching=["Finish by squeezing the glutes, not by arching the lower back.", "Keep the shins vertical at the top."],
        mistakes=["Over-arching the lower back to reach the top.", "Pushing through the toes instead of the whole foot."]),
    _ex("starter.barbell_rdl", "starter-barbell-rdl", "Barbell Romanian deadlift", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["barbell"], ["hamstrings", "glutes"],
        "From standing, push the hips back to lower the bar along the legs, then stand tall.",
        ["Keep the bar close and stop if the back rounds."], secondary=["lower back"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the bar brushing the thighs the whole way down.", "Feel the hamstrings load as the hips travel back."],
        mistakes=["Turning the hinge into a squat by bending the knees.", "Letting the bar drift away from the legs."]),
    _ex("starter.barbell_curl", "starter-barbell-curl", "Barbell biceps curl", Mode.REPETITIONS_AND_LOAD,
        "strength", "curl", ["barbell"], ["biceps"],
        "Curl the bar to shoulder height and lower it under control without swinging.",
        ["Choose a load you can lift without jerking the back."], secondary=["forearms"],
        coaching=["Keep the elbows pinned by the ribs.", "Lower under control for the full count."],
        mistakes=["Swinging the torso to start each rep.", "Letting the elbows drift forward at the top."]),
    _ex("starter.close_grip_bench", "starter-close-grip-bench-press", "Close-grip bench press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["barbell", "bench"], ["triceps", "chest"],
        "With hands about shoulder-width, lower the bar to the lower chest and press back up.",
        ["Use a spotter or safeties for working loads."], secondary=["shoulders"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the elbows tucked toward the ribs.", "Drive the bar up in a straight line."],
        mistakes=["Gripping so narrow the wrists ache.", "Flaring the elbows wide like a standard bench."]),

    # --- expanded dumbbell strength (repetitions_and_load) ---
    _ex("starter.db_goblet_squat_tempo", "starter-dumbbell-front-squat", "Dumbbell front squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["dumbbell"], ["quadriceps", "glutes"],
        "Hold two dumbbells at the shoulders and squat to a controlled depth, then stand tall.",
        ["Stop at a depth you can control."], secondary=["core"],
        coaching=["Keep the ribcage stacked over the hips.", "Drive the knees out in line with the toes."],
        mistakes=["Letting the chest collapse forward.", "Rising onto the toes out of the bottom."]),
    _ex("starter.db_incline_press", "starter-dumbbell-incline-press", "Dumbbell incline press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["dumbbell", "bench"], ["chest", "shoulders"],
        "On an inclined bench, press the dumbbells up over the upper chest and lower them under control.",
        ["Choose a load that keeps every rep controlled."], secondary=["triceps"],
        coaching=["Lower until the elbows are level with the torso.", "Press the dumbbells slightly together at the top."],
        mistakes=["Clashing the dumbbells at the top.", "Dropping the elbows below a comfortable stretch."]),
    _ex("starter.db_row_bench", "starter-dumbbell-chest-supported-row", "Chest-supported dumbbell row", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal pull", ["dumbbell", "bench"], ["back", "lats"],
        "Lying face-down on an incline bench, row the dumbbells to the ribs and lower under control.",
        ["Keep the head in a neutral line with the spine."], secondary=["biceps"],
        coaching=["Pull the elbows back toward the hips.", "Let the shoulder blades move rather than only the arms."],
        mistakes=["Peeling the chest off the bench to lift more.", "Shrugging instead of rowing."]),
    _ex("starter.db_lateral_raise", "starter-dumbbell-lateral-raise", "Dumbbell lateral raise", Mode.REPETITIONS_AND_LOAD,
        "strength", "raise", ["dumbbell"], ["shoulders"],
        "Raise the dumbbells out to the sides to shoulder height and lower them under control.",
        ["Use a light load and avoid shrugging."], secondary=["traps"],
        coaching=["Lead with the elbows, not the hands.", "Stop at shoulder height rather than swinging higher."],
        mistakes=["Using momentum from the hips to throw the weights up.", "Shrugging the traps toward the ears."]),
    _ex("starter.db_bicep_curl", "starter-dumbbell-biceps-curl", "Dumbbell biceps curl", Mode.REPETITIONS_AND_LOAD,
        "strength", "curl", ["dumbbell"], ["biceps"],
        "Curl the dumbbells to shoulder height and lower them under control.",
        ["Choose a load you can lift without swinging."], secondary=["forearms"],
        coaching=["Keep the elbows fixed by the sides.", "Control the lowering phase for the full range."],
        mistakes=["Swinging the torso to move the weight.", "Cutting the lowering phase short."]),
    _ex("starter.db_triceps_extension", "starter-dumbbell-overhead-triceps-extension", "Overhead dumbbell triceps extension", Mode.REPETITIONS_AND_LOAD,
        "strength", "extension", ["dumbbell"], ["triceps"],
        "Hold one dumbbell overhead and lower it behind the head, then extend the elbows to lock out.",
        ["Keep the load light enough to control behind the head."], secondary=["shoulders"],
        coaching=["Keep the upper arms pointing at the ceiling.", "Move only at the elbows."],
        mistakes=["Letting the elbows flare wide.", "Dropping the weight too far and losing control."]),
    _ex("starter.db_bulgarian_split_squat", "starter-dumbbell-bulgarian-split-squat", "Dumbbell Bulgarian split squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "lunge", ["dumbbell", "bench"], ["quadriceps", "glutes"],
        "With the rear foot on a bench, lower into a split squat and drive back up through the front foot.",
        ["Hold a support nearby if balance is uncertain."], secondary=["core"], unilateral=True, difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep most of the weight through the front heel.", "Lower straight down rather than forward."],
        mistakes=["Pushing off the back foot to stand.", "Letting the front knee cave inward."]),
    _ex("starter.db_step_up", "starter-dumbbell-step-up", "Dumbbell step-up", Mode.REPETITIONS_AND_LOAD,
        "strength", "lunge", ["dumbbell", "box"], ["quadriceps", "glutes"],
        "Step onto a box driving through the lead foot, then lower under control and alternate.",
        ["Use a box height you can control without pushing off the floor."], secondary=["core"], unilateral=True,
        coaching=["Drive through the whole lead foot.", "Control the descent rather than dropping down."],
        mistakes=["Pushing hard off the trailing foot.", "Letting the lead knee collapse inward."]),
    _ex("starter.db_shrug", "starter-dumbbell-shrug", "Dumbbell shrug", Mode.REPETITIONS_AND_LOAD,
        "strength", "raise", ["dumbbell"], ["traps"],
        "Lift the shoulders straight up toward the ears and lower them under control.",
        ["Avoid rolling the shoulders; move straight up and down."], secondary=["forearms"],
        coaching=["Pause briefly at the top.", "Keep the arms relaxed and let the traps do the work."],
        mistakes=["Rolling the shoulders in circles.", "Using the biceps to bend the arms."]),

    # --- kettlebell / cable / machine (repetitions_and_load) ---
    _ex("starter.kb_swing", "starter-kettlebell-swing", "Kettlebell swing", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["kettlebell"], ["glutes", "hamstrings"],
        "Hike the bell back between the legs and snap the hips forward to float it to chest height.",
        ["Keep the movement a hip hinge, not a squat or a lift with the arms."], secondary=["core", "back"],
        difficulty=Difficulty.INTERMEDIATE,
        coaching=["Drive the bell with the hips, not the shoulders.", "Let the bell float at the top rather than lifting it."],
        mistakes=["Squatting the swing instead of hinging.", "Using the arms to raise the bell."]),
    _ex("starter.kb_goblet_squat", "starter-kettlebell-goblet-squat", "Kettlebell goblet squat", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["kettlebell"], ["quadriceps", "glutes"],
        "Hold the bell at the chest and squat to a controlled depth, then stand tall.",
        ["Stop at a depth you can control."], secondary=["core"],
        coaching=["Keep the elbows tucked under the bell.", "Drive the knees out over the toes."],
        mistakes=["Letting the heels lift.", "Rounding the upper back forward."]),
    _ex("starter.kb_front_rack_lunge", "starter-kettlebell-front-rack-reverse-lunge", "Kettlebell front-rack reverse lunge", Mode.REPETITIONS_AND_LOAD,
        "strength", "lunge", ["kettlebell"], ["quadriceps", "glutes"],
        "Hold bells in the front rack, step back into a controlled lunge, and return, alternating legs.",
        ["Use a stride you can control."], secondary=["core"], unilateral=True, difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the torso tall with the ribcage down.", "Lower the back knee straight toward the floor."],
        mistakes=["Leaning forward over the front thigh.", "Taking a stride so short the front knee shoots past the toes."]),
    _ex("starter.cable_row", "starter-cable-seated-row", "Seated cable row", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal pull", ["cable", "machine"], ["back", "lats"],
        "Sit tall and pull the handle to the lower ribs, then return under control with a long spine.",
        ["Keep the torso still; avoid heaving with the lower back."], secondary=["biceps"],
        coaching=["Lead with the elbows toward the hips.", "Let the shoulder blades glide together at the end."],
        mistakes=["Rowing by leaning far back each rep.", "Rounding forward to reach at the return."]),
    _ex("starter.cable_lat_pulldown", "starter-cable-lat-pulldown", "Lat pulldown", Mode.REPETITIONS_AND_LOAD,
        "strength", "vertical pull", ["cable", "machine"], ["lats", "back"],
        "Pull the bar to the upper chest with a tall torso, then return under control.",
        ["Avoid leaning far back to force the bar down."], secondary=["biceps"],
        coaching=["Drive the elbows down toward the ribs.", "Keep the chest lifted throughout."],
        mistakes=["Swinging the torso to yank the bar.", "Pulling the bar behind the neck."]),
    _ex("starter.cable_triceps_pushdown", "starter-cable-triceps-pushdown", "Cable triceps pushdown", Mode.REPETITIONS_AND_LOAD,
        "strength", "extension", ["cable", "machine"], ["triceps"],
        "With the elbows by the sides, extend the arms down to lock out and return under control.",
        ["Keep the shoulders relaxed and down."], secondary=[],
        coaching=["Pin the elbows to the ribs.", "Squeeze to a full lockout each rep."],
        mistakes=["Letting the elbows drift forward.", "Leaning over the weight to push it down."]),
    _ex("starter.cable_face_pull", "starter-cable-face-pull", "Cable face pull", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal pull", ["cable", "machine"], ["upper back", "shoulders"],
        "Pull the rope toward the face with high elbows, then return under control.",
        ["Use a light load and keep the neck relaxed."], secondary=["traps"],
        coaching=["Pull the hands apart as they reach the face.", "Keep the elbows at shoulder height."],
        mistakes=["Turning it into a heavy row with the whole body.", "Dropping the elbows low."]),
    _ex("starter.leg_press", "starter-machine-leg-press", "Machine leg press", Mode.REPETITIONS_AND_LOAD,
        "strength", "squat", ["machine"], ["quadriceps", "glutes"],
        "Lower the platform to a controlled depth and press it back without locking the knees harshly.",
        ["Keep the lower back in contact with the pad."], secondary=["hamstrings"],
        coaching=["Push evenly through the whole foot.", "Stop the descent before the hips tuck under."],
        mistakes=["Letting the lower back round off the pad at the bottom.", "Snapping the knees into a hard lockout."]),
    _ex("starter.leg_extension", "starter-machine-leg-extension", "Machine leg extension", Mode.REPETITIONS_AND_LOAD,
        "strength", "extension", ["machine"], ["quadriceps"],
        "Extend the knees to straighten the legs, then lower under control.",
        ["Set the pad so the knee axis lines up with the machine."], secondary=[],
        coaching=["Pause briefly at the top.", "Lower slowly rather than letting the weight drop."],
        mistakes=["Slamming the weight stack at the bottom.", "Using momentum to kick the legs up."]),
    _ex("starter.leg_curl", "starter-machine-leg-curl", "Machine leg curl", Mode.REPETITIONS_AND_LOAD,
        "strength", "leg curl", ["machine"], ["hamstrings"],
        "Curl the pad toward the glutes and lower it under control.",
        ["Keep the hips down on the pad."], secondary=["calves"],
        coaching=["Curl smoothly without jerking.", "Control the lowering phase fully."],
        mistakes=["Lifting the hips to complete the curl.", "Letting the weight drop back down."]),
    _ex("starter.chest_press_machine", "starter-machine-chest-press", "Machine chest press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["machine"], ["chest", "triceps"],
        "Press the handles forward to near lockout and return under control.",
        ["Set the seat so the handles line up with mid-chest."], secondary=["shoulders"],
        coaching=["Keep the shoulder blades back against the pad.", "Stop just short of a hard lockout."],
        mistakes=["Shrugging the shoulders forward to press.", "Letting the handles snap back at the return."]),

    # --- expanded bodyweight strength (repetitions_only) ---
    _ex("starter.pike_push_up", "starter-pike-push-up", "Pike push-up", Mode.REPETITIONS_ONLY,
        "strength", "vertical push", [], ["shoulders", "triceps"],
        "In an inverted-V position, lower the crown of the head toward the floor and press back up.",
        ["Reduce the hip height if the shoulders feel strained."], secondary=["core"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Stack the hips over the shoulders for a vertical press.", "Keep the elbows tracking back, not flared wide."],
        mistakes=["Turning it into a flat push-up by dropping the hips.", "Letting the head jut forward instead of down."]),
    _ex("starter.diamond_push_up", "starter-diamond-push-up", "Diamond push-up", Mode.REPETITIONS_ONLY,
        "strength", "horizontal push", [], ["triceps", "chest"],
        "With the hands close under the chest, lower with braced elbows and press back up.",
        ["Drop to the knees if full reps cannot stay controlled."], secondary=["shoulders"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the elbows brushing the ribs.", "Hold a straight line from head to heels."],
        mistakes=["Letting the hips sag toward the floor.", "Flaring the elbows out to the sides."]),
    _ex("starter.pseudo_planche_push_up", "starter-decline-push-up", "Decline push-up", Mode.REPETITIONS_ONLY,
        "strength", "horizontal push", ["box"], ["chest", "shoulders"],
        "With the feet raised on a box, lower the chest to the floor and press back up.",
        ["Lower the foot height if the shoulders feel strained."], secondary=["triceps", "core"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the body in one line from the raised feet.", "Lower until the chest is near the floor."],
        mistakes=["Letting the hips pike up.", "Shortening the range near the bottom."]),
    _ex("starter.jump_squat", "starter-jump-squat", "Bodyweight jump squat", Mode.REPETITIONS_ONLY,
        "strength", "squat", [], ["quadriceps", "glutes"],
        "Squat to a controlled depth and jump, landing softly back into the next rep.",
        ["Land softly with bent knees; skip if joints feel sensitive."], secondary=["calves"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Absorb each landing by bending the knees and hips.", "Reset your balance before the next jump."],
        mistakes=["Landing with stiff, straight legs.", "Letting the knees cave in on landing."]),
    _ex("starter.split_squat", "starter-bodyweight-split-squat", "Bodyweight split squat", Mode.REPETITIONS_ONLY,
        "strength", "lunge", [], ["quadriceps", "glutes"],
        "In a staggered stance, lower the back knee toward the floor and drive back up through the front foot.",
        ["Hold a support if balance is uncertain."], secondary=["core"], unilateral=True,
        coaching=["Keep the front heel planted.", "Lower straight down rather than drifting forward."],
        mistakes=["Pushing off the back foot to stand.", "Letting the front knee cave inward."]),
    _ex("starter.single_leg_glute_bridge", "starter-single-leg-glute-bridge", "Single-leg glute bridge", Mode.REPETITIONS_ONLY,
        "strength", "hinge", ["exercise mat"], ["glutes"],
        "With one foot planted, drive the hips up to a level bridge and lower with control.",
        ["Move through a range that keeps the lower back comfortable."], secondary=["hamstrings", "core"], unilateral=True,
        coaching=["Keep the hips level as they rise.", "Finish by squeezing the glute, not arching the back."],
        mistakes=["Letting the raised-side hip drop.", "Over-arching the lower back at the top."]),
    _ex("starter.hip_hinge_goodmorning", "starter-bodyweight-good-morning", "Bodyweight good morning", Mode.REPETITIONS_ONLY,
        "strength", "hinge", [], ["hamstrings", "glutes"],
        "With hands at the chest, push the hips back to hinge forward with a long spine, then stand tall.",
        ["Move only as far as the back stays long and comfortable."], secondary=["lower back"],
        coaching=["Push the hips back rather than bending the waist.", "Keep a soft bend in the knees."],
        mistakes=["Rounding the back to reach lower.", "Squatting down instead of hinging back."]),
    _ex("starter.calf_raise", "starter-bodyweight-calf-raise", "Standing calf raise", Mode.REPETITIONS_ONLY,
        "strength", "calf raise", [], ["calves"],
        "Rise onto the balls of the feet, pause, and lower the heels under control.",
        ["Hold a support for balance if needed."], secondary=[],
        coaching=["Pause at the top of each rep.", "Lower the heels slowly for a full range."],
        mistakes=["Bouncing quickly through the reps.", "Cutting the range short at the bottom."]),
    _ex("starter.superman", "starter-superman", "Superman hold-to-rep", Mode.REPETITIONS_ONLY,
        "core", "anti-extension", ["exercise mat"], ["lower back"],
        "Lying face-down, lift the chest and thighs slightly off the floor and lower under control.",
        ["Lift only to a comfortable, gentle range."], secondary=["glutes"],
        coaching=["Lengthen through the crown of the head as you lift.", "Keep the neck in line with the spine."],
        mistakes=["Cranking the head and neck back.", "Jerking up into an aggressive arch."]),
    _ex("starter.mountain_climber", "starter-mountain-climber", "Mountain climber", Mode.REPETITIONS_ONLY,
        "core", "anti-extension", ["exercise mat"], ["core"],
        "From a plank, drive one knee toward the chest and switch legs under control.",
        ["Slow the pace to keep the hips level and the back stable."], secondary=["shoulders"], unilateral=True,
        coaching=["Keep the hips low and level, not bouncing.", "Move the legs while the shoulders stay stacked over the hands."],
        mistakes=["Letting the hips pike up with each drive.", "Rushing so the trunk twists side to side."]),
    _ex("starter.russian_twist", "starter-russian-twist", "Seated trunk rotation", Mode.REPETITIONS_ONLY,
        "core", "rotation", ["exercise mat"], ["obliques", "core"],
        "Seated with a leaned-back torso, rotate the trunk side to side under control.",
        ["Keep the spine long and rotate only as far as is comfortable."], secondary=[], unilateral=True,
        coaching=["Turn from the ribcage, not just the arms.", "Keep the chest tall as you rotate."],
        mistakes=["Rounding the back and yanking side to side.", "Moving the arms while the trunk stays still."]),
    _ex("starter.hollow_rock", "starter-hollow-rock", "Hollow body rock", Mode.REPETITIONS_ONLY,
        "core", "anti-extension", ["exercise mat"], ["core"],
        "In a hollow position with the lower back pressed down, rock gently through the range.",
        ["Bend the knees to make the position easier."], secondary=["hip flexors"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the lower back pinned to the floor.", "Rock from the whole body, staying rigid."],
        mistakes=["Letting the lower back arch off the floor.", "Bending at the hips instead of staying hollow."]),
    _ex("starter.band_pull_apart", "starter-band-pull-apart", "Band pull-apart", Mode.REPETITIONS_ONLY,
        "strength", "horizontal pull", ["resistance band"], ["upper back", "shoulders"],
        "Hold a band at shoulder height and pull it apart to the chest, then return under control.",
        ["Use a band tension you can control through the full range."], secondary=["traps"],
        coaching=["Squeeze the shoulder blades together.", "Keep the arms roughly straight throughout."],
        mistakes=["Shrugging the shoulders up to the ears.", "Letting the band snap back on the return."]),
    _ex("starter.band_row", "starter-band-row", "Resistance band row", Mode.REPETITIONS_ONLY,
        "strength", "horizontal pull", ["resistance band"], ["back", "lats"],
        "Anchor the band and row the handles to the ribs, then return with a long spine.",
        ["Set an anchor that will hold the band securely."], secondary=["biceps"],
        coaching=["Lead with the elbows toward the hips.", "Keep the torso still as you row."],
        mistakes=["Leaning back to move the handles.", "Shrugging instead of rowing."]),
    _ex("starter.band_squat", "starter-band-squat", "Resistance band squat", Mode.REPETITIONS_ONLY,
        "strength", "squat", ["resistance band"], ["quadriceps", "glutes"],
        "Stand on the band, hold the handles at the shoulders, and squat to a controlled depth.",
        ["Choose a band tension you can control at the top."], secondary=["core"],
        coaching=["Drive the knees out over the toes.", "Keep even tension on the band throughout."],
        mistakes=["Letting the knees cave inward.", "Rising onto the toes out of the bottom."]),

    # --- expanded duration (holds & mobility) ---
    _ex("starter.hollow_hold", "starter-hollow-hold", "Hollow body hold", Mode.DURATION,
        "core", "isometric", ["exercise mat"], ["core"],
        "Hold a hollow position with the lower back pressed into the floor for the planned time.",
        ["Bend the knees to reduce difficulty."], secondary=["hip flexors"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Press the lower back flat the entire hold.", "Reach the arms long past the head if it stays controlled."],
        mistakes=["Letting the lower back arch off the floor.", "Holding the breath through the set."]),
    _ex("starter.glute_bridge_hold", "starter-glute-bridge-hold", "Glute bridge hold", Mode.DURATION,
        "strength", "isometric", ["exercise mat"], ["glutes"],
        "Hold a level bridge with the hips lifted for the planned time.",
        ["Move through a range that keeps the lower back comfortable."], secondary=["hamstrings"],
        coaching=["Keep the ribcage down and the glutes squeezed.", "Keep the shins roughly vertical."],
        mistakes=["Over-arching the lower back to lift higher.", "Letting the hips sag during the hold."]),
    _ex("starter.side_plank_hold", "starter-side-plank-hold", "Side plank hold", Mode.DURATION,
        "core", "isometric", ["exercise mat"], ["obliques", "core"],
        "Hold a braced side position on one forearm with the hips lifted for the planned time.",
        ["Drop the bottom knee to reduce difficulty."], secondary=["shoulders"], unilateral=True,
        coaching=["Stack the shoulder over the elbow.", "Lift the hips so the body is one straight line."],
        mistakes=["Letting the hips sag toward the floor.", "Rolling the chest toward the ground."]),
    _ex("starter.wall_sit_hold", "starter-wall-sit-hold", "Wall sit hold", Mode.DURATION,
        "strength", "isometric", [], ["quadriceps"],
        "Hold a seated position against a wall with the thighs toward parallel for the planned time.",
        ["Raise the hips higher to make the hold easier."], secondary=["glutes"],
        coaching=["Keep the whole back flat against the wall.", "Press evenly through both heels."],
        mistakes=["Sliding the hips too low too soon.", "Drifting the knees past the toes."]),
    _ex("starter.deep_squat_hold", "starter-deep-squat-hold", "Deep squat hold", Mode.DURATION,
        "mobility", "static stretch", [], ["hip flexors"],
        "Hold a comfortable deep squat position, using a support if needed, for the planned time.",
        ["Hold a support in front and only go as deep as is comfortable."], secondary=["adductors"],
        coaching=["Let the elbows gently press the knees outward.", "Keep the heels down if the position allows."],
        mistakes=["Forcing depth that lifts the heels.", "Rounding hard through the lower back."]),
    _ex("starter.doorway_pec_stretch", "starter-doorway-chest-stretch", "Doorway chest stretch", Mode.DURATION,
        "mobility", "static stretch", [], ["chest"],
        "With the forearm on a doorframe, step gently forward to feel a light chest stretch and hold.",
        ["Ease off if the stretch feels sharp rather than gentle."], secondary=["shoulders"], unilateral=True,
        coaching=["Keep the shoulder down and relaxed.", "Breathe slowly and let the stretch ease in."],
        mistakes=["Pushing into a sharp, painful range.", "Shrugging the shoulder up toward the ear."]),
    _ex("starter.thread_the_needle", "starter-thread-the-needle", "Thread-the-needle rotation", Mode.DURATION,
        "mobility", "spinal flow", ["exercise mat"], ["upper back"],
        "On hands and knees, slowly reach one arm under the body and back out for the planned time.",
        ["Move gently within a comfortable range."], secondary=["shoulders"], unilateral=True,
        coaching=["Move slowly and follow the hand with the eyes.", "Let the upper back rotate rather than forcing it."],
        mistakes=["Rushing the rotation.", "Forcing the range past comfort."]),
    _ex("starter.hamstring_stretch", "starter-standing-hamstring-stretch", "Standing hamstring stretch", Mode.DURATION,
        "mobility", "static stretch", [], ["hamstrings"],
        "With one heel on a low surface and a long spine, hinge gently forward to feel a light stretch and hold.",
        ["Ease off if the stretch feels sharp."], secondary=["glutes"], unilateral=True,
        coaching=["Keep the back long as you hinge.", "Feel a gentle stretch, not a strain."],
        mistakes=["Rounding the back to reach further.", "Bouncing into the stretch."]),

    # --- expanded distance_and_duration (conditioning) ---
    _ex("starter.brisk_walk_outdoor", "starter-brisk-walk", "Brisk walk", Mode.DISTANCE_AND_DURATION,
        "cardio", "walking", [], ["lower body"],
        "Walk briskly at a steady, comfortable pace for the planned distance and time.",
        ["Choose a route and pace that feel comfortable."]),
    _ex("starter.incline_treadmill_walk", "starter-incline-treadmill-walk", "Incline treadmill walk", Mode.DISTANCE_AND_DURATION,
        "cardio", "walking", ["treadmill"], ["lower body"],
        "Walk on a gentle incline at a steady pace for the planned distance and time.",
        ["Use the safety stop and hold the rail if balance feels uncertain."], secondary=["calves"],
        coaching=["Keep an upright posture rather than leaning on the rails.", "Set an incline you can sustain comfortably."],
        mistakes=["Hanging on the handrails and dropping the effort.", "Starting at an incline that is too steep to sustain."]),
    _ex("starter.tempo_run", "starter-tempo-run", "Steady tempo run", Mode.DISTANCE_AND_DURATION,
        "cardio", "running", [], ["lower body"],
        "Run at a steady, moderately hard but sustainable pace for the planned distance and time.",
        ["Ease to a jog or walk if the effort becomes unsustainable."], secondary=["calves"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Hold a pace you could sustain for the whole distance.", "Keep the breathing rhythmic and steady."],
        mistakes=["Starting far too fast to hold the pace.", "Tensing the shoulders and arms."]),
    _ex("starter.bike_intervals", "starter-bike-steady-intervals", "Stationary bike steady intervals", Mode.DISTANCE_AND_DURATION,
        "cardio", "cycling", ["stationary bike"], ["lower body"],
        "Cycle at a steady, moderate effort for the planned distance and time.",
        ["Set a resistance you can sustain comfortably."], secondary=["quadriceps"],
        coaching=["Keep a smooth, even pedal cadence.", "Choose a resistance that keeps the effort steady."],
        mistakes=["Setting resistance so high the form breaks down.", "Bouncing in the saddle at high cadence."]),
    _ex("starter.row_intervals", "starter-row-steady", "Rowing machine steady piece", Mode.DISTANCE_AND_DURATION,
        "cardio", "rowing", ["rowing machine"], ["back", "legs"],
        "Row at a steady, controlled rhythm for the planned distance and time.",
        ["Keep the movement smooth and controlled."], secondary=["core"],
        coaching=["Drive with the legs first, then the back and arms.", "Return in the reverse order under control."],
        mistakes=["Yanking with the arms before the legs drive.", "Rounding the back at the catch."]),

    # --- expanded bodyweight_or_assisted_repetitions ---
    _ex("starter.pull_up", "starter-pull-up", "Pull-up", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical pull", ["pull-up station"], ["lats", "back"],
        "Pull the chin toward the bar and lower under control to a full hang.",
        ["Avoid dropping quickly into the bottom position."], secondary=["biceps"], difficulty=Difficulty.ADVANCED,
        coaching=["Start each rep from a controlled full hang.", "Drive the elbows down toward the ribs."],
        mistakes=["Kipping or swinging to complete reps.", "Cutting the range short at the top or bottom."]),
    _ex("starter.chin_up", "starter-chin-up", "Chin-up", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical pull", ["pull-up station"], ["biceps", "lats"],
        "With palms facing you, pull the chin toward the bar and lower under control.",
        ["Lower under control rather than dropping."], secondary=["back"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep the ribcage down and core braced.", "Pull the elbows down and back."],
        mistakes=["Swinging the legs to generate momentum.", "Shrugging the shoulders at the top."]),
    _ex("starter.dip", "starter-parallel-bar-dip", "Parallel bar dip", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical push", ["dip station"], ["chest", "triceps"],
        "Lower between the bars to a comfortable depth and press back up to lockout.",
        ["Use a range where the shoulders stay comfortable."], secondary=["shoulders"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Keep a slight forward lean for the chest.", "Lower only as far as the shoulders stay comfortable."],
        mistakes=["Dropping too deep and straining the shoulders.", "Bouncing out of the bottom."]),
    _ex("starter.ring_row", "starter-ring-row", "Ring or bar row (feet forward)", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "horizontal pull", ["pull-up station"], ["back", "lats"],
        "Hanging under a bar or rings, pull the chest up and lower under control.",
        ["Raise the anchor height to make the row easier."], secondary=["biceps"],
        coaching=["Keep the body in one straight line.", "Pull the chest to the bar, not just the chin."],
        mistakes=["Letting the hips sag toward the floor.", "Shortening the range near the top."]),
    _ex("starter.assisted_pistol", "starter-assisted-pistol-squat", "Assisted pistol squat", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "squat", [], ["quadriceps", "glutes"],
        "Holding a support, lower on one leg to a controlled depth and drive back up.",
        ["Hold a sturdy support and only descend as far as you can control."], secondary=["core"], unilateral=True,
        difficulty=Difficulty.ADVANCED,
        coaching=["Keep the working heel planted.", "Use the support only as much as needed."],
        mistakes=["Collapsing into the bottom position.", "Letting the knee cave inward."]),
    _ex("starter.negative_dip", "starter-negative-dip", "Negative dip", Mode.BODYWEIGHT_OR_ASSISTED_REPETITIONS,
        "strength", "vertical push", ["dip station"], ["triceps", "chest"],
        "Start at the top of a dip and lower slowly under control to a comfortable depth.",
        ["Step or jump back to the top rather than straining up."], secondary=["shoulders"],
        coaching=["Lower for a slow, even count.", "Keep the shoulders down away from the ears."],
        mistakes=["Dropping quickly instead of lowering.", "Sinking past a comfortable shoulder range."]),

    # --- accessory, carries and remaining coverage ---
    _ex("starter.db_floor_press", "starter-dumbbell-floor-press", "Dumbbell floor press", Mode.REPETITIONS_AND_LOAD,
        "strength", "horizontal push", ["dumbbell"], ["chest", "triceps"],
        "Lying on the floor, press the dumbbells up over the chest and lower until the upper arms touch down.",
        ["Let the upper arms rest briefly at the bottom to control the range."], secondary=["shoulders"],
        coaching=["Pause when the upper arms reach the floor.", "Keep the wrists stacked over the elbows."],
        mistakes=["Bouncing the elbows off the floor.", "Flaring the elbows straight out."]),
    _ex("starter.db_pullover", "starter-dumbbell-pullover", "Dumbbell pullover", Mode.REPETITIONS_AND_LOAD,
        "strength", "vertical pull", ["dumbbell", "bench"], ["lats", "chest"],
        "Lying on a bench, lower one dumbbell back over the head with a slight elbow bend, then pull it back over the chest.",
        ["Use a light load and keep the range comfortable for the shoulders."], secondary=["core"],
        coaching=["Keep the ribcage down as the arms travel back.", "Move the weight in a smooth arc."],
        mistakes=["Over-arching the lower back at the stretch.", "Bending the elbows to press instead of pulling over."]),
    _ex("starter.db_reverse_fly", "starter-dumbbell-reverse-fly", "Dumbbell reverse fly", Mode.REPETITIONS_AND_LOAD,
        "strength", "raise", ["dumbbell"], ["upper back", "shoulders"],
        "Hinged forward, raise the dumbbells out to the sides to shoulder height and lower under control.",
        ["Use a light load and avoid shrugging."], secondary=["traps"],
        coaching=["Lead with the elbows and squeeze the shoulder blades.", "Keep a soft, fixed bend in the elbows."],
        mistakes=["Swinging the weights up with momentum.", "Shrugging the shoulders toward the ears."]),
    _ex("starter.db_hammer_curl", "starter-dumbbell-hammer-curl", "Dumbbell hammer curl", Mode.REPETITIONS_AND_LOAD,
        "strength", "curl", ["dumbbell"], ["biceps", "forearms"],
        "With palms facing each other, curl the dumbbells to shoulder height and lower under control.",
        ["Choose a load you can lift without swinging."], secondary=[],
        coaching=["Keep the elbows pinned by the sides.", "Hold the neutral grip through the whole rep."],
        mistakes=["Swinging the torso to move the weight.", "Letting the elbows drift forward."]),
    _ex("starter.db_arnold_press", "starter-dumbbell-arnold-press", "Dumbbell Arnold press", Mode.REPETITIONS_AND_LOAD,
        "strength", "vertical push", ["dumbbell"], ["shoulders", "triceps"],
        "From a palms-in start at the shoulders, rotate and press the dumbbells overhead, then reverse under control.",
        ["Stop the set if overhead pressing becomes uncomfortable."], secondary=["core"], difficulty=Difficulty.INTERMEDIATE,
        coaching=["Rotate the palms smoothly as you press.", "Keep the ribcage down and core braced."],
        mistakes=["Leaning back to press the weight up.", "Rushing the rotation and losing control."]),
    _ex("starter.db_farmer_carry", "starter-dumbbell-farmer-carry", "Dumbbell farmer's carry", Mode.DURATION,
        "strength", "carry", ["dumbbell"], ["forearms", "core"],
        "Hold a dumbbell in each hand and walk tall with braced posture for the planned time.",
        ["Choose a load you can carry with an upright, controlled posture."], secondary=["traps"],
        coaching=["Stand tall with the shoulders down and back.", "Take short, controlled steps."],
        mistakes=["Letting the shoulders round forward under the load.", "Leaning to one side while walking."]),
    _ex("starter.db_suitcase_carry", "starter-dumbbell-suitcase-carry", "Dumbbell suitcase carry", Mode.DURATION,
        "core", "carry", ["dumbbell"], ["obliques", "core"],
        "Hold one dumbbell at one side and walk tall, resisting the lean, for the planned time.",
        ["Choose a load you can carry without leaning."], secondary=["forearms"], unilateral=True,
        coaching=["Stay level; resist the pull toward the loaded side.", "Keep the shoulders square as you walk."],
        mistakes=["Leaning away from or toward the weight.", "Letting the loaded shoulder hike up."]),
    _ex("starter.cable_pull_through", "starter-cable-pull-through", "Cable pull-through", Mode.REPETITIONS_AND_LOAD,
        "strength", "hinge", ["cable", "machine"], ["glutes", "hamstrings"],
        "Facing away from a low cable, hinge the hips back and then stand tall by driving the hips forward.",
        ["Keep the back long and stop if it rounds."], secondary=["lower back"],
        coaching=["Push the hips back rather than squatting down.", "Finish by squeezing the glutes, not leaning back."],
        mistakes=["Turning the hinge into a squat.", "Rounding the lower back at the bottom."]),
    _ex("starter.cable_woodchop", "starter-cable-woodchop", "Cable woodchop", Mode.REPETITIONS_AND_LOAD,
        "core", "rotation", ["cable", "machine"], ["obliques", "core"],
        "Rotate and pull the handle diagonally across the body, then return under control.",
        ["Use a light load and rotate only as far as is comfortable."], secondary=[], unilateral=True,
        coaching=["Turn from the ribcage, pivoting the back foot.", "Keep the arms roughly fixed and move from the trunk."],
        mistakes=["Yanking with only the arms.", "Over-rotating the lower back."]),
    _ex("starter.seated_calf_raise", "starter-machine-seated-calf-raise", "Seated calf raise", Mode.REPETITIONS_AND_LOAD,
        "strength", "calf raise", ["machine"], ["calves"],
        "With the pad on the knees, rise onto the balls of the feet, pause, and lower the heels under control.",
        ["Move through a comfortable range at the bottom."], secondary=[],
        coaching=["Pause at the top of each rep.", "Lower the heels slowly for a full stretch."],
        mistakes=["Bouncing quickly through the reps.", "Cutting the range short."]),
    _ex("starter.reverse_crunch", "starter-reverse-crunch", "Reverse crunch", Mode.REPETITIONS_ONLY,
        "core", "anti-extension", ["exercise mat"], ["core"],
        "Lying on the back, curl the knees toward the chest by lifting the hips, then lower under control.",
        ["Move through a range that keeps the lower back comfortable."], secondary=["hip flexors"],
        coaching=["Curl the pelvis up rather than swinging the legs.", "Lower slowly without arching the back."],
        mistakes=["Swinging the legs to create momentum.", "Letting the lower back arch off the floor."]),
    _ex("starter.bench_dip", "starter-bench-dip", "Bench dip", Mode.REPETITIONS_ONLY,
        "strength", "vertical push", ["bench"], ["triceps"],
        "With the hands on a bench behind you, lower the hips by bending the elbows and press back up.",
        ["Keep the range where the shoulders stay comfortable."], secondary=["chest", "shoulders"],
        coaching=["Keep the hips close to the bench.", "Bend the elbows straight back, not out."],
        mistakes=["Letting the shoulders roll forward at the bottom.", "Drifting the hips far from the bench."]),
    _ex("starter.inchworm", "starter-inchworm", "Inchworm walkout", Mode.REPETITIONS_ONLY,
        "mobility", "spinal flow", ["exercise mat"], ["core"],
        "Hinge to the floor, walk the hands out to a plank, then walk them back and stand tall.",
        ["Bend the knees as needed to reach the floor comfortably."], secondary=["hamstrings", "shoulders"],
        coaching=["Keep the hips steady as the hands walk out.", "Move slowly and stay braced in the plank."],
        mistakes=["Letting the hips sag in the plank.", "Rushing so the movement loses control."]),
    _ex("starter.copenhagen_hold", "starter-copenhagen-hold", "Copenhagen side hold", Mode.DURATION,
        "core", "isometric", ["bench", "exercise mat"], ["adductors"],
        "On your side with the top leg on a bench, lift the hips to a straight line and hold for the planned time.",
        ["Support the bottom leg on the floor to reduce difficulty."], secondary=["obliques"], unilateral=True,
        difficulty=Difficulty.ADVANCED,
        coaching=["Keep the body in one straight line.", "Press the top leg down into the bench to hold."],
        mistakes=["Letting the hips sag toward the floor.", "Rolling the torso forward or back."]),
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

    # --- push / pull / legs ---
    _template("starter.tmpl.push", "Push Day",
        "Chest, shoulders, and triceps pressing session.",
        ["strength", "hypertrophy"], 50, 7, [
            _slot("starter.push_up", "warm_up", 1, [_reps(1, 6, 8, rir=3, set_type="warm_up")]),
            _slot("starter.barbell_bench_press", "main", 1, [_load(n, 6, 8, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_shoulder_press", "main", 2, [_load(n, 8, 10, 10, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_lateral_raise", "main", 3, [_load(n, 12, 15, 6) for n in range(1, 3)]),
            _slot("starter.cable_triceps_pushdown", "main", 4, [_load(n, 10, 12, 15) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.pull", "Pull Day",
        "Back and biceps pulling session.",
        ["strength", "hypertrophy"], 50, 7, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.cable_lat_pulldown", "main", 1, [_load(n, 8, 10, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.barbell_row", "main", 2, [_load(n, 8, 10, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.cable_face_pull", "main", 3, [_load(n, 12, 15, 15) for n in range(1, 3)]),
            _slot("starter.db_bicep_curl", "main", 4, [_load(n, 10, 12, 10) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.legs", "Leg Day",
        "Full lower-body session with squat, hinge, and single-leg work.",
        ["strength", "hypertrophy"], 55, 8, [
            _slot("starter.bodyweight_squat", "warm_up", 1, [_reps(1, 10, 12, set_type="warm_up")]),
            _slot("starter.back_squat", "main", 1, [_load(n, 5, 8, 45, rpe=7) for n in range(1, 4)]),
            _slot("starter.barbell_rdl", "main", 2, [_load(n, 8, 10, 45, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_bulgarian_split_squat", "main", 3, [_load(n, 8, 10, 12) for n in range(1, 3)]),
            _slot("starter.calf_raise", "cool_down", 1, [_reps(1, 15, 20, set_type="back_off")]),
        ]),

    # --- strength emphasis ---
    _template("starter.tmpl.upper_strength", "Upper Body Strength",
        "Lower-rep upper-body strength focus on the main press and pull.",
        ["strength", "intermediate"], 55, 8, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.barbell_bench_press", "main", 1, [_load(n, 4, 6, 45, rpe=8) for n in range(1, 5)]),
            _slot("starter.barbell_row", "main", 2, [_load(n, 5, 6, 45, rpe=8) for n in range(1, 4)]),
            _slot("starter.barbell_overhead_press", "main", 3, [_load(n, 5, 6, 25, rpe=8) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.lower_strength", "Lower Body Strength",
        "Lower-rep lower-body strength focus on squat and deadlift.",
        ["strength", "intermediate"], 55, 8, [
            _slot("starter.bodyweight_squat", "warm_up", 1, [_reps(1, 10, 12, set_type="warm_up")]),
            _slot("starter.back_squat", "main", 1, [_load(n, 3, 5, 55, rpe=8) for n in range(1, 5)]),
            _slot("starter.barbell_deadlift", "main", 2, [_load(n, 3, 5, 70, rpe=8) for n in range(1, 4)]),
            _slot("starter.front_plank", "cool_down", 1, [_dur(1, 40, set_type="back_off")]),
        ]),
    _template("starter.tmpl.upper_hypertrophy", "Upper Body Hypertrophy",
        "Higher-rep upper-body volume across push and pull.",
        ["hypertrophy", "intermediate"], 55, 7, [
            _slot("starter.push_up", "warm_up", 1, [_reps(1, 8, 10, set_type="warm_up")]),
            _slot("starter.db_incline_press", "main", 1, [_load(n, 10, 12, 14) for n in range(1, 4)]),
            _slot("starter.db_row_bench", "main", 2, [_load(n, 10, 12, 14) for n in range(1, 4)]),
            _slot("starter.db_lateral_raise", "main", 3, [_load(n, 12, 15, 6) for n in range(1, 4)]),
            _slot("starter.db_hammer_curl", "main", 4, [_load(n, 10, 12, 10) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.lower_hypertrophy", "Lower Body Hypertrophy",
        "Higher-rep lower-body volume with accessories.",
        ["hypertrophy", "intermediate"], 55, 7, [
            _slot("starter.bodyweight_squat", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.leg_press", "main", 1, [_load(n, 10, 12, 80) for n in range(1, 4)]),
            _slot("starter.leg_curl", "main", 2, [_load(n, 10, 12, 25) for n in range(1, 4)]),
            _slot("starter.leg_extension", "main", 3, [_load(n, 12, 15, 25) for n in range(1, 3)]),
            _slot("starter.seated_calf_raise", "main", 4, [_load(n, 12, 15, 20) for n in range(1, 3)]),
        ]),

    # --- body-part splits ---
    _template("starter.tmpl.chest_triceps", "Chest and Triceps",
        "Pressing volume for the chest paired with triceps accessories.",
        ["hypertrophy", "intermediate"], 50, 7, [
            _slot("starter.push_up", "warm_up", 1, [_reps(1, 8, 10, set_type="warm_up")]),
            _slot("starter.barbell_bench_press", "main", 1, [_load(n, 8, 10, 35, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_incline_press", "main", 2, [_load(n, 10, 12, 12) for n in range(1, 3)]),
            _slot("starter.close_grip_bench", "main", 3, [_load(n, 8, 10, 30) for n in range(1, 3)]),
            _slot("starter.cable_triceps_pushdown", "main", 4, [_load(n, 12, 15, 15) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.back_biceps", "Back and Biceps",
        "Vertical and horizontal pulling paired with biceps accessories.",
        ["hypertrophy", "intermediate"], 50, 7, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.cable_lat_pulldown", "main", 1, [_load(n, 8, 10, 40) for n in range(1, 4)]),
            _slot("starter.cable_row", "main", 2, [_load(n, 10, 12, 40) for n in range(1, 3)]),
            _slot("starter.barbell_curl", "main", 3, [_load(n, 8, 10, 20) for n in range(1, 3)]),
            _slot("starter.db_hammer_curl", "main", 4, [_load(n, 10, 12, 10) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.shoulders_arms", "Shoulders and Arms",
        "Overhead pressing with lateral, biceps, and triceps accessories.",
        ["hypertrophy", "intermediate"], 45, 7, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.db_shoulder_press", "main", 1, [_load(n, 8, 10, 10) for n in range(1, 4)]),
            _slot("starter.db_lateral_raise", "main", 2, [_load(n, 12, 15, 6) for n in range(1, 4)]),
            _slot("starter.db_bicep_curl", "main", 3, [_load(n, 10, 12, 10) for n in range(1, 3)]),
            _slot("starter.db_triceps_extension", "main", 4, [_load(n, 10, 12, 10) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.posterior_chain", "Posterior Chain",
        "Hinge-focused session for the hamstrings, glutes, and back.",
        ["strength", "intermediate"], 50, 7, [
            _slot("starter.glute_bridge", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.barbell_deadlift", "main", 1, [_load(n, 5, 6, 65, rpe=8) for n in range(1, 4)]),
            _slot("starter.barbell_hip_thrust", "main", 2, [_load(n, 8, 10, 40) for n in range(1, 4)]),
            _slot("starter.leg_curl", "main", 3, [_load(n, 10, 12, 25) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.quad_emphasis", "Quad Emphasis",
        "Squat-pattern focus with quad accessories.",
        ["hypertrophy", "intermediate"], 50, 7, [
            _slot("starter.bodyweight_squat", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.barbell_front_squat", "main", 1, [_load(n, 6, 8, 35, rpe=7) for n in range(1, 4)]),
            _slot("starter.leg_press", "main", 2, [_load(n, 10, 12, 80) for n in range(1, 3)]),
            _slot("starter.db_step_up", "main", 3, [_load(n, 10, 12, 10) for n in range(1, 3)]),
            _slot("starter.leg_extension", "main", 4, [_load(n, 12, 15, 25) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.glute_emphasis", "Glute Emphasis",
        "Hinge and bridge focus for the glutes.",
        ["hypertrophy", "intermediate"], 45, 7, [
            _slot("starter.glute_bridge", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.barbell_hip_thrust", "main", 1, [_load(n, 8, 10, 45, rpe=7) for n in range(1, 4)]),
            _slot("starter.cable_pull_through", "main", 2, [_load(n, 12, 15, 25) for n in range(1, 3)]),
            _slot("starter.db_bulgarian_split_squat", "main", 3, [_load(n, 10, 12, 10) for n in range(1, 3)]),
            _slot("starter.single_leg_glute_bridge", "cool_down", 1, [_reps(1, 10, 12, set_type="back_off")]),
        ]),

    # --- dumbbell-only ---
    _template("starter.tmpl.db_full_body", "Dumbbell Full Body",
        "Complete full-body session using only dumbbells.",
        ["strength", "general_health"], 45, 7, [
            _slot("starter.dead_bug", "warm_up", 1, [_reps(1, 8, 10, set_type="warm_up")]),
            _slot("starter.db_goblet_squat_tempo", "main", 1, [_load(n, 8, 10, 12) for n in range(1, 4)]),
            _slot("starter.db_incline_press", "main", 2, [_load(n, 8, 10, 12) for n in range(1, 4)]),
            _slot("starter.db_row_bench", "main", 3, [_load(n, 10, 12, 12) for n in range(1, 3)]),
            _slot("starter.db_farmer_carry", "cool_down", 1, [_dur(1, 40, set_type="back_off")]),
        ]),
    _template("starter.tmpl.db_upper", "Dumbbell Upper Body",
        "Dumbbell-only upper-body push and pull.",
        ["strength", "general_health"], 40, 7, [
            _slot("starter.push_up", "warm_up", 1, [_reps(1, 6, 8, set_type="warm_up")]),
            _slot("starter.db_incline_press", "main", 1, [_load(n, 8, 10, 12) for n in range(1, 4)]),
            _slot("starter.db_row_bench", "main", 2, [_load(n, 8, 10, 12) for n in range(1, 4)]),
            _slot("starter.db_arnold_press", "main", 3, [_load(n, 8, 10, 8) for n in range(1, 3)]),
            _slot("starter.db_hammer_curl", "main", 4, [_load(n, 10, 12, 10) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.db_lower", "Dumbbell Lower Body",
        "Dumbbell-only lower-body squat, hinge, and single-leg work.",
        ["strength", "general_health"], 40, 7, [
            _slot("starter.bodyweight_squat", "warm_up", 1, [_reps(1, 10, 12, set_type="warm_up")]),
            _slot("starter.db_goblet_squat_tempo", "main", 1, [_load(n, 10, 12, 12) for n in range(1, 4)]),
            _slot("starter.rdl", "main", 2, [_load(n, 8, 10, 14) for n in range(1, 4)]),
            _slot("starter.db_bulgarian_split_squat", "main", 3, [_load(n, 8, 10, 10) for n in range(1, 3)]),
            _slot("starter.calf_raise", "cool_down", 1, [_reps(1, 15, 20, set_type="back_off")]),
        ]),

    # --- kettlebell & home / bodyweight ---
    _template("starter.tmpl.kb_full_body", "Kettlebell Full Body",
        "Kettlebell circuit blending hinge, squat, and carry.",
        ["conditioning", "general_health"], 35, 7, [
            _slot("starter.glute_bridge", "warm_up", 1, [_reps(1, 10, 12, set_type="warm_up")]),
            _slot("starter.kb_swing", "main", 1, [_load(n, 12, 15, 16, rpe=7) for n in range(1, 4)]),
            _slot("starter.kb_goblet_squat", "main", 2, [_load(n, 10, 12, 16) for n in range(1, 3)]),
            _slot("starter.kb_front_rack_lunge", "main", 3, [_load(n, 8, 10, 12) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.bw_full_body", "Bodyweight Full Body",
        "No-equipment full-body strength circuit.",
        ["general_health", "beginner"], 30, 6, [
            _slot("starter.bodyweight_squat", "main", 1, [_reps(n, 12, 15) for n in range(1, 4)]),
            _slot("starter.push_up", "main", 2, [_reps(n, 8, 12) for n in range(1, 4)]),
            _slot("starter.split_squat", "main", 3, [_reps(n, 8, 10) for n in range(1, 3)]),
            _slot("starter.hollow_hold", "cool_down", 1, [_dur(1, 30, set_type="back_off")]),
        ]),
    _template("starter.tmpl.home_strength", "Home Strength (Minimal Kit)",
        "Home session using bands, a bench, and bodyweight.",
        ["general_health", "beginner"], 35, 6, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.band_squat", "main", 1, [_reps(n, 12, 15) for n in range(1, 4)]),
            _slot("starter.incline_push_up", "main", 2, [_reps(n, 8, 12) for n in range(1, 3)]),
            _slot("starter.band_row", "main", 3, [_reps(n, 12, 15) for n in range(1, 3)]),
            _slot("starter.side_plank_hold", "cool_down", 1, [_dur(1, 25, set_type="back_off")]),
        ]),
    _template("starter.tmpl.full_body_a", "Full Body A",
        "Balanced full-body session leading with a squat and press.",
        ["strength", "general_health"], 50, 7, [
            _slot("starter.dead_bug", "warm_up", 1, [_reps(1, 8, 10, set_type="warm_up")]),
            _slot("starter.back_squat", "main", 1, [_load(n, 6, 8, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.db_bench", "main", 2, [_load(n, 8, 10, 14) for n in range(1, 4)]),
            _slot("starter.cable_row", "main", 3, [_load(n, 10, 12, 40) for n in range(1, 3)]),
            _slot("starter.front_plank", "cool_down", 1, [_dur(1, 40, set_type="back_off")]),
        ]),
    _template("starter.tmpl.full_body_b", "Full Body B",
        "Balanced full-body session leading with a hinge and pull.",
        ["strength", "general_health"], 50, 7, [
            _slot("starter.bird_dog", "warm_up", 1, [_reps(1, 8, 10, set_type="warm_up")]),
            _slot("starter.barbell_rdl", "main", 1, [_load(n, 8, 10, 40, rpe=7) for n in range(1, 4)]),
            _slot("starter.cable_lat_pulldown", "main", 2, [_load(n, 8, 10, 40) for n in range(1, 4)]),
            _slot("starter.db_shoulder_press", "main", 3, [_load(n, 8, 10, 10) for n in range(1, 3)]),
            _slot("starter.reverse_crunch", "cool_down", 1, [_reps(1, 12, 15, set_type="back_off")]),
        ]),

    # --- core & conditioning ---
    _template("starter.tmpl.core_circuit", "Core Circuit",
        "Short standalone core session mixing anti-extension, rotation, and holds.",
        ["general_health", "conditioning"], 20, 6, [
            _slot("starter.dead_bug", "main", 1, [_reps(n, 8, 10) for n in range(1, 3)]),
            _slot("starter.side_plank_hold", "main", 2, [_dur(n, 25) for n in range(1, 3)]),
            _slot("starter.hollow_hold", "main", 3, [_dur(n, 25) for n in range(1, 3)]),
            _slot("starter.russian_twist", "cool_down", 1, [_reps(1, 12, 16, set_type="back_off")]),
        ]),
    _template("starter.tmpl.conditioning_intervals", "Cardio Intervals Mix",
        "Steady conditioning across bike and rower.",
        ["conditioning", "endurance"], 30, 6, [
            _slot("starter.brisk_walk_outdoor", "warm_up", 1, [_dist(1, 300, 0.4, rpe=4, set_type="warm_up")]),
            _slot("starter.bike_intervals", "main", 1, [_dist(1, 600, 3.5, rpe=6)]),
            _slot("starter.row_intervals", "main", 2, [_dist(1, 480, 1.2, rpe=6)]),
        ]),
    _template("starter.tmpl.arms_focus", "Arms Focus",
        "Direct biceps and triceps accessory session.",
        ["hypertrophy", "general_health"], 30, 6, [
            _slot("starter.band_pull_apart", "warm_up", 1, [_reps(1, 12, 15, set_type="warm_up")]),
            _slot("starter.barbell_curl", "main", 1, [_load(n, 8, 10, 20) for n in range(1, 3)]),
            _slot("starter.cable_triceps_pushdown", "main", 2, [_load(n, 10, 12, 15) for n in range(1, 3)]),
            _slot("starter.db_hammer_curl", "main", 3, [_load(n, 10, 12, 10) for n in range(1, 3)]),
            _slot("starter.bench_dip", "main", 4, [_reps(n, 8, 12) for n in range(1, 3)]),
        ]),
    _template("starter.tmpl.mobility_flow_b", "Mobility Flow B",
        "Second gentle mobility session for general movement quality.",
        ["recovery", "general_health"], 25, 4, [
            _slot("starter.cat_cow", "warm_up", 1, [_dur(1, 60, rpe=3, set_type="warm_up")]),
            _slot("starter.thread_the_needle", "main", 1, [_dur(1, 40, rpe=3)]),
            _slot("starter.deep_squat_hold", "main", 2, [_dur(1, 40, rpe=3)]),
            _slot("starter.hamstring_stretch", "cool_down", 1, [_dur(1, 30, set_type="back_off")]),
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
    {
        "key": "starter.prog.push_pull_legs",
        "name": "Push / Pull / Legs (6-Day)",
        "description": "A four-week, six-day push/pull/legs split for a general gym context.",
        "goal_tags": ["hypertrophy", "intermediate"],
        "duration_weeks": 4,
        "coach_notes": "Higher-frequency structure; review the volume before assigning.",
        "trainee_instructions": "Take the seventh day as rest; adjust if six sessions is too much.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.push", "monday", 1),
            _session("starter.tmpl.pull", "tuesday", 1),
            _session("starter.tmpl.legs", "wednesday", 1),
            _session("starter.tmpl.push", "friday", 1),
            _session("starter.tmpl.pull", "saturday", 1),
            _session("starter.tmpl.legs", "sunday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.ppl_3day",
        "name": "Push / Pull / Legs (3-Day)",
        "description": "A three-week, three-day push/pull/legs split for a lighter schedule.",
        "goal_tags": ["hypertrophy", "beginner"],
        "duration_weeks": 3,
        "coach_notes": "Approachable three-day version of the split.",
        "trainee_instructions": "Leave a rest day between sessions where possible.",
        "weeks": _repeat_weeks(3, [
            _session("starter.tmpl.push", "monday", 1),
            _session("starter.tmpl.pull", "wednesday", 1),
            _session("starter.tmpl.legs", "friday", 1),
        ]),
    },
    {
        "key": "starter.prog.hypertrophy_4day",
        "name": "Hypertrophy Upper/Lower (4-Day)",
        "description": "A four-week, four-day higher-volume upper/lower split.",
        "goal_tags": ["hypertrophy", "intermediate"],
        "duration_weeks": 4,
        "coach_notes": "Volume-oriented structure; adjust sets to the trainee.",
        "trainee_instructions": "Pair each upper day with the following lower day.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.upper_hypertrophy", "monday", 1),
            _session("starter.tmpl.lower_hypertrophy", "tuesday", 1),
            _session("starter.tmpl.upper_hypertrophy", "thursday", 1),
            _session("starter.tmpl.lower_hypertrophy", "friday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.dumbbell_only",
        "name": "Dumbbell-Only Full Body (3-Day)",
        "description": "A four-week, three-day plan using only dumbbells.",
        "goal_tags": ["strength", "general_health"],
        "duration_weeks": 4,
        "coach_notes": "Minimal-equipment structure suitable for home or a light gym.",
        "trainee_instructions": "Rest at least a day between sessions.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.db_upper", "monday", 1),
            _session("starter.tmpl.db_lower", "wednesday", 1),
            _session("starter.tmpl.db_full_body", "friday", 1),
        ], deload_last=True),
    },
    {
        "key": "starter.prog.general_strength_3day",
        "name": "General Strength (3-Day Full Body)",
        "description": "A four-week, three-day full-body strength plan alternating emphasis.",
        "goal_tags": ["strength", "intermediate"],
        "duration_weeks": 4,
        "coach_notes": "General structure without advanced periodization claims.",
        "trainee_instructions": "Train on non-consecutive days when possible.",
        "weeks": _repeat_weeks(4, [
            _session("starter.tmpl.full_body_a", "monday", 1),
            _session("starter.tmpl.lower_strength", "wednesday", 1),
            _session("starter.tmpl.upper_strength", "friday", 1),
        ], deload_last=True),
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
        for cue in item.get("coaching_cues", []):
            _check_text(f"exercise {item['key']} coaching cue", cue)
        for mistake in item.get("common_mistakes", []):
            _check_text(f"exercise {item['key']} common mistake", mistake)

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
