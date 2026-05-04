import { useQuery } from '@tanstack/react-query'
import { getRun } from './commands'

export function useRun(runId: string | null) {
  return useQuery({
    queryKey: ['run', runId],
    queryFn: () => getRun(runId!),
    enabled: !!runId,
    retry: false,
  })
}
