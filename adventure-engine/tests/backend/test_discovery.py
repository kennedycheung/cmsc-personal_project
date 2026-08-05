"""The Activity Discovery Engine calls SerpAPI, a real paid/keyed service --
httpx.get is mocked here the same way it's mocked for every other external
API in this suite (see documentation/testing.md). SERPAPI_KEY is set to a
fake value for these tests via monkeypatch on the shared `settings`
singleton, restored automatically after each test.
"""

from unittest.mock import patch

import pytest
from app.core.config import settings as app_settings
from app.services.discovery import buckets as buckets_module
from app.services.discovery import merge as merge_module
from app.services.discovery import query_builder
from app.services.discovery import ranking as ranking_module
from app.services.discovery import routing as routing_module
from app.services.discovery.enrichment import MAX_ENRICHED_CANDIDATES, enrich_candidates
from app.services.discovery.interests import classify_interests
from app.services.discovery.serpapi_client import SerpApiError, serpapi_search
from app.services.discovery.types import CandidateAttraction, DiscoveryRequest, EnrichedAttraction, RawResult


@pytest.fixture(autouse=True)
def _serpapi_key(monkeypatch):
    monkeypatch.setattr(app_settings, "serpapi_key", "test-key")


@pytest.fixture(autouse=True)
def _clear_serpapi_cache():
    from app.services.discovery import serpapi_client

    serpapi_client._cache.clear()
    yield
    serpapi_client._cache.clear()


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def _sample_request() -> DiscoveryRequest:
    return DiscoveryRequest(latitude=35.7148, longitude=139.7967, location_label="Tokyo", interests=["history"])


# --- Step 1: interest classification ---------------------------------------


def test_classify_interests_prefers_structured_tags():
    assert classify_interests("something about food", ["history", "not_a_real_category"]) == ["history"]


def test_classify_interests_falls_back_to_keyword_matching():
    # Order follows the _KEYWORDS table's own iteration order, not the input text's.
    assert classify_interests("looking for a museum and some cheap food", None) == ["food", "museums", "budget"]


def test_classify_interests_empty_when_nothing_matches():
    assert classify_interests("asdfghjkl", None) == []


# --- Step 2: per-engine query building --------------------------------------


def test_query_builder_produces_distinct_queries_per_engine():
    request = _sample_request()
    interests = ["history"]

    events = query_builder.build_google_events_params(request, interests)
    maps = query_builder.build_google_maps_params(request, interests)
    tripadvisor = query_builder.build_tripadvisor_params(request, interests)
    yelp = query_builder.build_yelp_params(request, interests)

    query_strings = {events["q"], maps["q"], tripadvisor["q"], yelp["find_desc"]}
    # Every engine gets its own tailored query -- not the same string reused.
    assert len(query_strings) == 4
    assert "find_loc" in yelp and "find_desc" in yelp
    assert "ll" in maps


# --- Step 4: fuzzy merge -----------------------------------------------------


def test_merge_candidates_collapses_near_duplicate_names():
    results = [
        RawResult(engine="tripadvisor", name="Senso-ji", latitude=35.7148, longitude=139.7967, rating=4.5),
        RawResult(engine="yelp", name="Sensoji Temple", latitude=35.71485, longitude=139.79675, rating=4.6),
        RawResult(engine="google_maps", name="Sensō-ji", latitude=35.71481, longitude=139.79668, rating=4.4),
    ]

    candidates = merge_module.merge_candidates(results)

    assert len(candidates) == 1
    assert candidates[0].engines == {"tripadvisor", "yelp", "google_maps"}


def test_merge_candidates_keeps_distinct_far_apart_results():
    results = [
        RawResult(engine="tripadvisor", name="Senso-ji", latitude=35.7148, longitude=139.7967),
        RawResult(engine="yelp", name="Tokyo Tower", latitude=35.6586, longitude=139.7454),
    ]

    candidates = merge_module.merge_candidates(results)

    assert len(candidates) == 2


def test_merge_candidates_skips_results_without_coordinates():
    results = [RawResult(engine="google_events", name="Some Festival", latitude=None, longitude=None)]
    assert merge_module.merge_candidates(results) == []


# --- Step 5: capped enrichment ------------------------------------------------


def test_enrichment_caps_at_max_enriched_candidates():
    candidates = [
        CandidateAttraction(
            name=f"Place {i}",
            address=None,
            latitude=35.0,
            longitude=139.0,
            external_ids={"tripadvisor": str(i)},
            engines={"tripadvisor"},
            sources=[],
            rating=4.0,
            review_count=100 - i,  # descending popularity
        )
        for i in range(MAX_ENRICHED_CANDIDATES + 5)
    ]

    with patch("app.services.discovery.enrichment.serpapi_search") as mock_search:
        mock_search.return_value = {"hours": {"monday": "09:00-17:00"}}
        enriched, _warnings = enrich_candidates(candidates)

    assert len(enriched) == len(candidates)
    enriched_with_hours = [e for e in enriched if e.hours is not None]
    # 2 calls per enriched candidate (place + reviews); only the top
    # MAX_ENRICHED_CANDIDATES by popularity should have been enriched.
    assert len(enriched_with_hours) == MAX_ENRICHED_CANDIDATES


# --- Step 6: ranking ----------------------------------------------------------


def _make_enriched(categories: list[str], rating: float | None = 4.0, review_count: int = 100) -> EnrichedAttraction:
    candidate = CandidateAttraction(
        name="Test Place",
        address=None,
        latitude=35.7148,
        longitude=139.7967,
        external_ids={},
        engines={"google_maps"},
        sources=[],
        rating=rating,
        review_count=review_count,
        categories=categories,
    )
    return EnrichedAttraction(candidate=candidate, rating=rating, review_count=review_count, categories=categories)


def test_ranking_rewards_interest_match():
    request = _sample_request()
    matching = _make_enriched(["history"])
    non_matching = _make_enriched(["shopping"])

    ranked = ranking_module.rank_attractions([matching, non_matching], request, ["history"])

    assert ranked[0].attraction.categories == ["history"]
    assert ranked[0].score > ranked[1].score


def test_ranking_neutral_interest_score_without_requested_interests():
    request = _sample_request()
    attraction = _make_enriched(["history"])
    ranked = ranking_module.rank_attractions([attraction], request, [])
    assert ranked[0].score_breakdown["interest_match"] == 0.5


# --- Step 7: buckets -----------------------------------------------------------


def test_is_free_predicate_matches_only_zero_price_level():
    request = _sample_request()
    free_attraction = _make_enriched(["nature"])
    free_attraction.price_level = 0
    paid_attraction = _make_enriched(["nature"])
    paid_attraction.price_level = 3

    ranked = ranking_module.rank_attractions([free_attraction, paid_attraction], request, [])
    free_ranked = next(r for r in ranked if r.attraction.price_level == 0)
    paid_ranked = next(r for r in ranked if r.attraction.price_level == 3)

    assert buckets_module._is_free(free_ranked) is True
    assert buckets_module._is_free(paid_ranked) is False


def test_is_hidden_gem_predicate_requires_high_rating_and_low_reviews():
    # Tested directly against the predicate (as this repo's other tests do
    # for pure scoring helpers, e.g. itinerary.py's _score_activity) rather
    # than through the full build_recommendation_buckets pipeline, since
    # higher-priority buckets (Best Overall/Best Value) can legitimately
    # claim every candidate in a tiny pool before Best Hidden Gem's turn --
    # exactly the "not already used by a higher-priority bucket" behavior
    # from the approved design, which a 2-candidate pool isn't large enough
    # to exercise meaningfully.
    request = _sample_request()
    hidden_gem = _make_enriched(["history"], rating=4.8, review_count=10)
    popular = _make_enriched(["history"], rating=4.2, review_count=5000)

    ranked = ranking_module.rank_attractions([hidden_gem, popular], request, [])
    gem_ranked = next(r for r in ranked if r.attraction.review_count == 10)
    popular_ranked = next(r for r in ranked if r.attraction.review_count == 5000)

    assert buckets_module._is_hidden_gem(gem_ranked) is True
    assert buckets_module._is_hidden_gem(popular_ranked) is False


# --- Step 8: routing -----------------------------------------------------------


def test_build_route_chains_pairwise_legs():
    a = _make_enriched(["history"])
    b = _make_enriched(["food"])
    c = _make_enriched(["nature"])

    directions_payload = {
        "directions": [{"formatted_distance": "1.2 km", "formatted_duration": "15 mins", "distance": 1200, "duration": 900}]
    }

    with patch.object(routing_module, "serpapi_search", return_value=directions_payload) as mock_search:
        route = routing_module.build_route([a, b, c])

    assert mock_search.call_count == 2  # one call per consecutive pair, not one big multi-stop call
    assert route is not None
    assert len(route.legs) == 2
    assert route.total_duration_minutes == pytest.approx(30.0)


def test_build_route_none_for_fewer_than_two_stops():
    assert routing_module.build_route([_make_enriched(["history"])]) is None


# --- serpapi_client caching ------------------------------------------------


def test_serpapi_search_caches_repeat_calls():
    with patch("app.services.discovery.serpapi_client.httpx.get", return_value=_FakeResponse({"ok": True})) as mock_get:
        serpapi_search("google_maps", {"q": "test"})
        serpapi_search("google_maps", {"q": "test"})

    assert mock_get.call_count == 1


def test_serpapi_search_raises_on_api_reported_error():
    with patch("app.services.discovery.serpapi_client.httpx.get", return_value=_FakeResponse({"error": "bad key"})):
        with pytest.raises(SerpApiError):
            serpapi_search("google_maps", {"q": "test-error"})


# --- Full pipeline / endpoint ------------------------------------------------


def _fake_serpapi_get(url, params=None, timeout=None):
    engine = (params or {}).get("engine")
    payloads = {
        # Shapes below match real, live-verified SerpAPI responses (see
        # documentation/activity_discovery_engine.md), not guessed ones --
        # e.g. venues/TripAdvisor/Yelp search results carry no coordinates
        # at all, TripAdvisor's list key is "places" not "results", and
        # Yelp's categories are {"title": ...} objects, not plain strings.
        "google_events": {
            "events_results": [
                {
                    "title": "Sanja Matsuri Festival",
                    "venue": {"name": "Sensoji Temple", "rating": 4.5, "reviews": 20},
                    "date": {"start_date": "2026-08-10"},
                }
            ]
        },
        "google_maps": {
            "local_results": [
                {
                    "title": "Sensoji Temple",
                    "address": "2 Chome-3-1 Asakusa",
                    "gps_coordinates": {"latitude": 35.7148, "longitude": 139.7967},
                    "place_id": "gm-1",
                    "rating": 4.6,
                    "reviews": 5000,
                    "price": "$",
                    "types": ["history", "temple"],
                }
            ]
        },
        "tripadvisor": {
            "places": [
                {
                    "title": "Senso-ji",
                    "location": "Asakusa, Tokyo",
                    "place_id": 187147,
                    "rating": 4.5,
                    "reviews": 12000,
                    "place_type": "history",
                }
            ]
        },
        "yelp": {
            "organic_results": [
                {
                    "title": "Local Ramen Shop",
                    "neighborhoods": "Asakusa",
                    "place_ids": ["ramen-shop-1"],
                    "rating": 4.2,
                    "reviews": 30,
                    "price": "$",
                    "categories": [{"title": "food"}],
                }
            ]
        },
        "tripadvisor_place": {"hours": {"monday": "06:00-17:00"}, "price_level": "$"},
        "tripadvisor_reviews": {"reviews": [{"snippet": "Beautiful historic temple."}]},
        "yelp_place": {"place_results": {"hours": {"monday": "11:00-22:00"}, "images": ["https://example.com/ramen.jpg"]}},
        "yelp_reviews": {"reviews": [{"comment": {"text": "Great ramen!"}}]},
        "google_maps_directions": {
            "directions": [{"formatted_distance": "0.5 km", "formatted_duration": "6 mins", "distance": 500, "duration": 360}]
        },
    }
    return _FakeResponse(payloads.get(engine, {}))


def test_discover_endpoint_full_pipeline(client):
    with patch("app.services.discovery.serpapi_client.httpx.get", side_effect=_fake_serpapi_get):
        response = client.post(
            "/api/discover/",
            json={
                "latitude": 35.7148,
                "longitude": 139.7967,
                "location_label": "Tokyo",
                "interests": ["history", "food"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert len(body["buckets"]["best_overall"]) >= 1
    # Sensoji/Senso-ji from 3 different engines should have merged into one entry.
    overall_names = [a["name"] for a in body["buckets"]["best_overall"]]
    sensoji_mentions = [n for n in overall_names if "ensō" in n.lower() or "enso" in n.lower()]
    assert len(sensoji_mentions) <= 1


def test_discover_endpoint_503_when_not_configured(client, monkeypatch):
    monkeypatch.setattr(app_settings, "serpapi_key", "")
    response = client.post(
        "/api/discover/", json={"latitude": 35.7, "longitude": 139.8, "location_label": "Tokyo"}
    )
    assert response.status_code == 503
