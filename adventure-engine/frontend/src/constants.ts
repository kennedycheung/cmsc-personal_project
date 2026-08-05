export const AVAILABLE_INTERESTS = [
  'hiking',
  'food',
  'culture',
  'history',
  'adventure',
  'relaxation',
  'nightlife',
  'scenery',
  'wildlife',
];

// Values match the backend's TimeBucket enum exactly (app/services/travel_time.py)
// -- sent as opaque strings so the backend owns the bucket-to-distance mapping.
export interface TimeBucketOption {
  value: string;
  label: string;
}

export const TIME_BUCKETS: TimeBucketOption[] = [
  { value: 'two_hours', label: '2 hours' },
  { value: 'half_day', label: 'Half day' },
  { value: 'full_day', label: 'Full day' },
  { value: 'weekend', label: 'Weekend' },
  { value: 'three_to_four_days', label: '3-4 days' },
  { value: 'five_to_seven_days', label: '5-7 days' },
  { value: 'one_week', label: '1 week' },
  { value: 'two_weeks', label: '2 weeks' },
];

// Buckets under a day are treated as a local adventure -- no flights/hotels,
// just nearby real activities. Mirrors travel_time.LOCAL_ADVENTURE_BUCKETS.
export const LOCAL_ADVENTURE_BUCKET_VALUES = new Set(['two_hours', 'half_day', 'full_day']);

export interface TravelScopeOption {
  value: string;
  label: string;
  description: string;
}

export const TRAVEL_SCOPES: TravelScopeOption[] = [
  { value: 'stay_local', label: 'Stay local', description: 'Keep it close to home' },
  { value: 'day_trip', label: 'Day trip', description: "Somewhere you can get to and from today" },
  { value: 'overnight_trip', label: 'Overnight trip', description: 'Worth staying a night or more' },
  { value: 'anywhere_within_budget', label: 'Anywhere within my budget', description: 'No distance limit' },
];

// Mirrors the backend's INTEREST_CATEGORIES exactly
// (app/services/discovery/interests.py) -- the Activity Discovery Engine's
// own interest vocabulary, distinct from AVAILABLE_INTERESTS above.
export const DISCOVERY_INTERESTS = [
  'food',
  'museums',
  'nature',
  'shopping',
  'architecture',
  'nightlife',
  'festivals',
  'hidden_gems',
  'family',
  'adventure',
  'photography',
  'luxury',
  'budget',
  'history',
];

export const LOCAL_ACTIVITY_GROUPS: TimeBucketOption[] = [
  { value: 'nature', label: 'Nature' },
  { value: 'food', label: 'Food' },
  { value: 'culture', label: 'Culture' },
  { value: 'entertainment', label: 'Entertainment' },
  { value: 'shopping', label: 'Shopping' },
  { value: 'outdoor_recreation', label: 'Outdoor recreation' },
  { value: 'relaxation', label: 'Relaxation' },
];
