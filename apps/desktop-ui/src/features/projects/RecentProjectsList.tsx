import { useNavigate } from 'react-router-dom'
import { useProjects } from '../../lib/tauri/useProjects'
import { useAppStore } from '../../stores/appStore'
import { Badge, severityFromString } from '../../components/ui/Badge'
import { formatDate } from '../../lib/utils/format'
import { Spinner } from '../../components/ui/Spinner'

function statusSeverity(status: string) {
  if (status === 'analyzed' || status === 'completed') return 'low'
  if (status === 'importing' || status === 'analyzing') return 'mid'
  return 'neutral'
}

function nextRoute(status: string, id: string) {
  if (status === 'completed' || status === 'analyzed') return `/analysis/${id}`
  return `/analysis/${id}`
}

export function RecentProjectsList() {
  const navigate = useNavigate()
  const { setSelectedProjectId } = useAppStore()
  const { data: projects, isLoading } = useProjects()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Spinner />
      </div>
    )
  }

  if (!projects?.length) {
    return (
      <p className="text-sm text-[var(--color-muted)] py-4">No projects yet. Import a file above to get started.</p>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
      {projects.map((project) => (
        <button
          key={project.id}
          type="button"
          onClick={() => {
            setSelectedProjectId(project.id)
            navigate(nextRoute(project.status, project.id))
          }}
          className="text-left rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 hover:border-[var(--color-accent)]/40 hover:bg-[var(--color-surface-raised)] transition-colors cursor-pointer"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <p className="text-sm font-medium text-[var(--color-text)] truncate">{project.name}</p>
            <Badge severity={statusSeverity(project.status)}>{project.status}</Badge>
          </div>
          {project.source_filename ? (
            <p className="text-xs text-[var(--color-muted)] truncate mb-1">{project.source_filename}</p>
          ) : null}
          <p className="text-xs text-[var(--color-border)]">{formatDate(project.updated_at)}</p>
        </button>
      ))}
    </div>
  )
}
