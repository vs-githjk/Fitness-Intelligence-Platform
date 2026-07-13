export type Role = 'coach' | 'trainee'
export interface User { id: string; email: string; first_name: string; last_name: string; role: Role }
export interface AuthResponse { access_token: string; token_type: string; user: User }
export interface AssessmentData {
  age?: number; height_cm?: number; weight_kg?: number; selected_goal?: string; target_weight_kg?: number;
  hydration_ml?: number; sleep_hours?: number; sleep_quality?: number; wake_refreshed?: boolean;
  daily_steps?: number; activity_types: string[]; activity_minutes_weekly?: number;
  workout_frequency_weekly?: number; average_rpe?: number; workout_duration_minutes?: number; perceived_recovery?: number;
  stress_level?: number; resting_heart_rate?: number; palpitations: boolean; shortness_of_breath: boolean; chest_pain: boolean;
  calorie_mode?: string; calorie_target?: number; calorie_intake?: number; protein_target_g?: number; protein_intake_g?: number;
  carbohydrate_intake_g?: number; healthy_fat_intake_g?: number; fruit_servings?: number; vegetable_servings?: number; fiber_g?: number; meal_consistency?: number;
}
export interface Assessment { id: string; status: string; schema_version: string; responses: AssessmentData; missing_required_fields: string[]; submitted_at: string | null; updated_at: string }
export interface ComponentScore { key: string; raw_inputs: Record<string, unknown>; normalized_score: number; weight: number; weighted_contribution: number; status: string; explanation: string }
export interface RiskFlag { rule_key: string; severity: string; status: string; title: string; explanation: string; recommended_action: string; triggering_inputs: Record<string, unknown>; rule_version: string; triggered_at: string }
export interface Recommendation { key: string; category: string; priority: string; trigger: string; recommended_action: string; supporting_calculation: Record<string, unknown>; safety_text?: string }
export interface HealthIndex { id: string; trainee_id: string; assessment_id: string; overall_score: number; band: string; scoring_version: string; calculated_at: string; components: ComponentScore[]; missing_fields: string[]; risk_flags: RiskFlag[]; recommendations: Recommendation[] }
export interface TraineeSummary { trainee_id: string; name: string; email: string; assessment_status: string; current_score: number | null; band: string | null; open_alerts: number }
export interface TraineeDetail { trainee: User; profile: Record<string, unknown> | null; assessment_status: string; health_index: HealthIndex | null }
