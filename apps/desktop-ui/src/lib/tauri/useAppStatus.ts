import { useQuery } from '@tanstack/react-query'
import { getAppStatus } from './commands'

export function useAppStatus() {
  return useQuery({
    queryKey: ['status'],
    queryFn: getAppStatus,
    refetchInterval: 5000,
    retry: false,
  })
}
