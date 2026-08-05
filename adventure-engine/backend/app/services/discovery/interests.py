"""Step 1: classify a discovery request into structured interest tags.

Structured interests (passed directly -- the same comma-separated-tag chip
convention used everywhere else in this app, e.g. AVAILABLE_INTERESTS on
the frontend) are preferred and just validated/normalized here. Free text
is only used as a fallback, matched against a small documented keyword
table -- not an ML/LLM call, consistent with this app's "real APIs or
honest local math, not fabricated intelligence" approach elsewhere (see
osm_activities.py's _CATEGORY_SYNONYMS for the same spirit).
"""

INTEREST_CATEGORIES: list[str] = [
    "food",
    "museums",
    "nature",
    "shopping",
    "architecture",
    "nightlife",
    "festivals",
    "hidden_gems",
    "family",
    "adventure",
    "photography",
    "luxury",
    "budget",
    "history",
]

# keyword -> category. Deliberately small and literal, a documented
# assumption table rather than a claim of real natural-language understanding.
_KEYWORDS: dict[str, str] = {
    "food": "food", "restaurant": "food", "eat": "food", "dining": "food", "cafe": "food",
    "museum": "museums", "gallery": "museums", "exhibit": "museums",
    "nature": "nature", "hike": "nature", "hiking": "nature", "park": "nature", "outdoor": "nature",
    "shop": "shopping", "shopping": "shopping", "market": "shopping", "mall": "shopping",
    "architecture": "architecture", "building": "architecture", "landmark": "architecture",
    "nightlife": "nightlife", "bar": "nightlife", "club": "nightlife", "nightclub": "nightlife",
    "festival": "festivals", "event": "festivals", "concert": "festivals",
    "hidden": "hidden_gems", "gem": "hidden_gems", "secret": "hidden_gems", "local": "hidden_gems",
    "family": "family", "kid": "family", "kids": "family", "children": "family",
    "adventure": "adventure", "thrill": "adventure", "extreme": "adventure",
    "photo": "photography", "photography": "photography", "scenic": "photography", "view": "photography",
    "luxury": "luxury", "upscale": "luxury", "fine": "luxury",
    "budget": "budget", "cheap": "budget", "free": "budget",
    "history": "history", "historic": "history", "historical": "history", "heritage": "history",
}


def classify_interests(free_text: str | None, requested: list[str] | None) -> list[str]:
    """Returns a de-duplicated, validated list of interest categories.

    `requested` (structured tags from the caller) wins outright when it
    contains at least one valid category. `free_text` is only classified as
    a fallback when no usable structured interests were supplied.
    """
    if requested:
        normalized = [tag.strip().lower() for tag in requested if tag.strip()]
        valid = [tag for tag in normalized if tag in INTEREST_CATEGORIES]
        if valid:
            return list(dict.fromkeys(valid))

    if not free_text:
        return []

    lowered = free_text.lower()
    matched = [category for keyword, category in _KEYWORDS.items() if keyword in lowered]
    return list(dict.fromkeys(matched))
