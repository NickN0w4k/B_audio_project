import { useAppStore } from '../../stores/appStore'
import { useAppStatus } from '../../lib/tauri/useAppStatus'
import { useProject } from '../../lib/tauri/useProject'

export function TopBar() {
  const { selectedProjectId } = useAppStore()
  const { data: status } = useAppStatus()
  const { data: project } = useProject(selectedProjectId)

  const projectName = project?.project.name ?? null
  const hasGpu = status?.cuda_available ?? false
  const gpuName = status?.gpu_name ?? 'GPU'

  return (
    <header className="flex items-center justify-between px-4 h-11 border-b border-[var(--color-border)] bg-[var(--color-surface)] flex-shrink-0">
      <div className="flex items-center gap-3">
        <span className="text-xs font-semibold tracking-widest text-[var(--color-muted)] uppercase">
          B Audio
        </span>
        {projectName ? (
          <>
            <span className="text-[var(--color-border)]">/</span>
            <span className="text-sm text-[var(--color-text)] truncate max-w-64">{projectName}</span>
          </>
        ) : null}
      </div>

      <div className="flex items-center gap-2">
        {status ? (
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              hasGpu
                ? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]'
                : 'bg-[var(--color-border)] text-[var(--color-muted)]'
            }`}
          >
            {hasGpu ? gpuName : 'CPU Only'}
          </span>
        ) : (
          <span className="text-xs text-[var(--color-muted)]">Booting…</span>
        )}
      </div>
    </header>
  )
}
