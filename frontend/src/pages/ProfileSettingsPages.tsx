import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { api } from '../api'
import { AVATAR_ACCEPT_ATTR, removeAvatar, setAvatar, validateAvatarFile } from '../avatar'
import { useAccountQueryScope, useAuth } from '../auth'
import { AppShell } from '../components/AppShell'
import { Avatar } from '../components/Avatar'
import { Badge, Button, Card, Field, LoadingState, PageHeader, SelectInput, StatusNotice, TextArea, TextInput } from '../components/ui'
import { UserPreferences, UserProfile } from '../types'

function splitSpecialties(value: string): string[] {
  const seen: string[] = []
  for (const raw of value.split(',')) {
    const label = raw.trim()
    if (label && !seen.includes(label)) seen.push(label)
  }
  return seen
}

const TIMEZONES = ['UTC', 'America/Los_Angeles', 'America/New_York', 'America/Sao_Paulo', 'Europe/London', 'Europe/Berlin', 'Africa/Johannesburg', 'Asia/Kolkata', 'Asia/Singapore', 'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland']
const LOCALES = [['en', 'English'], ['en-US', 'English (United States)'], ['en-GB', 'English (United Kingdom)']]

const profileSchema = z.object({
  preferred_display_name: z.string().max(120, 'Keep the display name under 120 characters'),
  bio: z.string().max(1000, 'Keep your bio under 1000 characters'),
  headline: z.string().max(160, 'Keep your headline under 160 characters'),
  coaching_specialties: z.string().max(400, 'Keep your specialties list shorter'),
  years_of_experience: z.string().refine(
    value => value === '' || (/^\d{1,3}$/.test(value) && Number(value) <= 80),
    'Enter a whole number of years from 0 to 80',
  ),
  certifications_text: z.string().max(1000, 'Keep certifications under 1000 characters'),
  training_goals: z.string().max(1000, 'Keep your goals under 1000 characters'),
})
type ProfileForm = z.infer<typeof profileSchema>

const EMPTY_PROFILE_FORM: ProfileForm = {
  preferred_display_name: '', bio: '', headline: '', coaching_specialties: '',
  years_of_experience: '', certifications_text: '', training_goals: '',
}

/** Avatar upload / replace / remove with a client-side preview. */
function AvatarField({ profile, name, demo }: { profile: UserProfile; name: string; demo: boolean }) {
  const scope = useAccountQueryScope(); const queryClient = useQueryClient()
  const inputRef = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileError, setFileError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  async function refresh() {
    // The avatar URL is stable across replacements, so the cached blob must be
    // invalidated explicitly for the new photo to appear.
    await queryClient.invalidateQueries({ queryKey: [...scope, 'me-profile'] })
    await queryClient.invalidateQueries({ queryKey: [...scope, 'avatar-blob'] })
  }

  function choose(file: File | undefined) {
    if (!file) return
    const problem = validateAvatarFile(file)
    if (problem) { setFileError(problem); return }
    setFileError(''); setNotice('')
    if (preview) URL.revokeObjectURL(preview)
    setSelected(file); setPreview(URL.createObjectURL(file))
  }

  function clearSelection() {
    if (preview) URL.revokeObjectURL(preview)
    setSelected(null); setPreview(null); setFileError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const upload = useMutation({
    mutationFn: () => setAvatar(selected as File),
    onSuccess: async () => { clearSelection(); setNotice('Your photo was updated.'); await refresh() },
    onError: (error: Error) => setFileError(error.message),
  })
  const remove = useMutation({
    mutationFn: () => removeAvatar(),
    onSuccess: async () => { clearSelection(); setNotice('Your photo was removed.'); await refresh() },
    onError: (error: Error) => setFileError(error.message),
  })

  const hasPhoto = Boolean(profile.avatar)
  const busy = upload.isPending || remove.isPending

  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Profile photo</h2>
        <p className="mt-1 text-sm text-secondary">A JPEG, PNG, WEBP, or GIF up to 5&nbsp;MB. Your assigned coach or trainees can see it.</p>
      </div>
      {notice && <StatusNotice tone="positive" title="Photo updated">{notice}</StatusNotice>}
      {fileError && <StatusNotice tone="risk" title="We could not update your photo">{fileError}</StatusNotice>}
      <div className="flex flex-wrap items-center gap-4">
        {preview
          ? <img src={preview} alt="" className="size-24 shrink-0 rounded-full object-cover" data-testid="avatar-preview" />
          : <Avatar name={name} src={profile.avatar?.content_url} size="xl" />}
        <div className="flex flex-wrap gap-2">
          <input ref={inputRef} type="file" accept={AVATAR_ACCEPT_ATTR} className="sr-only" aria-label="Choose a profile photo" disabled={demo || busy} onChange={event => choose(event.target.files?.[0])} />
          {selected
            ? <>
                <Button type="button" onClick={() => upload.mutate()} loading={upload.isPending} disabled={demo}>Upload photo</Button>
                <Button type="button" variant="ghost" onClick={clearSelection} disabled={busy}>Cancel</Button>
              </>
            : <>
                <Button type="button" variant="secondary" onClick={() => inputRef.current?.click()} disabled={demo || busy}>{hasPhoto ? 'Replace photo' : 'Add photo'}</Button>
                {hasPhoto && <Button type="button" variant="ghost" onClick={() => remove.mutate()} loading={remove.isPending} disabled={demo}>Remove</Button>}
              </>}
        </div>
      </div>
    </Card>
  )
}

export function ProfilePage() {
  const { user } = useAuth(); const demo = Boolean(user?.is_demo)
  const isCoach = user?.role === 'coach'
  const fallbackName = user ? `${user.first_name} ${user.last_name}` : ''
  const scope = useAccountQueryScope(); const queryClient = useQueryClient()
  const [message, setMessage] = useState(''); const [apiError, setApiError] = useState('')
  const query = useQuery({ queryKey: [...scope, 'me-profile'], queryFn: () => api<UserProfile>('/me/profile') })
  const form = useForm<ProfileForm>({ resolver: zodResolver(profileSchema), defaultValues: EMPTY_PROFILE_FORM, mode: 'onBlur' })
  const { register, reset, watch, handleSubmit, formState: { errors } } = form
  useEffect(() => {
    if (!query.data) return
    reset({
      preferred_display_name: query.data.preferred_display_name ?? '',
      bio: query.data.bio ?? '',
      headline: query.data.headline ?? '',
      coaching_specialties: (query.data.coaching_specialties ?? []).join(', '),
      years_of_experience: query.data.years_of_experience != null ? String(query.data.years_of_experience) : '',
      certifications_text: query.data.certifications_text ?? '',
      training_goals: query.data.training_goals ?? '',
    })
  }, [query.data, reset])

  const mutation = useMutation({
    mutationFn: (data: ProfileForm) => {
      const payload: Record<string, unknown> = {
        preferred_display_name: data.preferred_display_name,
        bio: data.bio,
      }
      if (isCoach) {
        payload.headline = data.headline
        payload.coaching_specialties = splitSpecialties(data.coaching_specialties)
        payload.years_of_experience = data.years_of_experience === '' ? null : Number(data.years_of_experience)
        payload.certifications_text = data.certifications_text
      } else {
        payload.training_goals = data.training_goals
      }
      return api<UserProfile>('/me/profile', { method: 'PUT', body: JSON.stringify(payload) })
    },
    onSuccess: async (data) => { setApiError(''); setMessage('Your profile was saved.'); queryClient.setQueryData([...scope, 'me-profile'], data); await queryClient.invalidateQueries({ queryKey: [...scope, 'me-profile'] }) },
    onError: (error: Error) => setApiError(error.message),
  })

  if (query.isLoading) return <AppShell><LoadingState label="Loading your profile" /></AppShell>
  if (query.isError || !query.data) return <AppShell><div className="mx-auto max-w-2xl"><StatusNotice tone="risk" title="We could not load your profile">Refresh the page to try again.</StatusNotice></div></AppShell>

  const specialtyPreview = splitSpecialties(watch('coaching_specialties'))

  return <AppShell>
    <div className="mx-auto max-w-2xl space-y-6">
      <PageHeader eyebrow="Account" title="Your profile" description={isCoach ? 'Your professional profile, shown to the trainees you coach. Self-declared and never verified.' : 'Shared identity used across FitIntel 360. Self-declared and never verified.'} />
      {demo && <StatusNotice tone="info" title="Demo workspace">This is a read-only demo. Profile editing is disabled.</StatusNotice>}
      <AvatarField profile={query.data} name={query.data.preferred_display_name || fallbackName} demo={demo} />
      <form onSubmit={handleSubmit(data => mutation.mutate(data))} className="space-y-6">
        {message && <StatusNotice tone="positive" title="Profile saved">{message}</StatusNotice>}
        {apiError && <StatusNotice tone="risk" title="We could not save your profile">{apiError} Your entries remain on this page; try again.</StatusNotice>}
        <Card className="space-y-5">
          <Field id="preferred_display_name" label="Preferred display name" optional help="How you would like to be shown. Defaults to your account name when empty." error={errors.preferred_display_name?.message}>{({ id, describedBy, invalid }) => <TextInput id={id} maxLength={120} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('preferred_display_name')} />}</Field>
          {isCoach && <Field id="headline" label="Headline" optional help="A short professional tagline, e.g. “Strength & conditioning coach”." error={errors.headline?.message}>{({ id, describedBy, invalid }) => <TextInput id={id} maxLength={160} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('headline')} />}</Field>}
          <Field id="bio" label={isCoach ? 'Coaching philosophy' : 'Bio'} optional help={isCoach ? 'How you coach and who you work best with. Avoid sensitive personal or health details.' : 'A short description. Avoid sensitive personal or health details.'} error={errors.bio?.message}>{({ id, describedBy, invalid }) => <TextArea id={id} rows={5} maxLength={1000} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('bio')} />}</Field>
        </Card>
        {isCoach && <Card className="space-y-5">
          <h2 className="text-lg font-semibold">Professional details</h2>
          <Field id="coaching_specialties" label="Specialties" optional help="Comma-separated, e.g. “Powerlifting, Mobility, Fat loss”." error={errors.coaching_specialties?.message}>{({ id, describedBy, invalid }) => <TextInput id={id} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('coaching_specialties')} />}</Field>
          {specialtyPreview.length > 0 && <div className="flex flex-wrap gap-2" data-testid="specialty-preview">{specialtyPreview.map(item => <Badge key={item} tone="info">{item}</Badge>)}</div>}
          <Field id="years_of_experience" label="Years of experience" optional help="A whole number of years." error={errors.years_of_experience?.message}>{({ id, describedBy, invalid }) => <TextInput id={id} inputMode="numeric" disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('years_of_experience')} />}</Field>
          <Field id="certifications_text" label="Certifications" optional help="Plain text only. List certifications as you would like them shown; they are not verified." error={errors.certifications_text?.message}>{({ id, describedBy, invalid }) => <TextArea id={id} rows={3} maxLength={1000} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('certifications_text')} />}</Field>
        </Card>}
        {!isCoach && <Card className="space-y-5">
          <h2 className="text-lg font-semibold">Training goals</h2>
          <Field id="training_goals" label="What are you working toward?" optional help="Your goals help your coach tailor your program. Avoid sensitive health details." error={errors.training_goals?.message}>{({ id, describedBy, invalid }) => <TextArea id={id} rows={4} maxLength={1000} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('training_goals')} />}</Field>
        </Card>}
        <div className="flex justify-end"><Button type="submit" loading={mutation.isPending} disabled={demo} className="sm:min-w-44">Save profile</Button></div>
      </form>
    </div>
  </AppShell>
}

const preferencesSchema = z.object({
  timezone: z.string().min(1, 'Select a timezone'),
  weight_unit: z.enum(['kg', 'lb']),
  distance_unit: z.enum(['meters', 'kilometers', 'miles']),
  locale: z.string().min(1, 'Select a locale'),
})
type PreferencesForm = z.infer<typeof preferencesSchema>

export function SettingsPage() {
  const { user } = useAuth(); const demo = Boolean(user?.is_demo)
  const scope = useAccountQueryScope(); const queryClient = useQueryClient()
  const [message, setMessage] = useState(''); const [apiError, setApiError] = useState('')
  const query = useQuery({ queryKey: [...scope, 'me-preferences'], queryFn: () => api<UserPreferences>('/me/preferences') })
  const form = useForm<PreferencesForm>({ resolver: zodResolver(preferencesSchema), defaultValues: { timezone: 'UTC', weight_unit: 'kg', distance_unit: 'kilometers', locale: 'en' }, mode: 'onBlur' })
  const { register, reset, handleSubmit, formState: { errors } } = form
  useEffect(() => { if (query.data) reset({ timezone: query.data.timezone, weight_unit: query.data.weight_unit, distance_unit: query.data.distance_unit, locale: query.data.locale }) }, [query.data, reset])
  const mutation = useMutation({ mutationFn: (data: PreferencesForm) => api<UserPreferences>('/me/preferences', { method: 'PUT', body: JSON.stringify(data) }), onSuccess: async (data) => { setApiError(''); setMessage('Your settings were saved.'); queryClient.setQueryData([...scope, 'me-preferences'], data); await queryClient.invalidateQueries({ queryKey: [...scope, 'me-preferences'] }) }, onError: (error) => setApiError(error.message) })
  const timezoneOptions = query.data && !TIMEZONES.includes(query.data.timezone) ? [query.data.timezone, ...TIMEZONES] : TIMEZONES
  if (query.isLoading) return <AppShell><LoadingState label="Loading your settings" /></AppShell>
  return <AppShell><form onSubmit={handleSubmit(data => mutation.mutate(data))} className="mx-auto max-w-2xl space-y-6"><PageHeader eyebrow="Account" title="Settings" description="Display preferences applied across FitIntel 360. These change presentation only and never alter your recorded data." />{message && <StatusNotice tone="positive" title="Settings saved">{message}</StatusNotice>}{apiError && <StatusNotice tone="risk" title="We could not save your settings">{apiError} Your entries remain on this page; try again.</StatusNotice>}<Card className="space-y-5"><h2 className="text-lg font-semibold">Regional and units</h2><Field id="timezone" label="Timezone" help="Used for your local dates. Changing it does not reinterpret past records." error={errors.timezone?.message}>{({ id, describedBy, invalid }) => <SelectInput id={id} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('timezone')}>{timezoneOptions.map(zone => <option key={zone} value={zone}>{zone}</option>)}</SelectInput>}</Field><div className="grid gap-5 sm:grid-cols-2"><Field id="weight_unit" label="Weight unit" error={errors.weight_unit?.message}>{({ id, describedBy, invalid }) => <SelectInput id={id} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('weight_unit')}><option value="kg">Kilograms (kg)</option><option value="lb">Pounds (lb)</option></SelectInput>}</Field><Field id="distance_unit" label="Distance unit" error={errors.distance_unit?.message}>{({ id, describedBy, invalid }) => <SelectInput id={id} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('distance_unit')}><option value="kilometers">Kilometers</option><option value="miles">Miles</option><option value="meters">Meters</option></SelectInput>}</Field></div><Field id="locale" label="Language and formatting" help="Affects display formatting only." error={errors.locale?.message}>{({ id, describedBy, invalid }) => <SelectInput id={id} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('locale')}>{LOCALES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</SelectInput>}</Field></Card><Card className="space-y-3"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Theme</h2><span className="rounded-full bg-elevated px-2.5 py-1 text-xs font-semibold text-muted">Coming soon</span></div><p className="text-sm text-secondary">Appearance controls will arrive in a later update. Your current view follows the system theme.</p></Card><Card className="space-y-3"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Privacy</h2><span className="rounded-full bg-elevated px-2.5 py-1 text-xs font-semibold text-muted">Coming soon</span></div><p className="text-sm text-secondary">Granular privacy controls are planned. Your data is already scoped to your account and your assigned coach relationship.</p></Card><Card className="space-y-3"><div className="flex items-center justify-between"><h2 className="text-lg font-semibold">Accessibility</h2><span className="rounded-full bg-elevated px-2.5 py-1 text-xs font-semibold text-muted">Coming soon</span></div><p className="text-sm text-secondary">Additional accessibility preferences are planned. The interface already supports keyboard navigation and screen readers.</p></Card><div className="flex justify-end"><Button type="submit" loading={mutation.isPending} disabled={demo} className="sm:min-w-44">Save settings</Button></div></form></AppShell>
}
