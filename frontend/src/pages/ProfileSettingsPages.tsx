import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { z } from 'zod'
import { api } from '../api'
import { useAccountQueryScope, useAuth } from '../auth'
import { AppShell } from '../components/AppShell'
import { Button, Card, Field, LoadingState, PageHeader, SelectInput, StatusNotice, TextArea, TextInput } from '../components/ui'
import { UserPreferences, UserProfile } from '../types'

const TIMEZONES = ['UTC', 'America/Los_Angeles', 'America/New_York', 'America/Sao_Paulo', 'Europe/London', 'Europe/Berlin', 'Africa/Johannesburg', 'Asia/Kolkata', 'Asia/Singapore', 'Asia/Tokyo', 'Australia/Sydney', 'Pacific/Auckland']
const LOCALES = [['en', 'English'], ['en-US', 'English (United States)'], ['en-GB', 'English (United Kingdom)']]

const profileSchema = z.object({
  preferred_display_name: z.string().max(120, 'Keep the display name under 120 characters'),
  bio: z.string().max(1000, 'Keep your bio under 1000 characters'),
})
type ProfileForm = z.infer<typeof profileSchema>

export function ProfilePage() {
  const { user } = useAuth(); const demo = Boolean(user?.is_demo)
  const scope = useAccountQueryScope(); const queryClient = useQueryClient()
  const [message, setMessage] = useState(''); const [apiError, setApiError] = useState('')
  const query = useQuery({ queryKey: [...scope, 'me-profile'], queryFn: () => api<UserProfile>('/me/profile') })
  const form = useForm<ProfileForm>({ resolver: zodResolver(profileSchema), defaultValues: { preferred_display_name: '', bio: '' }, mode: 'onBlur' })
  const { register, reset, handleSubmit, formState: { errors } } = form
  useEffect(() => { if (query.data) reset({ preferred_display_name: query.data.preferred_display_name ?? '', bio: query.data.bio ?? '' }) }, [query.data, reset])
  const mutation = useMutation({ mutationFn: (data: ProfileForm) => api<UserProfile>('/me/profile', { method: 'PUT', body: JSON.stringify(data) }), onSuccess: async (data) => { setApiError(''); setMessage('Your profile was saved.'); queryClient.setQueryData([...scope, 'me-profile'], data); await queryClient.invalidateQueries({ queryKey: [...scope, 'me-profile'] }) }, onError: (error) => setApiError(error.message) })
  if (query.isLoading) return <AppShell><LoadingState label="Loading your profile" /></AppShell>
  return <AppShell><form onSubmit={handleSubmit(data => mutation.mutate(data))} className="mx-auto max-w-2xl space-y-6"><PageHeader eyebrow="Account" title="Your profile" description="Shared identity used across FitIntel 360. Self-declared and never verified." />{message && <StatusNotice tone="positive" title="Profile saved">{message}</StatusNotice>}{apiError && <StatusNotice tone="risk" title="We could not save your profile">{apiError} Your entries remain on this page; try again.</StatusNotice>}<Card className="space-y-5"><Field id="preferred_display_name" label="Preferred display name" optional help="How you would like to be shown. Defaults to your account name when empty." error={errors.preferred_display_name?.message}>{({ id, describedBy, invalid }) => <TextInput id={id} maxLength={120} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('preferred_display_name')} />}</Field><Field id="bio" label="Bio" optional help="A short description. Avoid sensitive personal or health details." error={errors.bio?.message}>{({ id, describedBy, invalid }) => <TextArea id={id} rows={5} maxLength={1000} disabled={demo} aria-describedby={describedBy} invalid={invalid} {...register('bio')} />}</Field></Card><div className="flex justify-end"><Button type="submit" loading={mutation.isPending} disabled={demo} className="sm:min-w-44">Save profile</Button></div></form></AppShell>
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
