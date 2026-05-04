import { convertFileSrc, isTauri } from '@tauri-apps/api/core'

export function toAudioSrc(path?: string | null): string | null {
  if (!path) return null
  if (isTauri()) return convertFileSrc(path)
  return `file:///${path.replace(/\\/g, '/')}`
}

export function formatDuration(sec?: number | null): string {
  if (sec == null) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

export function formatHz(hz?: number | null): string {
  if (hz == null) return '—'
  return hz >= 1000 ? `${(hz / 1000).toFixed(1)} kHz` : `${hz} Hz`
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

export function formatStepLabel(stepName: string): string {
  const labels: Record<string, string> = {
    normalize: 'Normalizing audio',
    analyze: 'Analyzing signal',
    separate_stems: 'Separating stems',
    repair_vocals: 'Repairing vocals',
    repair_music: 'Repairing music',
    reconstruct: 'Reconstructing mix',
    export: 'Exporting final file',
  }
  return labels[stepName] ?? stepName.split('_').map((p) => p.charAt(0).toUpperCase() + p.slice(1)).join(' ')
}
