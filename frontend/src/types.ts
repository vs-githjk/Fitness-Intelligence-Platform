export type Role = 'coach' | 'trainee'
export interface User { id: string; email: string; first_name: string; last_name: string; role: Role }
export interface AuthResponse { access_token: string; token_type: string; user: User }

export interface AssessmentData {
  age?: number; height_cm?: number; weight_kg?: number; selected_goal?: string; target_weight_kg?: number
  hydration_ml?: number; sleep_hours?: number; sleep_quality?: number; wake_refreshed?: boolean
  daily_steps?: number; activity_types: string[]; activity_minutes_weekly?: number
  workout_frequency_weekly?: number; average_rpe?: number; workout_duration_minutes?: number; perceived_recovery?: number
  stress_level?: number; resting_heart_rate?: number; palpitations: boolean; shortness_of_breath: boolean; chest_pain: boolean
  calorie_mode?: string; calorie_target?: number; calorie_intake?: number; protein_target_g?: number; protein_intake_g?: number
  carbohydrate_intake_g?: number; healthy_fat_intake_g?: number; fruit_servings?: number; vegetable_servings?: number; fiber_g?: number; meal_consistency?: number
}

export interface Assessment {
  id: string; status: string; schema_version: string; responses: AssessmentData
  missing_required_fields: string[]; submitted_at: string | null; updated_at: string
}

export interface ComponentScore {
  key: string; raw_inputs: Record<string, unknown>; normalized_score: number; weight: number
  weighted_contribution: number; status: string; explanation: string
}
export interface RiskFlag {
  rule_key: string; severity: string; status: string; title: string; explanation: string
  recommended_action: string; triggering_inputs: Record<string, unknown>; rule_version: string; triggered_at: string
}
export interface Recommendation {
  key: string; category: string; priority: string; trigger: string; recommended_action: string
  supporting_calculation: Record<string, unknown>; safety_text?: string
}
export interface HealthIndex {
  id: string; trainee_id: string; assessment_id: string; overall_score: number; band: string
  scoring_version: string; calculated_at: string; components: ComponentScore[]; missing_fields: string[]
  risk_flags: RiskFlag[]; recommendations: Recommendation[]
}

export interface Profile {
  id: string; user_id: string; age?: number; height_cm?: number; weight_kg?: number
  selected_goal?: string; target_weight_kg?: number; timezone: string
}
export interface TraineeSummary {
  trainee_id: string; name: string; email: string; assessment_status: string; current_score: number | null
  band: string | null; open_alerts: number; selected_goal?: string | null
  assessment_updated_at?: string | null; baseline_calculated_at?: string | null
  latest_check_in_date?: string | null; latest_check_in_at?: string | null
  latest_readiness_score?: number | null; latest_readiness_state?: string | null
  checked_in_today: boolean; open_daily_alerts: number
}
export interface TraineeDetail {
  trainee: User; profile: Profile | null; assessment_status: string; assessment?: Assessment | null
  health_index: HealthIndex | null
}
export interface CoachAlert {
  id: string; trainee_id: string; rule_key: string; severity: string; title: string
  explanation: string; recommended_action: string; triggered_at: string
}
export interface CoachRelationship {
  assignment_status: string; coach_id?: string | null; coach_name?: string | null; coach_email?: string | null
}

export interface DailyCheckInData {
  sleep_hours: number; sleep_quality: number; wake_refreshed: boolean
  soreness: number; fatigue: number; stress: number; steps: number; exercised: boolean
  exercise_minutes?: number | null; session_rpe?: number | null; activity_types: string[]
  water_liters: number; calories_consumed?: number | null; protein_grams?: number | null
  nutrition_adherence?: number | null; overall_feeling: 'very_poor' | 'poor' | 'okay' | 'good' | 'excellent'
  note?: string | null
}
export interface DailyCheckIn extends DailyCheckInData {
  id: string; trainee_id: string; local_date: string; timezone: string
  submitted_at: string; created_at: string; updated_at: string
}
export interface DailyScoreComponent {
  key: string; group: string; raw_inputs: Record<string, unknown>; normalized_score: number
  weight: number; contribution: number; status: string; explanation: string; missing: boolean
}
export interface DailyScoreSummary {
  id: string; trainee_id: string; daily_check_in_id: string; local_date: string
  recovery_score: number; activity_score: number; nutrition_score: number | null
  readiness_score: number; readiness_state: string; scoring_version: string; calculated_at: string
}
export interface DailyScore extends DailyScoreSummary {
  components: DailyScoreComponent[]; missing_fields: string[]
  recent_training_load: { window_days: number; daily_loads: number[]; total: number; tolerance_score: number }
  risk_flags: RiskFlag[]; recommendations: Recommendation[]
}
export interface TrendPoint {
  date: string; value: number | null; missing: boolean
  rolling_average?: number | null; difference_from_previous?: number | null
}
export interface TrendSeries { key: string; label: string; unit: string; points: TrendPoint[] }
export interface DailyTrends { start_date: string; end_date: string; timezone: string; series: TrendSeries[] }
export interface DailyAlert extends CoachAlert {
  daily_score_snapshot_id: string; rule_version: string; status: string
  triggering_inputs: Record<string, unknown>; resolved_at?: string | null
}
