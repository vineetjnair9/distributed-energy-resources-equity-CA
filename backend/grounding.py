"""Deterministic checks that a summary's claims match the evidence it cites.

Citation checks prove a summary points at real records from its own region,
but not that the text states them correctly. A pilot run showed the failure
that matters: with all sections generated in one request, one section borrowed
another's caveat ("observed as zero in nearly every region") and misstated a
percentile, while citing the right records. These checks catch the claims a
screening reader acts on: residual percentiles and observed-zero statements.

Pure functions over strings, so the API, the generator, and audits share them.
"""

import re

PERCENTILE = re.compile(r"\b(\d{1,3})(?:st|nd|rd|th)\b")
# Thresholds named in flag definitions, not region-specific results.
DEFINITIONAL_PERCENTILES = {"25", "75"}
ZERO_CLAIM = re.compile(
    r"observed (?:value )?(?:was|is|as|were|are) (?:reported as )?zero"
    r"|(?:was|were|is) zero in (?:nearly|almost|most|\d+%)"
    r"|zero in nearly every",
    re.IGNORECASE,
)
ZERO_SUPPORT = re.compile(
    r"actual value of 0(?![.\d]*[1-9])|observed as zero in|is 0 \w+\.|reported as zero|"
    r"is 0(?:\.0+)? (?:MW|chargers|turbines)",
    re.IGNORECASE,
)


def _ordinal(n):
    n = int(n)
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def claim_problems(summary_text, evidence_texts):
    """Return human-readable problems; an empty list means the claims check out."""
    evidence = " ".join(evidence_texts)
    problems = []
    stated = set(PERCENTILE.findall(summary_text)) - DEFINITIONAL_PERCENTILES
    unsupported = sorted(stated - set(PERCENTILE.findall(evidence)), key=int)
    if unsupported:
        problems.append(
            "states percentile ranks not in its cited evidence: "
            + ", ".join(_ordinal(p) for p in unsupported)
        )
    zero = ZERO_CLAIM.search(summary_text)
    if zero and not ZERO_SUPPORT.search(evidence):
        problems.append(f'says "{zero.group(0)}" but its cited evidence reports no zero')
    return problems
