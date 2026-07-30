import { useQuery } from '@tanstack/react-query';

import { resolveLocation } from '../services/geocode';

export function useGeocode(query: string, enabled: boolean) {
  return useQuery({
    queryKey: ['geocode', query],
    queryFn: () => resolveLocation(query),
    enabled: enabled && query.trim().length > 0,
    retry: false,
  });
}
