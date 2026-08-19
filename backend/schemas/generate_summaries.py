"""Generate evidence-linked summaries for each ZCTA data category.

The pipeline deliberately separates descriptive context from model screening:

1. Select evidence deterministically for each category.
2. Generate every available category section in one structured model request.
3. Validate and store each section with category-scoped evidence links.
4. Generate an overview in a second request from the stored category summaries,
   never directly from
   the full raw evidence packet.

Run a no-cost evidence preview before a pilot generation:

    python backend/schemas/generate_summaries.py --region-id 90001 --dry-run

Generate or replace selected sections:

    python backend/schemas/generate_summaries.py \
        --region-id 90001 \
        --category community_demographics model_pv overview \
        --replace-existing
"""

import argparse
import json
import os
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Sequence

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "der_tool.db"
load_dotenv(PROJECT_ROOT / ".env")

# Luna is inexpensive enough for the full ZCTA run and supports both Structured
# Outputs and Batch. Set DER_SUMMARY_MODEL to compare a stronger model in a pilot.
SUMMARY_MODEL = os.getenv("DER_SUMMARY_MODEL", "gpt-5.6-luna")
SUMMARY_VERSION = "llm_category_summary_v3_dynamic_models"
DEFAULT_REGION_LIMIT = 1
DEFAULT_CATEGORY_EVIDENCE_LIMIT = 20
MAX_MODEL_ROWS_PER_CATEGORY = 4
MIN_OVERVIEW_SOURCE_SECTIONS = 2

BASELINE_MODEL_MARKER = "Model 1 baseline (climate controls)"
DEFAULT_MODEL_FALLBACKS = (
    "Model 6B county fe",
    "Model 2D (add housing structure and tenure)",
    "Model 7 (infrastructure controls, outcome-safe)",
    "Model 8 add demand proxy",
)


@dataclass(frozen=True)
class DescriptiveCategory:
    label: str
    metric_categories: tuple[str, ...]
    focus: str
    sentence_budget: str = "1 to 3 sentences"


@dataclass(frozen=True)
class ModelCategory:
    label: str
    outcome_name: str
    preferred_model_marker: str
    focus: str
    residual_guidance: str


DESCRIPTIVE_CATEGORIES = {
    "community_demographics": DescriptiveCategory(
        label="Population and demographics",
        metric_categories=("demographic",),
        focus=(
            "Describe population and racial or ethnic composition. Convert shares "
            "to percentages when helpful, but do not infer relationships with DER "
            "outcomes or individual households. The evidence carries only the "
            "shares listed; they do not enumerate every group and will not sum to "
            "100%. Add one clause noting that other groups are not reported in "
            "the evidence, so no reader treats the remainder as any particular "
            "group. Write about the ZCTA itself: never make this summary, the "
            "evidence, or your own reporting the subject of a sentence. Report "
            "the shares in the order supplied."
        ),
    ),
    "socioeconomic_housing": DescriptiveCategory(
        label="Socioeconomic and housing context",
        sentence_budget="2 to 4 sentences",
        metric_categories=("socioeconomic", "education", "housing"),
        focus=(
            "Describe income, poverty, education, tenure, and housing composition "
            "as context. Preserve denominator definitions supplied in the evidence, "
            "including the age-25-or-older education denominator. Report every "
            "metric supplied in the packet, including median housing value and the "
            "smaller housing-structure shares; do not drop a supplied metric to "
            "save space. Do not claim these conditions explain an energy outcome."
        ),
    ),
    "energy_resource_context": DescriptiveCategory(
        label="Climate, resource, and demand context",
        metric_categories=("demand", "weather", "solar_resource", "wind_resource"),
        focus=(
            "Describe electricity demand and the available climate or resource "
            "indicators. NASA POWER values are coarse gridded indicators assigned "
            "from the ZCTA centroid, not precise ZIP-level measurements. When "
            "reported electricity usage is supplied, attribute it to its named "
            "source and carry the coverage caveat from the evidence; do not "
            "present it as total ZCTA consumption."
        ),
    ),
    "observed_der": DescriptiveCategory(
        label="Observed DER and infrastructure",
        metric_categories=("der_observed",),
        focus=(
            "Describe the reported PV, storage, charger, and turbine observations "
            "in their supplied units. Say that a value is reported as zero; do not "
            "turn a recorded zero into a claim that infrastructure definitively "
            "does not exist."
        ),
    ),
    "energy_affordability": DescriptiveCategory(
        label="Energy affordability",
        sentence_budget="3 to 4 sentences, one measure per sentence",
        metric_categories=("energy_affordability",),
        focus=(
            "Describe and define each available measure in plain language: energy "
            "burden, the affordability index, and the affordability gap. Preserve "
            "the supplied CEC definitions, including what the index combines and "
            "the gap's stated affordability threshold. Do not rank the measures as "
            "high or low without an explicit benchmark in the evidence. The 7% "
            "threshold in the gap definition applies to household burdens, so never "
            "compare it against this ZCTA-level burden or conclude from that "
            "comparison that energy is affordable here."
        ),
    ),
}

MODEL_CATEGORIES = {
    "model_pv": ModelCategory(
        label="PV screening results",
        outcome_name="y_pv",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess whether the PV residual signal persists across the two "
            "selected specifications."
        ),
        residual_guidance=(
            "For this DER outcome, a negative residual means observed adoption is "
            "below the model prediction; a positive residual means it is above."
        ),
    ),
    "model_storage": ModelCategory(
        label="Storage screening results",
        outcome_name="y_storage",
        preferred_model_marker="Model 9 + pv control (most controlled)",
        focus=(
            "Assess whether the storage residual signal persists across the two "
            "selected specifications."
        ),
        residual_guidance=(
            "For this DER outcome, a negative residual means observed deployment is "
            "below the model prediction; a positive residual means it is above."
        ),
    ),
    "model_chargers": ModelCategory(
        label="Charger screening results",
        outcome_name="y_chargers",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess the aggregate-charger residual signal. Charger-type observations "
            "belong in the observed-DER section, not this model comparison."
        ),
        residual_guidance=(
            "For this DER outcome, a negative residual means observed charger "
            "availability is below the model prediction; a positive residual means "
            "it is above."
        ),
    ),
    "model_level1_chargers": ModelCategory(
        label="Level 1 charger screening results",
        outcome_name="y_level1_chargers",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess the Level 1 charger residual signal without treating it as a "
            "count of all chargers or combining it with other charger outcomes."
        ),
        residual_guidance=(
            "A negative residual means observed Level 1 charger availability is "
            "below the model prediction; a positive residual means it is above."
        ),
    ),
    "model_level2_chargers": ModelCategory(
        label="Level 2 charger screening results",
        outcome_name="y_level2_chargers",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess the Level 2 charger residual signal without treating it as a "
            "count of all chargers or combining it with other charger outcomes."
        ),
        residual_guidance=(
            "A negative residual means observed Level 2 charger availability is "
            "below the model prediction; a positive residual means it is above."
        ),
    ),
    "model_dc_fast_chargers": ModelCategory(
        label="DC fast charger screening results",
        outcome_name="y_dc_fast_chargers",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess the DC fast charger residual signal without treating it as a "
            "count of all chargers or combining it with other charger outcomes."
        ),
        residual_guidance=(
            "A negative residual means observed DC fast charger availability is "
            "below the model prediction; a positive residual means it is above."
        ),
    ),
    "model_wind_capacity": ModelCategory(
        label="Wind-capacity screening results",
        outcome_name="y_wind_mw",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Assess the modeled wind-capacity residual signal. Do not describe the "
            "underlying turbine inventory as household-level distributed wind."
        ),
        residual_guidance=(
            "A negative residual means observed wind capacity is below the model "
            "prediction; a positive residual means it is above."
        ),
    ),
    "model_turbines": ModelCategory(
        label="Turbine-presence screening results",
        outcome_name="any_turbines",
        preferred_model_marker="Model 7 (infrastructure controls, outcome-safe)",
        focus=(
            "Describe this as a turbine-presence screening result. Do not interpret "
            "it as household-level distributed wind adoption."
        ),
        residual_guidance=(
            "The outcome records turbine presence. A negative residual means the "
            "observed binary outcome is below the fitted value; treat it only as a "
            "screening signal."
        ),
    ),
    "model_energy_burden": ModelCategory(
        label="Energy-burden screening results",
        outcome_name="energy_burden_pct",
        preferred_model_marker="Model 9A (predicting burden)",
        focus=(
            "Compare the residual direction and priority status across the supplied "
            "specifications. Follow the selected-specification guidance in the packet."
        ),
        residual_guidance=(
            "For burden outcomes, a positive residual means observed burden exceeds "
            "the model prediction. A priority flag identifies unusually high, not "
            "unusually low, residual burden."
        ),
    ),
    "model_affordability_gap": ModelCategory(
        label="Affordability-gap screening results",
        outcome_name="log_energy_gap_per_capita",
        preferred_model_marker="Model 9A (predicting burden)",
        focus=(
            "Compare the residual direction and priority status across the supplied "
            "specifications. Follow the selected-specification guidance in the packet."
        ),
        residual_guidance=(
            "For this affordability outcome, a positive residual means the observed "
            "transformed gap exceeds the model prediction. A priority flag identifies "
            "an unusually high residual gap."
        ),
    ),
}

OVERVIEW_CATEGORY = "overview"
SECTION_CATEGORIES = tuple(DESCRIPTIVE_CATEGORIES) + tuple(MODEL_CATEGORIES)
SUMMARY_CATEGORIES = SECTION_CATEGORIES + (OVERVIEW_CATEGORY,)
CATEGORY_ORDER = {category: index for index, category in enumerate(SUMMARY_CATEGORIES)}

METRIC_ORDER = (
    "total_population",
    "pct_black",
    "pct_hispanic",
    "pct_asian",
    "median_household_income",
    "poverty_rate",
    "pct_bachelors_plus",
    "median_housing_value",
    "owner_occupied_rate",
    "pct_single_family_units",
    "pct_multifamily_units",
    "pct_mobile_home_units",
    "pct_other_housing_units",
    "kwh_annual_total",
    "cdd65_2023",
    "hdd65_2023",
    "ghi_mean_kwh_m2_day_2023",
    "wind_ws10m_mean_2023",
    "wind_ws50m_mean_2023",
    "PV_system_size_DC",
    "storage_capacity_mw",
    "total_chargers",
    "level1_chargers",
    "level2_chargers",
    "dc_fast_chargers",
    "wind_turbine_count",
    "wind_capacity_mw",
    "energy_burden_pct",
    "energy_affordability_index",
    "energy_affordability_gap",
)
METRIC_ORDER_INDEX = {metric: index for index, metric in enumerate(METRIC_ORDER)}

SectionCategory = Literal[
    "community_demographics",
    "socioeconomic_housing",
    "energy_resource_context",
    "observed_der",
    "energy_affordability",
    "model_pv",
    "model_storage",
    "model_chargers",
    "model_level1_chargers",
    "model_level2_chargers",
    "model_dc_fast_chargers",
    "model_wind_capacity",
    "model_turbines",
    "model_energy_burden",
    "model_affordability_gap",
]


class SummaryPayload(BaseModel):
    """Schema-constrained result returned by the OpenAI Responses API."""

    model_config = ConfigDict(extra="forbid")

    summary_text: str = Field(
        min_length=1,
        description="A concise evidence-grounded summary with no citation footer.",
    )
    evidence_ids_used: list[StrictInt] = Field(
        min_length=1,
        description="Only evidence IDs that directly support claims in summary_text.",
    )

    @field_validator("summary_text")
    @classmethod
    def clean_summary_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary_text must not be blank")
        if "evidence used:" in value.lower():
            raise ValueError("summary_text must not include an Evidence used line")
        return value

    @field_validator("evidence_ids_used")
    @classmethod
    def deduplicate_evidence_ids(cls, values: list[int]) -> list[int]:
        return list(dict.fromkeys(values))


class SectionSummaryPayload(SummaryPayload):
    """One independently citable section in a batched region response."""

    category: SectionCategory


class SectionBatchPayload(BaseModel):
    """All requested category sections returned by one model call."""

    model_config = ConfigDict(extra="forbid")

    sections: list[SectionSummaryPayload] = Field(min_length=1)

    @field_validator("sections")
    @classmethod
    def require_unique_categories(
        cls,
        values: list[SectionSummaryPayload],
    ) -> list[SectionSummaryPayload]:
        categories = [section.category for section in values]
        if len(categories) != len(set(categories)):
            raise ValueError("sections must contain each category at most once")
        return values


@dataclass(frozen=True)
class LLMResult:
    payload: SummaryPayload
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class SectionBatchResult:
    payload: SectionBatchPayload
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class StoredSummary:
    summary_id: int
    changed: bool


@dataclass(frozen=True)
class StoredSectionBatch:
    summary_ids: dict[str, int]
    changed: bool


@dataclass
class OverviewSource:
    summary_id: int
    category: str
    summary_text: str
    evidence_ids: list[int]
    generated_at: str | None = None


_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    """Construct the client lazily so dry runs do not require an API key."""
    global _client
    if _client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        # A full-corpus run sits at the organization's tokens-per-minute ceiling,
        # so 429s are routine rather than exceptional. The SDK default of two
        # retries exhausts under sustained pressure and silently drops regions.
        _client = OpenAI(max_retries=8)
    return _client


def validate_summary_schema(conn: sqlite3.Connection) -> None:
    """Fail early when the database predates category-based summaries."""
    columns = {
        row["name"]: row
        for row in conn.execute("PRAGMA table_info(summary_responses)").fetchall()
    }
    category = columns.get("category")
    if category is None:
        raise RuntimeError(
            "summary_responses.category is missing; rebuild or migrate the database first"
        )
    if not category["notnull"]:
        raise RuntimeError(
            "summary_responses.category must be NOT NULL before generating summaries"
        )


def get_metric_evidence_for_category(
    conn: sqlite3.Connection,
    region_id: str,
    metric_categories: Sequence[str],
    limit: int = DEFAULT_CATEGORY_EVIDENCE_LIMIT,
) -> list[sqlite3.Row]:
    """Return metric evidence using structured metric categories and names."""
    if not metric_categories or limit <= 0:
        return []

    placeholders = ",".join("?" for _ in metric_categories)
    rows = conn.execute(
        f"""
        SELECT
            e.evidence_id,
            e.region_id,
            e.evidence_text,
            e.source_name,
            e.source_url,
            e.evidence_type,
            e.created_at,
            m.metric_name,
            m.metric_value,
            m.metric_unit,
            m.metric_category,
            m.observed_at
        FROM metric_observations m
        JOIN evidence_chunks e
          ON e.region_id = m.region_id
         AND e.evidence_type = 'metric'
         AND e.source_name = m.source_name
         AND INSTR(e.evidence_text, ' ' || m.metric_name || ' is ') > 0
        WHERE m.region_id = ?
          AND m.metric_category IN ({placeholders})
        ORDER BY e.evidence_id
        """,
        (region_id, *metric_categories),
    ).fetchall()

    rows = sorted(
        rows,
        key=lambda row: (
            METRIC_ORDER_INDEX.get(row["metric_name"], len(METRIC_ORDER_INDEX)),
            row["evidence_id"],
        ),
    )

    selected = []
    seen_ids = set()
    for row in rows:
        if row["evidence_id"] in seen_ids:
            continue
        selected.append(row)
        seen_ids.add(row["evidence_id"])

    available = len(selected)
    if available > limit:
        dropped = [row["metric_name"] for row in selected[limit:]]
        print(
            f"Warning: {region_id} {'/'.join(metric_categories)} has {available} "
            f"evidence rows but the limit is {limit}; dropping "
            f"{', '.join(dropped)}.",
            file=sys.stderr,
        )
    return selected[:limit]


def get_model_evidence_for_outcome(
    conn: sqlite3.Connection,
    region_id: str,
    outcome_name: str,
) -> list[sqlite3.Row]:
    """Retrieve all evidence-backed model outputs for one outcome."""
    return conn.execute(
        """
        SELECT
            e.evidence_id,
            e.region_id,
            e.evidence_text,
            e.source_name,
            e.source_url,
            e.evidence_type,
            e.created_at,
            m.outcome_name,
            m.model_version,
            m.actual_value,
            m.predicted_value,
            m.residual_value,
            m.residual_percentile,
            m.priority_flag,
            m.assumptions,
            m.generated_at AS model_generated_at
        FROM model_outputs m
        JOIN evidence_chunks e
          ON e.region_id = m.region_id
         AND e.evidence_type = 'model_output'
         AND INSTR(
             e.evidence_text,
             'For region ' || m.region_id || ', model ' || m.model_version ||
             ' for ' || m.outcome_name || ' estimated'
         ) = 1
        WHERE m.region_id = ?
          AND m.outcome_name = ?
        ORDER BY m.model_version, e.evidence_id
        """,
        (region_id, outcome_name),
    ).fetchall()


def _first_model_matching(
    rows: Sequence[sqlite3.Row],
    marker: str,
    excluded_ids: set[int],
) -> sqlite3.Row | None:
    for row in rows:
        if row["evidence_id"] not in excluded_ids and marker in row["model_version"]:
            return row
    return None


def select_model_evidence(
    rows: Sequence[sqlite3.Row],
    preferred_marker: str,
    limit: int = MAX_MODEL_ROWS_PER_CATEGORY,
) -> list[sqlite3.Row]:
    """Select baseline plus one predeclared preferred or fallback model."""
    if limit <= 0:
        return []

    selected = []
    selected_ids: set[int] = set()

    baseline = _first_model_matching(rows, BASELINE_MODEL_MARKER, selected_ids)
    if baseline is not None:
        selected.append(baseline)
        selected_ids.add(baseline["evidence_id"])

    comparison_markers = (preferred_marker,) + tuple(
        marker for marker in DEFAULT_MODEL_FALLBACKS if marker != preferred_marker
    )
    for marker in comparison_markers:
        if len(selected) >= limit:
            break
        comparison = _first_model_matching(rows, marker, selected_ids)
        if comparison is not None:
            selected.append(comparison)
            selected_ids.add(comparison["evidence_id"])

    # A partially populated model table should still yield a usable section.
    if not selected and rows:
        selected.append(rows[0])

    return selected[:limit]


def get_evidence_for_category(
    conn: sqlite3.Connection,
    region_id: str,
    category: str,
    limit: int = DEFAULT_CATEGORY_EVIDENCE_LIMIT,
) -> list[sqlite3.Row]:
    """Select the bounded evidence packet for one summary category."""
    if category in DESCRIPTIVE_CATEGORIES:
        config = DESCRIPTIVE_CATEGORIES[category]
        return get_metric_evidence_for_category(
            conn,
            region_id,
            config.metric_categories,
            limit=limit,
        )

    if category in MODEL_CATEGORIES:
        config = MODEL_CATEGORIES[category]
        rows = get_model_evidence_for_outcome(conn, region_id, config.outcome_name)
        return select_model_evidence(
            rows,
            preferred_marker=config.preferred_model_marker,
            limit=min(limit, MAX_MODEL_ROWS_PER_CATEGORY),
        )

    if category == OVERVIEW_CATEGORY:
        raise ValueError("overview is generated from stored category summaries")
    raise ValueError(f"Unknown summary category: {category}")


def _model_display_name(model_version: str) -> str:
    """Strip the outcome and output-mode wrapper from an exported model name."""
    parts = [part.strip() for part in model_version.split(" | ")]
    return parts[1] if len(parts) >= 3 else model_version


def _selected_model_guidance(
    category: str,
    evidence_rows: Sequence[sqlite3.Row],
    preferred_marker: str | None = None,
) -> str:
    model_names = [
        _model_display_name(row["model_version"])
        for row in evidence_rows
        if "model_version" in row.keys()
    ]
    if not model_names:
        return ""

    guidance = (
        "Selected specifications, in evidence order: "
        + "; ".join(model_names)
        + ". Use only these model labels; never name an unselected specification."
    )
    comparison_names = model_names[1:]
    comparison_name = comparison_names[0] if comparison_names else None

    if len(comparison_names) > 1:
        guidance += (
            " Report the residual direction and priority status for every "
            "selected specification, and say plainly whether they agree."
        )

    # The comparison specifications are chosen per region from an ordered
    # fallback list, so two regions can be compared against different models.
    # Say so when this region did not get the preferred one.
    if (
        comparison_names
        and preferred_marker
        and not any(preferred_marker in name for name in comparison_names)
    ):
        guidance += (
            " This outcome's preferred comparison was not available for this "
            "region, so the comparisons above are fallbacks. Say that the "
            "comparison specifications are the ones available for this region, "
            "and still never name the unavailable specification."
        )

    if category in {"model_energy_burden", "model_affordability_gap"}:
        if any("Model 9A" in name for name in comparison_names):
            guidance += (
                " Model 9A adds DER outcomes and answers a different descriptive "
                "prediction question; do not present it as a robustness version of "
                "the baseline. State that distinction in the section every time "
                "Model 9A is the comparison, so the caveat does not appear for "
                "some regions and not others."
            )
        elif comparison_name:
            guidance += (
                " The selected comparison is an added-control robustness/context "
                "specification for the same outcome; assess whether the screening "
                "signal persists across it."
            )

    if category == "model_storage" and comparison_names:
        if any("Model 9 + pv control" in name for name in comparison_names):
            guidance += (
                " The selected comparison is the storage-specific PV-control model; "
                "it may be described as the most-controlled specification."
            )
        else:
            guidance += (
                " The selected comparison is an infrastructure-controls robustness "
                "specification, not the storage-specific PV-control model."
            )

    return guidance


def category_task_rules(
    category: str,
    evidence_rows: Sequence[sqlite3.Row] = (),
) -> str:
    """Return the section-specific rules included in a batch packet."""
    if category in DESCRIPTIVE_CATEGORIES:
        config = DESCRIPTIVE_CATEGORIES[category]
        return (
            f"Section: {config.label}.\n"
            f"Focus: {config.focus}\n"
            f"Write {config.sentence_budget}. Keep the section descriptive. State "
            "the shared observation period once when it is supplied in the evidence."
        )

    if category in MODEL_CATEGORIES:
        config = MODEL_CATEGORIES[category]
        selected_model_guidance = _selected_model_guidance(
            category,
            evidence_rows,
            config.preferred_model_marker,
        )
        return (
            f"Section: {config.label}.\n"
            f"Outcome: {config.outcome_name}.\n"
            f"Focus: {config.focus}\n"
            f"Selected-specification guidance: {selected_model_guidance}\n"
            f"Residual interpretation: {config.residual_guidance}\n"
            "Write 4 to 5 sentences. Compare only the supplied specifications, "
            "covering every one of them. "
            "When the evidence says the observed value is zero, say the observed "
            "value was zero rather than that it was estimated or predicted as "
            "zero, and do not describe a positive residual as observed deployment "
            "above the prediction. When the evidence says the outcome is observed as zero in "
            "nearly every region, carry that caveat: the percentile orders fitted "
            "values and does not establish an observed shortfall here. When the "
            "evidence says a rounded percentile falls on the cutoff, report the "
            "priority status without restating the numeric cutoff rule as the "
            "explanation. When the residual direction differs across the selected "
            "specifications, say the direction did not persist. When the evidence "
            "gives the count of all fitted specifications sharing a residual "
            "direction, report that count in one clause; it shows how contested "
            "the direction is beyond the specifications compared here. "
            "The actual, predicted, and residual values may be on a transformed "
            "model scale, so emphasize direction, the ordinal residual percentile, "
            "and the stated priority status instead of presenting transformed values "
            "as natural units. Explain priority in plain language; never print the "
            "internal numeric flag code."
        )

    raise ValueError(f"Cannot build section rules for {category}")


def build_section_batch_prompt(
    region_id: str,
    evidence_by_category: dict[str, Sequence[sqlite3.Row]],
) -> tuple[str, str]:
    """Build one prompt containing isolated evidence packets for all sections."""
    if not evidence_by_category:
        raise ValueError("At least one category evidence packet is required")

    instructions = """
You write concise, independently citable sections for a Distributed Energy Resource
equity decision-support tool.

Use only the supplied evidence. Do not invent facts or use outside knowledge. Do not
infer an association merely because two facts appear in the same packet. Never claim
that race, income, housing, climate, utility context, or socioeconomic conditions cause
an observed or modeled outcome. Treat model residuals and flags as screening signals,
not proof of causation or need. Do not call a value high, low, above average, or below
average unless the evidence supplies a benchmark. Refer to the geography as a ZCTA.
Preserve definitions and units from the evidence. Use its human-readable precision;
do not expose additional decimal places or raw database-style values.
Do not label community characteristics as constraints, vulnerability, disadvantage,
underservice, or need. For transformed model residuals, state only positive or negative
direction; never characterize their magnitude as slight, small, large, or substantial.

Write in the past tense throughout, including for model results. Report a percentile
below the first as "below the 1st percentile" rather than as the 0th percentile. Keep
each reported value at the precision used in the evidence.

Each category packet is an isolated evidence scope. Produce exactly one section for
every supplied packet, preserve its category key exactly, and produce no extra
categories. A section may use only evidence IDs from its own packet. Never carry a fact
or evidence ID from one category into another. Return only evidence IDs that directly
support claims in that section. Do not add an Evidence used line or citation footer.
""".strip()

    packets = []
    for category in SECTION_CATEGORIES:
        evidence_rows = evidence_by_category.get(category)
        if not evidence_rows:
            continue
        packets.append(
            {
                "category": category,
                "task_rules": category_task_rules(category, evidence_rows),
                "evidence": [
                    {
                        "evidence_id": row["evidence_id"],
                        "text": row["evidence_text"],
                    }
                    for row in evidence_rows
                ],
            }
        )

    prompt = json.dumps(
        {
            "region_id": region_id,
            "category_packets": packets,
        },
        ensure_ascii=False,
        indent=2,
    )
    return instructions, prompt


def _extract_usage(response) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None, None
    return getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)


def validate_llm_evidence_ids(
    payload: SummaryPayload,
    allowed_evidence_ids: set[int],
) -> SummaryPayload:
    invalid_ids = sorted(set(payload.evidence_ids_used) - allowed_evidence_ids)
    if invalid_ids:
        raise ValueError(f"Summary cited evidence IDs not in its packet: {invalid_ids}")
    if not payload.evidence_ids_used:
        raise ValueError("Summary must cite at least one supplied evidence ID")
    return payload


def validate_section_batch_payload(
    payload: SectionBatchPayload,
    evidence_by_category: dict[str, Sequence[sqlite3.Row]],
) -> SectionBatchPayload:
    expected_categories = set(evidence_by_category)
    returned_categories = {section.category for section in payload.sections}
    if returned_categories != expected_categories:
        missing = sorted(expected_categories - returned_categories)
        unexpected = sorted(returned_categories - expected_categories)
        raise ValueError(
            f"Section category mismatch: missing={missing}, unexpected={unexpected}"
        )

    for section in payload.sections:
        allowed_ids = {
            row["evidence_id"] for row in evidence_by_category[section.category]
        }
        validate_llm_evidence_ids(section, allowed_ids)
    return payload


def generate_section_batch_with_llm(
    region_id: str,
    evidence_by_category: dict[str, Sequence[sqlite3.Row]],
) -> SectionBatchResult:
    """Generate all requested category sections in one structured response."""
    instructions, prompt = build_section_batch_prompt(
        region_id,
        evidence_by_category,
    )
    response = get_openai_client().responses.parse(
        model=SUMMARY_MODEL,
        reasoning={"effort": "none"},
        instructions=instructions,
        input=prompt,
        text_format=SectionBatchPayload,
    )
    payload = response.output_parsed
    if payload is None:
        raise ValueError("The model response did not contain parsed category sections")

    payload = validate_section_batch_payload(payload, evidence_by_category)
    input_tokens, output_tokens = _extract_usage(response)
    return SectionBatchResult(payload, input_tokens, output_tokens)


def get_existing_summary_id(
    conn: sqlite3.Connection,
    region_id: str,
    category: str,
    model_version: str = SUMMARY_VERSION,
) -> int | None:
    row = conn.execute(
        """
        SELECT summary_id
        FROM summary_responses
        WHERE region_id = ?
          AND category = ?
          AND model_version = ?
        """,
        (region_id, category, model_version),
    ).fetchone()
    return None if row is None else row["summary_id"]


def link_summary_to_evidence(
    conn: sqlite3.Connection,
    summary_id: int,
    evidence_ids: Sequence[int],
) -> None:
    conn.executemany(
        """
        INSERT OR IGNORE INTO summary_evidence (summary_id, evidence_id)
        VALUES (?, ?)
        """,
        [(summary_id, evidence_id) for evidence_id in dict.fromkeys(evidence_ids)],
    )


def log_llm_usage(
    conn: sqlite3.Connection,
    region_id: str,
    task_type: str,
    input_tokens: int | None,
    output_tokens: int | None,
    created_at: str,
) -> None:
    conn.execute(
        """
        INSERT INTO llm_usage_log (
            user_id,
            region_id,
            task_type,
            model_name,
            input_tokens,
            output_tokens,
            estimated_cost_usd,
            created_at
        )
        VALUES (NULL, ?, ?, ?, ?, ?, NULL, ?)
        """,
        (
            region_id,
            task_type,
            SUMMARY_MODEL,
            input_tokens,
            output_tokens,
            created_at,
        ),
    )


def store_summary_response(
    conn: sqlite3.Connection,
    region_id: str,
    category: str,
    payload: SummaryPayload,
    metric_snapshot: dict,
    existing_summary_id: int | None = None,
    model_version: str = SUMMARY_VERSION,
    generated_at: str | None = None,
) -> int:
    """Insert or atomically replace one summary and its evidence links."""
    generated_at = generated_at or datetime.now(timezone.utc).isoformat()
    snapshot_json = json.dumps(metric_snapshot, sort_keys=True)

    if existing_summary_id is None:
        cursor = conn.execute(
            """
            INSERT INTO summary_responses (
                category,
                region_id,
                summary_text,
                metric_snapshot,
                model_version,
                generated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                category,
                region_id,
                payload.summary_text,
                snapshot_json,
                model_version,
                generated_at,
            ),
        )
        summary_id = cursor.lastrowid
    else:
        summary_id = existing_summary_id
        conn.execute(
            "DELETE FROM summary_evidence WHERE summary_id = ?",
            (summary_id,),
        )
        conn.execute(
            """
            UPDATE summary_responses
            SET summary_text = ?,
                metric_snapshot = ?,
                generated_at = ?
            WHERE summary_id = ?
            """,
            (
                payload.summary_text,
                snapshot_json,
                generated_at,
                summary_id,
            ),
        )

    link_summary_to_evidence(conn, summary_id, payload.evidence_ids_used)
    return summary_id


def generate_and_store_section_batch(
    conn: sqlite3.Connection,
    region_id: str,
    categories: Sequence[str],
    evidence_limit: int = DEFAULT_CATEGORY_EVIDENCE_LIMIT,
    replace_existing: bool = False,
) -> StoredSectionBatch:
    """Generate pending category sections in one call and store them atomically."""
    requested_categories = tuple(dict.fromkeys(categories))
    invalid_categories = sorted(set(requested_categories) - set(SECTION_CATEGORIES))
    if invalid_categories:
        raise ValueError(f"Not section categories: {invalid_categories}")

    existing_ids: dict[str, int] = {}
    evidence_by_category: dict[str, Sequence[sqlite3.Row]] = {}
    skipped_existing = []
    skipped_without_evidence = []

    for category in requested_categories:
        existing_id = get_existing_summary_id(conn, region_id, category)
        if existing_id is not None:
            existing_ids[category] = existing_id
            if not replace_existing:
                skipped_existing.append(category)
                continue

        evidence_rows = get_evidence_for_category(
            conn,
            region_id,
            category,
            limit=evidence_limit,
        )
        if not evidence_rows:
            skipped_without_evidence.append(category)
            continue
        evidence_by_category[category] = evidence_rows

    if skipped_existing:
        print(
            f"Skipping {region_id} existing sections: "
            f"{', '.join(skipped_existing)}."
        )
    if skipped_without_evidence:
        print(
            f"Skipping {region_id} sections without evidence: "
            f"{', '.join(skipped_without_evidence)}."
        )
    if not evidence_by_category:
        return StoredSectionBatch(existing_ids, changed=False)

    result = generate_section_batch_with_llm(region_id, evidence_by_category)
    sections_by_category = {
        section.category: section for section in result.payload.sections
    }
    generated_at = datetime.now(timezone.utc).isoformat()
    batch_categories = [
        category for category in SECTION_CATEGORIES if category in evidence_by_category
    ]
    stored_ids = dict(existing_ids)

    try:
        for category in batch_categories:
            section = sections_by_category[category]
            evidence_rows = evidence_by_category[category]
            evidence_ids = [row["evidence_id"] for row in evidence_rows]
            metric_snapshot = {
                "region_id": region_id,
                "category": category,
                "evidence_ids_retrieved": evidence_ids,
                "evidence_ids_linked": section.evidence_ids_used,
                "source_model_versions": [
                    row["model_version"]
                    for row in evidence_rows
                    if "model_version" in row.keys()
                ],
                "source_observation_periods": sorted(
                    {
                        str(row["observed_at"])
                        for row in evidence_rows
                        if "observed_at" in row.keys() and row["observed_at"] is not None
                    }
                ),
                "batch_categories": batch_categories,
                "summary_model": SUMMARY_MODEL,
                "summary_version": SUMMARY_VERSION,
            }
            stored_ids[category] = store_summary_response(
                conn,
                region_id,
                category,
                section,
                metric_snapshot,
                existing_summary_id=existing_ids.get(category),
                generated_at=generated_at,
            )

        log_llm_usage(
            conn,
            region_id,
            "category_summary_batch",
            result.input_tokens,
            result.output_tokens,
            generated_at,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    actions = [
        f"{category}={stored_ids[category]}"
        for category in batch_categories
    ]
    print(
        f"Generated {region_id} section batch ({len(batch_categories)} sections): "
        f"{', '.join(actions)}"
    )
    return StoredSectionBatch(stored_ids, changed=True)


def get_overview_sources(
    conn: sqlite3.Connection,
    region_id: str,
    model_version: str = SUMMARY_VERSION,
) -> list[OverviewSource]:
    """Load category summaries and their raw evidence links for synthesis."""
    rows = conn.execute(
        """
        SELECT
            sr.summary_id,
            sr.category,
            sr.summary_text,
            sr.generated_at,
            se.evidence_id
        FROM summary_responses sr
        LEFT JOIN summary_evidence se
          ON se.summary_id = sr.summary_id
        WHERE sr.region_id = ?
          AND sr.model_version = ?
          AND sr.category != ?
        ORDER BY sr.summary_id, se.evidence_id
        """,
        (region_id, model_version, OVERVIEW_CATEGORY),
    ).fetchall()

    by_id: dict[int, OverviewSource] = {}
    for row in rows:
        source = by_id.setdefault(
            row["summary_id"],
            OverviewSource(
                summary_id=row["summary_id"],
                category=row["category"],
                summary_text=row["summary_text"],
                evidence_ids=[],
                generated_at=row["generated_at"],
            ),
        )
        if row["evidence_id"] is not None:
            source.evidence_ids.append(row["evidence_id"])

    return sorted(
        (source for source in by_id.values() if source.evidence_ids),
        key=lambda source: CATEGORY_ORDER.get(source.category, len(CATEGORY_ORDER)),
    )


def overview_is_stale(
    conn: sqlite3.Connection,
    region_id: str,
    sources: Sequence[OverviewSource],
    model_version: str = SUMMARY_VERSION,
) -> bool:
    """Report whether any source section is newer than the stored overview.

    Regenerating a single category with --category leaves the overview behind,
    still citing summary text that has since been replaced. Compare timestamps so
    a stale overview is rebuilt instead of silently surviving.
    """
    row = conn.execute(
        """
        SELECT generated_at
        FROM summary_responses
        WHERE region_id = ?
          AND category = ?
          AND model_version = ?
        """,
        (region_id, OVERVIEW_CATEGORY, model_version),
    ).fetchone()
    if row is None or row["generated_at"] is None:
        return False

    source_times = [
        source.generated_at for source in sources if source.generated_at is not None
    ]
    if not source_times:
        return False
    return max(source_times) > row["generated_at"]


def missing_section_categories(
    conn: sqlite3.Connection,
    region_id: str,
    sources: Sequence[OverviewSource],
) -> list[str]:
    """Return section categories this region has no summary for.

    A region can be missing a whole subject area (90010 has no affordability
    sections at all). Without naming the gap the overview reads as though the
    subject was assessed and found unremarkable.
    """
    present = {source.category for source in sources}
    return [
        category
        for category in SECTION_CATEGORIES
        if category not in present
    ]


def build_overview_prompt(
    region_id: str,
    sources: Sequence[OverviewSource],
    missing_categories: Sequence[str] = (),
) -> tuple[str, str]:
    instructions = """
You write the integrated overview for a Distributed Energy Resource equity
decision-support tool. Synthesize only the supplied, already validated category
summaries. Do not introduce a new fact, relationship, causal explanation, ranking, or
interpretation. Do not infer that community characteristics explain energy outcomes.
Treat model results only as screening signals.

Write 3 to 5 sentences and prioritize at most three decision-relevant findings. Mention
a material limitation when one is stated in the source summaries. Return only evidence
IDs attached to the source sections that directly support the overview. Do not add an
Evidence used line or citation footer. Do not label community characteristics as
constraints, vulnerability, disadvantage, underservice, or need. Do not characterize
the magnitude of a transformed residual; report only its direction, ordinal percentile,
and stated priority status.

Refer to the geography as a ZCTA, never as "the region" or "the area". Write about the
ZCTA itself rather than about these summaries. State only what applies; never explain
why a caveat, rule, or comparison did not apply, and never mention the evidence, the
packet, or these instructions.

Write in the past tense throughout. When a source summary says an outcome is observed
as zero in nearly every region, or that a positive residual reflects a negative fitted
value, do not present that outcome as a headline finding; a screening signal on an
outcome with almost no observed variation does not distinguish this region. When the
listed unavailable categories are non-empty, state in one clause that those subjects
were not assessed for this region, so a reader does not read their absence as a finding.
Never compare a ZCTA-level energy burden to the 7% household affordability threshold;
they are different units of analysis.
""".strip()

    section_lines = []
    for source in sources:
        ids = ", ".join(str(evidence_id) for evidence_id in source.evidence_ids)
        section_lines.append(
            f"[Section {source.category}; supporting evidence IDs: {ids}] "
            f"{source.summary_text}"
        )

    unavailable = ", ".join(missing_categories) if missing_categories else "none"
    prompt = f"""
Region ID: {region_id}

Categories with no summary for this region (not assessed): {unavailable}

Validated category summaries:
{chr(10).join(section_lines)}
""".strip()
    return instructions, prompt


def generate_overview_with_llm(
    region_id: str,
    sources: Sequence[OverviewSource],
    missing_categories: Sequence[str] = (),
) -> LLMResult:
    instructions, prompt = build_overview_prompt(
        region_id,
        sources,
        missing_categories,
    )
    response = get_openai_client().responses.parse(
        model=SUMMARY_MODEL,
        reasoning={"effort": "none"},
        instructions=instructions,
        input=prompt,
        text_format=SummaryPayload,
    )
    payload = response.output_parsed
    if payload is None:
        raise ValueError("The model response did not contain a parsed overview")

    allowed_ids = {
        evidence_id
        for source in sources
        for evidence_id in source.evidence_ids
    }
    payload = validate_llm_evidence_ids(payload, allowed_ids)
    input_tokens, output_tokens = _extract_usage(response)
    return LLMResult(payload, input_tokens, output_tokens)


def generate_and_store_overview(
    conn: sqlite3.Connection,
    region_id: str,
    replace_existing: bool = False,
) -> StoredSummary | None:
    existing_id = get_existing_summary_id(conn, region_id, OVERVIEW_CATEGORY)
    sources = get_overview_sources(conn, region_id)
    stale = existing_id is not None and overview_is_stale(conn, region_id, sources)

    if existing_id is not None and not replace_existing:
        if not stale:
            print(f"Skipping {region_id}/overview: summary already exists.")
            return StoredSummary(existing_id, changed=False)
        print(
            f"Rebuilding {region_id}/overview: a category summary is newer than "
            "the stored overview."
        )

    if len(sources) < MIN_OVERVIEW_SOURCE_SECTIONS:
        print(
            f"Skipping {region_id}/overview: requires at least "
            f"{MIN_OVERVIEW_SOURCE_SECTIONS} category summaries."
        )
        return None

    missing_categories = missing_section_categories(conn, region_id, sources)
    result = generate_overview_with_llm(region_id, sources, missing_categories)
    metric_snapshot = {
        "region_id": region_id,
        "category": OVERVIEW_CATEGORY,
        "source_summary_ids": [source.summary_id for source in sources],
        "source_categories": [source.category for source in sources],
        "unavailable_categories": missing_categories,
        "evidence_ids_linked": result.payload.evidence_ids_used,
        "summary_model": SUMMARY_MODEL,
        "summary_version": SUMMARY_VERSION,
    }
    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        summary_id = store_summary_response(
            conn,
            region_id,
            OVERVIEW_CATEGORY,
            result.payload,
            metric_snapshot,
            existing_summary_id=existing_id,
            generated_at=generated_at,
        )
        log_llm_usage(
            conn,
            region_id,
            "category_summary:overview",
            result.input_tokens,
            result.output_tokens,
            generated_at,
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    action = "Replaced" if existing_id is not None else "Generated"
    print(f"{action} {region_id}/overview: summary_id={summary_id}")
    return StoredSummary(summary_id, changed=True)


def normalize_region_id(value: str) -> str:
    return value.strip().split(".")[0].zfill(5)


def select_region_ids(conn: sqlite3.Connection, args: argparse.Namespace) -> list[str]:
    if args.region_id:
        requested = list(dict.fromkeys(normalize_region_id(value) for value in args.region_id))
        placeholders = ",".join("?" for _ in requested)
        found = [
            row["region_id"]
            for row in conn.execute(
                f"""
                SELECT region_id
                FROM regions
                WHERE region_id IN ({placeholders})
                ORDER BY region_id
                """,
                requested,
            ).fetchall()
        ]
        missing = sorted(set(requested) - set(found))
        if missing:
            print(f"Warning: region IDs not found: {', '.join(missing)}", file=sys.stderr)
        return found

    if args.all:
        return [
            row["region_id"]
            for row in conn.execute(
                "SELECT region_id FROM regions ORDER BY region_id"
            ).fetchall()
        ]

    return [
        row["region_id"]
        for row in conn.execute(
            "SELECT region_id FROM regions ORDER BY region_id LIMIT ?",
            (args.limit,),
        ).fetchall()
    ]


def preview_region(
    conn: sqlite3.Connection,
    region_id: str,
    categories: Sequence[str],
    evidence_limit: int,
) -> None:
    for category in categories:
        if category == OVERVIEW_CATEGORY:
            sources = get_overview_sources(conn, region_id)
            source_names = ", ".join(source.category for source in sources) or "none"
            print(f"{region_id}/overview: existing source sections={source_names}")
            continue
        rows = get_evidence_for_category(
            conn,
            region_id,
            category,
            limit=evidence_limit,
        )
        ids = ",".join(str(row["evidence_id"]) for row in rows) or "none"
        print(f"{region_id}/{category}: {len(rows)} evidence rows [{ids}]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate and store category-based LLM summaries by ZCTA."
    )
    targets = parser.add_mutually_exclusive_group()
    targets.add_argument(
        "--all",
        action="store_true",
        help="Generate summaries for all regions.",
    )
    targets.add_argument(
        "--region-id",
        nargs="+",
        help="One or more specific region IDs to summarize.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_REGION_LIMIT,
        help=f"Number of regions for a pilot run. Defaults to {DEFAULT_REGION_LIMIT}.",
    )
    parser.add_argument(
        "--category",
        nargs="+",
        choices=SUMMARY_CATEGORIES,
        help="Categories to generate. Defaults to all categories.",
    )
    parser.add_argument(
        "--replace-existing",
        action="store_true",
        help="Replace existing summaries for the current category summary version.",
    )
    parser.add_argument(
        "--evidence-limit",
        type=int,
        default=DEFAULT_CATEGORY_EVIDENCE_LIMIT,
        help="Maximum evidence rows supplied to each category.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print selected evidence without calling the API or writing summaries.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit must be positive")
    if args.evidence_limit <= 0:
        parser.error("--evidence-limit must be positive")

    requested_categories = tuple(args.category or SUMMARY_CATEGORIES)
    section_categories = tuple(
        category for category in requested_categories if category != OVERVIEW_CATEGORY
    )
    wants_overview = OVERVIEW_CATEGORY in requested_categories

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # Each region commits a handful of rows between multi-second API calls, so
    # several processes can split the region list. Wait for the write lock
    # instead of failing the region when their commits overlap.
    conn.execute("PRAGMA busy_timeout = 30000")
    failures: list[str] = []
    stale_overviews: list[str] = []
    try:
        validate_summary_schema(conn)
        region_ids = select_region_ids(conn, args)

        for region_id in region_ids:
            if args.dry_run:
                preview_region(
                    conn,
                    region_id,
                    requested_categories,
                    args.evidence_limit,
                )
                continue

            section_changed = False
            section_failed = False
            if section_categories:
                try:
                    stored = generate_and_store_section_batch(
                        conn,
                        region_id,
                        section_categories,
                        evidence_limit=args.evidence_limit,
                        replace_existing=args.replace_existing,
                    )
                    section_changed = stored.changed
                except Exception as exc:
                    conn.rollback()
                    section_failed = True
                    failure = f"{region_id}/section_batch: {exc}"
                    failures.append(failure)
                    print(f"Failed {failure}", file=sys.stderr)

            if wants_overview and section_failed:
                print(
                    f"Skipping {region_id}/overview because its section batch failed.",
                    file=sys.stderr,
                )
            elif not wants_overview and section_changed:
                # Regenerating a subset of categories leaves the stored overview
                # citing text that no longer exists. Say so rather than let it
                # pass as current.
                stale_overviews.append(region_id)
                print(
                    f"Warning: {region_id} sections changed but overview was not "
                    "requested; the stored overview is now stale.",
                    file=sys.stderr,
                )
            elif wants_overview:
                try:
                    generate_and_store_overview(
                        conn,
                        region_id,
                        replace_existing=args.replace_existing or section_changed,
                    )
                except Exception as exc:
                    conn.rollback()
                    failure = f"{region_id}/overview: {exc}"
                    failures.append(failure)
                    print(f"Failed {failure}", file=sys.stderr)
    finally:
        conn.close()

    if stale_overviews:
        print(
            f"{len(stale_overviews)} overview(s) are stale after this run. Refresh "
            "them with: --region-id "
            f"{' '.join(stale_overviews)} --category overview",
            file=sys.stderr,
        )

    if failures:
        print(f"Completed with {len(failures)} failed category summaries.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
