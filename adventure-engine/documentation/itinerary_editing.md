# Map selection UX and interactive itinerary editing

Implemented in [`frontend/src/components/AdventureMap.tsx`](../frontend/src/components/AdventureMap.tsx),
[`frontend/src/components/ItineraryDayEditor.tsx`](../frontend/src/components/ItineraryDayEditor.tsx),
[`frontend/src/pages/DestinationPage.tsx`](../frontend/src/pages/DestinationPage.tsx),
and two new backend endpoints in
[`backend/app/api/routes/activities.py`](../backend/app/api/routes/activities.py) and
[`backend/app/api/routes/itineraries.py`](../backend/app/api/routes/itineraries.py).

## Overview

Two related problems with the original map/itinerary experience:

1. The map always rendered every stored activity for a destination as a
   marker, with no link between the activity list and the map, and no way to
   tell which markers belonged to a generated itinerary versus the wider
   pool of destination activities.
2. A generated itinerary was a dead end — read-only JSON rendered as static
   text, with no way to reorder stops, swap one out, remove it, or ask for a
   different plan for just one day without regenerating the whole trip.

## Map selection

`AdventureMap` is now a controlled component (`DestinationPage` owns the
state): `selectedActivityId`, `onSelectActivity`, `showAllActivities`.

- **Hidden by default, shown on demand**: once an itinerary exists, the
  map's primary markers are the itinerary's own stops (already numbered by
  day). The full destination activity list only appears as dimmed,
  secondary markers when the "Show nearby activities" checkbox is checked —
  before any itinerary is generated, all activities show unconditionally
  (there's nothing else to show yet).
- **Click-to-select, bidirectional**: activity cards and itinerary list
  items in `DestinationPage` are clickable, setting `selectedActivityId`;
  markers on the map gain `eventHandlers.click` doing the same in reverse.
  Either direction flies the map to that point (`MapFlyToController`, a
  small internal component using react-leaflet's `useMap()` — not used
  anywhere in this codebase before) and opens that marker's popup via a
  `Record<number, L.Marker>` ref map.
- The pre-existing accessibility fallback (a `role="img"` wrapper with the
  same information duplicated as text) is unchanged — none of this
  interactivity removes that text-equivalent path.

## Editable itineraries

Itinerary editing happens entirely in **client-side React state**, not a
persisted draft on the backend. `DestinationPage` seeds
`editableDays` from the itinerary query's response via a `useEffect`, then
every edit (reorder, remove, swap, regenerate-day) mutates that local copy.
This matches how the rest of the app treats itineraries — `SavedAdventure`
(see [`authentication.md`](authentication.md)) already only persists a
frozen snapshot for logged-in users, and there's no concept of an anonymous
draft-itinerary row anywhere else in the schema. Introducing one just for
mid-edit state would be a new persistence concept for something that's
naturally ephemeral until the user chooses to save it.

`ItineraryDayEditor` (one per day) owns:

- **Reorder** — drag-and-drop via `@dnd-kit/core` + `@dnd-kit/sortable` (a
  new dependency; there was no drag-and-drop library in this codebase
  before). On drop, the day's activity order updates and the displayed
  day total re-derives from that new order — see "Real travel time" below.
- **Remove** — filters the activity out of the day's list.
- **Swap** — calls `GET /api/activities/{id}/alternatives`, which ranks
  other activities in the same destination by tag overlap with the target
  (the same set-intersection idea as `recommendation.py`'s interest
  matching, just activity-to-activity) and excludes activities already used
  elsewhere in the trip. Picking a result replaces that stop in place,
  keeping its scheduled time slot.
- **Regenerate day** — calls `POST /api/itineraries/{destination_id}/regenerate-day`
  with every activity id used on the trip's *other* days as
  `locked_activity_ids`, so the rebuilt day can't duplicate them. This reuses
  `itinerary.py`'s own single-day scheduling logic (`_build_day`, extracted
  from `generate_itinerary` for this purpose) — same scoring, same
  diversity/time-of-day/neighborhood behavior as the original generation.

None of these are optimistic-cache mutations against the itinerary query —
they're plain `useMutation` calls (the first use of React Query mutations in
this codebase; every prior hook was a `useQuery`) whose results get folded
into `editableDays` by the caller.

## Real travel time on reorder

The original `total_travel_minutes` per day is a sum of each activity's own
flat `travel_minutes` field (a placeholder, not a real route — see
[`itinerary_algorithm.md`](itinerary_algorithm.md)). Once a day is
reordered, that flat sum is no longer an honest travel estimate for the new
order. `ItineraryDayEditor` re-runs the existing `useWalkingRoute` hook
(originally built only to draw the map's route polylines in
`AdventureMap`) against the day's current stop order and displays its real
OSRM-derived duration instead, falling back to the flat sum if OSRM is
unavailable. `getWalkingRoute` (`services/routing.ts`)
was extended to return `{ points, durationMinutes }` instead of just
`points` to make this duration available; `AdventureMap`'s route polylines
were updated for the new shape but are otherwise unaffected.

## What's deliberately not built

- **Freestanding "add a new stop"** (not replacing an existing one) isn't a
  separate action — "swap" already covers adding a different activity into
  an existing slot. A dedicated "append a stop to this day" control would
  need a variant of the alternatives endpoint that doesn't rank against a
  specific target activity, which didn't seem worth a second endpoint for
  this pass.
- **Persisting mid-edit state** for anonymous users (e.g. surviving a page
  reload) isn't implemented, consistent with the "client state only until
  saved" design above.
