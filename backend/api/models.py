"""Typed response contracts for the DER API.

These models are the API contract: FastAPI validates every response against
them and publishes them in the OpenAPI document at /api/openapi.json, which the
frontend's TypeScript types mirror (frontend/src/api/types.ts).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    message: str
    database: str | None = Field(
        None, description="Database file name (never a full server path)."
    )
    synthetic: bool = Field(
        False, description="True when serving the synthetic fixture database."
    )
    setup_command: str | None = None


class Utility(BaseModel):
    utility_id: int
    utility_acronym: str | None
    utility_name: str
    utility_type: str | None


class Region(BaseModel):
    region_id: str = Field(description="Five-character ZCTA, the stable key across every table.")
    region_name: str | None
    region_type: str
    state: str | None
    county: str | None
    utility: Utility | None


class RegionList(BaseModel):
    total: int = Field(description="Matching regions before limit/offset.")
    limit: int
    offset: int
    items: list[Region]


class Metric(BaseModel):
    metric_name: str
    metric_value: float
    display_value: str = Field(description="Human-readable value with units.")
    metric_unit: str | None
    metric_category: str | None
    source_name: str | None
    observed_at: str | None


class Geometry(BaseModel):
    geometry_wkt: str
    geometry_format: str
    crs: str | None


class RegionDetail(BaseModel):
    region: Region
    metrics: list[Metric]
    missing_metric_categories: list[str] = Field(
        description="Metric categories with no observation for this region."
    )
    geometry: Geometry | None


class ModelOutput(BaseModel):
    model_output_id: int
    outcome_name: str
    model_version: str
    actual_value: float | None
    predicted_value: float | None
    residual_value: float | None
    residual_percentile: float | None = Field(
        description="Rank of the residual within the fitted sample, 0 to 1."
    )
    priority_flag: bool | None = Field(
        description=(
            "DER outcomes: residual at or below the 25th percentile. "
            "Affordability outcomes: at or above the 75th percentile."
        )
    )
    assumptions: str | None
    generated_at: str | None


class ModelOutputList(BaseModel):
    region_id: str
    items: list[ModelOutput]


class Evidence(BaseModel):
    evidence_id: int
    region_id: str | None
    evidence_text: str
    evidence_type: str | None
    source_name: str | None
    source_url: str | None


class CompareMetricRow(BaseModel):
    metric_name: str
    metric_unit: str | None
    metric_category: str | None
    values: dict[str, float | None]
    display_values: dict[str, str | None]


class CompareModelRow(BaseModel):
    outcome_name: str
    model_version: str
    residual_percentile: dict[str, float | None]
    priority_flag: dict[str, bool | None]


class CompareResponse(BaseModel):
    region_ids: list[str]
    regions: list[Region]
    metrics: list[CompareMetricRow]
    model_outputs: list[CompareModelRow]
    overviews: dict[str, "SummaryResponse"]


class FacetCount(BaseModel):
    value: str
    label: str
    count: int


class Facets(BaseModel):
    counties: list[FacetCount]
    utilities: list[FacetCount]
    outcomes: list[FacetCount] = Field(description="Outcomes with stored model outputs.")


class ScreeningRow(BaseModel):
    region: Region
    flagged_count: int
    specification_count: int
    mean_residual_percentile: float | None


class ScreeningResponse(BaseModel):
    outcome_name: str
    direction: Literal["low", "high", "absolute"] = Field(
        description="Which residuals the priority flag marks for this outcome."
    )
    total: int = Field(description="Regions with at least one flagged specification.")
    items: list[ScreeningRow]


class SummaryRequest(BaseModel):
    region_id: str = Field(max_length=16, examples=["90001"])
    category: str = Field("overview", max_length=64, examples=["overview", "observed_der", "model_pv"])


class SummaryResponse(BaseModel):
    status: Literal["available", "unavailable"] = Field(
        description=(
            "'available' only when a stored summary exists and every cited evidence "
            "record exists and belongs to this region. Otherwise 'unavailable', "
            "with the reason and the retrieved evidence still returned."
        )
    )
    summary_id: int | None
    region_id: str
    category: str
    summary_text: str | None
    evidence_ids: list[int]
    evidence: list[Evidence]
    metric_snapshot: dict[str, Any] | None
    model_version: str | None
    generated_at: str | None
    warnings: list[str] = Field(description="Caveats a reader must see with the summary.")


class SummaryCategory(BaseModel):
    category: str
    summary_id: int
    model_version: str | None
    generated_at: str | None
    evidence_count: int


class SummaryCategoryList(BaseModel):
    region_id: str
    items: list[SummaryCategory]


CompareResponse.model_rebuild()
