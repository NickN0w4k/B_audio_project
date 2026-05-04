import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { openSourceFileDialog, importProject } from '../../lib/tauri/commands'
import { useAppStore } from '../../stores/appStore'
import { Spinner } from '../../components/ui/Spinner'
import { cn } from '../../lib/utils/cn'

export function ImportArea() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { setSelectedProjectId, setImporting, setError } = useAppStore()
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handlePath(path: string) {
    setLoading(true)
    setImporting(true)
    setError(null)
    try {
      const project = await importProject(path)
      setSelectedProjectId(project.project.id)
      await queryClient.invalidateQueries({ queryKey: ['projects'] })
      navigate(`/analysis/${project.project.id}`)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setImporting(false)
    }
  }

  async function handleClick() {
    try {
      const path = await openSourceFileDialog()
      if (path) await handlePath(path)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) void handlePath((file as File & { path?: string }).path ?? '')
  }

  return (
    <button
      type="button"
      onClick={() => void handleClick()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      disabled={loading}
      className={cn(
        'w-full rounded-[var(--radius-lg)] border-2 border-dashed transition-colors cursor-pointer flex flex-col items-center justify-center gap-3 py-14',
        dragging
          ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/5'
          : 'border-[var(--color-border)] hover:border-[var(--color-accent)]/50 hover:bg-[var(--color-surface)]',
        loading && 'pointer-events-none',
      )}
    >
      {loading ? (
        <Spinner />
      ) : (
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--color-muted)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
      )}
      <div className="text-center">
        <p className="text-sm font-medium text-[var(--color-text)]">
          {loading ? 'Importing…' : 'Drop a file or click to browse'}
        </p>
        <p className="text-xs text-[var(--color-muted)] mt-1">WAV · FLAC · MP3</p>
      </div>
    </button>
  )
}
