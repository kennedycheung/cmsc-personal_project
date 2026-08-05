import { apiGet, apiPost } from './api';
import type { DayItinerary, ItineraryResponse } from './types';

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

export interface RegenerateDayParams {
  day: number;
  days: number;
  lockedActivityIds: number[];
  budget?: number;
  interests?: string;
}

export function regenerateItineraryDay(
  destinationId: number,
  params: RegenerateDayParams,
): Promise<DayItinerary> {
  return apiPost<DayItinerary>(`/itineraries/${destinationId}/regenerate-day`, {
    day: params.day,
    days: params.days,
    locked_activity_ids: params.lockedActivityIds,
    budget: params.budget,
    interests: params.interests,
  });
}
