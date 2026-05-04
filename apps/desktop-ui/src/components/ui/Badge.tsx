import { cn } from '../../lib/utils/cn'

type Severity = 'high' | 'mid' | 'low' | 'neutral' | 'accent'

const colors: Record<Severity, string> = {
  high: 'bg-[var(--color-high)]/15 text-[var(--color-high)]',
  mid: 'bg-[var(--color-mid)]/15 text-[var(--color-mid)]',
  low: 'bg-[var(--color-low)]/15 text-[var(--color-low)]',
  neutral: 'bg-[var(--color-border)] text-[var(--color-muted)]',
  accent: 'bg-[var(--color-accent)]/15 text-[var(--color-accent)]',
}

type BadgeProps = {
  severity?: Severity
  children: React.ReactNode
  className?: string
}

export function Badge({ severity = 'neutral', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium uppercase tracking-wide',
        colors[severity],
        className,
      )}
    >
      {children}
    </span>
  )
}

export function severityFromString(s?: string | null): Severity {
  if (s === 'high') return 'high'
  if (s === 'medium' || s === 'mid') return 'mid'
  if (s === 'low') return 'low'
  return 'neutral'
}
