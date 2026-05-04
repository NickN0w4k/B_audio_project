import { Badge } from '../../components/ui/Badge'
import type { AnalysisReport } from '../../lib/tauri/types'

type Props = {
  report: AnalysisReport | null | undefined
}

export function PresetSelector({ report }: Props) {
  if (!report) return null

  const preset = report.recommended_preset ?? 'AI Song Cleanup'
  const modules = report.planned_repair_modules ?? []

  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] px-5 py-4 flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <Badge severity="accent">{preset}</Badge>
        <span className="text-xs text-[var(--color-muted)]">Preset</span>
      </div>
      {modules.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {modules.map((mod) => (
            <span
              key={mod}
              className="text-xs rounded px-2 py-0.5 bg-[var(--color-surface-raised)] text-[var(--color-muted)] border border-[var(--color-border)]"
            >
              {mod}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  )
}
