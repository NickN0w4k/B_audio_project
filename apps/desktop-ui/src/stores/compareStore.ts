import { create } from 'zustand'

type CompareStore = {
  abSide: 'original' | 'repaired'
  playbackPosition: number
  isPlaying: boolean

  setAbSide: (side: 'original' | 'repaired') => void
  setPlaybackPosition: (pos: number) => void
  setIsPlaying: (v: boolean) => void
  toggleSide: () => void
}

export const useCompareStore = create<CompareStore>((set, get) => ({
  abSide: 'repaired',
  playbackPosition: 0,
  isPlaying: false,

  setAbSide: (side) => set({ abSide: side }),
  setPlaybackPosition: (pos) => set({ playbackPosition: pos }),
  setIsPlaying: (v) => set({ isPlaying: v }),
  toggleSide: () => set({ abSide: get().abSide === 'original' ? 'repaired' : 'original' }),
}))
