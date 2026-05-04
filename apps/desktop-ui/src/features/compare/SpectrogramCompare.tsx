import { toAudioSrc } from '../../lib/utils/format'

type Props = {
  originalPath?: string | null
  repairedPath?: string | null
}

export function SpectrogramCompare({ originalPath, repairedPath }: Props) {
  const origSrc = toAudioSrc(originalPath)
  const repSrc = toAudioSrc(repairedPath)

  if (!origSrc && !repSrc) return null

  return (
    <div className="flex flex-col gap-2">
      <h3 className="text-xs font-semibold uppercase tracking-widest text-[var(--color-muted)]">
        Spectrogram
      </h3>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">Original</span>
          {origSrc ? (
            <img
              src={origSrc}
              alt="Original spectrogram"
              className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
            />
          ) : (
            <div className="flex items-center justify-center h-24 rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)]">
              <span className="text-xs text-[var(--color-muted)]">Unavailable</span>
            </div>
          )}
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-xs text-[var(--color-muted)]">After repair</span>
          {repSrc ? (
            <img
              src={repSrc}
              alt="Post-repair spectrogram"
              className="w-full rounded-[var(--radius-md)] border border-[var(--color-border)]"
            />
          ) : (
            <div className="flex items-center justify-center h-24 rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)]">
              <span className="text-xs text-[var(--color-muted)]">Not generated yet</span>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
