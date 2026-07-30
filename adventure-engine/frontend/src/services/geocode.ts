import { apiGet } from './api';

export interface GeocodeResult {
  latitude: number;
  longitude: number;
  label: string;
  country: string | null;
}

export function resolveLocation(query: string): Promise<GeocodeResult> {
  return apiGet<GeocodeResult>('/geocode/', { query });
}
