import { useMutation } from '@tanstack/react-query';

import { getActivityAlternatives } from '../services/activities';

export function useActivityAlternatives() {
  return useMutation({
    mutationFn: ({ activityId, excludeIds }: { activityId: number; excludeIds: number[] }) =>
      getActivityAlternatives(activityId, excludeIds),
  });
}
