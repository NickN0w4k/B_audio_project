import { convertFileSrc, invoke as tauriInvoke, isTauri } from '@tauri-apps/api/core'
import { listen } from '@tauri-apps/api/event'
import { useEffect, useMemo, useRef, useState } from 'react'

type AppStatus = {
  app_name: string
  storage_dir: string
  database_path: string
  engine_entry: string
  python_command: string
  cuda_available: boolean
  gpu_name?: string | null
  active_run_id?: string | null
}

type ProjectSummary = {
  id: string
  name: string
  status: string
  created_at: string
  updated_at: string
  source_filename?: string | null
}

type SourceFileRecord = {
  id: string
  project_id: string
  original_path: string
  normalized_path?: string | null
  filename: string
  duration_sec?: number | null
  sample_rate?: number | null
  channels?: number | null
  format?: string | null
}

type RunSummary = {
  id: string
  project_id: string
  preset: string
  intensity: string
  status: string
  started_at?: string | null
  finished_at?: string | null
  report_path?: string | null
  failure_message?: string | null
}

type RunStepSummary = {
  id: string
  run_id: string
  step_name: string
  status: string
  started_at?: string | null
  finished_at?: string | null
  metrics_json?: string | null
}

type RunDetail = {
  run: RunSummary
  steps: RunStepSummary[]
  assets: Array<{
    id: string
    project_id: string
    run_id?: string | null
    kind: string
    path: string
    metadata_json?: string | null
  }>
  exports: Array<{
    id: string
    run_id: string
    format: string
    path: string
    created_at: string
  }>
}

type AssetKind =
  | 'normalized_audio'
  | 'mix_preview'
  | 'cleaned_export'
  | 'stem_vocals'
  | 'stem_music'
  | 'repaired_vocals'
  | 'repaired_music'

type RunStatusEvent = {
  run_id: string
  status: string
  message?: string | null
}

type RunStepEvent = {
  run_id: string
  status: string
  step_name: string
  message: string
  progress: number
}

type ProjectDetail = {
  project: ProjectSummary
  source_file: SourceFileRecord
  analysis_report?: {
    id: string
    project_id: string
    report_path: string
    recommended_preset?: string | null
    suggested_intensity?: string | null
    planned_repair_modules: string[]
    runtime_estimate_sec?: number | null
    overall_confidence?: number | null
    estimated_cutoff_hz?: number | null
    spectrogram_path?: string | null
    summary_json?: string | null
    created_at: string
    issues: Array<{
      id: string
      label: string
      severity: string
      confidence?: number | null
      description: string
      artifact_title?: string | null
      detection?: string | null
      repair?: string | null
    }>
  } | null
  latest_run?: RunSummary | null
}

type StartRunRequest = {
  project_id: string
  preset: string
  intensity: string
  apply_light_finishing: boolean
  export_stems: boolean
  gpu_enabled: boolean
}

type ExportResult = {
  export_id: string
  path: string
  format: string
}

type AnalyzeProjectResult = {
  analysis_report_path: string
  normalized_path: string
}

type Screen = 'Home' | 'Analysis' | 'Repair' | 'Compare' | 'Export'

const NAV_STEPS: Screen[] = ['Home', 'Analysis', 'Repair', 'Compare', 'Export']

async function invoke<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) {
    throw new Error('Tauri runtime is not available in the browser preview.')
  }
  return tauriInvoke<T>(command, args)
}

function toAudioSrc(path?: string | null): string | null {
  if (!path) return null
  if (isTauri()) return convertFileSrc(path)
  return `file:///${path.replace(/\\/g, '/')}`
}

function formatStepLabel(stepName: string): string {
  return stepName
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function assetLabel(kind: string): string {
  const labels: Record<AssetKind, string> = {
    normalized_audio: 'Normalized Working File',
    mix_preview: 'Preview Mix',
    cleaned_export: 'Cleaned Export',
    stem_vocals: 'Stem: Vocals',
    stem_music: 'Stem: Music',
    repaired_vocals: 'Repaired Vocals',
    repaired_music: 'Repaired Music',
  }
  return labels[kind as AssetKind] ?? kind
}

function formatCutoffText(report?: ProjectDetail['analysis_report'] | null): string {
  if (!report) return 'Detected cutoff: unavailable'
  if (report.estimated_cutoff_hz == null) return 'Detected cutoff: not detected in this analysis report'
  return `Detected cutoff: ${report.estimated_cutoff_hz} Hz`
}

function intensityDescription(intensity: 'light' | 'medium' | 'strong'): string {
  switch (intensity) {
    case 'light':
      return 'Uses gentler EQ and compression moves. Best when the track already sounds close and you want to avoid over-processing.'
    case 'medium':
      return 'Balanced default. Applies enough correction to fix common AI artifacts without pushing the sound too far.'
    case 'strong':
      return 'Uses deeper EQ cuts, boosts, and stronger dynamic control. Best for obvious artifacts, but more likely to change the original tone.'
  }
}

export function App() {
  const [status, setStatus] = useState<AppStatus | null>(null)
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [selectedProject, setSelectedProject] = useState<ProjectDetail | null>(null)
  const [selectedRun, setSelectedRun] = useState<RunDetail | null>(null)
  const [sourcePath, setSourcePath] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [isImporting, setIsImporting] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [liveStep, setLiveStep] = useState<RunStepEvent | null>(null)
  const [compareTarget, setCompareTarget] = useState<'original' | 'preview' | 'export'>('preview')
  const [screen, setScreen] = useState<Screen>('Home')

  // Repair setup options
  const [intensity, setIntensity] = useState<'light' | 'medium' | 'strong'>('medium')
  const [exportStems, setExportStems] = useState(false)
  const [applyFinishing, setApplyFinishing] = useState(false)
  const [gpuEnabled, setGpuEnabled] = useState(true)

  // Export options
  const [exportFormat, setExportFormat] = useState<'wav' | 'flac'>('wav')
  const [isExporting, setIsExporting] = useState(false)

  const projectRequestRef = useRef(0)
  const runRequestRef = useRef(0)
  const selectedProjectIdRef = useRef<string | null>(null)
  const selectedRunIdRef = useRef<string | null>(null)

  const previewAsset = selectedRun?.assets.find((a) => a.kind === 'mix_preview')
  const normalizedAsset = selectedRun?.assets.find((a) => a.kind === 'normalized_audio')
  const cleanedExport = selectedRun?.exports[0]
  const repairModules = selectedProject?.analysis_report?.planned_repair_modules ?? []
  const recommendedRepairIntensity =
    (selectedProject?.analysis_report?.suggested_intensity as 'light' | 'medium' | 'strong' | undefined) ?? 'medium'
  const extraAudioAssets =
    selectedRun?.assets.filter(
      (a) => !['mix_preview', 'normalized_audio', 'cleaned_export'].includes(a.kind),
    ) ?? []
  const compareSource =
    compareTarget === 'original'
      ? { label: 'Original Source', path: selectedProject?.source_file.original_path ?? null }
      : compareTarget === 'export'
        ? { label: 'Cleaned Export', path: cleanedExport?.path ?? null }
        : { label: 'Preview Mix', path: previewAsset?.path ?? null }
  const runtimeLabel = status?.cuda_available ? 'GPU Ready' : 'CPU Only'
  const runtimeDetail = status?.cuda_available
    ? (status.gpu_name ?? 'CUDA device detected')
    : 'CUDA not available'
  const hasActiveRun = Boolean(status?.active_run_id)
  const isBusy = isAnalyzing || Boolean(status?.active_run_id)
  const overlayTitle = isAnalyzing ? 'Analyzing Track' : 'Processing Cleanup'
  const overlayDescription = isAnalyzing
    ? 'Inspecting the song and generating a reusable issue report.'
    : 'Running the cleanup pipeline on the current project.'

  // Auto-advance screen based on run state
  const autoScreen = useMemo<Screen>(() => {
    if (!selectedProject) return 'Home'
    if (selectedRun?.run.status === 'completed' && isRunning) return 'Compare'
    if (selectedProject.analysis_report) return 'Analysis'
    return 'Home'
  }, [isRunning, selectedProject, selectedRun])

  // Keep screen in sync when run state changes, but don't override manual nav
  const prevAutoScreen = useRef(autoScreen)
  useEffect(() => {
    if (autoScreen !== prevAutoScreen.current) {
      prevAutoScreen.current = autoScreen
      setScreen(autoScreen)
    }
  }, [autoScreen])

  useEffect(() => {
    selectedProjectIdRef.current = selectedProject?.project.id ?? null
  }, [selectedProject?.project.id])

  useEffect(() => {
    selectedRunIdRef.current = selectedRun?.run.id ?? null
  }, [selectedRun?.run.id])

  async function loadRun(runId?: string | null) {
    const requestId = ++runRequestRef.current
    if (!runId) {
      if (requestId === runRequestRef.current) setSelectedRun(null)
      return null
    }
    const runDetail = await invoke<RunDetail>('get_run', { runId })
    if (requestId === runRequestRef.current) setSelectedRun(runDetail)
    return runDetail
  }

  async function loadProject(projectId?: string | null) {
    const requestId = ++projectRequestRef.current
    if (!projectId) {
      if (requestId === projectRequestRef.current) setSelectedProject(null)
      await loadRun(null)
      return null
    }
    const project = await invoke<ProjectDetail>('get_project', { projectId })
    if (requestId !== projectRequestRef.current) return project
    setSelectedProject(project)
    await loadRun(project.latest_run?.id)
    return project
  }

  useEffect(() => {
    async function bootstrap() {
      setIsLoading(true)
      setError(null)
      try {
        const [appStatus, projectList] = await Promise.all([
          invoke<AppStatus>('get_app_status'),
          invoke<{ projects: ProjectSummary[] }>('list_projects'),
        ])
        setStatus(appStatus)
        setProjects(projectList.projects)
        if (projectList.projects[0]) {
          await loadProject(projectList.projects[0].id)
        }
      } catch (e) {
        setError((e as Error).message)
      } finally {
        setIsLoading(false)
      }
    }
    void bootstrap()
  }, [])

  useEffect(() => {
    let unsubStatus: (() => void) | undefined
    let unsubStep: (() => void) | undefined

    async function bind() {
      if (!isTauri()) return

      unsubStatus = await listen<RunStatusEvent>('run-status', async (event) => {
        setMessage(`Run ${event.payload.run_id} ${event.payload.status}.`)
        setIsRunning(event.payload.status === 'running')
        if (event.payload.status !== 'running') {
          setLiveStep(null)
        }
        if (event.payload.status === 'failed') {
          setError(
            event.payload.message ??
              `Run ${event.payload.run_id} failed. Check the latest run details and try again.`,
          )
        }
        if (event.payload.status === 'completed') {
          setScreen('Compare')
        }
        await refreshStatus()
        if (selectedProjectIdRef.current) await refreshProjects(selectedProjectIdRef.current)
        try {
          await loadRun(event.payload.run_id)
        } catch {
          // ignore transient failures while run record settles
        }
      })

      unsubStep = await listen<RunStepEvent>('run-step', async (event) => {
        setLiveStep(event.payload)
        if (selectedRunIdRef.current === event.payload.run_id) {
          await loadRun(event.payload.run_id)
        }
      })
    }

    void bind()
    return () => {
      unsubStatus?.()
      unsubStep?.()
    }
  }, [])

  useEffect(() => {
    if (!selectedProject?.project.id || !status?.active_run_id) return
    const id = window.setInterval(() => {
      void refreshStatus()
      void refreshProjects(selectedProject.project.id)
    }, 1000)
    return () => window.clearInterval(id)
  }, [status?.active_run_id, selectedProject?.project.id])

  async function refreshStatus() {
    const next = await invoke<AppStatus>('get_app_status')
    setStatus(next)
    setIsRunning(Boolean(next.active_run_id))
  }

  async function refreshProjects(selectId?: string) {
    const list = await invoke<{ projects: ProjectSummary[] }>('list_projects')
    setProjects(list.projects)
    const target = selectId ?? list.projects[0]?.id
    if (!target) {
      await loadProject(null)
      return
    }
    await loadProject(target)
  }

  async function chooseFile() {
    setError(null)
    try {
      const r = await invoke<{ path?: string | null }>('open_source_file_dialog')
      if (r.path) setSourcePath(r.path)
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function handleImport() {
    if (!sourcePath.trim()) {
      setError('Please choose or enter a valid local file path.')
      return
    }
    setIsImporting(true)
    setError(null)
    setMessage(null)
    try {
      const result = await invoke<{ project: ProjectDetail }>('import_project', {
        input: { source_path: sourcePath },
      })
      setSourcePath('')
      setMessage(`Imported: ${result.project.project.name}`)
      await runProjectAnalysis(result.project.project.id, true)
      await refreshStatus()
      setScreen('Analysis')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setIsImporting(false)
    }
  }

  async function openProject(projectId: string) {
    setError(null)
    setMessage(null)
    try {
      const project = await loadProject(projectId)
      setScreen(project?.analysis_report ? 'Analysis' : 'Repair')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function startRun() {
    if (!selectedProject) {
      setError('Import or select a project first.')
      return
    }
    if (!selectedProject.analysis_report) {
      setError('Run analysis first before starting cleanup.')
      return
    }
    const request: StartRunRequest = {
      project_id: selectedProject.project.id,
      preset: 'ai_song_cleanup',
      intensity,
      apply_light_finishing: applyFinishing,
      export_stems: exportStems,
      gpu_enabled: gpuEnabled,
    }
    setIsRunning(true)
    setError(null)
    setMessage('Starting cleanup run...')
    try {
      const result = await invoke<{ run_id: string; status: string }>('start_project_run', {
        request,
      })
      setMessage(`Run ${result.run_id} started.`)
      await refreshStatus()
      await refreshProjects(selectedProject.project.id)
      await loadRun(result.run_id)
    } catch (e) {
      setError((e as Error).message)
      setIsRunning(false)
    }
  }

  async function handleExport() {
    if (!selectedRun || !selectedProject) return
    setIsExporting(true)
    setError(null)
    try {
      const result = await invoke<ExportResult>('export_audio', {
        request: {
          run_id: selectedRun.run.id,
          project_id: selectedProject.project.id,
          format: exportFormat,
        },
      })
      setMessage(`Export saved: ${result.path}`)
      await loadRun(selectedRun.run.id)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setIsExporting(false)
    }
  }

  async function runProjectAnalysis(projectId: string, silentMessage = false) {
    setIsAnalyzing(true)
    setError(null)
    if (!silentMessage) setMessage('Running analysis...')
    try {
      await invoke<AnalyzeProjectResult>('analyze_project', {
        request: { project_id: projectId },
      })
      await refreshProjects(projectId)
      if (!silentMessage) setMessage('Analysis complete.')
      setScreen('Analysis')
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  // ── Screens ────────────────────────────────────────────────────────────────

  function screenHome() {
    return (
      <>
        <section className="hero-card">
          <h2>Import a local source file</h2>
          <p>
            Choose a WAV, FLAC, or MP3 file. The app creates a local project and preserves the
            original.
          </p>
          <div className="input-row">
            <input
              value={sourcePath}
              onChange={(e) => setSourcePath(e.target.value)}
              placeholder="C:\\Music\\example-song.mp3"
            />
            <button type="button" className="ghost-button" onClick={() => void chooseFile()}>
              Browse
            </button>
            <button type="button" onClick={() => void handleImport()} disabled={isImporting || isLoading}>
              {isImporting ? 'Importing...' : 'Import Project'}
            </button>
          </div>
        </section>

        <section className="grid two-up">
          <article className="panel">
            <div className="panel-header-row">
              <h3>Projects</h3>
              <button
                type="button"
                className="ghost-button"
                onClick={() => void refreshProjects(selectedProject?.project.id)}
              >
                Refresh
              </button>
            </div>
            {isLoading ? <p>Loading projects...</p> : null}
            <ul className="project-list">
              {projects.map((project) => (
                <li key={project.id}>
                  <div>
                    <strong>{project.name}</strong>
                    <div className="meta-text">
                      {project.source_filename ?? 'No source file'} · {project.status}
                    </div>
                  </div>
                  <button type="button" onClick={() => void openProject(project.id)}>
                    Open
                  </button>
                </li>
              ))}
              {!projects.length && !isLoading ? <li>No projects yet.</li> : null}
            </ul>
          </article>

          <article className="panel">
            <h3>System Readiness</h3>
            <ul className="status-list stacked">
              <li>Storage: {status?.storage_dir ?? 'Unavailable'}</li>
              <li>Database: {status?.database_path ?? 'Unavailable'}</li>
              <li>Python: {status?.python_command ?? 'Unavailable'}</li>
              <li>Runtime: {status ? runtimeLabel : 'Unavailable'}</li>
              <li>Device: {status ? runtimeDetail : 'Unavailable'}</li>
              <li>Engine: {status?.engine_entry ?? 'Unavailable'}</li>
            </ul>
          </article>
        </section>
      </>
    )
  }

  function screenAnalysis() {
    return (
      <section className="panel screen-panel">
        <div className="panel-header-row">
          <h3>Analysis Report</h3>
          {selectedProject ? (
            <div>
              <button
                type="button"
                className="ghost-button"
                onClick={() => void runProjectAnalysis(selectedProject.project.id)}
                disabled={isAnalyzing || isRunning}
              >
                {isAnalyzing ? 'Analyzing...' : 'Re-run Analysis'}
              </button>
              <button
                type="button"
                onClick={() => setScreen('Repair')}
                disabled={!selectedProject.analysis_report}
                style={{ marginLeft: '0.75rem' }}
              >
                Continue to Repair Setup
              </button>
            </div>
          ) : null}
        </div>

        {!selectedProject ? (
          <p>No project selected. Go to Home and import or open a project.</p>
        ) : selectedProject.analysis_report ? (
          <>
            <div className="analysis-summary-row">
              <div className="analysis-pill">
                {selectedProject.source_file.filename}
              </div>
              <div className="analysis-pill">
                Recommended: {selectedProject.analysis_report.recommended_preset ?? 'Pending'}
              </div>
              <div className="analysis-pill">
                Est. runtime: {selectedProject.analysis_report.runtime_estimate_sec ?? '—'} sec
              </div>
              <div className="analysis-pill">
                Confidence: {selectedProject.analysis_report.overall_confidence ?? '—'}
              </div>
              <div className="analysis-pill">
                Suggested intensity: {recommendedRepairIntensity}
              </div>
            </div>
            {selectedProject.analysis_report.spectrogram_path ? (
              <article className="panel" style={{ marginBottom: '1rem' }}>
                <h4>Spectrogram</h4>
                <p className="meta-text">
                  Use the frequency scale on the image to spot sharp high-frequency cutoffs and check whether any air remains above the cutoff region.
                </p>
                <p className="meta-text">{formatCutoffText(selectedProject.analysis_report)}</p>
                <img
                  className="spectrogram-image"
                  src={toAudioSrc(selectedProject.analysis_report.spectrogram_path) ?? undefined}
                  alt="Analysis spectrogram"
                />
              </article>
            ) : null}
            <article className="panel" style={{ marginBottom: '1rem' }}>
              <h4>Planned Repair Modules</h4>
              <ul className="module-list">
                {repairModules.map((module) => (
                  <li key={module}>{module}</li>
                ))}
              </ul>
            </article>
            <div className="analysis-grid">
              {selectedProject.analysis_report.issues.map((issue) => (
                <article key={issue.id} className="analysis-card">
                  <div className={`severity severity-${issue.severity}`}>{issue.severity}</div>
                  <h4>{issue.artifact_title ?? issue.label}</h4>
                  <p className="meta-text">Confidence: {issue.confidence ?? '—'}</p>
                  <p>{issue.description}</p>
                  {issue.detection || issue.repair ? (
                    <>
                      {issue.detection ? <p className="meta-text"><strong>Detection:</strong> {issue.detection}</p> : null}
                      {issue.repair ? <p className="meta-text"><strong>Repair:</strong> {issue.repair}</p> : null}
                    </>
                  ) : null}
                </article>
              ))}
            </div>
          </>
        ) : (
          <div>
            <p>No analysis report yet.</p>
            <button
              type="button"
              onClick={() => void runProjectAnalysis(selectedProject.project.id)}
              disabled={isAnalyzing || isRunning}
            >
              {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        )}
      </section>
    )
  }

  function screenRepair() {
    return (
      <section className="panel screen-panel">
        <div className="panel-header-row">
          <h3>Repair Setup</h3>
          <button
            type="button"
            onClick={() => void startRun()}
            disabled={!selectedProject || !selectedProject.analysis_report || hasActiveRun || isAnalyzing}
          >
            {hasActiveRun ? 'Running...' : 'Start AI Song Cleanup'}
          </button>
        </div>

        {!selectedProject ? (
          <p>No project selected. Go to Home and import or open a project.</p>
        ) : (
          <div className="repair-setup-grid">
            <article className="setup-card">
              <h4>Project</h4>
              <p className="meta-text">{selectedProject.project.name}</p>
              <p className="meta-text path-wrap">{selectedProject.source_file.original_path}</p>
            </article>

            <article className="setup-card">
              <h4>Intensity</h4>
              <p className="meta-text">Controls how aggressively corrections are applied.</p>
              <p className="meta-text">
                Suggested by analysis: <strong>{recommendedRepairIntensity}</strong>
              </p>
              <div className="option-group">
                {(['light', 'medium', 'strong'] as const).map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    className={intensity === lvl ? 'option-button option-active' : 'option-button'}
                    onClick={() => setIntensity(lvl)}
                  >
                    {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                  </button>
                ))}
              </div>
              <p className="meta-text intensity-description">{intensityDescription(intensity)}</p>
            </article>

            <article className="setup-card">
              <h4>Options</h4>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={gpuEnabled}
                  onChange={(e) => setGpuEnabled(e.target.checked)}
                />
                <span>GPU acceleration {status?.cuda_available ? '(available)' : '(not detected)'}</span>
              </label>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={exportStems}
                  onChange={(e) => setExportStems(e.target.checked)}
                />
                <span>Export individual stems</span>
              </label>
              <label className="toggle-row">
                <input
                  type="checkbox"
                  checked={applyFinishing}
                  onChange={(e) => setApplyFinishing(e.target.checked)}
                />
                <span>Apply light finishing pass (optional polish)</span>
              </label>
            </article>

            {selectedProject.analysis_report ? (
              <article className="setup-card">
                <h4>Detected Issues</h4>
                {selectedProject.analysis_report.issues.map((issue) => (
                  <div key={issue.id} className="issue-row">
                    <span className={`severity severity-${issue.severity}`}>{issue.severity}</span>
                    <span>{issue.label}</span>
                  </div>
                ))}
              </article>
            ) : (
              <article className="setup-card">
                <h4>Analysis Required</h4>
                <p className="meta-text">
                  Run analysis first to detect issues and unlock cleanup settings based on the report.
                </p>
                <button
                  type="button"
                  onClick={() => void runProjectAnalysis(selectedProject.project.id)}
                  disabled={isAnalyzing || isRunning}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
                </button>
              </article>
            )}

            {selectedProject.analysis_report ? (
              <article className="setup-card">
                <h4>Active Repair Modules</h4>
                <ul className="module-list compact">
                  {repairModules.map((module) => (
                    <li key={module}>{module}</li>
                  ))}
                </ul>
              </article>
            ) : null}
          </div>
        )}
      </section>
    )
  }

  function renderProgressOverlay() {
    if (!isBusy) return null

    const overallProgress = liveStep ? Math.round(liveStep.progress * 100) : 0

    return (
      <div className="progress-overlay-backdrop" role="status" aria-live="polite">
        <div className="progress-overlay-card">
          <div className="panel-header-row">
            <div>
              <h3>{overlayTitle}</h3>
              <p className="meta-text">{overlayDescription}</p>
            </div>
            <span className="runtime-pill runtime-pill-gpu">
              {isAnalyzing ? 'Analysis' : 'Cleanup'}
            </span>
          </div>

          <div className="progress-bar-track">
            <div className="progress-bar-fill" style={{ width: `${overallProgress}%` }} />
          </div>

          <p className="meta-text progress-label">
            {liveStep ? `${formatStepLabel(liveStep.step_name)} · ${overallProgress}%` : 'Working...'}
          </p>

          <p className="meta-text">
            {isAnalyzing
              ? 'Preparing normalized audio and updating the issue report.'
              : liveStep?.message ?? 'Starting cleanup pipeline...'}
          </p>

          {!isAnalyzing && selectedRun?.steps.length ? (
            <ul className="status-list stacked run-steps progress-overlay-steps">
              {selectedRun.steps.map((step) => (
                <li key={step.id}>
                  <div>
                    <strong>{formatStepLabel(step.step_name)}</strong>
                    {liveStep &&
                    liveStep.run_id === step.run_id &&
                    liveStep.step_name === step.step_name ? (
                      <div className="meta-text">{liveStep.message}</div>
                    ) : null}
                  </div>
                  <span className="step-status">{step.status}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>
    )
  }

  function screenCompare() {
    return (
      <>
        <section className="panel screen-panel">
          <div className="panel-header-row">
            <h3>Compare</h3>
            <div className="compare-toggle-row">
              {(['original', 'preview', 'export'] as const).map((t) => (
                <button
                  key={t}
                  type="button"
                  className={
                    compareTarget === t ? 'ghost-button compare-active' : 'ghost-button'
                  }
                  onClick={() => setCompareTarget(t)}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="compare-grid">
            <article className="audio-card compare-card">
              <h4>Original</h4>
              {selectedProject ? (
                <>
                  <p className="meta-text path-wrap">
                    {selectedProject.source_file.original_path}
                  </p>
                  <audio
                    controls
                    src={toAudioSrc(selectedProject.source_file.original_path) ?? undefined}
                  />
                </>
              ) : (
                <p className="meta-text">No project selected.</p>
              )}
            </article>

            <article className="audio-card compare-card compare-card-focus">
              <h4>{compareSource.label}</h4>
              {compareSource.path ? (
                <>
                  <p className="meta-text path-wrap">{compareSource.path}</p>
                  <audio controls src={toAudioSrc(compareSource.path) ?? undefined} />
                </>
              ) : (
                <p className="meta-text">Not available yet.</p>
              )}
            </article>
          </div>
        </section>

        <section className="panel screen-panel" style={{ marginTop: '1.5rem' }}>
          <h3>All Stems</h3>
          <div className="audio-grid">
            {extraAudioAssets.map((asset) => (
              <article key={asset.id} className="audio-card">
                <h4>{assetLabel(asset.kind)}</h4>
                <p className="meta-text path-wrap">{asset.path}</p>
                <audio controls src={toAudioSrc(asset.path) ?? undefined} />
              </article>
            ))}
            {!extraAudioAssets.length ? (
              <p className="meta-text">No stem assets registered.</p>
            ) : null}
          </div>
          {normalizedAsset ? (
            <p className="meta-text path-wrap" style={{ marginTop: '1rem' }}>
              Normalized working file: {normalizedAsset.path}
            </p>
          ) : null}
          <div style={{ marginTop: '1.5rem' }}>
            <button type="button" onClick={() => setScreen('Export')}>
              Continue to Export
            </button>
            <button
              type="button"
              className="ghost-button"
              style={{ marginLeft: '0.75rem' }}
              onClick={() => void startRun()}
              disabled={isRunning || !selectedProject}
            >
              Run Again with Different Settings
            </button>
          </div>
        </section>
      </>
    )
  }

  function screenExport() {
    return (
      <section className="panel screen-panel">
        <div className="panel-header-row">
          <h3>Export</h3>
          <button
            type="button"
            onClick={() => void handleExport()}
            disabled={!selectedRun || isExporting}
          >
            {isExporting ? 'Exporting...' : 'Confirm Export'}
          </button>
        </div>

        {!selectedRun ? (
          <p className="meta-text">
            No completed run yet. Complete a cleanup run first, then return here.
          </p>
        ) : (
          <div className="repair-setup-grid">
            <article className="setup-card">
              <h4>Output Format</h4>
              <p className="meta-text">Choose the format for your final export file.</p>
              <div className="option-group">
                {(['wav', 'flac'] as const).map((fmt) => (
                  <button
                    key={fmt}
                    type="button"
                    className={
                      exportFormat === fmt ? 'option-button option-active' : 'option-button'
                    }
                    onClick={() => setExportFormat(fmt)}
                  >
                    {fmt.toUpperCase()}
                    {fmt === 'wav' ? ' · 16-bit 48kHz' : ' · Lossless'}
                  </button>
                ))}
              </div>
            </article>

            {cleanedExport ? (
              <article className="setup-card">
                <h4>Current Export</h4>
                <p className="meta-text path-wrap">{cleanedExport.path}</p>
                <p className="meta-text">Format: {cleanedExport.format.toUpperCase()}</p>
                <audio
                  controls
                  src={toAudioSrc(cleanedExport.path) ?? undefined}
                  style={{ width: '100%', marginTop: '0.75rem' }}
                />
              </article>
            ) : (
              <article className="setup-card">
                <h4>Current Export</h4>
                <p className="meta-text">Click "Confirm Export" to generate the file in the selected format.</p>
              </article>
            )}

            {exportStems && extraAudioAssets.length > 0 ? (
              <article className="setup-card">
                <h4>Stem Exports</h4>
                {extraAudioAssets.map((asset) => (
                  <p key={asset.id} className="meta-text path-wrap">
                    {assetLabel(asset.kind)}: {asset.path}
                  </p>
                ))}
              </article>
            ) : null}
          </div>
        )}
      </section>
    )
  }

  // ── Shell ──────────────────────────────────────────────────────────────────

  function renderScreen() {
    switch (screen) {
      case 'Home': return screenHome()
      case 'Analysis': return screenAnalysis()
      case 'Repair': return screenRepair()
      case 'Compare': return screenCompare()
      case 'Export': return screenExport()
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">B Audio</div>
        <nav>
          {NAV_STEPS.map((step) => (
            <button
              key={step}
              type="button"
              className={step === screen ? 'nav-item nav-item-active' : 'nav-item'}
              onClick={() => setScreen(step)}
            >
              {step}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="eyebrow">Local AI Song Cleanup</div>
            <h1>{screen}</h1>
          </div>
          <div className="status-group">
            <span>Local</span>
            <span
              className={
                status?.cuda_available ? 'runtime-pill runtime-pill-gpu' : 'runtime-pill'
              }
            >
              {runtimeLabel}
            </span>
            <span>{status?.active_run_id ? 'Run Active' : 'Idle'}</span>
            <span>{status ? 'Engine Ready' : 'Booting'}</span>
          </div>
        </header>

        {error ? <div className="banner error">{error}</div> : null}
        {message ? <div className="banner success">{message}</div> : null}

        {renderScreen()}
        {renderProgressOverlay()}
      </main>
    </div>
  )
}
