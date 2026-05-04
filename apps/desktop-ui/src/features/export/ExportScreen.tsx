import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useProject } from '../../lib/tauri/useProject'
import { useRun } from '../../lib/tauri/useRun'
import { useAppStore } from '../../stores/appStore'
import { exportAudio } from '../../lib/tauri/commands'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { toAudioSrc } from '../../lib/utils/format'
import { cn } from '../../lib/utils/cn'

export function ExportScreen() {
  const { projectId, runId } = useParams<{ projectId: string; runId: string }>()
  const queryClient = useQueryClient()
  const {
    setSelectedProjectId,
    setSelectedRunId,
    setExporting,
    setError,
    clearError,
    isExporting,
    error,
    exportFormat,
    setExportFormat,
  } = useAppStore()

  useEffect(() => {
    if (projectId) setSelectedProjectId(projectId)
    if (runId && runId !== 'latest') setSelectedRunId(runId)
  }, [projectId, runId])

  const { data: project, isLoading: projectLoading } = useProject(projectId ?? null)
  const effectiveRunId = runId !== 'latest' ? runId ?? null : project?.latest_run?.id ?? null
  const { data: run, isLoading: runLoading } = useRun(effectiveRunId)

  const existingExport = run?.exports[0] ?? null
  const src = project?.source_file

  async function handleExport() {
    if (!effectiveRunId || !projectId) return
    setExporting(true)
    setError(null)
    try {
      await exportAudio({
        run_id: effectiveRunId,
        project_id: projectId,
        format: exportFormat,
      })
      await queryClient.invalidateQueries({ queryKey: ['run', effectiveRunId] })
    } catch (e) {
      setError((e as Error).message ?? String(e))
    } finally {
      setExporting(false)
    }
  }

  if (projectLoading || runLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Spinner />
      </div>
    )
  }

  if (!project || !run) {
    return (
      <p className="text-sm text-[var(--color-muted)]">
        No completed run found. Complete a cleanup run first.
      </p>
    )
  }

  return (
    <div className="max-w-xl mx-auto flex flex-col gap-6">
      {error ? (
        <div className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] bg-[var(--color-high)]/10 border border-[var(--color-high)]/30 px-4 py-3">
          <p className="text-sm text-[var(--color-high)]">{error}</p>
          <button type="button" onClick={clearError} className="text-xs text-[var(--color-high)] opacity-60 hover:opacity-100 cursor-pointer">Dismiss</button>
        </div>
      ) : null}

      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)]">{project.project.name}</h1>
        {src ? (
          <p className="text-xs text-[var(--color-muted)] mt-0.5">
            {src.filename} · 48 kHz stereo · repaired mix
          </p>
        ) : null}
      </div>

      {/* Format selection */}
      <div className="flex flex-col gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
          Format
        </h3>
        <div className="flex gap-3">
          {(['wav', 'flac'] as const).map((fmt) => (
            <button
              key={fmt}
              type="button"
              onClick={() => setExportFormat(fmt)}
              className={cn(
                'flex-1 rounded-[var(--radius-md)] border px-4 py-3 text-sm font-medium text-left transition-colors cursor-pointer',
                exportFormat === fmt
                  ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
                  : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted)] hover:text-[var(--color-text)]',
              )}
            >
              <span className="block font-semibold">{fmt.toUpperCase()}</span>
              <span className="text-xs opacity-70">{fmt === 'wav' ? '16-bit · 48 kHz' : 'Lossless'}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Export button */}
      <Button
        variant="primary"
        className="w-full py-3"
        loading={isExporting}
        onClick={() => void handleExport()}
      >
        {isExporting ? 'Exporting…' : 'Export'}
      </Button>

      {/* Result */}
      {existingExport ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-low)]/30 bg-[var(--color-low)]/5 px-5 py-4 flex flex-col gap-2">
          <p className="text-xs font-medium text-[var(--color-low)]">Saved</p>
          <p className="text-xs text-[var(--color-muted)] break-all">{existingExport.path}</p>
          <p className="text-xs text-[var(--color-muted)]">{existingExport.format.toUpperCase()}</p>
          {toAudioSrc(existingExport.path) ? (
            <audio controls src={toAudioSrc(existingExport.path) ?? undefined} className="w-full mt-2" />
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
