"""Claim checks: a summary must state the percentiles and zeros its evidence states."""

from backend.grounding import claim_problems

PV_EVIDENCE = [
    "For region 90011, model y_pv | Model 6B county fe | raw for y_pv estimated an actual "
    "value of 2.6451, a predicted value of 4.368, and a residual of -1.7229. The residual "
    "ranks at the 6th percentile within the fitted sample. Priority status: flagged. For DER "
    "outcomes, flagged means the residual is at or below the outcome-model's "
    "25th-percentile residual cutoff.",
]


def test_accurate_summary_passes():
    text = ("The PV residual ranked at the 6th percentile and was flagged, meaning it fell at "
            "or below the 25th-percentile cutoff.")
    assert claim_problems(text, PV_EVIDENCE) == []


def test_misstated_percentile_is_caught():
    # Observed in the pilot: the 6th percentile was reported as "below the 1st".
    problems = claim_problems("It ranked below the 1st percentile in Model 6B.", PV_EVIDENCE)
    assert problems == ["states percentile ranks not in its cited evidence: 1st"]


def test_borrowed_zero_caveat_is_caught():
    # Observed in the pilot: a Level 1 charger caveat leaked into the PV section.
    text = "The observed value was zero, and the outcome was zero in nearly every region."
    assert any("reports no zero" in p for p in claim_problems(text, PV_EVIDENCE))


def test_zero_claim_backed_by_evidence_passes():
    evidence = ["For region 90050, ... metric wind_capacity_mw is 0 MW. Observation period: 2023.",
                "estimated an actual value of 0, a predicted value of 0.12. This outcome is "
                "observed as zero in 98% of fitted regions."]
    assert claim_problems("The observed value was zero in this ZCTA.", evidence) == []


def test_below_first_paraphrases_a_zeroth_percentile():
    evidence = ["The residual ranks at the 0th percentile within the fitted sample."]
    assert claim_problems("It ranked below the 1st percentile.", evidence) == []
    # ...but not when the evidence has no 0th percentile to paraphrase.
    assert claim_problems("It ranked below the 1st percentile.", PV_EVIDENCE)
