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
