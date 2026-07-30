import { apiGet } from './api';
import type { Recommendation } from './types';

export interface RecommendationParams {
  maxBudget?: number;
  interests?: string;
  topN?: number;
  originLat?: number;
  originLon?: number;
  timeBucket?: string;
  travelScope?: string;
  maxDistanceKm?: number;
}

export function getRecommendations(params: RecommendationParams): Promise<Recommendation[]> {
  return apiGet<Recommendation[]>('/recommendations/', {
    max_budget: params.maxBudget,
    interests: params.interests,
    top_n: params.topN,
    origin_lat: params.originLat,
    origin_lon: params.originLon,
    time_bucket: params.timeBucket,
    travel_scope: params.travelScope,
    max_distance_km: params.maxDistanceKm,
  });
}
