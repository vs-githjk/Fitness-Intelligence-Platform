import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CalendarDays, Dumbbell, Library, Lock } from 'lucide-react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api, ApiError } from '../../api'
import { useAccountQueryScope, useAuth } from '../../auth'
import { LibraryProgramDetail, LibraryProgramList, LibraryProgramSummary } from '../../types'
import { Badge, Button, Card, EmptyState, ErrorState, LoadingState, Modal, StatusNotice } from '../ui'
import { ProgrammingShell } from './ProgrammingShell'

const weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'] as const
const trackingLabel: Record<string, string> = { repetitions_and_load: 'Reps + load', repetitions_only: 'Reps', duration: 'Duration', distance_and_duration: 'Distance + duration', bodyweight_or_assisted_repetitions: 'Bodyweight / assisted' }

// Shared clone flow: create an independent coach-owned draft, then open it in the editor.
function useCloneLibraryProgram() {
  const scope = useAccountQueryScope(); const cache = useQueryClient(); const navigate = useNavigate()
  return useMutation({
    mutationFn: (programId: string) => api<{ id: string }>(`/program-library/${programId}/clone`, { method: 'POST' }),
    onSuccess: async result => { await cache.invalidateQueries({ queryKey: [...scope, 'training-programs'] }); navigate(`/coach/programming/programs/${result.id}`) },
  })
}

function ReadOnlyExplainer() {
  return <StatusNotice tone="info" title="Starter Library — read-only">Using a starter program creates your own editable draft. Future starter-library changes will not affect your copy. You can also build a program from scratch in <Link to="/coach/programming/programs" className="font-semibold underline">Programs</Link>.</StatusNotice>
}

function CloneConfirm({ target, onClose, onConfirm, pending, error }: { target: { id: string; name: string } | null; onClose: () => void; onConfirm: () => void; pending: boolean; error: string }) {
  return <Modal open={Boolean(target)} onClose={onClose} title="Use this starter program?" description="This creates your own editable draft. Future starter-library changes will not affect your copy.">
    <p className="text-sm text-secondary">A private draft copy of <strong className="text-foreground">{target?.name}</strong> will be added to your Programs. It stays a draft until you publish it, and it is not assigned to anyone automatically.</p>
    {error && <StatusNotice tone="risk" title="Clone unsuccessful" className="mt-4">{error}</StatusNotice>}
    <div className="mt-5 flex flex-col-reverse gap-3 sm:flex-row sm:justify-end"><Button variant="secondary" onClick={onClose}>Cancel</Button><Button loading={pending} onClick={onConfirm}>Create my draft</Button></div>
  </Modal>
}

export function StarterLibrary() {
  const { user } = useAuth(); const scope = useAccountQueryScope(); const demo = Boolean(user?.is_demo)
  const [target, setTarget] = useState<{ id: string; name: string } | null>(null); const [error, setError] = useState('')
  const query = useQuery({ queryKey: [...scope, 'starter-library'], queryFn: () => api<LibraryProgramList>('/program-library') })
  const clone = useCloneLibraryProgram()
  function confirm() { if (!target) return; setError(''); clone.mutate(target.id, { onError: caught => setError(caught instanceof ApiError ? caught.message : 'The program could not be copied.') }) }
  return <ProgrammingShell title="Starter Library" description="Browse ready-made starter programs and copy one into your own editable draft.">
    <ReadOnlyExplainer />
    {query.isLoading ? <LoadingState label="Loading starter programs" /> : query.error ? <ErrorState title="Starter Library unavailable" description={query.error.message} onRetry={() => query.refetch()} /> : !query.data?.items.length ? <EmptyState icon={Library} title="No starter programs yet" description="The starter library has not been installed for this workspace. You can create programs from scratch in Programs." /> : <div className="grid gap-4 xl:grid-cols-2">{query.data.items.map(item => <StarterCard key={item.id} item={item} demo={demo} onUse={() => setTarget({ id: item.id, name: item.name })} />)}</div>}
    <CloneConfirm target={target} onClose={() => { setTarget(null); setError('') }} onConfirm={confirm} pending={clone.isPending} error={error} />
  </ProgrammingShell>
}

function StarterCard({ item, demo, onUse }: { item: LibraryProgramSummary; demo: boolean; onUse: () => void }) {
  return <Card as="article" className="flex flex-col"><div className="flex flex-wrap items-center gap-2"><Badge tone="info"><Lock aria-hidden="true" className="mr-1 size-3" />Starter</Badge><Badge tone="neutral" className="capitalize">{item.level}</Badge></div><h2 className="mt-3 text-xl font-semibold">{item.name}</h2>{item.description && <p className="mt-1 text-sm text-secondary">{item.description}</p>}<div className="mt-3 grid grid-cols-2 gap-3 rounded-xl bg-elevated p-3 text-sm sm:grid-cols-3"><Metric label="Duration" value={`${item.duration_weeks} weeks`} /><Metric label="Sessions / week" value={item.sessions_per_week} /><Metric label="Equipment" value={item.equipment_summary.length ? item.equipment_summary.length : 'Minimal'} /></div><p className="mt-2 text-xs text-muted">{item.equipment_summary.length ? item.equipment_summary.join(', ') : 'Minimal or no equipment'}</p><div className="mt-auto flex flex-wrap gap-2 pt-5"><Link to={`/coach/programming/library/${item.id}`} className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-primary px-4 text-sm font-semibold text-white hover:bg-primary-hover"><CalendarDays aria-hidden="true" className="size-4" />View details</Link><Button variant="secondary" disabled={demo} title={demo ? 'Demo workspace — changes are disabled' : undefined} onClick={onUse}>Use this program</Button></div></Card>
}

export function StarterLibraryProgram() {
  const { programId = '' } = useParams(); const { user } = useAuth(); const scope = useAccountQueryScope(); const demo = Boolean(user?.is_demo)
  const [target, setTarget] = useState<{ id: string; name: string } | null>(null); const [error, setError] = useState('')
  const query = useQuery({ queryKey: [...scope, 'starter-library', programId], queryFn: () => api<LibraryProgramDetail>(`/program-library/${programId}`) })
  const clone = useCloneLibraryProgram()
  function confirm() { if (!target) return; setError(''); clone.mutate(target.id, { onError: caught => setError(caught instanceof ApiError ? caught.message : 'The program could not be copied.') }) }
  if (query.isLoading) return <ProgrammingShell title="Starter program" description="Read-only preview."><LoadingState label="Loading starter program" /></ProgrammingShell>
  if (query.error) return <ProgrammingShell title="Starter program" description="Read-only preview."><ErrorState title="Starter program unavailable" description={query.error.message} onRetry={() => query.refetch()} /></ProgrammingShell>
  const program = query.data!
  return <ProgrammingShell title={program.name} description="Read-only starter program. Copy it to create your own editable draft." action={<Button disabled={demo} title={demo ? 'Demo workspace — changes are disabled' : undefined} onClick={() => setTarget({ id: program.id, name: program.name })}><Library aria-hidden="true" className="size-4" />Use this program</Button>}>
    <StatusNotice tone="info" title="Starter Library — read-only">Using this program creates your own editable draft. Future starter-library changes will not affect your copy.</StatusNotice>
    <Card><div className="flex flex-wrap items-center gap-2"><Badge tone="info"><Lock aria-hidden="true" className="mr-1 size-3" />Starter</Badge><Badge tone="neutral" className="capitalize">{program.level}</Badge>{program.goal_tags.map(tag => <Badge key={tag}>{tag.replaceAll('_', ' ')}</Badge>)}</div>{program.description && <p className="mt-3 text-sm text-secondary">{program.description}</p>}<div className="mt-4 grid grid-cols-2 gap-3 rounded-xl bg-elevated p-3 text-sm sm:grid-cols-4"><Metric label="Duration" value={`${program.duration_weeks} weeks`} /><Metric label="Sessions / week" value={program.sessions_per_week} /><Metric label="Equipment" value={program.equipment_summary.length || 'Minimal'} /><Metric label="Level" value={program.level} /></div>{program.equipment_summary.length > 0 && <p className="mt-2 text-xs text-muted">Equipment: {program.equipment_summary.join(', ')}</p>}</Card>
    {program.weeks.map(week => <Card key={week.week_number} as="section"><div className="flex flex-wrap items-center gap-2"><h2 className="text-lg font-semibold">Week {week.week_number}{week.label ? ` · ${week.label}` : ''}</h2>{week.is_deload && <Badge tone="attention">Lighter week</Badge>}</div><div className="mt-3 grid gap-2 md:grid-cols-7">{weekdays.map(day => { const rows = week.sessions.filter(s => s.weekday === day); return <div key={day} className="min-w-0 rounded-lg border bg-elevated/60 p-2"><p className="text-xs font-bold capitalize text-muted">{day.slice(0, 3)}</p>{rows.length ? rows.map((session, index) => <div key={index} className="mt-2 rounded-lg bg-surface p-2 text-xs"><p className="font-semibold">{session.template.name}</p><p className="mt-0.5 text-muted">{session.required ? 'Required' : 'Optional'}{session.template.estimated_duration_minutes ? ` · ${session.template.estimated_duration_minutes} min` : ''}</p><ul className="mt-1 space-y-0.5 text-muted">{session.template.exercises.map((exercise, order) => <li key={order} className="flex items-center gap-1"><Dumbbell aria-hidden="true" className="size-3" />{exercise.name} <span className="text-[10px]">({trackingLabel[exercise.tracking_mode] ?? exercise.tracking_mode})</span></li>)}</ul></div>) : <p className="mt-2 text-xs text-muted">Rest</p>}</div> })}</div></Card>)}
    <p className="text-xs text-muted">{program.disclaimer}</p>
    <CloneConfirm target={target} onClose={() => { setTarget(null); setError('') }} onConfirm={confirm} pending={clone.isPending} error={error} />
  </ProgrammingShell>
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div><p className="text-xs text-muted">{label}</p><p className="mt-1 font-semibold capitalize">{value}</p></div> }
