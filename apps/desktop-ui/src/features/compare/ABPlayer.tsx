import { useEffect, useRef, useState } from 'react'
import WaveSurfer from 'wavesurfer.js'
import { useCompareStore } from '../../stores/compareStore'
import { Button } from '../../components/ui/Button'

type Props = {
  originalUrl: string | null
  repairedUrl: string | null
}

function IconPlay() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5,3 19,12 5,21" />
    </svg>
  )
}

function IconPause() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="4" width="4" height="16" /><rect x="14" y="4" width="4" height="16" />
    </svg>
  )
}

export function ABPlayer({ originalUrl, repairedUrl }: Props) {
  const containerRef = useRef<HTMLDivElement>(null)
  const wsRef = useRef<WaveSurfer | null>(null)
  const { abSide, toggleSide, setIsPlaying, setPlaybackPosition, isPlaying, playbackPosition } = useCompareStore()
  const [ready, setReady] = useState(false)
  const [time, setTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const prevSideRef = useRef(abSide)

  const currentUrl = abSide === 'original' ? originalUrl : repairedUrl

  useEffect(() => {
    if (!containerRef.current) return
    const ws = WaveSurfer.create({
      container: containerRef.current,
      waveColor: 'var(--color-border)',
      progressColor: 'var(--color-accent)',
      cursorColor: 'var(--color-accent)',
      height: 72,
      interact: true,
      normalize: true,
    })

    ws.on('ready', () => {
      setReady(true)
      setDuration(ws.getDuration())
    })
    ws.on('audioprocess', () => {
      setTime(ws.getCurrentTime())
      setPlaybackPosition(ws.getCurrentTime() / (ws.getDuration() || 1))
    })
    ws.on('play', () => setIsPlaying(true))
    ws.on('pause', () => setIsPlaying(false))
    ws.on('finish', () => setIsPlaying(false))

    wsRef.current = ws
    return () => { ws.destroy(); wsRef.current = null }
  }, [])

  useEffect(() => {
    if (!currentUrl || !wsRef.current) return
    const ws = wsRef.current
    const wasPlaying = ws.isPlaying()
    const pos = playbackPosition
    setReady(false)
    ws.load(currentUrl)
    ws.once('ready', () => {
      setReady(true)
      setDuration(ws.getDuration())
      ws.seekTo(Math.min(pos, 1))
      if (wasPlaying) void ws.play()
    })
  }, [currentUrl])

  useEffect(() => {
    if (prevSideRef.current !== abSide) {
      prevSideRef.current = abSide
    }
  }, [abSide])

  function togglePlay() {
    if (!wsRef.current || !ready) return
    void wsRef.current.playPause()
  }

  function formatTime(s: number) {
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col gap-3">
      {/* A/B Toggle */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => useCompareStore.getState().setAbSide('original')}
          className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors cursor-pointer ${
            abSide === 'original'
              ? 'bg-[var(--color-surface-raised)] text-[var(--color-text)] border border-[var(--color-border)]'
              : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
          }`}
        >
          A · Original
        </button>
        <button
          type="button"
          onClick={() => useCompareStore.getState().setAbSide('repaired')}
          className={`text-xs px-3 py-1.5 rounded-full font-medium transition-colors cursor-pointer ${
            abSide === 'repaired'
              ? 'bg-[var(--color-accent)]/15 text-[var(--color-accent)] border border-[var(--color-accent)]/30'
              : 'text-[var(--color-muted)] hover:text-[var(--color-text)]'
          }`}
        >
          B · Repaired
        </button>
        <button
          type="button"
          onClick={toggleSide}
          className="ml-auto text-xs text-[var(--color-muted)] hover:text-[var(--color-text)] cursor-pointer"
        >
          Switch ⇄
        </button>
      </div>

      {/* Waveform */}
      <div
        ref={containerRef}
        className="w-full rounded-[var(--radius-md)] bg-[var(--color-surface)] border border-[var(--color-border)] overflow-hidden px-3 py-2"
        style={{ minHeight: 88 }}
      />

      {/* Transport */}
      <div className="flex items-center gap-3">
        <Button
          variant="secondary"
          onClick={togglePlay}
          disabled={!ready || !currentUrl}
          className="w-10 h-10 p-0"
        >
          {isPlaying ? <IconPause /> : <IconPlay />}
        </Button>
        <span className="text-xs text-[var(--color-muted)] font-mono tabular-nums">
          {formatTime(time)} / {formatTime(duration)}
        </span>
        {!currentUrl ? (
          <span className="text-xs text-[var(--color-muted)] ml-auto">
            {abSide === 'original' ? 'Original not available' : 'Repaired audio not available'}
          </span>
        ) : null}
      </div>
    </div>
  )
}
