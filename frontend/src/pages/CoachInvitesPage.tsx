import { Copy, Link2, MailPlus, UserPlus } from 'lucide-react'
import { FormEvent, useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api'
import { useAuth } from '../auth'
import { AppShell } from '../components/AppShell'
import { Badge, Button, Card, EmptyState, Field, PageHeader, SelectInput, StatusNotice, TextInput } from '../components/ui'
import { CoachInvite, CreatedCoachInvite } from '../types'

function statusTone(status: CoachInvite['status']) {
  if (status === 'active') return 'positive' as const
  if (status === 'used') return 'info' as const
  if (status === 'expired') return 'attention' as const
  return 'neutral' as const
}

function inviteLink(token: string): string {
  const url = new URL('/register', window.location.origin)
  url.searchParams.set('role', 'trainee')
  url.hash = `invite=${encodeURIComponent(token)}`
  return url.toString()
}

export function CoachInvitesPage() {
  const { user } = useAuth()
  const [invites, setInvites] = useState<CoachInvite[]>([])
  const [created, setCreated] = useState<CreatedCoachInvite | null>(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState('')

  const load = useCallback(async () => {
    try { setInvites(await api<CoachInvite[]>('/coach/invites')); setError('') }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : 'Invitations could not be loaded.') }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setError(''); setCreated(null)
    const formElement = event.currentTarget
    const form = new FormData(formElement)
    const intendedEmail = String(form.get('intended_email') ?? '').trim()
    try {
      const next = await api<CreatedCoachInvite>('/coach/invites', {
        method: 'POST',
        body: JSON.stringify({ intended_email: intendedEmail || null, expires_in_days: Number(form.get('expires_in_days')) }),
      })
      setCreated(next); formElement.reset(); await load()
    } catch (caught) { setError(caught instanceof ApiError ? caught.message : 'The invitation could not be created.') }
    finally { setBusy(false) }
  }

  async function copy(value: string, label: string) {
    try { await navigator.clipboard.writeText(value); setCopied(label) }
    catch { setCopied('Copy unavailable—select the value manually') }
  }

  async function revoke(invite: CoachInvite) {
    setBusy(true); setError('')
    try { await api(`/coach/invites/${invite.id}/revoke`, { method: 'POST' }); await load() }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : 'The invitation could not be revoked.') }
    finally { setBusy(false) }
  }

  return <AppShell><div className="space-y-8"><PageHeader eyebrow="Coach workspace" title="Trainee invitations" description="Create private, single-use invitations that assign each trainee directly to you." />
    {user?.is_demo && <StatusNotice tone="info" title="Demo invitations are read-only">You can review invitation history, but creating or revoking invitations is disabled.</StatusNotice>}
    <Card><h2 className="text-xl font-semibold">Create an invitation</h2><p className="mt-1 text-sm leading-6 text-secondary">FitIntel 360 does not send invitation emails. Create the invitation, then copy its code or link and share it through a trusted channel.</p><form onSubmit={create} className="mt-5 grid gap-5 sm:grid-cols-[1fr_12rem_auto]"><Field label="Restrict to trainee email (optional)" help="FitIntel 360 does not send this invitation by email. If an email is entered, only an account using that email can redeem the invitation. Leave it blank to allow any eligible trainee possessing the invitation to redeem it. Copy and share the generated link manually.">{({ id, describedBy, invalid }) => <TextInput id={id} name="intended_email" type="email" autoComplete="off" aria-describedby={describedBy} aria-invalid={invalid} />}</Field><Field label="Expires after">{({ id, describedBy, invalid }) => <SelectInput id={id} name="expires_in_days" defaultValue="7" aria-describedby={describedBy} aria-invalid={invalid}><option value="1">1 day</option><option value="3">3 days</option><option value="7">7 days</option><option value="14">14 days</option><option value="30">30 days</option></SelectInput>}</Field><Button type="submit" loading={busy} disabled={user?.is_demo} className="self-end"><MailPlus aria-hidden="true" className="size-4" />Create invite</Button></form></Card>
    {created && <StatusNotice tone="positive" title="Invitation created—copy it now"><p>The raw code and link are shown only now and cannot be recovered after this page is refreshed. FitIntel 360 will not email them; copy and share one manually through a trusted channel.</p><div className="mt-3 grid gap-3"><div className="flex min-w-0 flex-col gap-2 sm:flex-row"><code className="min-w-0 flex-1 overflow-x-auto rounded-lg bg-surface px-3 py-2 text-xs text-foreground">{created.token}</code><Button variant="secondary" onClick={() => copy(created.token, 'Code copied')}><Copy aria-hidden="true" className="size-4" />Copy invitation code</Button></div><div className="flex min-w-0 flex-col gap-2 sm:flex-row"><code className="min-w-0 flex-1 overflow-x-auto rounded-lg bg-surface px-3 py-2 text-xs text-foreground">{inviteLink(created.token)}</code><Button variant="secondary" onClick={() => copy(inviteLink(created.token), 'Link copied')}><Link2 aria-hidden="true" className="size-4" />Copy invitation link</Button></div>{copied && <p aria-live="polite" className="text-xs font-semibold">{copied}</p>}</div></StatusNotice>}
    {error && <StatusNotice tone="risk" title="Invitation action unsuccessful">{error}</StatusNotice>}
    <section aria-labelledby="invite-history"><h2 id="invite-history" className="text-xl font-semibold">Invitation history</h2><p className="mt-1 text-sm text-secondary">Raw invitation codes are never shown here.</p>{loading ? <p className="mt-5 text-sm text-secondary">Loading invitations…</p> : invites.length === 0 ? <div className="mt-5"><EmptyState icon={UserPlus} title="No invitations yet" description={user?.is_demo ? 'The demo coach has no invitation history.' : 'Create the first invitation to connect a trainee to your workspace.'} /></div> : <div className="mt-5 grid gap-3">{invites.map(invite => <Card key={invite.id} as="article" className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="min-w-0"><div className="flex flex-wrap items-center gap-2"><p className="truncate font-semibold">{invite.intended_email ?? 'Any invited email'}</p><Badge tone={statusTone(invite.status)}>{invite.status}</Badge></div><p className="mt-1 text-xs text-muted">Created {new Date(invite.created_at).toLocaleString()} · Expires {new Date(invite.expires_at).toLocaleString()}</p></div>{invite.status === 'active' && <Button variant="danger" disabled={busy || user?.is_demo} onClick={() => revoke(invite)}>Revoke</Button>}</Card>)}</div>}</section>
  </div></AppShell>
}
