import { zodResolver } from '@hookform/resolvers/zod'
import {
  Activity,
  Apple,
  BedDouble,
  Brain,
  Check,
  ChevronLeft,
  ChevronRight,
  ClipboardCheck,
  Droplets,
  Dumbbell,
  HeartPulse,
  Info,
  Ruler,
  Save,
  Sparkles,
  Target,
} from 'lucide-react'
import { ReactNode, useEffect, useRef, useState } from 'react'
import { FieldErrors, useForm, useWatch } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { api, ApiError } from '../api'
import { AppShell } from '../components/AppShell'
import {
  Button,
  Card,
  Chip,
  ChoiceCard,
  Field,
  LoadingState,
  PageHeader,
  ProgressBar,
  SegmentedControl,
  StatusNotice,
  TextInput,
} from '../components/ui'
import { formatDateTime, titleize } from '../lib/format'
import { Assessment, AssessmentData, HealthIndex } from '../types'

const number = (min: number, max: number) => z.preprocess(
  value => value === '' || Number.isNaN(value) ? undefined : value,
  z.number().min(min, `Must be at least ${min}`).max(max, `Must be ${max} or less`).optional(),
)
const schema = z.object({
  age: number(16, 100), height_cm: number(100, 250), weight_kg: number(30, 350), selected_goal: z.string().optional(), target_weight_kg: number(30, 350), hydration_ml: number(0, 10000),
  sleep_hours: number(0, 16), sleep_quality: number(1, 5), wake_refreshed: z.boolean().optional(), daily_steps: number(0, 100000), activity_types: z.array(z.string()), activity_minutes_weekly: number(0, 5000),
  workout_frequency_weekly: number(0, 14), average_rpe: number(0, 10), workout_duration_minutes: number(0, 600), perceived_recovery: number(1, 5), stress_level: number(0, 10), resting_heart_rate: number(30, 220),
  palpitations: z.boolean(), shortness_of_breath: z.boolean(), chest_pain: z.boolean(), calorie_mode: z.string().optional(), calorie_target: number(800, 8000), calorie_intake: number(0, 10000), protein_target_g: number(0, 500), protein_intake_g: number(0, 500), carbohydrate_intake_g: number(0, 1500), healthy_fat_intake_g: number(0, 500), fruit_servings: number(0, 30), vegetable_servings: number(0, 30), fiber_g: number(0, 150), meal_consistency: number(1, 5),
})

const defaults: AssessmentData = { activity_types: [], palpitations: false, shortness_of_breath: false, chest_pain: false }
const goals = [
  ['fat_loss', 'Fat loss', 'Build sustainable habits that support gradual fat loss.'],
  ['muscle_gain', 'Muscle gain', 'Support training adaptation and muscle development.'],
  ['strength', 'Strength', 'Prioritize progressive strength and recovery.'],
  ['endurance', 'Endurance', 'Build capacity for sustained aerobic performance.'],
  ['general_health', 'General health', 'Improve everyday health, energy, and consistency.'],
  ['athletic_performance', 'Athletic performance', 'Support sport-specific performance demands.'],
] as const
const activityOptions = ['walking', 'running', 'swimming', 'cycling', 'hiit', 'strength_training', 'functional_training', 'pilates', 'yoga', 'sports', 'gardening', 'housework', 'stair_climbing', 'active_commuting']
const stepMeta = [
  { title: 'Welcome', short: 'Welcome', icon: Sparkles, fields: [] as (keyof AssessmentData)[] },
  { title: 'Choose your fitness goal', short: 'Goal', icon: Target, fields: ['selected_goal'] as (keyof AssessmentData)[] },
  { title: 'Build your basic profile', short: 'Profile', icon: Ruler, fields: ['age', 'height_cm', 'weight_kg'] as (keyof AssessmentData)[] },
  { title: 'Understand your hydration', short: 'Hydration', icon: Droplets, fields: ['hydration_ml'] as (keyof AssessmentData)[] },
  { title: 'Tell us about your sleep', short: 'Sleep', icon: BedDouble, fields: ['sleep_hours', 'sleep_quality', 'wake_refreshed'] as (keyof AssessmentData)[] },
  { title: 'Describe your daily movement', short: 'Movement', icon: Activity, fields: ['daily_steps', 'activity_minutes_weekly'] as (keyof AssessmentData)[] },
  { title: 'Describe your training habits', short: 'Training', icon: Dumbbell, fields: ['workout_frequency_weekly', 'average_rpe'] as (keyof AssessmentData)[] },
  { title: 'Check in on stress', short: 'Stress', icon: Brain, fields: ['stress_level'] as (keyof AssessmentData)[] },
  { title: 'Cardiovascular information', short: 'Cardio', icon: HeartPulse, fields: [] as (keyof AssessmentData)[] },
  { title: 'Nutrition baseline', short: 'Nutrition', icon: Apple, fields: ['calorie_mode'] as (keyof AssessmentData)[] },
  { title: 'Review your assessment', short: 'Review', icon: ClipboardCheck, fields: [] as (keyof AssessmentData)[] },
]

function NumericField({ name, label, unit, min, max, optional = false, help, register, errors }: { name: keyof AssessmentData; label: string; unit?: string; min: number; max: number; optional?: boolean; help?: string; register: ReturnType<typeof useForm<AssessmentData>>['register']; errors: FieldErrors<AssessmentData> }) {
  const error = errors[name]?.message as string | undefined
  return <Field label={label} optional={optional} help={help} error={error} id={name}>{({ id, describedBy, invalid }) => <div className="relative"><TextInput id={id} type="number" inputMode="decimal" step="any" min={min} max={max} {...register(name, { valueAsNumber: true })} aria-describedby={describedBy} aria-invalid={invalid} className={unit ? 'pr-20' : ''} />{unit && <span className="pointer-events-none absolute bottom-3 right-3.5 text-sm font-medium text-muted">{unit}</span>}</div>}</Field>
}

function StepIntro({ children }: { children: ReactNode }) { return <p className="mb-7 max-w-2xl text-sm leading-6 text-secondary">{children}</p> }

function ReviewGrid({ data }: { data: AssessmentData }) {
  const sections = [
    ['Goal and profile', ['selected_goal', 'age', 'height_cm', 'weight_kg', 'target_weight_kg']],
    ['Daily baseline', ['hydration_ml', 'sleep_hours', 'sleep_quality', 'wake_refreshed', 'daily_steps', 'activity_minutes_weekly']],
    ['Training and stress', ['workout_frequency_weekly', 'average_rpe', 'workout_duration_minutes', 'perceived_recovery', 'stress_level']],
    ['Cardiovascular and nutrition', ['resting_heart_rate', 'palpitations', 'shortness_of_breath', 'chest_pain', 'calorie_mode', 'calorie_target', 'calorie_intake', 'protein_target_g', 'protein_intake_g', 'fruit_servings', 'vegetable_servings', 'fiber_g', 'meal_consistency']],
  ] as const
  return <div className="grid gap-4 md:grid-cols-2">{sections.map(([title, keys]) => <section key={title} className="rounded-xl border bg-elevated p-4"><h3 className="font-semibold">{title}</h3><dl className="mt-3 divide-y">{keys.filter(key => data[key] !== undefined).map(key => { const value = data[key]; return <div key={key} className="flex items-start justify-between gap-4 py-2.5 text-sm"><dt className="text-muted">{titleize(key)}</dt><dd className="max-w-[55%] text-right font-medium">{Array.isArray(value) ? value.map(titleize).join(', ') : typeof value === 'boolean' ? (value ? 'Yes' : 'No') : titleize(String(value))}</dd></div> })}</dl></section>)}</div>
}

function SubmittedReview({ assessment }: { assessment: Assessment }) {
  return <AppShell><div className="mx-auto max-w-4xl space-y-6"><PageHeader eyebrow="Assessment" title="Your submitted baseline" description={`Submitted ${assessment.submitted_at ? formatDateTime(assessment.submitted_at) : 'recently'}. These are the responses used for your current Health Index.`} action={<Link to="/trainee/dashboard" className="inline-flex min-h-11 items-center rounded-xl bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover">View Health Index</Link>} /><StatusNotice tone="info" title="Baseline locked">Submitted responses are preserved for auditability. Starting a new assessment version is intentionally deferred.</StatusNotice><Card><ReviewGrid data={assessment.responses} /></Card></div></AppShell>
}

export function OnboardingPage() {
  const [step, setStep] = useState(0); const [loading, setLoading] = useState(true); const [existing, setExisting] = useState<Assessment | null>(null)
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle'); const [saveMessage, setSaveMessage] = useState(''); const [lastSaved, setLastSaved] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false); const [acknowledged, setAcknowledged] = useState(false); const [errorSummary, setErrorSummary] = useState('')
  const headingRef = useRef<HTMLHeadingElement>(null); const errorRef = useRef<HTMLDivElement>(null)
  const form = useForm<AssessmentData>({ resolver: zodResolver(schema), defaultValues: defaults, mode: 'onBlur' })
  const { register, reset, control, setValue, getValues, trigger, setError, formState: { errors } } = form
  const values = useWatch({ control }) as AssessmentData

  useEffect(() => {
    api<Assessment>('/assessments/onboarding').then(assessment => {
      setExisting(assessment); reset({ ...defaults, ...assessment.responses }); setLastSaved(assessment.updated_at)
      if (assessment.status === 'draft') {
        const firstIncomplete = stepMeta.findIndex(item => item.fields.some(field => {
          const value = assessment.responses[field]
          return value === undefined || value === null || value === ''
        }))
        setStep(firstIncomplete > 0 ? firstIncomplete : 0)
      }
    }).catch(caught => {
      if (!(caught instanceof ApiError && caught.status === 404)) { setSaveState('error'); setSaveMessage(caught instanceof Error ? caught.message : 'We could not load your assessment.') }
    }).finally(() => setLoading(false))
  }, [reset])

  useEffect(() => { if (!loading) headingRef.current?.focus() }, [loading, step])
  useEffect(() => { if (errorSummary) errorRef.current?.focus() }, [errorSummary])

  async function saveDraft(): Promise<Assessment> {
    setSaveState('saving'); setSaveMessage('Saving your progress…')
    try {
      const data = schema.parse(getValues()) as AssessmentData
      const assessment = await api<Assessment>('/assessments/onboarding', { method: 'PUT', body: JSON.stringify({ responses: data }) })
      setExisting(assessment); setLastSaved(assessment.updated_at); setSaveState('saved'); setSaveMessage('Your progress was saved.')
      return assessment
    } catch (caught) {
      const message = caught instanceof z.ZodError ? 'Correct the highlighted value before saving.' : caught instanceof Error ? caught.message : 'We could not save this step. Your entries remain on this page; try again.'
      setSaveState('error'); setSaveMessage(message); throw caught
    }
  }

  async function validateCurrentStep(): Promise<boolean> {
    setErrorSummary('')
    const fields = stepMeta[step].fields
    const validRanges = fields.length ? await trigger(fields) : true
    const missing = fields.filter(field => getValues(field) === undefined || getValues(field) === '')
    missing.forEach(field => setError(field, { type: 'required', message: 'This field is required' }))
    if (!validRanges || missing.length) {
      setErrorSummary(`Check ${missing.length || 1} required ${missing.length === 1 ? 'field' : 'fields'} before continuing.`)
      return false
    }
    return true
  }

  async function continueStep() {
    if (!(await validateCurrentStep())) return
    try { await saveDraft(); setStep(current => Math.min(current + 1, stepMeta.length - 1)) } catch { /* save state contains retained-data guidance */ }
  }

  async function submitBaseline() {
    setErrorSummary('')
    const allRequired = stepMeta.flatMap(item => item.fields)
    const valid = await trigger(allRequired)
    const missing = allRequired.filter(field => getValues(field) === undefined || getValues(field) === '')
    missing.forEach(field => setError(field, { type: 'required', message: 'This field is required' }))
    if (!valid || missing.length) { setErrorSummary(`Your assessment still has ${missing.length || 'some'} required fields to complete. Use Back to review them.`); return }
    if (!acknowledged) { setErrorSummary('Confirm that your answers are accurate before calculating your baseline.'); return }
    setSubmitting(true)
    try { await saveDraft(); await api<HealthIndex>('/assessments/onboarding/submit', { method: 'POST' }); window.location.assign('/trainee/dashboard?baseline=created') }
    catch (caught) { setErrorSummary(caught instanceof Error ? caught.message : 'We could not calculate your baseline. Your saved assessment is still available; try again.') }
    finally { setSubmitting(false) }
  }

  if (loading) return <AppShell><LoadingState label="Loading your assessment" /></AppShell>
  if (existing?.status === 'submitted') return <SubmittedReview assessment={existing} />
  const current = stepMeta[step]; const CurrentIcon = current.icon

  return <AppShell><div className="mx-auto max-w-6xl"><PageHeader eyebrow="Onboarding assessment" title="Build your fitness baseline" description="One focused section at a time. Your answers create an explainable coaching baseline—not a medical diagnosis." /><div className="mt-7 grid items-start gap-6 lg:grid-cols-[14rem_minmax(0,1fr)]"><aside className="hidden lg:block"><ol aria-label="Assessment steps" className="space-y-1">{stepMeta.map((item, index) => { const Icon = item.icon; const active = index === step; const complete = index < step; return <li key={item.short}><button type="button" onClick={() => index <= step && setStep(index)} disabled={index > step} aria-current={active ? 'step' : undefined} className={`flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-left text-sm font-semibold ${active ? 'bg-primary/8 text-primary' : complete ? 'text-secondary hover:bg-elevated' : 'cursor-default text-disabled'}`}><span className={`grid size-7 shrink-0 place-items-center rounded-lg ${active ? 'bg-primary text-white' : complete ? 'bg-[rgb(var(--status-positive-bg))] text-positive' : 'bg-elevated'}`}>{complete ? <Check aria-hidden="true" className="size-4" /> : <Icon aria-hidden="true" className="size-4" />}</span>{item.short}</button></li> })}</ol></aside><div className="min-w-0"><div className="mb-4 lg:hidden"><div className="flex items-center justify-between text-xs font-semibold text-secondary"><span>Step {step + 1} of {stepMeta.length}</span><span>{Math.round((step + 1) / stepMeta.length * 100)}%</span></div><ProgressBar value={(step + 1) / stepMeta.length * 100} label={`Assessment progress: step ${step + 1} of ${stepMeta.length}`} className="mt-2" /></div><Card className="overflow-hidden"><div className="flex items-start gap-3 border-b pb-5"><span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><CurrentIcon aria-hidden="true" className="size-5" /></span><div><p className="text-xs font-semibold text-muted lg:hidden">Step {step + 1} of {stepMeta.length}</p><h2 ref={headingRef} tabIndex={-1} className="text-2xl font-semibold leading-tight">{current.title}</h2></div></div>{errorSummary && <div ref={errorRef} tabIndex={-1} role="alert" className="mt-5"><StatusNotice tone="risk" title="Check this section">{errorSummary}</StatusNotice></div>}<div className="py-7">{step === 0 && <WelcomeStep />}{step === 1 && <GoalStep value={values.selected_goal} onChange={value => setValue('selected_goal', value, { shouldDirty: true, shouldValidate: true })} error={errors.selected_goal?.message} />}{step === 2 && <ProfileStep register={register} errors={errors} />}{step === 3 && <HydrationStep register={register} errors={errors} />}{step === 4 && <SleepStep values={values} register={register} errors={errors} setValue={setValue} />}{step === 5 && <MovementStep values={values} register={register} errors={errors} setValue={setValue} />}{step === 6 && <TrainingStep register={register} errors={errors} />}{step === 7 && <StressStep register={register} errors={errors} />}{step === 8 && <CardioStep register={register} errors={errors} />}{step === 9 && <NutritionStep values={values} register={register} errors={errors} setValue={setValue} />}{step === 10 && <div><StepIntro>Check each section before calculation. You can use Back to change any answer.</StepIntro><ReviewGrid data={values} /><label className="mt-6 flex cursor-pointer items-start gap-3 rounded-xl border bg-elevated p-4"><input type="checkbox" checked={acknowledged} onChange={event => setAcknowledged(event.target.checked)} className="mt-0.5 size-5 rounded border-border text-primary focus:ring-focus" /><span className="text-sm leading-6"><span className="font-semibold">I confirm these answers are accurate to the best of my knowledge.</span><span className="mt-1 block text-muted">I understand the resulting score supports coaching decisions and is not a diagnosis.</span></span></label></div>}</div><div className="border-t pt-5"><div aria-live="polite" className={`mb-4 flex min-h-6 items-center gap-2 text-xs ${saveState === 'error' ? 'text-critical' : saveState === 'saved' ? 'text-positive' : 'text-muted'}`}>{saveState === 'saving' && <span className="size-3.5 animate-spin rounded-full border-2 border-primary border-t-transparent" aria-hidden="true" />}{saveState === 'saved' && <Check aria-hidden="true" className="size-4" />}{saveState === 'error' && <Info aria-hidden="true" className="size-4" />}<span>{saveMessage || (lastSaved ? `Last saved ${formatDateTime(lastSaved)}` : 'Your first Continue will save a draft.')}</span></div><div className="flex flex-col-reverse gap-3 sm:flex-row sm:items-center sm:justify-between"><Button variant="ghost" disabled={step === 0 || submitting} onClick={() => setStep(currentStep => Math.max(0, currentStep - 1))}><ChevronLeft aria-hidden="true" className="size-4" />Back</Button><div className="flex flex-col gap-3 sm:flex-row"><Button variant="secondary" disabled={submitting || saveState === 'saving'} onClick={() => saveDraft().catch(() => undefined)}><Save aria-hidden="true" className="size-4" />Save progress</Button>{step < stepMeta.length - 1 ? <Button onClick={continueStep} loading={saveState === 'saving'}>Save and continue<ChevronRight aria-hidden="true" className="size-4" /></Button> : <Button onClick={submitBaseline} loading={submitting}>Calculate my baseline</Button>}</div></div></div></Card></div></div></div></AppShell>
}

function WelcomeStep() { return <div><StepIntro>This assessment establishes a transparent baseline across sleep, hydration, movement, training, stress, cardiovascular information, and nutrition.</StepIntro><div className="grid gap-3 sm:grid-cols-3">{[['About 8 minutes', 'Complete at your own pace.'], ['Metric units', 'Use kilograms, centimetres, and millilitres.'], ['Explainable result', 'Every score contribution remains visible.']].map(([title, description]) => <div key={title} className="rounded-xl border bg-elevated p-4"><p className="font-semibold">{title}</p><p className="mt-1 text-sm leading-5 text-muted">{description}</p></div>)}</div><StatusNotice tone="info" title="Your information is sensitive" className="mt-5">Only you and your assigned coach can access this baseline through the application. Avoid continuing on a shared device.</StatusNotice></div> }

function GoalStep({ value, onChange, error }: { value?: string; onChange: (value: string) => void; error?: string }) { return <div><StepIntro>Your goal adjusts configured targets such as hydration and sleep. It does not create a medical or nutrition prescription.</StepIntro><fieldset><legend className="sr-only">Primary fitness goal</legend><div className="grid gap-3 sm:grid-cols-2">{goals.map(([key, title, description]) => <ChoiceCard key={key} selected={value === key} title={title} description={description} onClick={() => onChange(key)} />)}</div>{error && <p className="mt-2 text-sm font-medium text-critical">{error}</p>}</fieldset></div> }

function ProfileStep({ register, errors }: FormProps) { return <div><StepIntro>Body measurements help calculate weight-relative targets. They are used for coaching calculations, not diagnosis.</StepIntro><div className="grid gap-5 sm:grid-cols-2"><NumericField name="age" label="Age" unit="years" min={16} max={100} register={register} errors={errors} /><NumericField name="height_cm" label="Height" unit="cm" min={100} max={250} register={register} errors={errors} /><NumericField name="weight_kg" label="Current weight" unit="kg" min={30} max={350} register={register} errors={errors} /><NumericField name="target_weight_kg" label="Target weight" unit="kg" optional min={30} max={350} register={register} errors={errors} /></div></div> }
function HydrationStep({ register, errors }: FormProps) { return <div><StepIntro>Report a typical day rather than your best day. Your target is calculated from weight and goal, and score credit is capped at 100%.</StepIntro><div className="max-w-md"><NumericField name="hydration_ml" label="Typical daily water intake" unit="ml" min={0} max={10000} register={register} errors={errors} help="Do not force excessive water intake. Individual needs vary." /></div></div> }

interface FormProps { register: ReturnType<typeof useForm<AssessmentData>>['register']; errors: FieldErrors<AssessmentData> }
interface SetValueProps extends FormProps { values: AssessmentData; setValue: ReturnType<typeof useForm<AssessmentData>>['setValue'] }

function SleepStep({ values, register, errors, setValue }: SetValueProps) { return <div><StepIntro>Sleep duration, perceived quality, and whether you wake refreshed each contribute to the sleep component.</StepIntro><div className="grid gap-5 sm:grid-cols-2"><NumericField name="sleep_hours" label="Average sleep duration" unit="hours" min={0} max={16} register={register} errors={errors} /><NumericField name="sleep_quality" label="Sleep quality" unit="1–5" min={1} max={5} register={register} errors={errors} /><div className="sm:col-span-2"><SegmentedControl label="Do you usually wake feeling refreshed?" value={values.wake_refreshed === undefined ? undefined : String(values.wake_refreshed)} options={[{ value: 'true', label: 'Yes' }, { value: 'false', label: 'No' }]} onChange={value => setValue('wake_refreshed', value === 'true', { shouldDirty: true, shouldValidate: true })} />{errors.wake_refreshed && <p className="mt-2 text-sm text-critical">{errors.wake_refreshed.message}</p>}</div></div></div> }

function MovementStep({ values, register, errors, setValue }: SetValueProps) { const selected = values.activity_types ?? []; return <div><StepIntro>Weekly minutes determine activity credit. Activity types add context but are not ranked against each other.</StepIntro><div className="grid gap-5 sm:grid-cols-2"><NumericField name="daily_steps" label="Typical daily steps" unit="steps" min={0} max={100000} register={register} errors={errors} /><NumericField name="activity_minutes_weekly" label="Activity each week" unit="minutes" min={0} max={5000} register={register} errors={errors} /></div><fieldset className="mt-6"><legend className="text-sm font-semibold">Activities you currently do <span className="font-normal text-muted">(optional)</span></legend><div className="mt-3 flex flex-wrap gap-2">{activityOptions.map(activity => <Chip key={activity} selected={selected.includes(activity)} onClick={() => setValue('activity_types', selected.includes(activity) ? selected.filter(item => item !== activity) : [...selected, activity], { shouldDirty: true })}>{titleize(activity)}</Chip>)}</div></fieldset></div> }
function TrainingStep({ register, errors }: FormProps) { return <div><StepIntro>Report your typical recent training pattern. This does not diagnose overtraining or injury risk.</StepIntro><div className="grid gap-5 sm:grid-cols-2"><NumericField name="workout_frequency_weekly" label="Workouts each week" unit="sessions" min={0} max={14} register={register} errors={errors} /><NumericField name="average_rpe" label="Average effort" unit="RPE 0–10" min={0} max={10} register={register} errors={errors} help="0 is rest; 10 is maximal perceived effort." /><NumericField name="workout_duration_minutes" label="Typical workout duration" unit="minutes" optional min={0} max={600} register={register} errors={errors} /><NumericField name="perceived_recovery" label="Perceived recovery" unit="1–5" optional min={1} max={5} register={register} errors={errors} /></div></div> }
function StressStep({ register, errors }: FormProps) { return <div><StepIntro>Use your overall current experience. A higher self-reported value reduces this component score but does not create a diagnosis.</StepIntro><div className="max-w-md"><NumericField name="stress_level" label="Current stress level" unit="0–10" min={0} max={10} register={register} errors={errors} help="0 means no reported stress; 10 means very high reported stress." /></div></div> }
function CardioStep({ register, errors }: FormProps) { return <div><StepIntro>These optional responses help identify information that may need coach or professional review. They are not used to diagnose a condition.</StepIntro><div className="max-w-md"><NumericField name="resting_heart_rate" label="Resting heart rate" unit="bpm" optional min={30} max={220} register={register} errors={errors} /></div><fieldset className="mt-6"><legend className="text-sm font-semibold">Have you recently experienced any of these?</legend><div className="mt-3 grid gap-3 sm:grid-cols-3">{([['palpitations', 'Palpitations'], ['shortness_of_breath', 'Shortness of breath'], ['chest_pain', 'Chest discomfort']] as const).map(([name, label]) => <label key={name} className="flex min-h-14 cursor-pointer items-center gap-3 rounded-xl border bg-surface p-3 text-sm font-semibold hover:bg-elevated"><input type="checkbox" {...register(name)} className="size-5 rounded border-border text-primary focus:ring-focus" />{label}</label>)}</div></fieldset><StatusNotice tone="critical" title="When to seek immediate help" className="mt-5">Seek immediate professional medical help if chest pain or breathing difficulty is severe, worsening, or happening now.</StatusNotice></div> }
function NutritionStep({ values, register, errors, setValue }: SetValueProps) { return <div><StepIntro>Only values you provide are used. The platform does not invent or medically prescribe calorie targets.</StepIntro><SegmentedControl label="Current calorie approach" value={values.calorie_mode} options={[{ value: 'maintenance', label: 'Maintenance' }, { value: 'deficit', label: 'Deficit' }, { value: 'surplus', label: 'Surplus' }]} onChange={value => setValue('calorie_mode', value, { shouldDirty: true, shouldValidate: true })} />{errors.calorie_mode && <p className="mt-2 text-sm text-critical">{errors.calorie_mode.message}</p>}<div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-3"><NumericField name="calorie_target" label="Entered calorie target" unit="kcal" optional min={800} max={8000} register={register} errors={errors} /><NumericField name="calorie_intake" label="Estimated intake" unit="kcal" optional min={0} max={10000} register={register} errors={errors} /><NumericField name="protein_target_g" label="Protein target" unit="g" optional min={0} max={500} register={register} errors={errors} /><NumericField name="protein_intake_g" label="Protein intake" unit="g" optional min={0} max={500} register={register} errors={errors} /><NumericField name="fruit_servings" label="Fruit" unit="servings" optional min={0} max={30} register={register} errors={errors} /><NumericField name="vegetable_servings" label="Vegetables" unit="servings" optional min={0} max={30} register={register} errors={errors} /><NumericField name="fiber_g" label="Fiber" unit="g" optional min={0} max={150} register={register} errors={errors} /><NumericField name="meal_consistency" label="Meal consistency" unit="1–5" optional min={1} max={5} register={register} errors={errors} /></div></div> }
