import { useQuery } from '@tanstack/react-query'
import { getProject } from './commands'

export function useProject(projectId: string | null) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => getProject(projectId!),
    enabled: !!projectId,
    retry: false,
  })
}
