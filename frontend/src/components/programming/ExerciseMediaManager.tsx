import { useMutation } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import { ExerciseDetail, ExerciseMedia, ExerciseVersion } from '../../types'
import {
  ExerciseMediaSlot,
  acceptFor,
  isVideoSlot,
  removeExerciseMedia,
  setExerciseMedia,
  validateExerciseMedia,
} from '../../exerciseMedia'
import { MediaImage, MediaVideo } from '../AuthorizedMedia'
import { Button, Card, StatusNotice } from '../ui'

const SLOTS: { slot: ExerciseMediaSlot; label: string; help: string }[] = [
  { slot: 'primary_image', label: 'Primary image', help: 'The main still shown with this exercise. JPEG, PNG, WEBP, or GIF up to 5 MB.' },
  { slot: 'secondary_image', label: 'Secondary image', help: 'An optional second angle or position. Up to 5 MB.' },
  { slot: 'demonstration_video', label: 'Demonstration video', help: 'An optional short clip. MP4 or WEBM up to 25 MB.' },
]

function CurrentMedia({ slot, media }: { slot: ExerciseMediaSlot; media: ExerciseMedia }) {
  if (isVideoSlot(slot)) return <MediaVideo src={media.content_url} className="aspect-video w-40" />
  return <MediaImage src={media.content_url} alt="Current media" className="size-20" />
}

function MediaSlotRow({ exerciseId, slot, label, help, media, disabled, onChanged }: {
  exerciseId: string; slot: ExerciseMediaSlot; label: string; help: string
  media: ExerciseMedia | null; disabled: boolean; onChanged: (detail: ExerciseDetail) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selected, setSelected] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [fileError, setFileError] = useState('')

  useEffect(() => () => { if (preview) URL.revokeObjectURL(preview) }, [preview])

  function choose(file: File | undefined) {
    if (!file) return
    const problem = validateExerciseMedia(slot, file)
    if (problem) { setFileError(problem); return }
    setFileError('')
    if (preview) URL.revokeObjectURL(preview)
    setSelected(file)
    setPreview(isVideoSlot(slot) ? null : URL.createObjectURL(file))
  }
  function clear() {
    if (preview) URL.revokeObjectURL(preview)
    setSelected(null); setPreview(null); setFileError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const upload = useMutation({
    mutationFn: () => setExerciseMedia(exerciseId, slot, selected as File),
    onSuccess: detail => { clear(); onChanged(detail) },
    onError: (error: Error) => setFileError(error.message),
  })
  const remove = useMutation({
    mutationFn: () => removeExerciseMedia(exerciseId, slot),
    onSuccess: detail => { clear(); onChanged(detail) },
    onError: (error: Error) => setFileError(error.message),
  })
  const busy = upload.isPending || remove.isPending

  return (
    <div className="space-y-2 rounded-xl border p-3">
      <div className="flex flex-wrap items-start gap-3">
        <div className="shrink-0">
          {preview
            ? <img src={preview} alt="" className="size-20 rounded-xl object-cover" data-testid={`media-preview-${slot}`} />
            : media
              ? <CurrentMedia slot={slot} media={media} />
              : <div className="grid size-20 place-items-center rounded-xl border border-dashed bg-elevated text-[0.65rem] text-muted">None</div>}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">{label}</p>
          <p className="mt-0.5 text-xs text-muted">{help}</p>
          <input ref={inputRef} type="file" accept={acceptFor(slot)} className="sr-only" aria-label={`Choose ${label.toLowerCase()}`} disabled={disabled || busy} onChange={event => choose(event.target.files?.[0])} />
          <div className="mt-2 flex flex-wrap gap-2">
            {selected
              ? <>
                  <Button type="button" onClick={() => upload.mutate()} loading={upload.isPending} disabled={disabled}>Upload</Button>
                  <Button type="button" variant="ghost" onClick={clear} disabled={busy}>Cancel</Button>
                </>
              : <>
                  <Button type="button" variant="secondary" onClick={() => inputRef.current?.click()} disabled={disabled || busy}>{media ? 'Replace' : 'Add'}</Button>
                  {media && <Button type="button" variant="ghost" onClick={() => remove.mutate()} loading={remove.isPending} disabled={disabled}>Remove</Button>}
                </>}
          </div>
        </div>
      </div>
      {fileError && <p className="text-xs font-medium text-risk">{fileError}</p>}
    </div>
  )
}

/** Upload / replace / remove images and a demonstration video on the editable draft. */
export function ExerciseMediaManager({ exerciseId, version, disabled, onChanged }: {
  exerciseId: string; version: ExerciseVersion; disabled: boolean; onChanged: (detail: ExerciseDetail) => void
}) {
  const media: Record<ExerciseMediaSlot, ExerciseMedia | null> = {
    primary_image: version.primary_image,
    secondary_image: version.secondary_image,
    demonstration_video: version.demonstration_video,
  }
  return (
    <Card className="space-y-4">
      <div>
        <h2 className="text-lg font-semibold">Media</h2>
        <p className="mt-1 text-sm text-secondary">Images and a demonstration video for this draft. Publishing freezes them into the version.</p>
      </div>
      {disabled && <StatusNotice tone="info" title="Media is read-only here">Media can only be changed on an editable draft you own.</StatusNotice>}
      <div className="space-y-3">
        {SLOTS.map(({ slot, label, help }) => (
          <MediaSlotRow key={slot} exerciseId={exerciseId} slot={slot} label={label} help={help} media={media[slot]} disabled={disabled} onChanged={onChanged} />
        ))}
      </div>
    </Card>
  )
}
