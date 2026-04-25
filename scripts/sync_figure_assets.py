#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from paper_figure_utils import sync_site_tree


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_FIGURES = ROOT / "outputs" / "figures"
STANDARDIZED_FIGURES = ROOT / "outputs" / "standardized_figures"
SITE_FIGURES = ROOT / "site" / "assets" / "figures"


def main() -> None:
    copied = []

    copied.extend(sync_site_tree(STANDARDIZED_FIGURES, SITE_FIGURES))

    generated = OUTPUT_FIGURES / "generated"
    if generated.exists():
        copied.extend(sync_site_tree(generated, SITE_FIGURES / "generated"))

    for subdir in [
        "pv_maps",
        "storage_maps",
        "chargers_maps",
        "wind_mw_maps",
    ]:
        src = OUTPUT_FIGURES / subdir
        if src.exists():
            copied.extend(sync_site_tree(src, SITE_FIGURES / "generated" / subdir, patterns=("*.png",)))

    print(f"Copied {len(copied)} figure assets into site/assets/figures")


if __name__ == "__main__":
    main()
