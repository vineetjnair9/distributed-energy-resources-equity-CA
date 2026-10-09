import type { CompareResponse, Evidence, Region, SummaryResponse } from "../api/client";

export const region = (id: string, county = "Alameda"): Region => ({
  region_id: id,
  region_name: `ZCTA ${id}`,
  region_type: "zcta",
  state: "CA",
  county,
  utility: { utility_id: 1, utility_acronym: "PG&E", utility_name: "Pacific Gas and Electric Company", utility_type: "IOU" },
});

export const evidence = (id: number, regionId = "94601"): Evidence => ({
  evidence_id: id,
  region_id: regionId,
  evidence_text: `Evidence text ${id}`,
  evidence_type: "metric",
  source_name: "ACS 5-year",
  source_url: "https://www.census.gov/programs-surveys/acs",
});

export const availableSummary: SummaryResponse = {
  status: "available",
  summary_id: 7,
  region_id: "94601",
  category: "overview",
  summary_text: "Grounded overview text.",
  evidence_ids: [11, 12],
  evidence: [evidence(11), evidence(12)],
  metric_snapshot: {},
  model_version: "llm_category_summary_v3",
  generated_at: "2026-01-01T00:00:00+00:00",
  warnings: [],
};

export const unavailableSummary: SummaryResponse = {
  ...availableSummary,
  status: "unavailable",
  summary_id: null,
  summary_text: null,
  model_version: null,
  generated_at: null,
  evidence_ids: [11],
  evidence: [evidence(11)],
  warnings: ["No stored summary exists for this region and category."],
};

export const comparison: CompareResponse = {
  region_ids: ["94601", "94611"],
  regions: [region("94601"), region("94611")],
  metrics: [
    {
      metric_name: "median_household_income",
      metric_unit: "dollars",
      metric_category: "socioeconomic",
      values: { "94601": 50000, "94611": 180000 },
      display_values: { "94601": "$50,000", "94611": "$180,000" },
    },
    {
      metric_name: "PV_system_size_DC",
      metric_unit: "MW",
      metric_category: "der_observed",
      values: { "94601": 1.2, "94611": null },
      display_values: { "94601": "1.2 MW", "94611": null },
    },
  ],
  model_outputs: [
    {
      outcome_name: "y_pv",
      model_version: "Model 7",
      residual_percentile: { "94601": 0.1, "94611": 0.6 },
      priority_flag: { "94601": true, "94611": false },
    },
  ],
  overviews: { "94601": availableSummary, "94611": { ...unavailableSummary, region_id: "94611" } },
};
