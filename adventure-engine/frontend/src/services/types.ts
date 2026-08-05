export interface Destination {
  id: number;
  name: string;
  country: string;
  region: string;
  description: string | null;
  budget_per_day: number;
  interests: string[];
  uniqueness_score: number;
  travel_difficulty: number;
  latitude: number;
  longitude: number;
}

export interface Activity {
  id: number;
  destination_id: number;
  name: string;
  description: string | null;
  category: string | null;
  tags: string | null;
  neighborhood: string | null;
  price: number;
  duration_hours: number | null;
  location: string | null;
  opening_time: string | null;
  closing_time: string | null;
  travel_minutes: number;
  latitude: number;
  longitude: number;
}

export interface ScoreBreakdown {
  budget_fit: number;
  interest_match: number;
  uniqueness: number;
  cost_efficiency: number;
  travel_difficulty: number;
}

export interface Recommendation {
  destination: Destination;
  adventure_score: number;
  score_breakdown: ScoreBreakdown;
}

export interface ScheduledActivity {
  activity: Activity;
  start_time: string;
  end_time: string;
}

export interface DayItinerary {
  day: number;
  activities: ScheduledActivity[];
  total_cost: number;
  total_travel_minutes: number;
}

export interface ItineraryResponse {
  destination: Destination;
  days: DayItinerary[];
  total_cost: number;
  warnings: string[];
}

export interface DiscoveredAttraction {
  name: string;
  address: string | null;
  latitude: number;
  longitude: number;
  rating: number | null;
  review_count: number | null;
  price_level: number | null;
  categories: string[];
  hours: Record<string, string> | null;
  review_summary: string | null;
  photos: string[];
  engines: string[];
  score: number;
  score_breakdown: Record<string, number>;
}

export interface RecommendationBuckets {
  best_overall: DiscoveredAttraction[];
  best_value: DiscoveredAttraction[];
  best_hidden_gem: DiscoveredAttraction[];
  best_family: DiscoveredAttraction[];
  best_evening: DiscoveredAttraction[];
  best_rainy_day: DiscoveredAttraction[];
  best_free: DiscoveredAttraction[];
}

export interface DiscoveryRouteLeg {
  from_name: string;
  to_name: string;
  distance_text: string | null;
  duration_text: string | null;
  duration_minutes: number | null;
}

export interface DiscoveryRoute {
  legs: DiscoveryRouteLeg[];
  total_duration_minutes: number;
}

export interface DiscoveryResponse {
  buckets: RecommendationBuckets;
  route: DiscoveryRoute | null;
  warnings: string[];
}
