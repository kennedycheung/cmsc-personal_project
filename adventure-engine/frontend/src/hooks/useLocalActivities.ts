import { useQuery } from '@tanstack/react-query';

import { getLocalActivities } from '../services/localActivities';
import type { LocalActivitiesParams } from '../services/localActivities';

export function useLocalActivities(params: LocalActivitiesParams, enabled: boolean) {
  return useQuery({
    queryKey: ['local-activities', params],
    queryFn: () => getLocalActivities(params),
    enabled,
  });
}
