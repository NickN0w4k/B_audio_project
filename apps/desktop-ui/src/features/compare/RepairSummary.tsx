import { useNavigate } from 'react-router-dom'
import { Badge, severityFromString } from '../../components/ui/Badge'
import { Button } from '../../components/ui/Button'
import type { AnalysisReport, RunSummary } from '../../lib/tauri/types'

type Props = {
  report: AnalysisReport | null | undefined
  run: RunSummary | null | undefined
  projectId: string
  runId: string
}

export function RepairSummary({ report, run, projectId, runId }: Props) {
  const navigate = useNavigate()

  if (!report) return null

  const issueCount = report.issues.length
  const highCount = report.issues.filter((i) => i.severity === 'high').length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)] mb-1">
            Repair Summary
          </h3>
          <p className="text-sm text-[var(--color-text)]">
            {issueCount} issue{issueCount !== 1 ? 's' : ''} addressed
            {highCount > 0 ? `, ${highCount} high severity` : ''}
          </p>
          {run?.intensity ? (
            <p className="text-xs text-[var(--color-muted)] mt-0.5">
              Intensity: {run.intensity}
            </p>
          ) : null}
        </div>
        <Button
          variant="primary"
          onClick={() => navigate(`/export/${projectId}/run/${runId}`)}
        >
          Export
        </Button>
      </div>

      <div className="flex flex-wrap gap-2">
        {report.issues.map((issue) => (
          <div
            key={issue.id}
            className="flex items-center gap-2 rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] px-3 py-1.5"
          >
            <Badge severity={severityFromString(issue.severity)}>{issue.severity}</Badge>
            <span className="text-xs text-[var(--color-text)]">{issue.artifact_title ?? issue.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
