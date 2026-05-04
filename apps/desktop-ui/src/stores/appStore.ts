import { create } from 'zustand'
import type { RunStepEvent } from '../lib/tauri/types'

type Intensity = 'light' | 'medium' | 'strong'

type AppStore = {
  selectedProjectId: string | null
  selectedRunId: string | null
  isImporting: boolean
  isAnalyzing: boolean
  isRunning: boolean
  isExporting: boolean
  liveStep: RunStepEvent | null
  error: string | null

  // Repair settings (persist across screens)
  intensity: Intensity
  exportStems: boolean
  applyFinishing: boolean
  gpuEnabled: boolean
  exportFormat: 'wav' | 'flac'

  setSelectedProjectId: (id: string | null) => void
  setSelectedRunId: (id: string | null) => void
  setImporting: (v: boolean) => void
  setAnalyzing: (v: boolean) => void
  setRunning: (v: boolean) => void
  setExporting: (v: boolean) => void
  setLiveStep: (step: RunStepEvent | null) => void
  setError: (err: string | null) => void
  clearError: () => void
  setIntensity: (v: Intensity) => void
  setExportStems: (v: boolean) => void
  setApplyFinishing: (v: boolean) => void
  setGpuEnabled: (v: boolean) => void
  setExportFormat: (v: 'wav' | 'flac') => void
}

export const useAppStore = create<AppStore>((set) => ({
  selectedProjectId: null,
  selectedRunId: null,
  isImporting: false,
  isAnalyzing: false,
  isRunning: false,
  isExporting: false,
  liveStep: null,
  error: null,
  intensity: 'medium',
  exportStems: false,
  applyFinishing: false,
  gpuEnabled: true,
  exportFormat: 'wav',

  setSelectedProjectId: (id) => set({ selectedProjectId: id }),
  setSelectedRunId: (id) => set({ selectedRunId: id }),
  setImporting: (v) => set({ isImporting: v }),
  setAnalyzing: (v) => set({ isAnalyzing: v }),
  setRunning: (v) => set({ isRunning: v }),
  setExporting: (v) => set({ isExporting: v }),
  setLiveStep: (step) => set({ liveStep: step }),
  setError: (err) => set({ error: err }),
  clearError: () => set({ error: null }),
  setIntensity: (v) => set({ intensity: v }),
  setExportStems: (v) => set({ exportStems: v }),
  setApplyFinishing: (v) => set({ applyFinishing: v }),
  setGpuEnabled: (v) => set({ gpuEnabled: v }),
  setExportFormat: (v) => set({ exportFormat: v }),
}))
