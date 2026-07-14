import { z } from 'zod'

const number = (min: number, max: number, integer = false) => z.preprocess(
  value => value === '' || value === null || value === undefined ? undefined : Number(value),
  (integer ? z.number().int() : z.number()).min(min).max(max),
)
const optionalNumber = (min: number, max: number, integer = false) => z.preprocess(
  value => value === '' || value === null || value === undefined ? null : Number(value),
  (integer ? z.number().int() : z.number()).min(min).max(max).nullable(),
)

export const checkInSchema = z.object({
  sleep_hours: number(0, 16),
  sleep_quality: number(1, 5, true),
  wake_refreshed: z.boolean(),
  soreness: number(0, 10, true),
  fatigue: number(0, 10, true),
  stress: number(0, 10, true),
  steps: number(0, 100000, true),
  exercised: z.boolean(),
  exercise_minutes: optionalNumber(1, 600, true),
  session_rpe: optionalNumber(0, 10),
  activity_types: z.array(z.string()),
  water_liters: number(0, 12),
  calories_consumed: optionalNumber(0, 10000),
  protein_grams: optionalNumber(0, 500),
  nutrition_adherence: optionalNumber(0, 100, true),
  overall_feeling: z.enum(['very_poor', 'poor', 'okay', 'good', 'excellent']),
  note: z.string().max(500).nullable().optional(),
}).superRefine((data, context) => {
  if (data.exercised && data.exercise_minutes == null) {
    context.addIssue({
      code: 'custom',
      path: ['exercise_minutes'],
      message: 'Enter the exercise duration',
    })
  }
  if (data.exercised && data.session_rpe == null) {
    context.addIssue({
      code: 'custom',
      path: ['session_rpe'],
      message: 'Enter the session RPE',
    })
  }
})
