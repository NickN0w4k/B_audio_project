import { useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useProject } from '../../lib/tauri/useProject'
import { useAppStore } from '../../stores/appStore'
import { analyzeProject } from '../../lib/tauri/commands'
import { IssueSummary } from './IssueSummary'
import { Spinner } from '../../components/ui/Spinner'
import { Button } from '../../components/ui/Button'
import { Badge } from '../../components/ui/Badge'
import { toAudioSrc, formatDuration, formatHz } from '../../lib/utils/format'

export function AnalysisScreen() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { setSelectedProjectId, setAnalyzing, setError, isAnalyzing, error, clearError } = useAppStore()

  useEffect(() => {
    if (projectId) setSelectedProjectId(projectId)
  }, [projectId])

  const { data: project, isLoading } = useProject(projectId ?? null)

  const report = project?.analysis_report

  async function runAnalysis() {
    if (!projectId) return
    setAnalyzing(true)
    setError(null)
    try {
      await analyzeProject(projectId)
      await queryClient.invalidateQueries({ queryKey: ['project', projectId] })
    } catch (e) {
      setError((e as Error).message ?? String(e))
    } finally {
      setAnalyzing(false)
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

  const src = project.source_file
  const specSrc = toAudioSrc(report?.spectrogram_path)

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-8">
      {error ? (
        <div className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] bg-[var(--color-high)]/10 border border-[var(--color-high)]/30 px-4 py-3">
          <p className="text-sm text-[var(--color-high)]">{error}</p>
          <button type="button" onClick={clearError} className="text-xs text-[var(--color-high)] opacity-60 hover:opacity-100 cursor-pointer">Dismiss</button>
        </div>
      ) : null}

      {/* File header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-base font-semibold text-[var(--color-text)]">{project.project.name}</h1>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            <span className="text-xs text-[var(--color-muted)]">{src.filename}</span>
            {src.duration_sec != null ? (
              <span className="text-xs text-[var(--color-muted)]">· {formatDuration(src.duration_sec)}</span>
            ) : null}
            {src.sample_rate != null ? (
              <span className="text-xs text-[var(--color-muted)]">· {src.sample_rate} Hz</span>
            ) : null}
            {src.format ? (
              <Badge severity="neutral">{src.format.toUpperCase()}</Badge>
            ) : null}
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <Button
            variant="ghost"
            loading={isAnalyzing}
            onClick={() => void runAnalysis()}
          >
            {report ? 'Re-analyze' : 'Analyze'}
          </Button>
          {report ? (
            <Button
              variant="primary"
              onClick={() => navigate(`/repair/${projectId}`)}
            >
              Run Cleanup →
            </Button>
          ) : null}
        </div>
      </div>

      {/* Spectrogram */}
      {specSrc ? (
        <div className="flex flex-col gap-2">
          <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
            Spectrogram
          </h3>
          {report?.estimated_cutoff_hz != null ? (
            <p className="text-xs text-[var(--color-muted)]">
              Estimated frequency cutoff: {formatHz(report.estimated_cutoff_hz)}
            </p>
          ) : null}
          <img
            src={specSrc}
            alt="Analysis spectrogram"
            className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
          />
        </div>
      ) : null}

      {/* Issues */}
      {report ? (
        <IssueSummary issues={report.issues} />
      ) : isAnalyzing ? (
        <div className="flex items-center gap-3">
          <Spinner className="size-4" />
          <span className="text-sm text-[var(--color-muted)]">Analyzing…</span>
        </div>
      ) : (
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 flex flex-col items-center gap-3 text-center">
          <p className="text-sm text-[var(--color-muted)]">No analysis report yet.</p>
          <Button onClick={() => void runAnalysis()}>Run Analysis</Button>
        </div>
      )}

      {/* Recommendation */}
      {report ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs text-[var(--color-muted)] mb-1">Recommended</p>
            <div className="flex items-center gap-2">
              <Badge severity="accent">{report.recommended_preset ?? 'AI Song Cleanup'}</Badge>
              {report.suggested_intensity ? (
                <span className="text-xs text-[var(--color-muted)]">· {report.suggested_intensity} intensity</span>
              ) : null}
              {report.runtime_estimate_sec != null ? (
                <span className="text-xs text-[var(--color-muted)]">· ~{Math.round(report.runtime_estimate_sec / 60)} min</span>
              ) : null}
            </div>
          </div>
          <Button onClick={() => navigate(`/repair/${projectId}`)}>
            Configure Repair →
          </Button>
        </div>
      ) : null}
    </div>
  )
}
