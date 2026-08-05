# Adventure Recommendation Engine

Implemented in [`backend/app/services/adventure_engine/`](../backend/app/services/adventure_engine/)
and exposed via `POST /api/adventures/recommend`.

## Why this exists

Every other recommendation path in this app either ranks among 64 fixed
seeded destinations (`recommendation.py`) or (optionally, behind a paid
key) aggregates SerpAPI results (`services/discovery/`). This engine is
different: it needs **zero paid/keyed APIs** — only OpenStreetMap/
Nominatim/Overpass and this app's existing free Open-Meteo integration —
and instead of returning "go to Milwaukee," it answers the traveler's
actual questions: *why this place, why now, what's actually there, what
will it cost, how do I get there, how should I spend my time.*

## Pipeline

```
Location Resolution  (caller-supplied lat/lon + label; see services/geocoding.py)
        v
Candidate Generation + Nearby Attraction Discovery  (real OSM data)
        v
Activity Clustering  (group nearby finds into coherent "adventures")
        v
Scoring  (8 independent, reusable factors, each with a reason)
        v
Ranking  (sort by weighted total score)
        v
Recommendation Generation  (deterministic, template-based reasoning)
        v
Itinerary Generation  (named time slots for the winning cluster)
```

### Candidate generation + nearby attraction discovery

Reuses `services/local_activities.py::discover_local_activities` directly
— the same live, non-persisted Overpass query machinery already built for
the progressive recommendation flow's local-adventure mode (see
[`progressive_recommendation_flow.md`](progressive_recommendation_flow.md)).
Nothing new was built here on purpose: "Build reusable search utilities
instead of one-off implementations" meant reusing what's already real and
tested, not writing a second Overpass client.

### Activity clustering (`clustering.py`)

Groups nearby discovered activities into `AdventureCluster`s instead of
scoring unrelated individual places one at a time — "coherent experiences"
rather than a flat list. Simple greedy spatial clustering (each
not-yet-clustered activity becomes a seed; anything within
`CLUSTER_RADIUS_KM` of it joins): a documented simplification, not a real
k-means/DBSCAN pass, same "simple heuristic over real data" spirit as
`services/discovery/merge.py`'s fuzzy-match clustering elsewhere in this
app. Nothing is dropped — a standout single attraction with nothing nearby
still becomes its own single-activity cluster.

### Scoring (`scoring.py`)

Eight independent, pure-function scorers, each producing a `ScoreReason`
(score + weight + a real, template-generated explanation — never
LLM/fabricated text). Adding a ninth factor means adding one function and
one line in `SCORE_WEIGHTS`, not touching the orchestrator.

| Factor | Weight | What it measures |
|---|---|---|
| `distance` | 0.15 | Haversine distance from the request origin to the cluster |
| `density` | 0.20 | How many attractions are clustered together |
| `diversity` | 0.15 | How many of the 7 OSM groups (nature/food/culture/entertainment/shopping/outdoor_recreation/relaxation) the cluster spans |
| `walkability` | 0.15 | Average pairwise distance between cluster members, converted to an estimated walking time |
| `interest_match` | 0.15 | Proportion of requested interests (group or category names) found in the cluster's tags |
| `budget_fit` | 0.05 | **Always neutral (0.5)** — OSM carries no real pricing data, and this engine does not fabricate one. See "Known limitation" below |
| `weather_fit` | 0.10 | Reuses `weather.py`'s real `is_bad_weather`/`is_good_weather` against the cluster's outdoor/indoor mix |
| `confidence` | 0.05 | What fraction of the cluster's activities have a description, hours, and address — i.e. how complete the real data actually is |

`confidence` is also surfaced as its own top-level field on each
recommendation (not just folded into the weighted score), since "how sure
are we" is a distinct question from "how good is it."

### Recommendation generation (`reasoning.py`)

`build_summary` turns the ranked `ScoreReason`s into one deterministic
sentence per top factor — "Chicago: 4 attractions clustered together;
Stops average ~8 min apart on foot." This is string templating over real
computed values, not generated text; it can never claim something the
scoring didn't actually find.

### Itinerary generation (`itinerary.py`)

Named time slots (`morning`, `late_morning`, `lunch`, `afternoon`,
`dinner`, `evening`) instead of a flat activity list, each slot filled
only when a cluster activity's OSM group/category genuinely matches that
slot's documented hints (`SLOT_HINTS`) — **a slot with nothing suitable is
skipped, not force-filled** with an arbitrary leftover. An earlier version
of this file did force-fill (a theater once landed in the "lunch" slot
because nothing else was left when that slot's turn came); it was fixed to
skip instead and let genuinely-unmatched activities fall through to
`optional_activities`, which is exactly what that field is for. Walking
time between consecutive stops uses the same documented assumption walking
speed as the `walkability` scoring factor (real OSRM routing is reserved
for the one itinerary a user actually views, the same way the frontend
already does for stored-Activity itineraries — running OSRM per candidate
cluster during ranking would mean dozens of route calls per request for
clusters nobody ends up seeing).

## Known limitation: budget scoring

OpenStreetMap does not carry real pricing data. Rather than estimate a
fake dollar figure (explicitly against this app's "do not fabricate"
principle), `budget_fit` always scores neutral and says so in its reason
text. A future `RestaurantProvider`/paid-data integration (see below)
could genuinely improve this.

## Future provider interfaces (`providers.py`)

Clean `Protocol` definitions for `FlightProvider`, `HotelProvider`,
`TransitProvider`, `EventProvider`, `RestaurantProvider` — every concrete
implementation today raises `ProviderUnavailableError`. Swapping in a real
integration later means replacing one entry in the `PROVIDERS` registry,
not changing `engine.py`. Deliberately **not** placeholder'd, because a
real implementation already exists and is reused directly instead:

- **Weather** — `services/weather.py` (Open-Meteo, real, free). `scoring.py`
  calls `is_bad_weather`/`is_good_weather` directly; no placeholder needed.
- **Basic restaurant/cafe discovery** — OSM via `local_activities.py`'s
  "food" group is already real data. `RestaurantProvider` is specifically
  for *premium* data (ratings, reviews, reservations) beyond bare
  existence/location, which OSM doesn't carry.
- **Multi-source aggregation** — a SerpAPI-based engine (Google Events/
  Maps/Directions, TripAdvisor, Yelp) already exists as a separate,
  optional feature (see
  [`activity_discovery_engine.md`](activity_discovery_engine.md)).
  It's intentionally not wired into this engine's core scoring — this
  engine works with **zero** paid keys, which is the whole point.
  `EventProvider` represents a *dedicated* ticketed-events API
  (Ticketmaster/Eventbrite) as a distinct future path, not a duplicate.

## API

`POST /api/adventures/recommend`

```json
{
  "latitude": 41.8781,
  "longitude": -87.6298,
  "location_label": "Chicago",
  "radius_km": 15.0,
  "interests": ["museum"],
  "max_budget": null
}
```

Returns up to 10 ranked recommendations, each with `total_score`,
`confidence`, the full `reasons` breakdown, a `summary` sentence, the
underlying `activities`, and (for multi-stop clusters) a full `itinerary`.

## Live-verified

Tested against real Overpass/Open-Meteo data for Chicago — real clusters
(a 4-stop cluster spanning a pizzeria, a sightseeing tour, a theater, and a
bookstore; correctly separated from more distant single-stop finds), real
reasoning text, and a real named-slot itinerary once the force-fill bug
above was caught and fixed. Every automated test still mocks the HTTP
layer (`tests/backend/test_adventure_engine.py`), same convention as this
app's other external-API tests.
