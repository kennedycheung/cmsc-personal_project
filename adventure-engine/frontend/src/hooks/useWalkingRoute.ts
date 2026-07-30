import { useQuery } from '@tanstack/react-query';

import { getWalkingRoute } from '../services/routing';
import type { LatLon } from '../services/routing';

export function useWalkingRoute(points: LatLon[]) {
  return useQuery({
    queryKey: ['walking-route', points],
    queryFn: () => getWalkingRoute(points),
    enabled: points.length >= 2,
    retry: 1,
    staleTime: 5 * 60_000,
  });
}
