import { cn } from '../../lib/utils/cn'

type Intensity = 'light' | 'medium' | 'strong'

const descriptions: Record<Intensity, string> = {
  light: 'Gentler corrections. Best when the track is close and you want minimal change.',
  medium: 'Balanced default. Fixes common AI artifacts without over-processing.',
  strong: 'Deeper corrections. Best for obvious artifacts — may shift the original tone.',
}

type Props = {
  value: Intensity
  onChange: (v: Intensity) => void
  recommended?: Intensity | null
}

export function IntensityPicker({ value, onChange, recommended }: Props) {
  const levels: Intensity[] = ['light', 'medium', 'strong']

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        {levels.map((lvl) => (
          <button
            key={lvl}
            type="button"
            onClick={() => onChange(lvl)}
            className={cn(
              'flex-1 rounded-[var(--radius-md)] border px-3 py-2.5 text-sm font-medium transition-colors cursor-pointer relative',
              value === lvl
                ? 'border-[var(--color-accent)] bg-[var(--color-accent)]/10 text-[var(--color-accent)]'
                : 'border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-muted)] hover:text-[var(--color-text)] hover:border-[var(--color-muted)]',
            )}
          >
            {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
            {recommended === lvl ? (
              <span className="absolute -top-1.5 left-1/2 -translate-x-1/2 text-[9px] font-semibold uppercase tracking-wide text-[var(--color-accent)] bg-[var(--color-bg)] px-1 rounded">
                rec
              </span>
            ) : null}
          </button>
        ))}
      </div>
      <p className="text-xs text-[var(--color-muted)] leading-relaxed">{descriptions[value]}</p>
    </div>
  )
}
