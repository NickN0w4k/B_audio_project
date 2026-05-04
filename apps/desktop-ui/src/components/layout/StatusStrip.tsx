import { useAppStore } from '../../stores/appStore'
import { RunProgress } from '../../features/runtime/RunProgress'

export function StatusStrip() {
  const { isRunning, isAnalyzing, error } = useAppStore()
  const busy = isRunning || isAnalyzing

  return (
    <footer
      className="flex items-center justify-between px-4 h-8 border-t border-[var(--color-border)] bg-[var(--color-surface)] flex-shrink-0"
      style={{ fontSize: '11px' }}
    >
      <div className="flex items-center gap-2 min-w-0">
        {error ? (
          <span className="text-[var(--color-high)] truncate">{error}</span>
        ) : busy ? (
          <RunProgress />
        ) : (
          <span className="text-[var(--color-muted)]">Ready</span>
        )}
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        <span className="text-[var(--color-border)]">B Audio</span>
      </div>
    </footer>
  )
}
