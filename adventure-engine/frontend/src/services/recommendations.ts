import { apiGet } from './api';
import type { Recommendation } from './types';

export interface RecommendationParams {
  maxBudget?: number;
  interests?: string;
  topN?: number;
}

export function getRecommendations(params: RecommendationParams): Promise<Recommendation[]> {
  return apiGet<Recommendation[]>('/recommendations/', {
    max_budget: params.maxBudget,
    interests: params.interests,
    top_n: params.topN,
  });
}
