from app.services.travel_time import (
    TimeBucket,
    is_local_adventure,
    max_distance_km,
    suggested_trip_days,
)


def test_local_adventure_buckets_under_a_day():
    assert is_local_adventure(TimeBucket.TWO_HOURS)
    assert is_local_adventure(TimeBucket.HALF_DAY)
    assert is_local_adventure(TimeBucket.FULL_DAY)
    assert not is_local_adventure(TimeBucket.WEEKEND)
    assert not is_local_adventure(TimeBucket.TWO_WEEKS)


def test_max_distance_grows_with_time():
    assert max_distance_km(TimeBucket.TWO_HOURS) < max_distance_km(TimeBucket.FULL_DAY)
    assert max_distance_km(TimeBucket.FULL_DAY) < max_distance_km(TimeBucket.WEEKEND)
    assert max_distance_km(TimeBucket.WEEKEND) < max_distance_km(TimeBucket.THREE_TO_FOUR_DAYS)


def test_longer_buckets_are_unconstrained():
    assert max_distance_km(TimeBucket.FIVE_TO_SEVEN_DAYS) is None
    assert max_distance_km(TimeBucket.ONE_WEEK) is None
    assert max_distance_km(TimeBucket.TWO_WEEKS) is None


def test_suggested_trip_days_covers_every_bucket():
    for bucket in TimeBucket:
        assert suggested_trip_days(bucket) >= 1
