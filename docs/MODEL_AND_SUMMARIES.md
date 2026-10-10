# Model layer and grounded summaries

## Model layer

**Pipeline (offline).** `notebooks/regression.ipynb`, run by
`python scripts/run_all.py --only models`, fits OLS specifications of each outcome on
ZCTA-level 2023 data and writes `data/processed/model_outputs_by_region.csv`. The
database builder loads that file into `model_outputs`. Nothing is fit or scored in a
request handler.

**Outcomes.** DER adoption and infrastructure per capita (`y_pv`, `y_storage`,
`y_chargers` and charger levels, `y_wind_mw`, `any_turbines`) and energy affordability
(`energy_burden_pct`, `log_energy_gap_per_capita`).

**Specifications.** About 25 per outcome, all built on core terms (log median income, Black, Hispanic and Asian shares, poverty rate). The ladder runs from the baseline (Model 1: core terms plus the outcome's climate control) through
demographic, socioeconomic, housing-structure and tenure controls (Model 2 variants),
county fixed effects (Model 6B), infrastructure controls (Model 7), a demand proxy
(Model 8), and the most-controlled storage model with a PV control (Model 9). Model
9A predicts burden. The paper (`site/paper.html`) gives full specifications.

**What is stored per region, outcome, and specification:** actual value, predicted
value, residual, the residual's percentile rank within the fitted sample, a priority
flag, the model assumptions, and a timestamp.

**Priority flag.**

| Outcome type | Flagged when | Reads as |
| --- | --- | --- |
| DER (`y_*`) | residual at or below the 25th percentile | adoption lower than similar places predict |
| Affordability | residual at or above the 75th percentile | burden higher than predicted |
| Other (`any_turbines`) | absolute residual at or above the 75th percentile | unusual in either direction |

**Interpreting it.** The app emphasizes agreement across specifications. The
screening endpoint ranks regions by the share of specifications that flag them, then
by mean residual rank. A region flagged by every specification is a sturdier lead
than one flagged by a single model.

**Assumptions and limitations.**
- Residuals are screening signals, not causal effects. They say a ZCTA differs from
  places with similar observed characteristics, not why.
- ZCTAs without ACS demographics are absent from the fitted sample, so they have no
  model outputs. The UI says so instead of showing an empty table.
- Linear fits can predict negative values for non-negative outcomes. Evidence text
  notes when a positive residual comes only from a negative prediction.
- When an outcome is zero in at least 95% of regions (wind, turbines), its percentile
  mainly orders fitted values. Evidence text carries that caveat.
- Weather and resource controls are NASA POWER gridded values at the ZCTA centroid.
- Reported electricity usage covers only the accounts in each utility's export.

## Grounded summaries

**Generation (offline, explicit).** `backend/schemas/generate_summaries.py` (and the
Batch API variant `generate_summaries_batch.py`) needs `OPENAI_API_KEY` and is never
run by the server or the database build. For each region it:

1. **Retrieves** a bounded evidence packet per category with
   `get_evidence_for_category`. Metric categories select metric evidence; model
   categories select up to four specifications, preferring the category's designated
   model.
2. **Generates** every section in one structured-output request. The model must
   return `evidence_ids_used`, and IDs outside the packet are rejected
   (`validate_llm_evidence_ids`).
3. **Stores** each section with its evidence links, a metric snapshot, the summary
   version, and a timestamp.
4. **Writes the overview** from the stored section summaries, never from raw evidence.
   Regions with too few sections get a fixed not-enough-data overview, which still
   cites evidence.

**Serving (online, retrieval only).** `POST /api/summaries` reads the stored record
and checks it before presenting it as grounded (`backend/services/summaries.py`):

| Situation | Response |
| --- | --- |
| Stored summary; every cited evidence record belongs to this region | `available`, with text, `evidence_ids`, full evidence, snapshot, version, and timestamp |
| Stored summary with no evidence links | `unavailable`. The text is withheld as unsupported. |
| Stored summary citing another region's evidence | `unavailable`. The text is withheld as untraceable. |
| No stored summary | `unavailable`. The retrieved evidence packet is returned instead. |
| Category with no evidence at all | `unavailable`, with a warning that no evidence exists |
| Not-enough-data overview | `available`, with an insufficient-data warning |
| Synthetic fixture text | `available`, with a synthetic-data warning |

The frontend never renders `summary_text` unless the status is `available`, and it
always lists the evidence behind what it shows. Tests cover each row of this table
(`tests/test_api.py`, grounding section, and `frontend/src/__tests__/components.test.tsx`).

**Version metadata.** `model_version` records the summary pipeline version
(`llm_category_summary_v3_dynamic_models`, or `fixture_template_v1` for the fixture).
The LLM model name is in `metric_snapshot.summary_model` and in `llm_usage_log`.
