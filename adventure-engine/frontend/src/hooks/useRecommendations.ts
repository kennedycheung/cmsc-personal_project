import { useQuery } from '@tanstack/react-query';

import { getRecommendations } from '../services/recommendations';
import type { RecommendationParams } from '../services/recommendations';

export function useRecommendations(params: RecommendationParams) {
  return useQuery({
    queryKey: ['recommendations', params],
    queryFn: () => getRecommendations(params),
  });
}
