import { ImportArea } from './ImportArea'
import { RecentProjectsList } from './RecentProjectsList'
import { useAppStore } from '../../stores/appStore'

export function HomeScreen() {
  const { error, clearError } = useAppStore()

  return (
    <div className="max-w-3xl mx-auto flex flex-col gap-8">
      {error ? (
        <div className="flex items-start justify-between gap-3 rounded-[var(--radius-md)] bg-[var(--color-high)]/10 border border-[var(--color-high)]/30 px-4 py-3">
          <p className="text-sm text-[var(--color-high)]">{error}</p>
          <button
            type="button"
            onClick={clearError}
            className="text-[var(--color-high)] text-xs opacity-60 hover:opacity-100 flex-shrink-0 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      ) : null}

      <section className="flex flex-col gap-3">
        <ImportArea />
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
          Recent Projects
        </h2>
        <RecentProjectsList />
      </section>
    </div>
  )
}
