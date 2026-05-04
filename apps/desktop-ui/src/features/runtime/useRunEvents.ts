import { useEffect } from 'react'
import { listen } from '@tauri-apps/api/event'
import { isTauri } from '@tauri-apps/api/core'
import { useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAppStore } from '../../stores/appStore'
import type { RunStatusEvent, RunStepEvent } from '../../lib/tauri/types'

export function useRunEvents() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { setRunning, setLiveStep, setError, selectedProjectId } = useAppStore()

  useEffect(() => {
    if (!isTauri()) return

    let unsubStatus: (() => void) | undefined
    let unsubStep: (() => void) | undefined

    async function bind() {
      unsubStatus = await listen<RunStatusEvent>('run-status', async (event) => {
        const { run_id, status, message } = event.payload

        setRunning(status === 'running')

        if (status !== 'running') setLiveStep(null)

        if (status === 'failed') {
          setError(message ?? `Run ${run_id} failed. Check details and try again.`)
        }

        await queryClient.invalidateQueries({ queryKey: ['status'] })
        await queryClient.invalidateQueries({ queryKey: ['projects'] })
        await queryClient.invalidateQueries({ queryKey: ['project', selectedProjectId] })
        await queryClient.invalidateQueries({ queryKey: ['run', run_id] })

        if (status === 'completed' && selectedProjectId) {
          navigate(`/compare/${selectedProjectId}/run/${run_id}`)
        }
      })

      unsubStep = await listen<RunStepEvent>('run-step', async (event) => {
        setLiveStep(event.payload)
        await queryClient.invalidateQueries({ queryKey: ['run', event.payload.run_id] })
      })
    }

    void bind()
    return () => {
      unsubStatus?.()
      unsubStep?.()
    }
  }, [selectedProjectId])
}
