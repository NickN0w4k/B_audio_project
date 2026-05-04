import { useAppStore } from '../../stores/appStore'
import { formatStepLabel } from '../../lib/utils/format'

export function RunProgress() {
  const { isRunning, isAnalyzing, liveStep } = useAppStore()

  if (!isRunning && !isAnalyzing) return null

  const label = isAnalyzing
    ? 'Analyzing signal'
    : liveStep
      ? formatStepLabel(liveStep.step_name)
      : 'Starting…'

  const pct = liveStep ? Math.round(liveStep.progress * 100) : 0

  return (
    <div className="flex items-center gap-3 min-w-0">
      <span className="text-[var(--color-muted)] text-xs truncate">{label}</span>
      {isRunning && liveStep ? (
        <div className="w-24 h-1 rounded-full bg-[var(--color-border)] overflow-hidden flex-shrink-0">
          <div
            className="h-full bg-[var(--color-accent)] transition-all duration-300"
            style={{ width: `${pct}%` }}
          />
        </div>
      ) : null}
      {isRunning && liveStep ? (
        <span className="text-[var(--color-muted)] text-xs flex-shrink-0">{pct}%</span>
      ) : null}
    </div>
  )
}
