import { useQuery } from '@tanstack/react-query';

import { getItinerary } from '../services/itineraries';
import type { ItineraryParams } from '../services/itineraries';

export function useItinerary(destinationId: number, params: ItineraryParams, enabled: boolean) {
  return useQuery({
    queryKey: ['itinerary', destinationId, params],
    queryFn: () => getItinerary(destinationId, params),
    enabled: enabled && Number.isFinite(destinationId),
  });
}
