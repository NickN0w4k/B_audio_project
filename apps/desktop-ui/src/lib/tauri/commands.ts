import { invoke as tauriInvoke, isTauri } from '@tauri-apps/api/core'
import type {
  AppStatus,
  ProjectSummary,
  ProjectDetail,
  RunDetail,
  StartRunRequest,
  ExportRequest,
  ExportResult,
  AnalyzeProjectResult,
} from './types'

async function invoke<T>(command: string, args?: Record<string, unknown>): Promise<T> {
  if (!isTauri()) throw new Error('Tauri runtime not available.')
  return tauriInvoke<T>(command, args)
}

export const initApp = () => invoke<void>('init_app')

export const getAppStatus = () => invoke<AppStatus>('get_app_status')

export const listProjects = () =>
  invoke<{ projects: ProjectSummary[] }>('list_projects').then((r) => r.projects)

export const getProject = (projectId: string) =>
  invoke<ProjectDetail>('get_project', { projectId })

export const getRun = (runId: string) =>
  invoke<RunDetail>('get_run', { runId })

export const openSourceFileDialog = () =>
  invoke<{ path?: string | null }>('open_source_file_dialog').then((r) => r.path ?? null)

export const importProject = (sourcePath: string) =>
  invoke<{ project: ProjectDetail }>('import_project', {
    input: { source_path: sourcePath },
  }).then((r) => r.project)

export const analyzeProject = (projectId: string) =>
  invoke<AnalyzeProjectResult>('analyze_project', { request: { project_id: projectId } })

export const startProjectRun = (request: StartRunRequest) =>
  invoke<{ run_id: string; status: string }>('start_project_run', { request })

export const exportAudio = (request: ExportRequest) =>
  invoke<ExportResult>('export_audio', { request })
