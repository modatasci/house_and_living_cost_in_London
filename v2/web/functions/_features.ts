// Allowlist of valid feature keys for vote validation.
// IMPORTANT: keep in sync with v2/web/src/lib/future-features.ts
export const FEATURE_KEYS = new Set<string>([
  "live-listings",
  "energy-bill-est",
  "cycling-driving",
  "saved-comparisons",
  "school-crime-data",
  "more-comparisons",
]);
