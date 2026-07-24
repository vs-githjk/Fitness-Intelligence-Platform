export type Role = 'coach' | 'trainee'
export interface User { id: string; email: string; first_name: string; last_name: string; role: Role; is_demo: boolean }
export interface AuthResponse { access_token: string; token_type: string; user: User }
export interface UserProfile {
  id: string; user_id: string
  preferred_display_name: string | null; bio: string | null
  headline: string | null; coaching_specialties: string[] | null
  years_of_experience: number | null; certifications_text: string | null
  training_goals: string | null
  avatar: MediaAsset | null
  created_at: string; updated_at: string
}
export interface PublicProfile {
  user_id: string; role: Role; full_name: string
  preferred_display_name: string | null; headline: string | null; bio: string | null
  coaching_specialties: string[]; years_of_experience: number | null
  certifications_text: string | null; training_goals: string | null
  avatar_url: string | null
}
export interface UserPreferences { id: string; user_id: string; timezone: string; weight_unit: WeightUnit; distance_unit: DistanceUnit; locale: string; theme: string | null; privacy_settings: Record<string, unknown>; accessibility_settings: Record<string, unknown>; created_at: string; updated_at: string }
export type MediaPurpose = 'generic' | 'avatar' | 'exercise_image' | 'exercise_gif' | 'exercise_video' | 'document'
export type MediaVisibility = 'private' | 'coach_trainee' | 'exercise'
export type MediaLifecycleStatus = 'active' | 'replaced' | 'soft_deleted' | 'purged'
export interface MediaAsset { id: string; owner_user_id: string; uploader_user_id: string | null; purpose: MediaPurpose; visibility: MediaVisibility; lifecycle_status: MediaLifecycleStatus; content_type: string; byte_size: number; checksum_sha256: string; original_filename: string | null; content_url: string; created_at: string; updated_at: string; deleted_at: string | null; replaced_at: string | null }
export interface CoachInvite {
  id: string; intended_email: string | null; status: 'active' | 'used' | 'expired' | 'revoked'
  expires_at: string; used_at: string | null; used_by_user_id: string | null
  revoked_at: string | null; created_at: string
}
export interface CreatedCoachInvite extends CoachInvite { token: string }

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
  avatar_url?: string | null
}
export interface TraineeDetail {
  trainee: User; profile: Profile | null; assessment_status: string; assessment?: Assessment | null
  health_index: HealthIndex | null; avatar_url?: string | null
}
export interface CoachAlert {
  id: string; trainee_id: string; rule_key: string; severity: string; title: string
  explanation: string; recommended_action: string; triggered_at: string
}
export interface CoachRelationship {
  assignment_status: string; coach_id?: string | null; coach_name?: string | null; coach_email?: string | null
  coach_avatar_url?: string | null
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

export type ExerciseScope = 'system' | 'coach_private'
export type ExerciseStatus = 'active' | 'archived'
export type ExerciseVersionStatus = 'draft' | 'published'
export type ExerciseTrackingMode = 'repetitions_and_load' | 'repetitions_only' | 'duration' | 'distance_and_duration' | 'bodyweight_or_assisted_repetitions'
export type ExerciseDifficulty = 'beginner' | 'intermediate' | 'advanced'
export interface ExerciseMedia { id: string; purpose: MediaPurpose; content_type: string; byte_size: number; original_filename: string | null; content_url: string }

export interface ExerciseDraftData {
  name: string; description: string | null; instructions: string
  tracking_mode: ExerciseTrackingMode; category: string; movement_pattern: string
  equipment: string[]; primary_muscle_groups: string[]; secondary_muscle_groups: string[]
  unilateral: boolean; safety_cues: string[]
  difficulty: ExerciseDifficulty | null; coaching_cues: string[]; common_mistakes: string[]
  image_url: string | null; thumbnail_url: string | null
}
export interface ExerciseVersion extends ExerciseDraftData {
  id: string; exercise_id: string; version_number: number; status: ExerciseVersionStatus
  primary_image: ExerciseMedia | null; secondary_image: ExerciseMedia | null; demonstration_video: ExerciseMedia | null
  content_hash: string | null; created_by_user_id: string | null
  created_at: string; updated_at: string; published_at: string | null
}
export interface ExerciseSummary {
  id: string; scope: ExerciseScope; owner_coach_id: string | null; slug: string
  status: ExerciseStatus; created_at: string; archived_at: string | null
  published_version: ExerciseVersion | null; draft_version: ExerciseVersion | null
}
export interface ExerciseDetail extends ExerciseSummary { versions: ExerciseVersion[] }

export type WorkoutTemplateStatus = 'active' | 'archived'
export type WorkoutTemplateSection = 'warm_up' | 'main' | 'cool_down'
export type WorkoutSetType = 'warm_up' | 'working' | 'back_off' | 'drop_set'
export type WeightUnit = 'kg' | 'lb'
export type DistanceUnit = 'meters' | 'kilometers' | 'miles'

export interface WorkoutSetPrescriptionData {
  set_number: number; set_type: WorkoutSetType
  repetitions_min: number | null; repetitions_max: number | null
  target_duration_seconds: number | null
  target_distance_value: number | null; target_distance_unit: DistanceUnit | null
  target_load_original_value: number | null; target_load_original_unit: WeightUnit | null
  target_assistance_original_value: number | null; target_assistance_original_unit: WeightUnit | null
  target_rpe: number | null; target_rir: number | null; rest_seconds: number | null
  tempo: string | null; instructions: string | null
}
export interface WorkoutSetPrescription extends WorkoutSetPrescriptionData {
  id: string; target_load_canonical_kg: number | null
  target_assistance_canonical_kg: number | null; created_at: string
}
export interface WorkoutTemplateExerciseData {
  exercise_version_id: string; section: WorkoutTemplateSection; display_order: number
  coach_notes: string | null; trainee_instructions: string | null
  sets: WorkoutSetPrescriptionData[]
}
export interface WorkoutTemplateExercise extends WorkoutTemplateExerciseData {
  id: string; created_at: string; exercise_version: ExerciseVersion
  sets: WorkoutSetPrescription[]
}
export interface WorkoutTemplateDraftData {
  name: string; description: string | null; goal_tags: string[]
  estimated_duration_minutes: number | null; target_session_rpe: number | null
  coach_notes: string | null; trainee_instructions: string | null
  exercises: WorkoutTemplateExerciseData[]
}
export interface WorkoutTemplateVersion extends Omit<WorkoutTemplateDraftData, 'exercises'> {
  id: string; workout_template_id: string; version_number: number
  version_status: 'draft' | 'published'; draft_revision: number
  content_hash: string | null; created_by_user_id: string | null
  created_at: string; updated_at: string; published_at: string | null
  exercises: WorkoutTemplateExercise[]
}
export interface WorkoutTemplateVersionSummary {
  id: string; version_number: number; version_status: 'draft' | 'published'
  draft_revision: number; name: string; content_hash: string | null
  updated_at: string; published_at: string | null
}
export interface WorkoutTemplateSummary {
  id: string; status: WorkoutTemplateStatus; name: string; goal_tags: string[]
  estimated_duration_minutes: number | null; target_session_rpe: number | null
  exercise_count: number; current_published_version_number: number | null
  published_at: string | null; has_draft: boolean; created_at: string
  updated_at: string; archived_at: string | null
}
export interface WorkoutTemplateList {
  items: WorkoutTemplateSummary[]; page: number; per_page: number; total: number
}
export interface WorkoutTemplateDetail {
  id: string; owner_coach_id: string; status: WorkoutTemplateStatus
  current_published_version_id: string | null; created_at: string; updated_at: string
  archived_at: string | null; draft_version: WorkoutTemplateVersion | null
  published_version: WorkoutTemplateVersion | null; versions: WorkoutTemplateVersionSummary[]
}

export type TrainingProgramStatus = 'active' | 'archived'
export type ProgramWeekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday'
export interface ProgramTemplateVersionSummary { id: string; workout_template_id: string; version_number: number; name: string; goal_tags: string[]; estimated_duration_minutes: number | null; target_session_rpe: number | null; exercise_count: number }
export interface ProgramSessionData { workout_template_version_id: string; weekday: ProgramWeekday; display_order: number; required: boolean; planned_duration_override_minutes: number | null; target_session_rpe_override: number | null; coach_notes: string | null; trainee_instructions: string | null }
export interface ProgramSession extends ProgramSessionData { id: string; workout_template_version: ProgramTemplateVersionSummary; created_at: string }
export interface ProgramWeekData { week_number: number; label: string | null; coach_notes: string | null; is_deload: boolean; sessions: ProgramSessionData[] }
export interface ProgramWeek extends Omit<ProgramWeekData, 'sessions'> { id: string; created_at: string; sessions: ProgramSession[] }
export interface TrainingProgramDraftData { name: string; description: string | null; goal_tags: string[]; duration_weeks: number; coach_notes: string | null; trainee_instructions: string | null; weeks: ProgramWeekData[] }
export interface TrainingProgramVersion extends Omit<TrainingProgramDraftData, 'weeks'> { id: string; training_program_id: string; version_number: number; version_status: 'draft' | 'published'; draft_revision: number; content_hash: string | null; created_by_user_id: string | null; created_at: string; updated_at: string; published_at: string | null; weeks: ProgramWeek[] }
export interface TrainingProgramVersionSummary { id: string; version_number: number; version_status: 'draft' | 'published'; draft_revision: number; name: string; content_hash: string | null; updated_at: string; published_at: string | null }
export interface TrainingProgramSummary { id: string; status: TrainingProgramStatus; name: string; goal_tags: string[]; duration_weeks: number; workout_slot_count: number; deload_week_count: number; current_published_version_number: number | null; published_at: string | null; has_draft: boolean; created_at: string; updated_at: string; archived_at: string | null }
export interface TrainingProgramList { items: TrainingProgramSummary[]; page: number; per_page: number; total: number }
export interface TrainingProgramDetail { id: string; owner_coach_id: string; status: TrainingProgramStatus; current_published_version_id: string | null; cloned_from_program_id: string | null; created_at: string; updated_at: string; archived_at: string | null; draft_version: TrainingProgramVersion | null; published_version: TrainingProgramVersion | null; versions: TrainingProgramVersionSummary[] }
export interface LibraryProgramSummary { id: string; name: string; description: string | null; level: string; duration_weeks: number; sessions_per_week: number; goal_tags: string[]; equipment_summary: string[]; published_version_id: string }
export interface LibraryProgramList { items: LibraryProgramSummary[]; disclaimer: string }
export interface LibraryExercisePreview { name: string; category: string; tracking_mode: ExerciseTrackingMode; set_count: number }
export interface LibraryTemplatePreview { name: string; estimated_duration_minutes: number | null; exercises: LibraryExercisePreview[] }
export interface LibrarySessionPreview { weekday: ProgramWeekday; display_order: number; required: boolean; template: LibraryTemplatePreview }
export interface LibraryWeekPreview { week_number: number; label: string | null; is_deload: boolean; sessions: LibrarySessionPreview[] }
export interface LibraryProgramDetail extends LibraryProgramSummary { coach_notes: string | null; trainee_instructions: string | null; weeks: LibraryWeekPreview[]; disclaimer: string }

export type TrainingAssignmentStatus = 'active' | 'scheduled' | 'superseded' | 'cancelled'
export type ScheduledWorkoutStatus = 'scheduled' | 'in_progress' | 'completed' | 'partial' | 'cancelled' | 'superseded' | 'skipped'
export type WorkoutSkipKind = 'ordinary' | 'safety'
export interface WorkoutScheduleSkipResult { id: string; scheduled_workout_id: string; trainee_id: string; status: ScheduledWorkoutStatus; scheduled_date: string; required: boolean; skip_kind: WorkoutSkipKind | null; skip_reason: string | null; skip_note: string | null; skipped_at: string | null }
export interface WorkoutReadinessContext { id: string | null; scheduled_workout_id: string | null; workout_session_id: string | null; daily_score_snapshot_id: string | null; available: boolean; readiness_score: number | null; readiness_state: string | null; source_local_date: string | null; calculation_timestamp: string | null; scoring_version: string | null; age_days: number | null; is_stale: boolean | null; captured_at: string | null; guidance: string }
export interface ScheduledWorkout { id: string | null; workout_session_id?: string | null; training_assignment_id: string | null; workout_template_version_id: string; scheduled_date: string; program_week_number: number; program_week_label: string | null; is_deload: boolean; weekday: ProgramWeekday; display_order: number; required: boolean; planned_duration_minutes: number | null; target_session_rpe: number | null; trainee_instructions: string | null; status: ScheduledWorkoutStatus; skip_kind?: WorkoutSkipKind | null; skip_reason?: string | null; skip_note?: string | null; skipped_at?: string | null; workout_template_version: ProgramTemplateVersionSummary; readiness_context?: WorkoutReadinessContext | null }
export interface TrainingAssignment { id: string; coach_id: string; trainee_id: string; training_program_version_id: string; status: TrainingAssignmentStatus; is_primary: boolean; effective_start_date: string; effective_end_date: string | null; timezone: string; program_name: string; program_version_number: number; duration_weeks: number; goal_tags: string[]; created_at: string; activated_at: string | null; superseded_at: string | null; cancelled_at: string | null }
export interface AssignmentHistoryEvent { id: string; training_assignment_id: string; event_type: 'assigned' | 'scheduled' | 'activated' | 'superseded' | 'cancelled'; effective_date: string; snapshot: Record<string, unknown>; created_at: string }
export interface TrainingAssignmentWorkspace { timezone: string; local_today: string; current_assignment: TrainingAssignment | null; upcoming_assignment: TrainingAssignment | null; assignment_history: TrainingAssignment[]; history_events: AssignmentHistoryEvent[]; scheduled_workouts: ScheduledWorkout[] }
export interface TrainingAssignmentPreview { timezone: string; effective_start_date: string; effective_end_date: string; program_name: string; program_version_number: number; replaces_current: boolean; replaces_upcoming: boolean; workouts: ScheduledWorkout[] }

export type WorkoutSessionStatus = 'in_progress' | 'completed' | 'ended_incomplete' | 'safety_ended'
export type WorkoutSessionExerciseStatus = 'not_started' | 'in_progress' | 'completed' | 'skipped' | 'paused_for_safety' | 'safety_stopped'
export type WorkoutSetLogStatus = 'planned' | 'completed' | 'skipped'
export interface WorkoutSetLog { id: string; source_prescription_id: string | null; source: 'prescribed' | 'trainee_added'; set_number: number; set_type: WorkoutSetType; tracking_mode: ExerciseTrackingMode; planned_repetitions_min: number | null; planned_repetitions_max: number | null; planned_duration_seconds: number | null; planned_distance_value: string | null; planned_distance_unit: DistanceUnit | null; planned_load_original_value: string | null; planned_load_original_unit: WeightUnit | null; planned_assistance_original_value: string | null; planned_assistance_original_unit: WeightUnit | null; planned_rpe: string | null; planned_rir: string | null; planned_rest_seconds: number | null; planned_tempo: string | null; planned_instructions: string | null; actual_repetitions: number | null; actual_load_original_value: string | null; actual_load_original_unit: WeightUnit | null; actual_load_canonical_kg: string | null; actual_assistance_original_value: string | null; actual_assistance_original_unit: WeightUnit | null; actual_assistance_canonical_kg: string | null; actual_duration_seconds: number | null; actual_distance_value: string | null; actual_distance_unit: DistanceUnit | null; actual_rpe: string | null; actual_rir: string | null; status: WorkoutSetLogStatus; completed_at: string | null; revision: number }
export interface WorkoutSessionExercise { id: string; source_workout_template_exercise_id: string; exercise_version_id: string; exercise_name: string; tracking_mode: ExerciseTrackingMode; safety_cues: string[]; section: WorkoutTemplateSection; display_order: number; trainee_instructions: string | null; prescription_snapshot: Record<string, unknown>; status: WorkoutSessionExerciseStatus; skip_reason: string | null; skip_note: string | null; sets: WorkoutSetLog[] }
export interface WorkoutSessionEvent { id: string; event_type: string; created_at: string }
export interface WorkoutSession { id: string; scheduled_workout_id: string; status: WorkoutSessionStatus; scheduled_workout_status: ScheduledWorkoutStatus; workout_name: string; program_name: string; program_version_number: number; scheduled_date: string; estimated_duration_minutes: number | null; target_session_rpe: number | null; trainee_instructions: string | null; started_at: string; last_activity_at: string; completed_at: string | null; ended_at: string | null; actual_duration_minutes: number | null; session_rpe: string | null; trainee_note: string | null; revision: number; readiness_context?: WorkoutReadinessContext | null; exercises: WorkoutSessionExercise[]; events: WorkoutSessionEvent[] }
export type SafetyCategory = 'pain' | 'unusual_discomfort' | 'chest_discomfort' | 'breathing_difficulty' | 'dizziness_or_faintness' | 'loss_of_balance' | 'equipment_or_environment' | 'other'
export type SafetySeverity = 'mild' | 'moderate' | 'severe'
export type SafetyReportStatus = 'open' | 'acknowledged' | 'resolved'
export interface WorkoutSafetyReview { id: string; coach_id: string; action: 'acknowledged' | 'resolved'; note: string | null; created_at: string }
export interface WorkoutSafetyReport { id: string; workout_session_id: string; workout_session_exercise_id: string | null; workout_set_log_id: string | null; trainee_id: string; category: SafetyCategory; severity: SafetySeverity; note: string | null; activity_stopped: boolean; occurred_at: string; created_at: string; status: SafetyReportStatus; session_status: WorkoutSessionStatus; exercise_status: WorkoutSessionExerciseStatus | null; guidance: string }
export interface CoachWorkoutSafetyReport extends WorkoutSafetyReport { trainee_name: string; trainee_email: string; workout_name: string; scheduled_date: string; exercise_name: string | null; reviews: WorkoutSafetyReview[] }

// --- Workout Intelligence analytics (Phase 7B, workout-load-v1) ---
export type WorkoutClassification = 'completed' | 'partial' | 'ordinary_skipped' | 'safety_skipped' | 'missed' | 'pending' | 'coach_cancelled' | 'superseded_or_rescheduled' | 'optional'
export type PlannedComparisonState = 'above_planned' | 'near_planned' | 'below_planned' | 'unavailable'
export interface PlannedVsCompleted { planned: number | null; completed: number | null; absolute_difference: number | null; ratio: number | null; state: PlannedComparisonState }
export interface WorkoutLoadWeek { week_start_local_date: string; timezone: string; planned_session_load_total: number; completed_session_load_total: number; difference: number; ratio: number | null; completed_count: number; partial_count: number; skipped_count: number; missed_count: number; resistance_volume_kg: string | null; unavailable_planned_load_count: number; unavailable_completed_load_count: number }
export interface WorkoutLoadResponse { start_date: string; end_date: string; timezone: string; weeks: WorkoutLoadWeek[]; planned_vs_completed: PlannedVsCompleted }
export interface WorkoutCompletion { eligible_required_count: number; completed_count: number; partial_count: number; ordinary_skipped_count: number; safety_skipped_count: number; missed_count: number; pending_count: number; coach_cancelled_count: number; superseded_or_rescheduled_count: number; optional_count: number; completion_adherence_percentage: number | null }
export interface PrescribedSetAdherence { planned_working_sets: number; completed_planned_working_sets: number; percentage: number | null }
export interface ExerciseAdherence { planned_exercises: number; completed_exercises: number; percentage: number | null }
export interface WorkoutAdherenceResponse { start_date: string; end_date: string; completion: WorkoutCompletion; prescribed_set_adherence: PrescribedSetAdherence; exercise_adherence: ExerciseAdherence }
export interface RecordedBestEntry { value: number; source_date: string; scheduled_workout_id: string; workout_session_id: string; set_number: number; exercise_version_id: string; canonical_kg?: string; original_value?: string | null; original_unit?: string | null; repetitions?: number }
export interface RecordedBestExercise { exercise_id: string; exercise_name: string; tracking_mode: ExerciseTrackingMode; highest_recorded_load: RecordedBestEntry | null; highest_recorded_repetitions: RecordedBestEntry | null; highest_recorded_volume: RecordedBestEntry | null }
export interface RecordedBestsResponse { scope: 'all_available_history'; exercises: RecordedBestExercise[] }
export interface CoachSessionSummary { workout_session_id: string | null; scheduled_workout_id: string; scheduled_date: string; workout_name: string | null; program_name: string | null; program_version_number: number | null; status: WorkoutSessionStatus; classification: WorkoutClassification; started_at: string; completed_at: string | null; ended_at: string | null; actual_duration_minutes: number | null; session_rpe: string | null; planned_session_load: number | null; completed_session_load: number | null; session_volume_kg: string | null; open_safety_report_count: number; skip_kind?: WorkoutSkipKind | null; skip_reason?: string | null; skip_note?: string | null; skipped_at?: string | null }
export interface CoachSessionList { start_date: string; end_date: string; sessions: CoachSessionSummary[] }
export interface WorkoutLoadSummaryOut { id: string | null; workout_session_id: string; calculation_version: string; planned_session_load: number | null; completed_session_load: number | null; session_volume_kg: string | null; completed_repetitions: number; completed_working_sets: number; completed_prescribed_sets: number; skipped_prescribed_sets: number; completed_added_sets: number; completed_exercises: number; total_duration_seconds: number | null; total_distance_meters: string | null; calculation_payload: Record<string, unknown>; calculated_at: string | null; persisted: boolean }
export interface CoachSessionDetail extends WorkoutSession { trainee_id: string; trainee_name: string | null; training_assignment_id: string | null; program_version_id: string | null; template_version_id: string; template_version_number: number | null; classification: WorkoutClassification; load_summary: WorkoutLoadSummaryOut; planned_vs_completed: PlannedVsCompleted; safety_reports: CoachWorkoutSafetyReport[]; read_only: boolean }
