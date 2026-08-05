import { useEffect, useMemo, useRef } from 'react';
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import { useWalkingRoute } from '../hooks/useWalkingRoute';
import type { LatLon } from '../services/routing';
import type { Activity, DayItinerary, Destination } from '../services/types';

const DAY_COLORS = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2'];
const SELECTED_ZOOM = 15;

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

function activityIcon(dimmed: boolean, selected: boolean): L.DivIcon {
  const classes = ['map-pin', dimmed ? 'map-pin--activity-dimmed' : 'map-pin--activity'];
  if (selected) classes.push('map-pin--selected');
  return createDivIcon(`<div class="${classes.join(' ')}"></div>`, selected ? 20 : 16);
}

function stopIcon(day: number, order: number, selected: boolean): L.DivIcon {
  const classes = ['map-pin', 'map-pin--stop'];
  if (selected) classes.push('map-pin--selected');
  return createDivIcon(
    `<div class="${classes.join(' ')}" style="background:${dayColor(day)}">${order}</div>`,
    selected ? 28 : 24,
  );
}

interface MapFlyToControllerProps {
  target: LatLon | null;
}

function MapFlyToController({ target }: MapFlyToControllerProps) {
  const map = useMap();

  useEffect(() => {
    if (target) {
      map.flyTo([target.lat, target.lon], SELECTED_ZOOM);
    }
  }, [map, target]);

  return null;
}

interface DayRouteProps {
  day: DayItinerary;
}

function DayRoute({ day }: DayRouteProps) {
  const points: LatLon[] = day.activities.map((item) => ({
    lat: item.activity.latitude,
    lon: item.activity.longitude,
  }));

  const { data: route, isError } = useWalkingRoute(points);

  if (points.length < 2) {
    return null;
  }

  const usedFallback = isError || !route;
  const path: [number, number][] = (usedFallback ? points : route.points).map((p) => [p.lat, p.lon]);

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
  selectedActivityId?: number | null;
  onSelectActivity?: (id: number) => void;
  showAllActivities?: boolean;
}

export default function AdventureMap({
  destination,
  activities,
  itineraryDays,
  selectedActivityId = null,
  onSelectActivity,
  showAllActivities = false,
}: AdventureMapProps) {
  const center: [number, number] = [destination.latitude, destination.longitude];
  const markerRefs = useRef<Record<number, L.Marker>>({});

  // Once an itinerary exists, the itinerary's own stop markers (below) are
  // the primary view -- the full destination activity list only overlays as
  // dimmed, secondary markers when explicitly requested, so the map isn't
  // cluttered with every activity by default.
  const hasItinerary = Boolean(itineraryDays && itineraryDays.length > 0);
  const shownActivities = !hasItinerary || showAllActivities ? activities : [];

  const bounds = useMemo(() => {
    const points: [number, number][] = [[destination.latitude, destination.longitude]];
    shownActivities.forEach((activity) => points.push([activity.latitude, activity.longitude]));
    itineraryDays?.forEach((day) =>
      day.activities.forEach((item) => points.push([item.activity.latitude, item.activity.longitude])),
    );
    return points;
  }, [destination, shownActivities, itineraryDays]);

  const flyToTarget = useMemo<LatLon | null>(() => {
    if (selectedActivityId == null) return null;
    const fromItinerary = itineraryDays
      ?.flatMap((day) => day.activities)
      .find((item) => item.activity.id === selectedActivityId)?.activity;
    const fromActivities = activities.find((activity) => activity.id === selectedActivityId);
    const match = fromItinerary ?? fromActivities;
    return match ? { lat: match.latitude, lon: match.longitude } : null;
  }, [selectedActivityId, itineraryDays, activities]);

  useEffect(() => {
    if (selectedActivityId != null) {
      markerRefs.current[selectedActivityId]?.openPopup();
    }
  }, [selectedActivityId, flyToTarget]);

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

        <MapFlyToController target={flyToTarget} />

        <Marker position={center} icon={destinationIcon}>
          <Popup>
            <strong>{destination.name}</strong>
            <br />
            {destination.country}
          </Popup>
        </Marker>

        {shownActivities.map((activity) => (
          <Marker
            key={activity.id}
            position={[activity.latitude, activity.longitude]}
            icon={activityIcon(hasItinerary, activity.id === selectedActivityId)}
            eventHandlers={{ click: () => onSelectActivity?.(activity.id) }}
            ref={(instance) => {
              if (instance) markerRefs.current[activity.id] = instance;
            }}
          >
            <Popup>
              <strong>{activity.name}</strong>
              <br />
              {activity.category ?? 'Activity'} · {activity.price > 0 ? `$${activity.price}` : 'Free'}
              {activity.location && (
                <>
                  <br />
                  {activity.location}
                </>
              )}
            </Popup>
          </Marker>
        ))}

        {itineraryDays?.map((day) => <DayRoute key={day.day} day={day} />)}

        {itineraryDays?.flatMap((day) =>
          day.activities.map((item, index) => (
            <Marker
              key={`day-${day.day}-stop-${item.activity.id}`}
              position={[item.activity.latitude, item.activity.longitude]}
              icon={stopIcon(day.day, index + 1, item.activity.id === selectedActivityId)}
              eventHandlers={{ click: () => onSelectActivity?.(item.activity.id) }}
              ref={(instance) => {
                if (instance) markerRefs.current[item.activity.id] = instance;
              }}
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
