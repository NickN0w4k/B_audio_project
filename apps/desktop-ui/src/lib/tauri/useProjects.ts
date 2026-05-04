import { useQuery } from '@tanstack/react-query'
import { listProjects } from './commands'

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
    retry: false,
  })
}
