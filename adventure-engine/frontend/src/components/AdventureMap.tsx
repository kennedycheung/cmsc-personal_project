import { useMemo } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useWalkingRoute } from '../hooks/useWalkingRoute';
import type { LatLon } from '../services/routing';
import type { Activity, DayItinerary, Destination } from '../services/types';

const DAY_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2'];

function dayColor(day: number): string {
  return DAY_COLORS[(day - 1) % DAY_COLORS.length];
}

function createDivIcon(html: string, size: number): L.DivIcon {
  return L.divIcon({
    html,
    className: 'adventure-map-pin',
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

const destinationIcon = createDivIcon('<div class="map-pin map-pin--destination">&#9733;</div>', 30);
const activityIcon = createDivIcon('<div class="map-pin map-pin--activity"></div>', 16);

function stopIcon(day: number, order: number): L.DivIcon {
  return createDivIcon(
    `<div class="map-pin map-pin--stop" style="background:${dayColor(day)}">${order}</div>`,
    24,
  );
}

interface DayRouteProps {
  day: DayItinerary;
}

function DayRoute({ day }: DayRouteProps) {
  const points: LatLon[] = day.activities.map((item) => ({
    lat: item.activity.latitude,
    lon: item.activity.longitude,
  }));

  const { data: routedPoints, isError } = useWalkingRoute(points);

  if (points.length < 2) {
    return null;
  }

  const usedFallback = isError || !routedPoints;
  const path: [number, number][] = (usedFallback ? points : routedPoints).map((p) => [p.lat, p.lon]);

  return (
    <Polyline
      positions={path}
      pathOptions={{ color: dayColor(day.day), weight: 4, opacity: 0.8, dashArray: usedFallback ? '8 8' : undefined }}
    />
  );
}

interface AdventureMapProps {
  destination: Destination;
  activities: Activity[];
  itineraryDays?: DayItinerary[];
}

export default function AdventureMap({ destination, activities, itineraryDays }: AdventureMapProps) {
  const center: [number, number] = [destination.latitude, destination.longitude];

  const bounds = useMemo(() => {
    const points: [number, number][] = [[destination.latitude, destination.longitude]];
    activities.forEach((activity) => points.push([activity.latitude, activity.longitude]));
    itineraryDays?.forEach((day) =>
      day.activities.forEach((item) => points.push([item.activity.latitude, item.activity.longitude])),
    );
    return points;
  }, [destination, activities, itineraryDays]);

  const hasRoutes = Boolean(itineraryDays && itineraryDays.some((day) => day.activities.length >= 2));

  return (
    <div>
      <MapContainer
        center={center}
        zoom={11}
        bounds={bounds.length > 1 ? L.latLngBounds(bounds) : undefined}
        boundsOptions={{ padding: [40, 40] }}
        scrollWheelZoom={false}
        className='map-container'
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
        />

        <Marker position={center} icon={destinationIcon}>
          <Popup>
            <strong>{destination.name}</strong>
            <br />
            {destination.country}
          </Popup>
        </Marker>

        {activities.map((activity) => (
          <Marker key={activity.id} position={[activity.latitude, activity.longitude]} icon={activityIcon}>
            <Popup>
              <strong>{activity.name}</strong>
              <br />
              {activity.category ?? 'Activity'} · {activity.price > 0 ? `$${activity.price}` : 'Free'}
            </Popup>
          </Marker>
        ))}

        {itineraryDays?.map((day) => <DayRoute key={day.day} day={day} />)}

        {itineraryDays?.flatMap((day) =>
          day.activities.map((item, index) => (
            <Marker
              key={`day-${day.day}-stop-${item.activity.id}`}
              position={[item.activity.latitude, item.activity.longitude]}
              icon={stopIcon(day.day, index + 1)}
            >
              <Popup>
                <strong>
                  Day {day.day} · Stop {index + 1}
                </strong>
                <br />
                {item.activity.name}
                <br />
                {item.start_time} – {item.end_time}
              </Popup>
            </Marker>
          )),
        )}
      </MapContainer>

      {hasRoutes && (
        <p className='map-legend'>
          Solid lines are street-network walking routes (OpenStreetMap data via OSRM); dashed lines are a
          straight-line fallback used when live routing is unavailable.
        </p>
      )}
    </div>
  );
}
