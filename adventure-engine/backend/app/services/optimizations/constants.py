"""Documented assumptions shared across the optimization calculators.

None of these are measured facts -- each is a stated simplification. See
documentation/backpacker_optimizations.md for the rationale behind every
value here.
"""

# Typical backpacker cost breakdown: ~40% lodging, ~35% food, ~25% local
# transport/activities. destination.budget_per_day bundles all of that, so
# lodging alone is estimated as this share of it.
LODGING_SHARE_OF_BUDGET = 0.40

# Deliberately low -- backpackers trade time for money more than average
# travelers. Override per-call for a different traveler profile.
TIME_VALUE_PER_HOUR_USD = 8.0

# Approximate budget bus/train fare per km (e.g. Southeast Asian and South
# American budget bus networks).
OVERLAND_COST_PER_KM_USD = 0.07

# Average overland speed including stops, borders, and transfers -- well
# below highway speed on purpose.
OVERLAND_SPEED_KMH = 50.0

# Beyond this, "take an overland bus back" stops being realistic. Past this
# threshold the open-jaw calculator still returns numbers but flags them.
OVERLAND_MAX_REASONABLE_KM = 2500.0
