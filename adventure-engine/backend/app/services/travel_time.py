"""Maps a traveler's available time to how far it's realistic to go.

Every distance here is a documented assumption, not a measured fact -- same
spirit as optimizations/constants.py. See
documentation/progressive_recommendation_flow.md for the full rationale.
"""

from enum import Enum


class TimeBucket(str, Enum):
    TWO_HOURS = "two_hours"
    HALF_DAY = "half_day"
    FULL_DAY = "full_day"
    WEEKEND = "weekend"
    THREE_TO_FOUR_DAYS = "three_to_four_days"
    FIVE_TO_SEVEN_DAYS = "five_to_seven_days"
    ONE_WEEK = "one_week"
    TWO_WEEKS = "two_weeks"


# Buckets under a day are treated as a "local adventure" -- no flights or
# hotels, just nearby real-world activities (see local_activities.py).
LOCAL_ADVENTURE_BUCKETS = {TimeBucket.TWO_HOURS, TimeBucket.HALF_DAY, TimeBucket.FULL_DAY}

# Default max straight-line distance (km) a destination search is
# constrained to, before any "stay local / day trip / overnight / anywhere"
# override is applied. `None` means unconstrained (still ranked by
# AdventureScore, just not distance-filtered).
DEFAULT_MAX_DISTANCE_KM: dict[TimeBucket, float | None] = {
    TimeBucket.TWO_HOURS: 15.0,
    TimeBucket.HALF_DAY: 15.0,
    TimeBucket.FULL_DAY: 150.0,
    TimeBucket.WEEKEND: 800.0,
    TimeBucket.THREE_TO_FOUR_DAYS: 2000.0,
    TimeBucket.FIVE_TO_SEVEN_DAYS: None,
    TimeBucket.ONE_WEEK: None,
    TimeBucket.TWO_WEEKS: None,
}

# Suggested itinerary length (days) per bucket, for pre-filling the
# eventual itinerary-generation step. Ranges use their lower bound.
SUGGESTED_TRIP_DAYS: dict[TimeBucket, int] = {
    TimeBucket.TWO_HOURS: 1,
    TimeBucket.HALF_DAY: 1,
    TimeBucket.FULL_DAY: 1,
    TimeBucket.WEEKEND: 2,
    TimeBucket.THREE_TO_FOUR_DAYS: 3,
    TimeBucket.FIVE_TO_SEVEN_DAYS: 5,
    TimeBucket.ONE_WEEK: 7,
    TimeBucket.TWO_WEEKS: 14,
}


class TravelScope(str, Enum):
    STAY_LOCAL = "stay_local"
    DAY_TRIP = "day_trip"
    OVERNIGHT_TRIP = "overnight_trip"
    ANYWHERE_WITHIN_BUDGET = "anywhere_within_budget"


# "Stay local" overrides the bucket's own distance with this tight radius,
# regardless of how much time is available -- the point of choosing it is
# explicitly not going far. "Anywhere within budget" removes the distance
# constraint entirely and leans on AdventureScore + budget alone.
STAY_LOCAL_OVERRIDE_KM = 50.0


def is_local_adventure(bucket: TimeBucket) -> bool:
    return bucket in LOCAL_ADVENTURE_BUCKETS


def max_distance_km(bucket: TimeBucket) -> float | None:
    return DEFAULT_MAX_DISTANCE_KM[bucket]


def resolve_max_distance_km(bucket: TimeBucket, scope: TravelScope | None) -> float | None:
    """The actual distance constraint for a recommendation search, given a
    time bucket and (for >=1-day trips) the traveler's stay-local/day-trip/
    overnight/anywhere choice from step 3 of the flow.
    """
    if scope == TravelScope.STAY_LOCAL:
        return STAY_LOCAL_OVERRIDE_KM
    if scope == TravelScope.ANYWHERE_WITHIN_BUDGET:
        return None
    return DEFAULT_MAX_DISTANCE_KM[bucket]


def suggested_trip_days(bucket: TimeBucket) -> int:
    return SUGGESTED_TRIP_DAYS[bucket]
