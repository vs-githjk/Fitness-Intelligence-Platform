import { Dumbbell, Eye, EyeOff, LockKeyhole, ShieldCheck, Sparkles, Users } from 'lucide-react'
import { FormEvent, ReactNode, useEffect, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api'
import { useAuth } from '../auth'
import { Button, ChoiceCard, Field, StatusNotice, TextInput } from '../components/ui'
import { EnvironmentBanner } from '../components/EnvironmentBanner'
import { appConfig } from '../env'
import { Assessment, AuthResponse, Role } from '../types'

function AuthFrame({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return <><EnvironmentBanner /><main className="min-h-screen bg-page lg:grid lg:grid-cols-[minmax(0,0.9fr)_minmax(30rem,1.1fr)]"><section className="relative hidden overflow-hidden bg-foreground px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20"><div className="absolute -right-36 top-1/3 size-96 rounded-full border border-white/10" aria-hidden="true" /><div className="absolute -right-12 top-1/2 size-52 rounded-full border border-white/10" aria-hidden="true" /><Link to="/" className="relative flex items-center gap-3 rounded-xl"><span className="grid size-10 place-items-center rounded-xl bg-primary"><ShieldCheck aria-hidden="true" className="size-5" /></span><span className="font-bold">Fitness Intelligence</span></Link><div className="relative max-w-lg"><p className="text-xs font-bold uppercase tracking-[0.18em] text-white/60">Calm athletic intelligence</p><h2 className="mt-4 text-5xl font-semibold leading-[1.08] text-white">Clear baselines.<br />Better conversations.</h2><p className="mt-6 max-w-md text-base leading-7 text-white/70">Understand the reported factors behind each score and focus coaching attention where it matters most.</p><div className="mt-9 grid gap-3 text-sm text-white/75"><p className="flex items-center gap-3"><Sparkles aria-hidden="true" className="size-4 text-white" />Deterministic, explainable scoring</p><p className="flex items-center gap-3"><LockKeyhole aria-hidden="true" className="size-4 text-white" />Role-aware access to sensitive data</p></div></div><p className="relative max-w-md text-xs leading-5 text-white/50">Coaching support only. Fitness Intelligence does not diagnose conditions or replace qualified medical care.</p></section><section className="flex min-h-screen items-center justify-center px-4 py-10 sm:px-8"><div className="w-full max-w-md"><Link to="/" className="mb-10 flex items-center gap-3 rounded-xl lg:hidden"><span className="grid size-10 place-items-center rounded-xl bg-primary text-white"><ShieldCheck aria-hidden="true" className="size-5" /></span><span className="font-bold">Fitness Intelligence</span></Link><p className="text-xs font-bold uppercase tracking-[0.16em] text-primary">Secure access</p><h1 className="mt-2 text-3xl font-bold sm:text-4xl">{title}</h1><p className="mt-3 text-sm leading-6 text-secondary">{subtitle}</p><div className="mt-8">{children}</div></div></section></main></>
}

function PasswordField({ name, label, autoComplete, error }: { name: string; label: string; autoComplete: string; error?: string }) {
  const [visible, setVisible] = useState(false)
  return <Field label={label} error={error} help={name === 'password' && autoComplete === 'new-password' ? 'Use at least 10 characters.' : undefined}>{({ id, describedBy, invalid }) => <div className="relative"><TextInput id={id} name={name} type={visible ? 'text' : 'password'} required minLength={autoComplete === 'new-password' ? 10 : undefined} autoComplete={autoComplete} aria-describedby={describedBy} aria-invalid={invalid} className="pr-12" /><button type="button" onClick={() => setVisible(value => !value)} className="absolute right-1 top-[0.4rem] grid size-10 place-items-center rounded-lg text-muted hover:bg-elevated hover:text-foreground" aria-label={visible ? 'Hide password' : 'Show password'}>{visible ? <EyeOff aria-hidden="true" className="size-[1.125rem]" /> : <Eye aria-hidden="true" className="size-[1.125rem]" />}</button></div>}</Field>
}

export function LoginPage() {
  const { user, setSession, sessionMessage, clearSessionMessage } = useAuth(); const navigate = useNavigate()
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  if (user) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/dashboard'} replace />
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); clearSessionMessage()
    const form = new FormData(event.currentTarget)
    try {
      const auth = await api<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify({ email: form.get('email'), password: form.get('password') }) })
      setSession(auth)
      if (auth.user.role === 'coach') navigate('/coach/dashboard')
      else {
        try {
          const assessment = await api<Assessment>('/assessments/onboarding')
          navigate(assessment.status === 'submitted' ? '/trainee/dashboard' : '/onboarding')
        } catch (assessmentError) {
          navigate(assessmentError instanceof ApiError && assessmentError.status === 404 ? '/onboarding' : '/trainee/dashboard')
        }
      }
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'We could not sign you in. Your email remains on this page; please try again.')
    } finally { setBusy(false) }
  }
  return <AuthFrame title="Welcome back" subtitle="Sign in to continue to your role-specific workspace.">{sessionMessage && <StatusNotice tone="attention" title="Session ended" className="mb-5">{sessionMessage}</StatusNotice>}<form onSubmit={submit} className="space-y-5" noValidate><Field label="Email address">{({ id, describedBy, invalid }) => <TextInput id={id} name="email" type="email" inputMode="email" required autoComplete="email" placeholder="you@example.com" aria-describedby={describedBy} aria-invalid={invalid} />}</Field><PasswordField name="password" label="Password" autoComplete="current-password" />{error && <StatusNotice tone="risk" title="Sign-in unsuccessful">{error}</StatusNotice>}<Button type="submit" loading={busy} className="w-full">Sign in</Button><Link to="/demo" className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-primary bg-primary/5 px-4 text-sm font-semibold text-primary hover:bg-primary/10"><Sparkles aria-hidden="true" className="size-4" />Explore Demo</Link><p className="text-center text-sm text-secondary">Need an account? <Link className="rounded font-semibold text-primary hover:text-primary-hover" to="/register">Create one</Link></p>{appConfig.isLocal ? <div className="rounded-xl bg-elevated p-4 text-xs leading-5 text-muted"><p className="font-semibold text-secondary">Local test accounts</p><p className="mt-1">Synthetic credentials may be available only in explicitly seeded local development.</p></div> : appConfig.isStaging ? <div className="rounded-xl bg-elevated p-4 text-xs leading-5 text-muted"><p className="font-semibold text-secondary">Staging access</p><p className="mt-1">Use synthetic test information only. Do not enter personal or medical data.</p></div> : null}</form></AuthFrame>
}

export function DemoPage() {
  const { user, setSession } = useAuth(); const navigate = useNavigate()
  const [busyRole, setBusyRole] = useState<Role | null>(null); const [error, setError] = useState('')
  if (user) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/today'} replace />
  async function enter(role: Role) {
    setBusyRole(role); setError('')
    try {
      const auth = await api<AuthResponse>('/auth/demo-session', { method: 'POST', body: JSON.stringify({ role }) })
      setSession(auth); navigate(role === 'coach' ? '/coach/dashboard' : '/trainee/today')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'The demo workspace could not be opened. Please try again.')
    } finally { setBusyRole(null) }
  }
  return <AuthFrame title="Explore the public demo" subtitle="Choose a synthetic, read-only workspace. No email, password, or invitation is required."><div className="space-y-5"><StatusNotice tone="info" title="Synthetic demonstration only">Demo information is fictional. Changes are disabled, and this workspace must not be used for personal or medical data.</StatusNotice><div className="grid gap-3 sm:grid-cols-2"><Button type="button" loading={busyRole === 'trainee'} disabled={busyRole !== null} onClick={() => enter('trainee')} className="min-h-24 flex-col"><Dumbbell aria-hidden="true" className="size-5" />View as Trainee</Button><Button type="button" variant="secondary" loading={busyRole === 'coach'} disabled={busyRole !== null} onClick={() => enter('coach')} className="min-h-24 flex-col"><Users aria-hidden="true" className="size-5" />View as Coach</Button></div>{error && <StatusNotice tone="risk" title="Demo unavailable">{error}</StatusNotice>}<div className="flex flex-wrap justify-center gap-x-5 gap-y-2 text-sm"><Link className="font-semibold text-primary" to="/login">Sign in</Link><Link className="font-semibold text-primary" to="/register">Create account</Link></div></div></AuthFrame>
}

export function RegisterPage() {
  const { user, setSession } = useAuth(); const navigate = useNavigate()
  const initial = new URLSearchParams(window.location.search)
  const fragment = new URLSearchParams(window.location.hash.slice(1))
  const initialRole = initial.get('role')
  const [role, setRole] = useState<Role | null>(initialRole === 'coach' || initialRole === 'trainee' ? initialRole : null)
  const [inviteCode] = useState(initial.get('invite') ?? fragment.get('invite') ?? '')
  const [error, setError] = useState(''); const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({}); const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (window.location.search || window.location.hash) window.history.replaceState({}, '', '/register')
  }, [])
  if (user) return <Navigate to={user.role === 'coach' ? '/coach/dashboard' : '/trainee/dashboard'} replace />
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setFieldErrors({})
    const form = new FormData(event.currentTarget)
    try {
      if (!role) { setError('Choose whether you are creating a coach or trainee account.'); setBusy(false); return }
      const auth = await api<AuthResponse>(`/auth/register/${role}`, { method: 'POST', body: JSON.stringify(Object.fromEntries(form)) })
      setSession(auth); navigate(role === 'coach' ? '/coach/dashboard' : '/onboarding')
    } catch (caught) {
      if (caught instanceof ApiError) { setError(caught.message); setFieldErrors(caught.details.fields ?? {}) }
      else setError('We could not create the account. Your entries remain on this page; please try again.')
    } finally { setBusy(false) }
  }
  return <AuthFrame title="Create your account" subtitle="Choose the workspace that matches how you will use the platform."><form onSubmit={submit} className="grid gap-5 sm:grid-cols-2" noValidate><fieldset className="sm:col-span-2"><legend className="text-sm font-semibold">What type of account are you creating?</legend><div className="mt-2 grid gap-3 sm:grid-cols-2"><ChoiceCard selected={role === 'coach'} title="Coach" description="Manage assigned trainees and create private invitations." onClick={() => { setRole('coach'); setError('') }} /><ChoiceCard selected={role === 'trainee'} title="Trainee" description="Join a coach using a private, single-use invitation." onClick={() => { setRole('trainee'); setError('') }} /></div></fieldset>{role && <><Field label="First name" error={fieldErrors.first_name}>{({ id, describedBy, invalid }) => <TextInput id={id} name="first_name" required autoComplete="given-name" aria-describedby={describedBy} aria-invalid={invalid} />}</Field><Field label="Last name" error={fieldErrors.last_name}>{({ id, describedBy, invalid }) => <TextInput id={id} name="last_name" required autoComplete="family-name" aria-describedby={describedBy} aria-invalid={invalid} />}</Field><div className="sm:col-span-2"><Field label="Email address" error={fieldErrors.email}>{({ id, describedBy, invalid }) => <TextInput id={id} name="email" type="email" inputMode="email" required autoComplete="email" aria-describedby={describedBy} aria-invalid={invalid} />}</Field></div><div className="sm:col-span-2"><PasswordField name="password" label="Create a password" autoComplete="new-password" error={fieldErrors.password} /></div>{role === 'coach' ? <div className="sm:col-span-2"><Field label="Coach registration code" help="Coach access is invitation-only. Enter the private code supplied by the platform owner." error={fieldErrors.registration_code}>{({ id, describedBy, invalid }) => <TextInput id={id} name="registration_code" required autoComplete="off" type="password" placeholder="Enter private registration code" aria-describedby={describedBy} aria-invalid={invalid} />}</Field></div> : <div className="sm:col-span-2"><Field label="Coach invitation code" help="Use the single-use code or registration link supplied by your coach." error={fieldErrors.invite_code}>{({ id, describedBy, invalid }) => <TextInput id={id} name="invite_code" required autoComplete="off" defaultValue={inviteCode} placeholder="Enter invitation code" aria-describedby={describedBy} aria-invalid={invalid} />}</Field></div>}</>}{error && <div className="sm:col-span-2"><StatusNotice tone="risk" title="Account not created">{error}</StatusNotice></div>}<Button type="submit" loading={busy} disabled={!role} className="sm:col-span-2">Create {role ?? ''} account</Button><p className="text-center text-sm text-secondary sm:col-span-2">Already registered? <Link className="rounded font-semibold text-primary hover:text-primary-hover" to="/login">Sign in</Link></p></form></AuthFrame>
}
