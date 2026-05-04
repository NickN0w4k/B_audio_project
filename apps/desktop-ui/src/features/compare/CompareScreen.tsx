import { useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { useProject } from '../../lib/tauri/useProject'
import { useRun } from '../../lib/tauri/useRun'
import { useAppStore } from '../../stores/appStore'
import { ABPlayer } from './ABPlayer'
import { SpectrogramCompare } from './SpectrogramCompare'
import { RepairSummary } from './RepairSummary'
import { Spinner } from '../../components/ui/Spinner'
import { toAudioSrc } from '../../lib/utils/format'

export function CompareScreen() {
  const { projectId, runId } = useParams<{ projectId: string; runId: string }>()
  const { setSelectedProjectId, setSelectedRunId } = useAppStore()

  useEffect(() => {
    if (projectId) setSelectedProjectId(projectId)
    if (runId && runId !== 'latest') setSelectedRunId(runId)
  }, [projectId, runId])

  const { data: project, isLoading: projectLoading } = useProject(projectId ?? null)
  const effectiveRunId = runId !== 'latest' ? runId ?? null : project?.latest_run?.id ?? null
  const { data: run, isLoading: runLoading } = useRun(effectiveRunId)

  if (projectLoading || runLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Spinner />
      </div>
    )
  }

  if (!project) {
    return <p className="text-sm text-[var(--color-muted)]">Project not found.</p>
  }

  const originalUrl = toAudioSrc(project.source_file.original_path)
  const repairedAsset = run?.assets.find((a) => a.kind === 'mix_preview') ?? run?.assets.find((a) => a.kind === 'cleaned_export')
  const repairedUrl = toAudioSrc(repairedAsset?.path)
  const analysisSpectrogram = project.analysis_report?.spectrogram_path
  const runSpectrogram = run?.assets.find((a) => a.kind === 'spectrogram')?.path

  return (
    <div className="max-w-4xl mx-auto flex flex-col gap-8">
      <div>
        <h1 className="text-base font-semibold text-[var(--color-text)]">{project.project.name}</h1>
        <p className="text-xs text-[var(--color-muted)] mt-0.5">Compare original vs repaired</p>
      </div>

      <ABPlayer originalUrl={originalUrl} repairedUrl={repairedUrl} />

      <div className="w-full h-px bg-[var(--color-border)]" />

      <SpectrogramCompare
        originalPath={analysisSpectrogram}
        repairedPath={runSpectrogram ?? repairedAsset?.path}
      />

      <div className="w-full h-px bg-[var(--color-border)]" />

      <RepairSummary
        report={project.analysis_report}
        run={run?.run}
        projectId={projectId ?? ''}
        runId={effectiveRunId ?? ''}
      />
    </div>
  )
}
