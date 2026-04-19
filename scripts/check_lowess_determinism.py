#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import build_site_index_assets as assets


LOWESS_OUTPUTS = (
    "nonwhite_lowess_small_multiples.svg",
    "education_lowess_small_multiples.svg",
)
LOWESS_METRICS = (
    "nonwhite_lowess_small_multiples_metrics.csv",
    "education_lowess_small_multiples_metrics.csv",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_once(base_dir: Path, df) -> dict[str, str]:
    assets.GENERATED = base_dir / "figures"
    assets.OUTPUT_TABLES = base_dir / "tables"

    assets.build_predictor_lowess_small_multiples(
        df,
        x_col="combined_nonwhite_share",
        x_label="Combined non-white share",
        title="Descriptive DER gradients by combined non-white share",
        subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
        output_name="nonwhite_lowess_small_multiples.png",
        metrics_name="nonwhite_lowess_small_multiples_metrics.csv",
    )
    assets.build_predictor_lowess_small_multiples(
        df,
        x_col="pct_bachelors_plus",
        x_label="Adults with bachelor's degree or higher",
        title="Descriptive DER gradients by educational attainment",
        subtitle="Curves are deterministic LOWESS fits with seeded bootstrap 95% confidence intervals.",
        output_name="education_lowess_small_multiples.png",
        metrics_name="education_lowess_small_multiples_metrics.csv",
    )

    hashes = {}
    for filename in LOWESS_OUTPUTS:
        path = assets.GENERATED / filename
        hashes[filename] = sha256(path)
    for filename in LOWESS_METRICS:
        path = assets.OUTPUT_TABLES / filename
        hashes[filename] = sha256(path)
    return hashes


def main() -> None:
    df = assets.derive_analysis_frame()
    with tempfile.TemporaryDirectory(prefix="lowess-determinism-") as tmp:
        tmp_path = Path(tmp)
        first = render_once(tmp_path / "first", df)
        second = render_once(tmp_path / "second", df)

    if first != second:
        raise SystemExit(f"LOWESS outputs are not deterministic:\nfirst={first}\nsecond={second}")

    print("LOWESS deterministic outputs verified:")
    for filename, digest in sorted(first.items()):
        print(f"{filename}: {digest}")


if __name__ == "__main__":
    main()
