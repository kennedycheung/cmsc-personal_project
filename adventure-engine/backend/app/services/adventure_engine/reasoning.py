"""Turns a cluster's ScoreReasons into a deterministic, human-readable
summary paragraph. Template-based, not generated text -- the summary only
ever restates what the scoring factors already computed, so it can never
claim something the underlying data doesn't support.
"""

from app.services.adventure_engine.types import ScoreReason

TOP_REASON_COUNT = 3
STRONG_SCORE_THRESHOLD = 0.6


def build_summary(reasons: list[ScoreReason], location_label: str) -> str:
    ranked = sorted(reasons, key=lambda r: r.score * r.weight, reverse=True)
    top = [r for r in ranked if r.score >= STRONG_SCORE_THRESHOLD][:TOP_REASON_COUNT]
    if not top:
        top = ranked[:2]

    sentences = [r.reason for r in top]
    return f"{location_label}: " + "; ".join(sentences) + "."
