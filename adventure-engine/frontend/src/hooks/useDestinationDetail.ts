import { useQuery } from '@tanstack/react-query';

import { getActivitiesForDestination } from '../services/activities';
import { getDestination } from '../services/destinations';

export function useDestination(destinationId: number) {
  return useQuery({
    queryKey: ['destination', destinationId],
    queryFn: () => getDestination(destinationId),
    enabled: Number.isFinite(destinationId),
  });
}

export function useDestinationActivities(destinationId: number) {
  return useQuery({
    queryKey: ['activities', destinationId],
    queryFn: () => getActivitiesForDestination(destinationId),
    enabled: Number.isFinite(destinationId),
  });
}
