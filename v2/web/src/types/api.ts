// Mirrors v2/api/app/schemas.py — keep in sync by hand for now.

export type BedroomCategory =
  | "Room"
  | "Studio"
  | "One Bedroom"
  | "Two Bedrooms"
  | "Three Bedrooms"
  | "Four or More Bedrooms";

export type CouncilTaxBand = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H";
export type TimeBucket = "rush" | "off_peak" | "now";
export type JourneyPreference = "leasttime" | "leastinterchange" | "leastwalking";

export interface PostcodeHit {
  postcode: string;
  borough_code: string;
  borough_name: string;
  lat: number | null;
  lng: number | null;
}

export interface Preferences {
  days_per_week: number;
  time_bucket: TimeBucket;
  modes: string[] | null;
  journey_preference: JourneyPreference;
  bedroom_category: BedroomCategory;
  council_tax_band: CouncilTaxBand;
}

export interface OriginInput {
  postcode: string;
  council_tax_band?: CouncilTaxBand | null;
}

export interface CompareRequest {
  destination: string;
  origins: OriginInput[];
  prefs: Preferences;
}

export interface JourneyStep {
  mode: string;
  start: string | null;
  end: string | null;
  duration_minutes: number | null;
  line: string | null;
  summary: string | null;
}

export interface JourneyResult {
  duration_minutes: number | null;
  single_fare_gbp: number | null;
  legs: number | null;
  steps: JourneyStep[];
}

export interface CostBreakdown {
  monthly_commute_gbp: number;
  monthly_rent_gbp: number | null;
  monthly_council_tax_gbp: number;
  monthly_total_gbp: number;
}

export interface OriginResult {
  origin: string;
  borough_name: string | null;
  journey: JourneyResult;
  cost: CostBreakdown;
  rent_quartiles: Record<string, number | null> | null;
  error: string | null;
}

export interface CompareResponse {
  destination: string;
  results: OriginResult[];
}

export interface Borough {
  code: string;
  name: string;
}

export interface HealthStatus {
  status: string;
  postcodes_loaded: number;
  has_coords_index: boolean;
  tfl_key_configured: boolean;
}
