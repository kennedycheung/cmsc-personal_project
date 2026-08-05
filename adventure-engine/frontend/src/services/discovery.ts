import { apiPost } from './api';
import type { DiscoveryResponse } from './types';

export interface DiscoveryRequestParams {
  latitude: number;
  longitude: number;
  locationLabel: string;
  interests?: string[];
  freeText?: string;
  maxBudget?: number;
}

export function discoverActivities(params: DiscoveryRequestParams): Promise<DiscoveryResponse> {
  return apiPost<DiscoveryResponse>('/discover/', {
    latitude: params.latitude,
    longitude: params.longitude,
    location_label: params.locationLabel,
    interests: params.interests,
    free_text: params.freeText,
    max_budget: params.maxBudget,
  });
}
