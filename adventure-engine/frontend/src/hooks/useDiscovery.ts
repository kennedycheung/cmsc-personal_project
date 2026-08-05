import { useMutation } from '@tanstack/react-query';

import { discoverActivities } from '../services/discovery';

export function useDiscovery() {
  return useMutation({
    mutationFn: discoverActivities,
  });
}
