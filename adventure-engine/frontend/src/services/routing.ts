export interface LatLon {
  lat: number;
  lon: number;
}

export interface WalkingRoute {
  points: LatLon[];
  durationMinutes: number;
}

// Public OSRM demo server, foot-routing profile. No API key, no Google Maps.
// Best-effort only: no uptime guarantee, so callers must fall back to a
// straight line (and the flat travel_minutes estimate) between stops if this fails.
const OSRM_BASE_URL = 'https://router.project-osrm.org/route/v1/foot';

export async function getWalkingRoute(points: LatLon[]): Promise<WalkingRoute> {
  if (points.length < 2) {
    return { points, durationMinutes: 0 };
  }

  const coordinates = points.map((point) => `${point.lon},${point.lat}`).join(';');
  const url = `${OSRM_BASE_URL}/${coordinates}?overview=full&geometries=geojson`;

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`OSRM routing request failed with status ${response.status}`);
  }

  const data = await response.json();
  const route = data?.routes?.[0];
  const geometry = route?.geometry?.coordinates;
  if (data.code !== 'Ok' || !Array.isArray(geometry)) {
    throw new Error('OSRM returned no usable route');
  }

  return {
    points: (geometry as [number, number][]).map(([lon, lat]) => ({ lat, lon })),
    durationMinutes: Math.round((route.duration ?? 0) / 60),
  };
}
