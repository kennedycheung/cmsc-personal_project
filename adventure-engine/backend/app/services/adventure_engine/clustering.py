"""Groups nearby OSM-discovered activities into coherent "adventure"
clusters, instead of scoring/ranking unrelated individual places.

Simple greedy spatial clustering: each not-yet-clustered activity becomes a
seed, and every remaining activity within CLUSTER_RADIUS_KM of that seed
joins its cluster. This is a documented simplification (a real k-means/
DBSCAN pass would produce tighter, seed-order-independent clusters) --
same "simple heuristic over real data, honestly documented" spirit as
discovery/merge.py's fuzzy-match clustering elsewhere in this app.
"""

from app.services.adventure_engine.types import AdventureCluster
from app.services.local_activities import LocalActivity
from app.services.optimizations.geo import haversine_km

CLUSTER_RADIUS_KM = 1.0


def _build_cluster(members: list[LocalActivity]) -> AdventureCluster:
    center_lat = sum(a.latitude for a in members) / len(members)
    center_lon = sum(a.longitude for a in members) / len(members)
    return AdventureCluster(
        activities=members,
        center_lat=center_lat,
        center_lon=center_lon,
        groups={a.group for a in members},
        categories={a.category for a in members},
    )


def cluster_activities(
    activities: list[LocalActivity], cluster_radius_km: float = CLUSTER_RADIUS_KM
) -> list[AdventureCluster]:
    """Returns one AdventureCluster per group of nearby activities. Nothing
    is dropped -- an activity with nothing else nearby still becomes its
    own single-activity cluster, since a genuinely standout single
    attraction (a famous landmark) is still a valid recommendation; the
    scoring stage's density/diversity factors naturally favor richer
    clusters over singletons rather than this stage silently discarding them.
    """
    remaining = list(activities)
    clusters: list[AdventureCluster] = []

    while remaining:
        seed = remaining.pop(0)
        members = [seed]
        still_remaining = []
        for activity in remaining:
            distance_km = haversine_km(seed.latitude, seed.longitude, activity.latitude, activity.longitude)
            if distance_km <= cluster_radius_km:
                members.append(activity)
            else:
                still_remaining.append(activity)
        remaining = still_remaining
        clusters.append(_build_cluster(members))

    return clusters
