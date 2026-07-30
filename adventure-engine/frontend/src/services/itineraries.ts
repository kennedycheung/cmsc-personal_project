import { apiGet } from './api';
import type { ItineraryResponse } from './types';

export interface ItineraryParams {
  days?: number;
  budget?: number;
  interests?: string;
}

export function getItinerary(destinationId: number, params: ItineraryParams): Promise<ItineraryResponse> {
  return apiGet<ItineraryResponse>(`/itineraries/${destinationId}`, {
    days: params.days,
    budget: params.budget,
    interests: params.interests,
  });
}
