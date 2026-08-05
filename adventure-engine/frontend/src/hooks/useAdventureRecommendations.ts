import { useMutation } from '@tanstack/react-query';

import { recommendAdventures } from '../services/adventures';

export function useAdventureRecommendations() {
  return useMutation({
    mutationFn: recommendAdventures,
  });
}
