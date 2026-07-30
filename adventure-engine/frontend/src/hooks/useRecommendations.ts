import { useQuery } from '@tanstack/react-query';

import { getRecommendations } from '../services/recommendations';
import type { RecommendationParams } from '../services/recommendations';

export function useRecommendations(params: RecommendationParams, enabled: boolean = true) {
  return useQuery({
    queryKey: ['recommendations', params],
    queryFn: () => getRecommendations(params),
    enabled,
  });
}
