import type { AnalysisIssue } from '../../lib/tauri/types'
import { IssueCard } from './IssueCard'

const CONFIDENCE_THRESHOLD = 0.3

type Props = {
  issues: AnalysisIssue[]
}

export function IssueSummary({ issues }: Props) {
  const visible = issues
    .filter((i) => (i.confidence ?? 1) >= CONFIDENCE_THRESHOLD)
    .sort((a, b) => (b.confidence ?? 0) - (a.confidence ?? 0))

  if (!visible.length) {
    return (
      <p className="text-sm text-[var(--color-muted)]">No significant issues detected.</p>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
        {visible.length} issue{visible.length !== 1 ? 's' : ''} detected
      </h3>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {visible.map((issue) => (
          <IssueCard key={issue.id} issue={issue} />
        ))}
      </div>
    </div>
  )
}
