# API reference

The machine-readable contract is [`openapi.json`](openapi.json), generated from the
FastAPI app (`python scripts/export_openapi.py`; CI fails if it is stale). A running
server also serves interactive docs at `/api/docs`. Response shapes are Pydantic
models in `backend/api/models.py`; the frontend's TypeScript types are generated
from the same file (`npm --prefix frontend run gen:types`).

All region resources use `region_id`, the five-character ZCTA (`"90001"`).

| Method | Path | Returns |
| --- | --- | --- |
| GET | `/health`, `/api/health` | Readiness: `ready` / `not_ready` (503) with a setup command; `synthetic` is true for the fixture |
| GET | `/api/regions?q=&county=&utility=&limit=&offset=` | Searchable, paginated region list with utility |
| GET | `/api/regions/{id}` | Region, all metrics with `display_value`, `missing_metric_categories`, geometry WKT |
| GET | `/api/regions/{id}/evidence?evidence_type=` | Evidence records (`metric` or `model_output`) with sources |
| GET | `/api/regions/{id}/summaries` | Which summary categories are stored, with evidence counts |
| GET | `/api/model-output/{id}?outcome_name=&model_version=` | Stored regression outputs: actual, predicted, residual, percentile, priority flag, assumptions |
| GET | `/api/compare?region_ids=A&region_ids=B` | 2–6 regions: metric rows and model rows keyed by region (missing = `null`), plus each overview summary |
| GET | `/api/screening?outcome_name=y_pv&county=&utility=&limit=` | Flagged regions ranked by agreement across specifications |
| GET | `/api/facets` | Counties, utilities, and modeled outcomes for filters |
| POST | `/api/summaries` `{"region_id", "category"}` | Stored grounded summary with cited evidence, or `unavailable` with retrieved evidence |
| GET | `/api/summary-categories` | Valid summary categories and labels |

## Examples

```bash
curl -s localhost:8000/api/regions?q=Fresno | jq '.items[].region_id'
curl -s localhost:8000/api/compare?region_ids=90001,90210 | jq '.metrics[0]'
curl -s -X POST localhost:8000/api/summaries \
  -H 'Content-Type: application/json' \
  -d '{"region_id": "90001", "category": "overview"}' | jq '{status, evidence_ids, warnings}'
```

A summary response always carries the fields the grounding contract requires:

```json
{
  "status": "available",
  "summary_id": 3,
  "region_id": "90001",
  "category": "overview",
  "summary_text": "…",
  "evidence_ids": [2, 14, 15, 699, 722],
  "evidence": [{"evidence_id": 2, "region_id": "90001", "evidence_text": "…", "source_name": "ACS 5-year", "source_url": "https://…"}],
  "metric_snapshot": {"…": "…"},
  "model_version": "llm_category_summary_v3_dynamic_models",
  "generated_at": "2026-08-19T00:00:00+00:00",
  "warnings": []
}
```

## Errors

| Status | When |
| --- | --- |
| 400 | `/compare` with fewer than 2 or more than 6 distinct regions |
| 404 | Unknown `region_id` (compare names every unknown ID), unknown screening outcome, unknown `/api/*` path |
| 422 | Invalid parameters, or an unknown summary category (response lists valid ones) |
| 503 | Database missing, unreadable, or incomplete; `/api/health` gives the setup command |
