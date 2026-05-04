export type AppStatus = {
  app_name: string
  storage_dir: string
  database_path: string
  engine_entry: string
  python_command: string
  cuda_available: boolean
  gpu_name?: string | null
  active_run_id?: string | null
}

export type ProjectSummary = {
  id: string
  name: string
  status: string
  created_at: string
  updated_at: string
  source_filename?: string | null
}

export type SourceFileRecord = {
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

export type RunSummary = {
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

export type RunStepSummary = {
  id: string
  run_id: string
  step_name: string
  status: string
  started_at?: string | null
  finished_at?: string | null
  metrics_json?: string | null
}

export type AssetRecord = {
  id: string
  project_id: string
  run_id?: string | null
  kind: string
  path: string
  metadata_json?: string | null
}

export type ExportRecord = {
  id: string
  run_id: string
  format: string
  path: string
  created_at: string
}

export type RunDetail = {
  run: RunSummary
  steps: RunStepSummary[]
  assets: AssetRecord[]
  exports: ExportRecord[]
}

export type AnalysisIssue = {
  id: string
  label: string
  severity: string
  confidence?: number | null
  description: string
  artifact_title?: string | null
  detection?: string | null
  repair?: string | null
}

export type AnalysisReport = {
  id: string
  project_id: string
  report_path: string
  schema_version?: string | null
  compatibility_notice?: string | null
  recommended_preset?: string | null
  suggested_intensity?: string | null
  planned_repair_modules: string[]
  runtime_estimate_sec?: number | null
  overall_confidence?: number | null
  estimated_cutoff_hz?: number | null
  spectrogram_path?: string | null
  summary_json?: string | null
  created_at: string
  issues: AnalysisIssue[]
}

export type ProjectDetail = {
  project: ProjectSummary
  source_file: SourceFileRecord
  analysis_report?: AnalysisReport | null
  latest_run?: RunSummary | null
}

export type StartRunRequest = {
  project_id: string
  preset: string
  intensity: string
  apply_light_finishing: boolean
  export_stems: boolean
  gpu_enabled: boolean
}

export type ExportRequest = {
  run_id: string
  project_id: string
  format: string
}

export type ExportResult = {
  export_id: string
  path: string
  format: string
}

export type AnalyzeProjectResult = {
  analysis_report_path: string
  normalized_path: string
}

export type RunStatusEvent = {
  run_id: string
  status: string
  message?: string | null
}

export type RunStepEvent = {
  run_id: string
  status: string
  step_name: string
  message: string
  progress: number
}
