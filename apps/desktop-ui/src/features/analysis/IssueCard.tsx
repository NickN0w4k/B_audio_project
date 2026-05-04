import { Badge, severityFromString } from '../../components/ui/Badge'
import type { AnalysisIssue } from '../../lib/tauri/types'

type Props = {
  issue: AnalysisIssue
  expanded?: boolean
}

export function IssueCard({ issue, expanded }: Props) {
  return (
    <div className="rounded-[var(--radius-lg)] border border-[var(--color-border)] bg-[var(--color-surface)] p-4 flex flex-col gap-2">
      <div className="flex items-center gap-2">
        <Badge severity={severityFromString(issue.severity)}>{issue.severity}</Badge>
        <h4 className="text-sm font-medium text-[var(--color-text)]">
          {issue.artifact_title ?? issue.label}
        </h4>
      </div>
      <p className="text-sm text-[var(--color-muted)] leading-relaxed">{issue.description}</p>
      {expanded && (issue.detection || issue.repair) ? (
        <div className="flex flex-col gap-1 mt-1 pt-2 border-t border-[var(--color-border-subtle)]">
          {issue.detection ? (
            <p className="text-xs text-[var(--color-muted)]">
              <span className="text-[var(--color-text)] font-medium">Detection: </span>
              {issue.detection}
            </p>
          ) : null}
          {issue.repair ? (
            <p className="text-xs text-[var(--color-muted)]">
              <span className="text-[var(--color-text)] font-medium">Repair: </span>
              {issue.repair}
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}
