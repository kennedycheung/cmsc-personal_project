import { apiPost } from './api';
import type { AdventureRecommendationResponse } from './types';

export interface AdventureRecommendationParams {
  latitude: number;
  longitude: number;
  locationLabel: string;
  radiusKm?: number;
  interests?: string[];
  maxBudget?: number;
}

export function recommendAdventures(
  params: AdventureRecommendationParams,
): Promise<AdventureRecommendationResponse> {
  return apiPost<AdventureRecommendationResponse>('/adventures/recommend', {
    latitude: params.latitude,
    longitude: params.longitude,
    location_label: params.locationLabel,
    radius_km: params.radiusKm,
    interests: params.interests,
    max_budget: params.maxBudget,
  });
}
