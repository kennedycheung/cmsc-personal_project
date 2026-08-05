"""Step 5: enriches the top-ranked merged candidates with Place/Review
details from TripAdvisor and Yelp. Capped to MAX_ENRICHED_CANDIDATES so a
single discovery request doesn't spend unbounded SerpAPI calls -- combined
with serpapi_client's response cache, this is the primary cost control for
this feature (a paid API, unlike everything else this app calls).

Google Maps results aren't separately enriched: SerpAPI's google_maps
search results already include rating/price/hours inline, unlike
TripAdvisor/Yelp's thinner search results which need the dedicated Place/
Reviews engines for that detail (see
documentation/activity_discovery_engine.md).
"""

import math

from app.services.discovery.serpapi_client import SerpApiError, serpapi_search
from app.services.discovery.types import CandidateAttraction, EnrichedAttraction

MAX_ENRICHED_CANDIDATES = 20
REVIEW_SUMMARY_SNIPPETS = 5
REVIEW_SNIPPET_LENGTH = 120


def _popularity_proxy(candidate: CandidateAttraction) -> float:
    """Cheap pre-rank used only to decide which candidates are worth
    spending enrichment calls on -- not the final ranking (see ranking.py)."""
    rating = candidate.rating or 0.0
    review_count = candidate.review_count or 0
    return rating * math.log1p(review_count) + len(candidate.engines)


def _enrich_tripadvisor(candidate: CandidateAttraction) -> dict:
    place_id = candidate.external_ids.get("tripadvisor")
    if not place_id:
        return {}

    details: dict = {}
    try:
        # NOTE: tripadvisor_place consistently timed out during live testing
        # (60s+, no response), so this parsing is best-effort/unverified --
        # every field access below is a no-op rather than a crash if the
        # shape turns out to differ once this engine is reachable again.
        # tripadvisor_reviews and the search-tier engine (see
        # search_engines.py) *were* verified live and use flat top-level
        # fields (no nested "location"/"business" wrapper), so this assumes
        # the same flat shape here.
        place = serpapi_search("tripadvisor_place", {"place_id": place_id})
        if place.get("hours"):
            details["hours"] = place["hours"]
        if place.get("price_level"):
            details["price_level"] = len(place["price_level"])
        if place.get("photos"):
            details["photos"] = [p.get("image") for p in place["photos"] if isinstance(p, dict) and p.get("image")]
    except SerpApiError:
        pass

    try:
        reviews = serpapi_search(
            "tripadvisor_reviews", {"place_id": place_id, "limit": REVIEW_SUMMARY_SNIPPETS}
        )
        # Verified live: the review text field is "snippet", not "text".
        snippets = [
            r.get("snippet", "")[:REVIEW_SNIPPET_LENGTH] for r in reviews.get("reviews", []) if r.get("snippet")
        ]
        if snippets:
            details["review_summary"] = " / ".join(snippets[:REVIEW_SUMMARY_SNIPPETS])
    except SerpApiError:
        pass

    return details


def _enrich_yelp(candidate: CandidateAttraction) -> dict:
    place_id = candidate.external_ids.get("yelp")
    if not place_id:
        return {}

    details: dict = {}
    try:
        # Verified live: details live under "place_results", and photos are
        # a flat list of image URL strings under "images" -- not "business"/
        # "photos" as SerpAPI's docs summary implied.
        place = serpapi_search("yelp_place", {"place_id": place_id})
        business = place.get("place_results", {})
        if business.get("hours"):
            details["hours"] = business["hours"]
        if business.get("price"):
            details["price_level"] = len(business["price"])
        if business.get("images"):
            details["photos"] = business["images"]
    except SerpApiError:
        pass

    try:
        reviews = serpapi_search("yelp_reviews", {"place_id": place_id})
        snippets = [
            (r.get("comment") or {}).get("text", "")[:REVIEW_SNIPPET_LENGTH] for r in reviews.get("reviews", [])
        ]
        snippets = [s for s in snippets if s]
        if snippets:
            details.setdefault("review_summary", " / ".join(snippets[:REVIEW_SUMMARY_SNIPPETS]))
    except SerpApiError:
        pass

    return details


def enrich_candidates(candidates: list[CandidateAttraction]) -> tuple[list[EnrichedAttraction], list[str]]:
    """Enriches the top MAX_ENRICHED_CANDIDATES (by a cheap popularity
    proxy) and passes the rest through unenriched -- still usable, just
    with only what the discovery-search engines already returned."""
    ranked_by_popularity = sorted(candidates, key=_popularity_proxy, reverse=True)
    to_enrich = {id(c) for c in ranked_by_popularity[:MAX_ENRICHED_CANDIDATES]}

    warnings: list[str] = []
    enriched: list[EnrichedAttraction] = []

    for candidate in candidates:
        details: dict = {}
        if id(candidate) in to_enrich:
            # TripAdvisor takes precedence over Yelp for fields both provide
            # (hours, price_level, photos) -- an explicit, documented
            # choice rather than silently picking whichever ran last.
            yelp_details = _enrich_yelp(candidate) if "yelp" in candidate.external_ids else {}
            ta_details = _enrich_tripadvisor(candidate) if "tripadvisor" in candidate.external_ids else {}
            details = {**yelp_details, **ta_details}

        enriched.append(
            EnrichedAttraction(
                candidate=candidate,
                hours=details.get("hours"),
                price_level=details.get("price_level", candidate.price_level),
                rating=candidate.rating,
                review_count=candidate.review_count,
                review_summary=details.get("review_summary"),
                photos=details.get("photos", []),
                categories=candidate.categories,
            )
        )

    return enriched, warnings
