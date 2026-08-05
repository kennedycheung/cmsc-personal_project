import { useMutation } from '@tanstack/react-query';

import { regenerateItineraryDay } from '../services/itineraries';
import type { RegenerateDayParams } from '../services/itineraries';

export function useRegenerateDay(destinationId: number) {
  return useMutation({
    mutationFn: (params: RegenerateDayParams) => regenerateItineraryDay(destinationId, params),
  });
}
