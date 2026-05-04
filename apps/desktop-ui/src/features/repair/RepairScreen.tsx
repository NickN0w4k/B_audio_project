import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useProject } from '../../lib/tauri/useProject'
import { useAppStore } from '../../stores/appStore'
import { startProjectRun } from '../../lib/tauri/commands'
import { IntensityPicker } from './IntensityPicker'
import { PresetSelector } from './PresetSelector'
import { Button } from '../../components/ui/Button'
import { Spinner } from '../../components/ui/Spinner'
import { RunProgress } from '../runtime/RunProgress'

export function RepairScreen() {
  const { projectId } = useParams<{ projectId: string }>()
  const queryClient = useQueryClient()
  const {
    setSelectedProjectId,
    setRunning,
    setError,
    clearError,
    setSelectedRunId,
    error,
    isRunning,
    intensity,
    setIntensity,
    exportStems,
    setExportStems,
    applyFinishing,
    setApplyFinishing,
    gpuEnabled,
    setGpuEnabled,
  } = useAppStore()

  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    if (projectId) setSelectedProjectId(projectId)
  }, [projectId])

  const { data: project, isLoading } = useProject(projectId ?? null)
  const report = project?.analysis_report
  const recommended = (report?.suggested_intensity as 'light' | 'medium' | 'strong' | undefined) ?? null

  async function handleStart() {
    if (!projectId || !report) return
    setError(null)
    setRunning(true)
    try {
      const result = await startProjectRun({
        project_id: projectId,
        preset: 'ai_song_cleanup',
        intensity,
        apply_light_finishing: applyFinishing,
        export_stems: exportStems,
        gpu_enabled: gpuEnabled,
      })
      setSelectedRunId(result.run_id)
      await queryClient.invalidateQueries({ queryKey: ['project', projectId] })
      await queryClient.invalidateQueries({ queryKey: ['run', result.run_id] })
    } catch (e) {
      setError((e as Error).message ?? String(e))
      setRunning(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Spinner />
      </div>
    )
  }

  if (!project) {
    return <p className="text-sm text-[var(--color-muted)]">Project not found.</p>
  }

  if (!report) {
    return (
      <div className="max-w-2xl mx-auto flex flex-col gap-6">
        <p className="text-sm text-[var(--color-muted)]">Analysis required before repair. Go to Analysis first.</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto flex flex-col gap-6">
      {error ? (
        <div className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] bg-[var(--color-high)]/10 border border-[var(--color-high)]/30 px-4 py-3">
          <p className="text-sm text-[var(--color-high)]">{error}</p>
          <button type="button" onClick={clearError} className="text-xs text-[var(--color-high)] opacity-60 hover:opacity-100 cursor-pointer">Dismiss</button>
        </div>
      ) : null}

      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)]">{project.project.name}</h1>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">Configure and start cleanup</p>
      </div>

      <PresetSelector report={report} />

      <div className="flex flex-col gap-2">
        <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
          Intensity
        </h3>
        <IntensityPicker
          value={intensity}
          onChange={setIntensity}
          recommended={recommended}
        />
      </div>

      {/* CTA */}
      {isRunning ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4">
          <RunProgress />
        </div>
      ) : (
        <Button
          variant="primary"
          className="w-full py-3 text-sm"
          onClick={() => void handleStart()}
          disabled={isRunning}
        >
          Start Cleanup
        </Button>
      )}

      {/* Advanced */}
      <div className="flex flex-col gap-3">
        <button
          type="button"
          onClick={() => setShowAdvanced((p) => !p)}
          className="flex items-center gap-2 text-xs text-[var(--color-muted)] hover:text-[var(--color-text)] cursor-pointer w-fit"
        >
          <span>{showAdvanced ? '▼' : '▶'}</span>
          Advanced options
        </button>

        {showAdvanced ? (
          <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 flex flex-col gap-3">
            <Toggle
              label="GPU acceleration"
              description="Use CUDA if available"
              checked={gpuEnabled}
              onChange={setGpuEnabled}
            />
            <Toggle
              label="Export stems"
              description="Save separated vocal and music tracks"
              checked={exportStems}
              onChange={setExportStems}
            />
            <Toggle
              label="Light finishing pass"
              description="Optional final polish after reconstruction"
              checked={applyFinishing}
              onChange={setApplyFinishing}
            />
          </div>
        ) : null}
      </div>
    </div>
  )
}

function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string
  description: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="mt-0.5 accent-[var(--color-accent)]"
      />
      <div>
        <p className="text-sm text-[var(--color-text)]">{label}</p>
        <p className="text-xs text-[var(--color-muted)]">{description}</p>
      </div>
    </label>
  )
}
