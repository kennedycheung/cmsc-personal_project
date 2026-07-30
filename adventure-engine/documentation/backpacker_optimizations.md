# Backpacker Optimization Features

Six cost/time optimization calculators aimed at budget travelers, each
explained mathematically here before its implementation in
`backend/app/services/optimizations/`. All six follow the same shape: take
real data already in this system (destination coordinates, budget_per_day,
curated reference data) plus a small number of documented assumptions, and
produce a **savings figure with a visible breakdown** — never just a single
opaque number.

Shared constants (`backend/app/services/optimizations/constants.py`), each
a documented assumption rather than a measured fact:

| Constant | Value | Used by | Rationale |
|---|---|---|---|
| `LODGING_SHARE_OF_BUDGET` | 0.40 | Overnight transport, Positioning | Typical backpacker cost breakdown is roughly 40% lodging / 35% food / 25% local transport + activities; `destination.budget_per_day` bundles all of that, so lodging alone is estimated as 40% of it. |
| `TIME_VALUE_PER_HOUR_USD` | 8.0 | Nearby airport | A deliberately low figure — backpackers, almost by definition, trade time for money more than average travelers. Override per-call if a different traveler profile is being modeled. |
| `OVERLAND_COST_PER_KM_USD` | 0.07 | Open-jaw routing | Approximate budget bus/train fare per km (e.g. Southeast Asian and South American budget bus networks). |
| `OVERLAND_SPEED_KMH` | 50.0 | Open-jaw routing | Average overland speed including stops, borders, and transfers — well below highway speed on purpose. |
| `OVERLAND_MAX_REASONABLE_KM` | 2500 | Open-jaw routing | Beyond this, "take an overland bus back" stops being realistic (this app's 64 seeded destinations span every continent; not every pair is an overland-connected circuit). The calculator still returns numbers past this threshold, but flags them. |

---

## 1. Nearby airport optimization

**Idea:** the "obvious" airport for a destination isn't always cheapest once
ground transport is included — a farther, budget-carrier-served airport can
win even after adding the extra transfer cost and time.

For each candidate airport *i* serving a destination:

```
EffectiveCost(i) = BaselineFare(i) + GroundTransportCost(i)
                    + (GroundTransportMinutes(i) / 60) * TIME_VALUE_PER_HOUR_USD

Recommended = argmin_i EffectiveCost(i)
SavingsVsPrimary = EffectiveCost(primary airport) - EffectiveCost(Recommended)
```

`BaselineFare` is a curated placeholder (no live multi-airport fare API
exists any more than a live single-fare one does — see
`deal_ingestion_pipeline.md` for the same limitation), but distance, ground
transport cost/time, and the airport set itself are real. Only 3 of the 14
seeded destinations have more than one airport modeled (Kyoto, Banff,
Queenstown) — genuine real-world examples of this exact backpacker
decision (Kyoto has no airport of its own at all; Banff and Queenstown both
have a much-farther, sometimes-cheaper alternate).

**Worked example — Kyoto:**

| Airport | Fare | Ground cost | Ground time | EffectiveCost |
|---|---|---|---|---|
| Kansai (KIX, primary) | $700 | $25 | 75 min | 700+25+10.0 = **735** |
| Itami (ITM) | $650 | $20 | 60 min | 650+20+8.0 = **678** |
| Chubu/Nagoya (NGO) | $600 | $40 | 150 min | 600+40+20.0 = **660** |

Recommended: NGO, saving **$75** over defaulting to KIX.

---

## 2. Overnight transportation savings

**Idea:** an overnight bus/train/red-eye flight does double duty — you sleep
in transit, so you skip paying for a hotel that night. The question is
whether the (sometimes higher) overnight fare is still less than the
lodging it replaces.

```
LodgingPerNight = destination.budget_per_day * LODGING_SHARE_OF_BUDGET
TransportPremium = OvernightPrice - DaytimePrice
NetSavings = (NightsSaved * LodgingPerNight) - TransportPremium
WorthIt = NetSavings > 0
```

`OvernightPrice`/`DaytimePrice` are supplied by the caller (real transport
pricing varies far too much to usefully seed), everything else comes from
the destination's own data.

**Worked example — Chiang Mai** (`budget_per_day = 70`):

```
LodgingPerNight = 70 * 0.40 = 28
Night train $25 vs daytime bus $15 -> TransportPremium = 10
NetSavings = 28 - 10 = 18   -> worth it, nets $18 while also saving a travel day
```

---

## 3. Open-jaw routing

**Idea:** flying `Home → B`, traveling overland through several places, and
flying home from wherever you end up (`C → Home`) avoids backtracking to
`B` just to catch the flight home — at the cost of a (possibly nonzero)
open-jaw fare premium versus a simple round trip.

```
BacktrackDistanceKm = haversine(LastStop, EntryCity)
BacktrackCost        = BacktrackDistanceKm * OVERLAND_COST_PER_KM_USD
BacktrackTimeHours   = BacktrackDistanceKm / OVERLAND_SPEED_KMH

FarePremium = (OneWayFareOut + OneWayFareBack) - RoundTripFare
NetSavings  = BacktrackCost - FarePremium
```

`NetSavings > 0` means the open-jaw itinerary saves money net of any fare
premium; the avoided `BacktrackTimeHours` is saved regardless of the sign
(time is never spent going somewhere just to leave from it). Distance is
computed for real from the two destinations' coordinates (haversine great-
circle distance); fares are caller-supplied, defaulting the premium to $0
(realistic — many budget carriers price one-ways at roughly half the round
trip). If `BacktrackDistanceKm` exceeds `OVERLAND_MAX_REASONABLE_KM`, the
result is flagged: some destination pairs in this system (e.g. Cape Town
and Kyoto) simply aren't an overland-connected circuit, and pretending a
92-hour bus ride is a real option would be dishonest.

**Worked example — Chiang Mai → Ho Chi Minh City** (a real overland
Southeast Asia backpacker route, via Laos/Cambodia):

```
BacktrackDistanceKm ≈ 1215 km  (computed from real coordinates)
BacktrackCost = 1215 * 0.07 ≈ $85
BacktrackTimeHours = 1215 / 50 ≈ 24.3 h

RoundTripFare = 900, OneWayOut = 500, OneWayBack = 480
FarePremium = (500 + 480) - 900 = 80

NetSavings = 85 - 80 = $5, plus ~24 hours of avoided backtracking
```

Small dollar savings, but the real win here is the day of travel time —
the calculator reports both, not just the dollar figure.

---

## 4. Positioning trips

**Idea:** flying cheaply to an intermediate hub first, then a separate
cheap onward flight, can beat one "direct" itinerary priced from home —
especially through hubs with strong budget-carrier networks (Reykjavik's
free-stopover program on transatlantic routes is the textbook real-world
example).

```
PositioningCost = Fare(Home → Hub) + Fare(Hub → Final)
                   + ExtraNights * (Hub.budget_per_day * LODGING_SHARE_OF_BUDGET)
NetSavings = DirectItineraryCost - PositioningCost
```

**Worked example — position through Reykjavik en route to Prague**
(`Reykjavik.budget_per_day = 240`, real seeded value):

```
Direct home -> Prague: $700

Home -> Reykjavik: $300
Reykjavik -> Prague: $180
1 extra night in Reykjavik: 240 * 0.40 = $96
PositioningCost = 300 + 180 + 96 = $576

NetSavings = 700 - 576 = $124
```

---

## 5. Seasonal arbitrage

**Idea:** the same destination's real cost swings with tourist season.
Each destination carries a curated 12-value monthly cost multiplier
(`Destination.seasonal_multipliers`, comma-separated Jan→Dec, 1.0 =
average, e.g. Reykjavik peaks in July at summer/midnight-sun season and is
cheapest in April) — the same comma-separated-text convention already used
for `interests`.

```
SeasonalCost(month) = destination.budget_per_day * Multiplier(month)

BestMonth = argmin_month SeasonalCost(month)
PeakMonth = argmax_month SeasonalCost(month)
SavingsVsPeak    = SeasonalCost(PeakMonth) - SeasonalCost(BestMonth)
SavingsVsCurrent = SeasonalCost(CurrentMonth) - SeasonalCost(BestMonth)
```

**Worked example — Reykjavik** (`budget_per_day = 240`):

```
Peak (July, x1.35):  240 * 1.35 = $324/day
Best (April, x0.80): 240 * 0.80 = $192/day
SavingsVsPeak = 324 - 192 = $132/day
```

These multipliers are curated from well-known tourism-season patterns per
destination (documented per-entry in `seed.py`), not derived from any
booking data — an explicit, stated simplification, same as the deal
connectors' placeholder data.

---

## 6. Currency arbitrage

**Idea:** `destination.budget_per_day` is a static USD estimate. If the
destination's local currency has weakened against the traveler's home
currency since that estimate was set, the destination is *currently*
cheaper in real terms than the static number suggests (and more expensive
if the local currency has strengthened). Unlike the placeholder-data
features above, this one uses a **real, free, live API**
([Frankfurter](https://www.frankfurter.app), backed by ECB reference
rates, no key required) for both the current rate and a one-year-ago
baseline — the same principle already applied to weather (Open-Meteo) and
walking routes (OSRM): use a real free API when one exists.

```
CurrentRate  = live_rate(home_currency -> local_currency), today
BaselineRate = live_rate(home_currency -> local_currency), 365 days ago

RelativeStrength   = BaselineRate / CurrentRate
AdjustedBudgetPerDay = destination.budget_per_day * RelativeStrength
Savings             = destination.budget_per_day - AdjustedBudgetPerDay
ArbitragePercent    = (1 - RelativeStrength) * 100
```

If `CurrentRate > BaselineRate` (home currency now buys more local currency
than a year ago), `RelativeStrength < 1`, so `AdjustedBudgetPerDay` comes in
below the static estimate — a positive `ArbitragePercent`, i.e. currently
cheaper than usual. The reverse holds if the local currency has
strengthened.

Frankfurter covers ECB-tracked currencies only, which excludes eight of our
64 seeded destinations' local currencies (Morocco/MAD, Argentina/ARS,
Vietnam/VND, Dominican Republic/DOP, Bahamas/BSD, Peru/PEN, Costa Rica/CRC,
UAE/AED) — those destinations report the arbitrage as unavailable rather
than guessing, the same graceful-degradation pattern used when
Open-Meteo can't be reached.

**Worked example — Kyoto** (`budget_per_day = 180`, currency JPY):

```
CurrentRate (today) = 163.68 JPY/USD
BaselineRate (1 year ago) = 148.77 JPY/USD

RelativeStrength = 148.77 / 163.68 = 0.9089
AdjustedBudgetPerDay = 180 * 0.9089 = $163.60
Savings = 180 - 163.60 = $16.40/day
ArbitragePercent = (1 - 0.9089) * 100 = 9.1%
```

The yen weakened ~9% against the dollar over the year, so Kyoto is
currently about 9% cheaper in real terms than its static budget estimate
suggests.
