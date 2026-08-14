import { Archive, BookOpen, Dumbbell, Plus, RotateCcw } from 'lucide-react'
import { useDeferredValue, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { api } from '../../api'
import { useAccountQueryScope, useAuth } from '../../auth'
import { ExerciseSummary } from '../../types'
import { Badge, Button, Card, EmptyState, ErrorState, LoadingState, mbFocusRing, SearchField, SelectInput } from '../ui'
import { MovementGlyph } from '../iron/MovementGlyph'
import { ProgrammingShell } from './ProgrammingShell'
import { PublicationBadge, TrackingModeBadge } from './ProgrammingBadges'

const PAGE_SIZE = 12

function currentVersion(exercise: ExerciseSummary) { return exercise.draft_version ?? exercise.published_version }
function unique(values: (string | undefined)[]) { return [...new Set(values.filter(Boolean) as string[])].sort() }

export function ExerciseLibrary() {
  const { user } = useAuth()
  const accountScope = useAccountQueryScope()
  const [scope, setScope] = useState('all'); const [status, setStatus] = useState('active'); const [search, setSearch] = useState('')
  const [category, setCategory] = useState('all'); const [movement, setMovement] = useState('all'); const [equipment, setEquipment] = useState('all'); const [tracking, setTracking] = useState('all'); const [page, setPage] = useState(1)
  // The free-text query is served by the deterministic, synonym-aware backend engine
  // (so "quads" finds quadriceps exercises); the facet dropdowns narrow the returned set
  // client-side. useDeferredValue keeps typing responsive without a manual debounce.
  const deferredSearch = useDeferredValue(search.trim())
  const query = useQuery({
    queryKey: [...accountScope, 'programming-exercises', deferredSearch],
    queryFn: () => api<ExerciseSummary[]>(
      `/coach/exercises?include_archived=true${deferredSearch ? `&search=${encodeURIComponent(deferredSearch)}` : ''}`,
    ),
  })
  const source = useMemo(() => query.data ?? [], [query.data])
  const options = useMemo(() => ({
    categories: unique(source.map(item => currentVersion(item)?.category)),
    movements: unique(source.map(item => currentVersion(item)?.movement_pattern)),
    equipment: unique(source.flatMap(item => currentVersion(item)?.equipment ?? [])),
  }), [source])
  // Server ranking order is preserved; facet dropdowns only narrow it.
  const filtered = useMemo(() => source.filter(item => {
    const version = currentVersion(item); if (!version) return false
    return (scope === 'all' || item.scope === scope)
      && item.status === status
      && (category === 'all' || version.category === category)
      && (movement === 'all' || version.movement_pattern === movement)
      && (equipment === 'all' || version.equipment.includes(equipment))
      && (tracking === 'all' || version.tracking_mode === tracking)
  }), [category, equipment, movement, scope, source, status, tracking])
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE)); const safePage = Math.min(page, pageCount)
  const rows = filtered.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE)
  function reset() { setScope('all'); setStatus('active'); setSearch(''); setCategory('all'); setMovement('all'); setEquipment('all'); setTracking('all'); setPage(1) }
  function update(setter: (value: string) => void, value: string) { setter(value); setPage(1) }

  return <ProgrammingShell title="Exercise library" description="Browse the system catalog and manage your private, versioned coaching exercises." action={user?.is_demo ? <Button disabled title="Demo workspace — changes are disabled"><Plus aria-hidden="true" className="size-4" />New exercise</Button> : <Link to="/coach/programming/exercises/new" className="inline-flex min-h-11 items-center gap-2 rounded-mb-control bg-mb-action px-4 font-structure text-mb-body font-semibold text-white transition-colors hover:bg-mb-action-hover"><Plus aria-hidden="true" className="size-4" />New exercise</Link>}>
    <Card><div className="flex flex-wrap gap-2" role="group" aria-label="Exercise ownership"><FilterButton active={scope === 'all'} onClick={() => update(setScope, 'all')}>All exercises</FilterButton><FilterButton active={scope === 'system'} onClick={() => update(setScope, 'system')}>System</FilterButton><FilterButton active={scope === 'coach_private'} onClick={() => update(setScope, 'coach_private')}>My Exercises</FilterButton></div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-[minmax(14rem,1.5fr)_repeat(5,minmax(8rem,1fr))]"><SearchField value={search} onChange={value => update(setSearch, value)} label="Search exercises" /><Filter label="Exercise status" value={status} onChange={value => update(setStatus, value)} options={[['active', 'Active'], ['archived', 'Archived']]} /><Filter label="Category" value={category} onChange={value => update(setCategory, value)} options={[['all', 'All categories'], ...options.categories.map(value => [value, value])]} /><Filter label="Movement pattern" value={movement} onChange={value => update(setMovement, value)} options={[['all', 'All movements'], ...options.movements.map(value => [value, value])]} /><Filter label="Equipment" value={equipment} onChange={value => update(setEquipment, value)} options={[['all', 'All equipment'], ...options.equipment.map(value => [value, value])]} /><Filter label="Tracking mode" value={tracking} onChange={value => update(setTracking, value)} options={[['all', 'All tracking'], ['repetitions_and_load', 'Reps + load'], ['repetitions_only', 'Repetitions'], ['duration', 'Duration'], ['distance_and_duration', 'Distance + duration'], ['bodyweight_or_assisted_repetitions', 'Bodyweight / assisted']]} /></div></Card>
    {query.isLoading ? <LoadingState label="Loading exercise library" /> : query.error ? <ErrorState title="Exercise library unavailable" description={query.error.message} onRetry={() => query.refetch()} /> : !rows.length ? <EmptyState icon={Dumbbell} title={deferredSearch ? `No match for “${deferredSearch}”` : 'No exercises match'} description={deferredSearch ? 'Try a muscle (quads, chest), a piece of equipment (dumbbell, barbell), or a movement (push, hinge) — or create your own exercise.' : source.length ? 'Adjust the ownership, status, or metadata filters.' : 'No exercises are currently available to this coach.'} action={(source.length || deferredSearch) ? <Button variant="secondary" onClick={reset}><RotateCcw aria-hidden="true" className="size-4" />Clear filters</Button> : undefined} /> : <><p className="font-structure text-mb-label text-mb-secondary" aria-live="polite">Showing {(safePage - 1) * PAGE_SIZE + 1}–{Math.min(safePage * PAGE_SIZE, filtered.length)} of {filtered.length} exercises</p><div className="grid gap-4 xl:grid-cols-2">{rows.map(exercise => <ExerciseCard key={exercise.id} exercise={exercise} />)}</div><Pagination page={safePage} pages={pageCount} onChange={setPage} /></>}
  </ProgrammingShell>
}

function ExerciseCard({ exercise }: { exercise: ExerciseSummary }) {
  const version = currentVersion(exercise)!; const safeThumbnail = version.thumbnail_url?.startsWith('https://') ? version.thumbnail_url : null
  const muscles = version.primary_muscle_groups.join(', ')
  // Scan hierarchy (§6): movement glyph → name → the muscle it trains (the lead meta,
  // so a "quads" search reads as quad-focused at a glance) → pattern → equipment.
  return <article className="group flex min-w-0 gap-4 rounded-mb-surface border border-mb-hairline bg-mb-surface p-4 shadow-mb-surface transition-colors duration-mb-micro hover:border-mb-ink/15 sm:p-5"><div className="grid size-16 shrink-0 place-items-center overflow-hidden rounded-mb-inset bg-mb-inset text-mb-ink/65 sm:size-20">{safeThumbnail ? <img src={safeThumbnail} alt="" className="size-full object-cover" loading="lazy" /> : <MovementGlyph pattern={version.movement_pattern} className="size-9 sm:size-10" strokeWidth={1.75} />}</div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-1.5"><Badge tone={exercise.scope === 'system' ? 'info' : 'neutral'}>{exercise.scope === 'system' ? 'System' : 'Private'}</Badge><TrackingModeBadge mode={version.tracking_mode} /><PublicationBadge draft={Boolean(exercise.draft_version)} published={Boolean(exercise.published_version)} />{exercise.status === 'archived' && <Badge tone="neutral"><Archive aria-hidden="true" className="mr-1 size-3" />Archived</Badge>}</div><h2 className="mt-2.5 font-structure text-mb-heading text-mb-ink">{version.name}</h2>{muscles && <p className="mt-1 font-structure text-mb-body font-medium text-mb-ink">{muscles}</p>}<p className="mt-1.5 font-structure text-mb-label text-mb-secondary">{version.category} · {version.movement_pattern}</p><p className="mt-1 font-structure text-mb-micro text-mb-muted">{version.equipment.length ? version.equipment.join(', ') : 'No equipment'}</p><Link to={`/coach/programming/exercises/${exercise.id}`} className={`mt-3 inline-flex min-h-11 items-center gap-2 rounded-mb-control font-structure text-mb-label font-semibold text-mb-action hover:underline ${mbFocusRing}`}><BookOpen aria-hidden="true" className="size-4" />{exercise.scope === 'system' ? 'View exercise' : exercise.draft_version ? 'Open draft' : 'View exercise'}</Link></div></article>
}

function FilterButton({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) { return <button type="button" aria-pressed={active} onClick={onClick} className={`min-h-11 rounded-full border px-4 font-structure text-mb-label font-semibold transition-colors ${active ? 'border-mb-ember/40 bg-mb-ember/10 text-mb-ink' : 'border-mb-hairline bg-mb-surface text-mb-secondary hover:bg-mb-inset hover:text-mb-ink'}`}>{children}</button> }
function Filter({ label, value, onChange, options }: { label: string; value: string; onChange: (value: string) => void; options: string[][] }) { return <div><SelectInput aria-label={label} className="mt-0" value={value} onChange={event => onChange(event.target.value)}>{options.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</SelectInput></div> }
function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) { if (pages <= 1) return null; return <nav aria-label="Exercise pages" className="flex items-center justify-center gap-3"><Button variant="secondary" disabled={page === 1} onClick={() => onChange(page - 1)}>Previous</Button><span className="text-sm text-secondary">Page {page} of {pages}</span><Button variant="secondary" disabled={page === pages} onClick={() => onChange(page + 1)}>Next</Button></nav> }
