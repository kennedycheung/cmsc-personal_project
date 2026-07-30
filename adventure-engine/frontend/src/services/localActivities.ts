import { apiGet } from './api';

export interface LocalActivity {
  name: string;
  description: string | null;
  group: string;
  category: string;
  location: string;
  latitude: number;
  longitude: number;
  distance_km: number;
  duration_hours: number;
  is_outdoor: boolean;
  opening_time: string | null;
  closing_time: string | null;
}

export interface LocalActivitiesResponse {
  origin_label: string;
  radius_km: number;
  groups: Record<string, LocalActivity[]>;
}

export interface LocalActivitiesParams {
  latitude: number;
  longitude: number;
  originLabel?: string;
  radiusKm?: number;
  groups?: string;
}

export function getLocalActivities(params: LocalActivitiesParams): Promise<LocalActivitiesResponse> {
  return apiGet<LocalActivitiesResponse>('/local-activities/', {
    latitude: params.latitude,
    longitude: params.longitude,
    origin_label: params.originLabel,
    radius_km: params.radiusKm,
    groups: params.groups,
  });
}
