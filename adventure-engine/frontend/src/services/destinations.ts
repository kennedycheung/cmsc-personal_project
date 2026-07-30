import { apiGet } from './api';
import type { Destination } from './types';

export interface DestinationSearchParams {
  region?: string;
  minBudget?: number;
  maxBudget?: number;
  interests?: string;
}

export function listDestinations(params?: { skip?: number; limit?: number }): Promise<Destination[]> {
  return apiGet<Destination[]>('/destinations/', params);
}

export function getDestination(id: number): Promise<Destination> {
  return apiGet<Destination>(`/destinations/${id}`);
}

export function searchDestinations(params: DestinationSearchParams): Promise<Destination[]> {
  return apiGet<Destination[]>('/destinations/search', {
    region: params.region,
    min_budget: params.minBudget,
    max_budget: params.maxBudget,
    interests: params.interests,
  });
}
