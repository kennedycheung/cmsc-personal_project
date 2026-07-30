import { apiGet } from './api';
import type { Activity } from './types';

export function listActivities(params?: { skip?: number; limit?: number }): Promise<Activity[]> {
  return apiGet<Activity[]>('/activities/', params);
}

export function getActivitiesForDestination(destinationId: number): Promise<Activity[]> {
  return apiGet<Activity[]>(`/activities/destination/${destinationId}`);
}
