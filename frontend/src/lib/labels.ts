// Display names for stored identifiers. Anything missing falls back to the raw
// identifier, so a new metric still renders, just less prettily.
export const METRIC_LABELS: Record<string, string> = {
  total_population: "Population",
  population: "Population",
  median_household_income: "Median household income",
  poverty_rate: "Poverty rate",
  pct_bachelors_plus: "Bachelor's degree or higher (25+)",
  pct_black: "Black (non-Hispanic)",
  pct_hispanic: "Hispanic or Latino",
  pct_asian: "Asian (non-Hispanic)",
  median_housing_value: "Median housing value",
  pct_single_family_units: "Single-family units",
  pct_multifamily_units: "Multifamily units",
  pct_mobile_home_units: "Mobile home units",
  pct_other_housing_units: "Other housing units",
  owner_occupied_rate: "Owner-occupied",
  PV_system_size_DC: "Rooftop PV capacity (DC)",
  storage_capacity_mw: "Storage capacity",
  total_chargers: "EV chargers (all)",
  level1_chargers: "Level 1 chargers",
  level2_chargers: "Level 2 chargers",
  dc_fast_chargers: "DC fast chargers",
  wind_capacity_mw: "Wind capacity",
  wind_turbine_count: "Wind turbines",
  energy_burden_pct: "Energy burden (% of income)",
  energy_affordability_index: "Affordability index",
  energy_affordability_gap: "Affordability gap",
  kwh_annual_total: "Reported electricity use",
  cdd65_2023: "Cooling degree days",
  hdd65_2023: "Heating degree days",
  ghi_mean_kwh_m2_day_2023: "Solar irradiance (GHI)",
  wind_ws10m_mean_2023: "Wind speed at 10 m",
  wind_ws50m_mean_2023: "Wind speed at 50 m",
};

export const CATEGORY_LABELS: Record<string, string> = {
  der_observed: "Observed DER",
  demographic: "Demographics",
  socioeconomic: "Socioeconomic",
  education: "Education",
  housing: "Housing",
  energy_affordability: "Energy affordability",
  demand: "Electricity demand",
  weather: "Weather",
  solar_resource: "Solar resource",
  wind_resource: "Wind resource",
};

export const CATEGORY_ORDER = Object.keys(CATEGORY_LABELS);

export const OUTCOME_LABELS: Record<string, string> = {
  y_pv: "Rooftop PV",
  y_storage: "Storage",
  y_chargers: "EV chargers",
  y_level1_chargers: "Level 1 chargers",
  y_level2_chargers: "Level 2 chargers",
  y_dc_fast_chargers: "DC fast chargers",
  y_wind_mw: "Wind capacity",
  any_turbines: "Turbine presence",
  energy_burden_pct: "Energy burden",
  energy_affordability_index: "Affordability index",
  log_energy_gap_per_capita: "Affordability gap",
};

// Lower-case phrases for running text ("Where rooftop solar is lower than ...").
export const OUTCOME_PHRASES: Record<string, string> = {
  y_pv: "rooftop solar",
  y_storage: "battery storage",
  y_chargers: "EV charging",
  y_level1_chargers: "Level 1 charging",
  y_level2_chargers: "Level 2 charging",
  y_dc_fast_chargers: "DC fast charging",
  y_wind_mw: "wind capacity",
  any_turbines: "turbine presence",
  energy_burden_pct: "energy burden",
  energy_affordability_index: "the affordability index",
  log_energy_gap_per_capita: "the affordability gap",
};

// Matches populate_tables: DER outcomes flag low residuals, burden outcomes high
// ones, and any other outcome flags large absolute residuals.
export const DER_OUTCOMES = new Set(["y_pv", "y_storage", "y_chargers", "y_level1_chargers", "y_level2_chargers", "y_dc_fast_chargers", "y_wind_mw"]);
export const BURDEN_OUTCOMES = new Set(["energy_burden_pct", "energy_affordability_index", "log_energy_gap_per_capita"]);

export type FlagDirection = "low" | "high" | "absolute";
export const flagDirection = (outcome: string): FlagDirection =>
  DER_OUTCOMES.has(outcome) ? "low" : BURDEN_OUTCOMES.has(outcome) ? "high" : "absolute";

export const KEY_METRICS = [
  "total_population",
  "median_household_income",
  "PV_system_size_DC",
  "total_chargers",
  "energy_burden_pct",
];

export const label = (map: Record<string, string>, key: string) => map[key] ?? key.replaceAll("_", " ");

export function flagMeaning(outcome: string) {
  return {
    low: "Priority means the residual is at or below the 25th percentile: observed adoption is lower than the model predicts.",
    high: "Priority means the residual is at or above the 75th percentile: observed burden is higher than the model predicts.",
    absolute: "Priority means the absolute residual is at or above the 75th percentile, in either direction.",
  }[flagDirection(outcome)];
}

export function percentile(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  const n = Math.round(value * 100);
  const suffix = n % 100 >= 11 && n % 100 <= 13 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" } as Record<number, string>)[n % 10] ?? "th";
  return `${n}${suffix}`;
}

export function number(value: number | null | undefined, digits = 3) {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("en-US", { maximumSignificantDigits: digits });
}

/** Model names arrive as "outcome | Model 7 (...) | mode" in the full build. */
export function modelName(version: string) {
  const parts = version.split(" | ").map((part) => part.trim());
  return parts.length >= 3 ? parts[1] : version;
}
