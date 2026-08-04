#!/usr/bin/env python3
"""One entrypoint for the whole pipeline: data -> models -> clustering -> figures.

Each stage is independently runnable, and every stage is skippable, so this doubles as
the "what order do things go in" documentation that was previously only in the README.

Quick start
-----------
    # Everything, reusing the fixed 2023 climate pulls (~15 min)
    CENSUS_API_KEY=... python scripts/run_all.py

    # Everything, re-pulling NASA POWER too (~1 hour longer, same values)
    CENSUS_API_KEY=... python scripts/run_all.py --full-external

    # No network at all: reuse every processed file, just refit and redraw
    python scripts/run_all.py --skip-data

    # Just redraw figures after editing paper_figure_utils.py
    python scripts/run_all.py --only figures

Stages
------
    data       rebuild_processed_data.py       -> data/processed/*.csv
    models     run_regression_notebook.py      -> outputs/{standardized_,}tables/*.csv
    clustering run_notebook.py clustering      -> outputs/tables/pca_kmeans_*.csv
    figures    regenerate_standardized_figures.py
               build_site_index_assets.py
               sync_figure_assets.py           -> outputs/**/*.png|svg|pdf, site/assets

Environment
-----------
    CENSUS_API_KEY   required unless --skip-data or --skip-external
    FIGURE_BG        'white' (default, journal-ready) or 'transparent'
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

STAGES = ["data", "models", "clustering", "figures"]


def _run(cmd: list[str], label: str) -> None:
    print(f"\n{'=' * 72}\n[{label}] {' '.join(str(c) for c in cmd)}\n{'=' * 72}", flush=True)
    started = time.monotonic()
    result = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise SystemExit(f"[{label}] FAILED after {elapsed:.0f}s (exit {result.returncode})")
    print(f"[{label}] done in {elapsed:.0f}s", flush=True)


def stage_data(args: argparse.Namespace) -> None:
    cmd = [sys.executable, str(SCRIPTS / "rebuild_processed_data.py")]
    if args.skip_external:
        cmd.append("--skip-external")
    elif not args.full_external:
        # Default: pull ACS live (needed for the housing-structure controls) but reuse
        # the 2023 NASA POWER files, which are a fixed historical reanalysis.
        cmd.append("--reuse-nasa")
    _run(cmd, "data")


def stage_models(args: argparse.Namespace) -> None:
    cmd = [sys.executable, str(SCRIPTS / "run_regression_notebook.py"), "--skip-figure-scripts"]
    if args.outcomes:
        cmd += ["--outcomes", *args.outcomes]
    _run(cmd, "models")


def stage_clustering(args: argparse.Namespace) -> None:
    _run([sys.executable, str(SCRIPTS / "run_notebook.py"), "clustering"], "clustering")


def stage_figures(args: argparse.Namespace) -> None:
    for script in ["regenerate_standardized_figures.py", "build_site_index_assets.py", "sync_figure_assets.py"]:
        _run([sys.executable, str(SCRIPTS / script)], f"figures:{script.replace('.py', '')}")


RUNNERS = {
    "data": stage_data,
    "models": stage_models,
    "clustering": stage_clustering,
    "figures": stage_figures,
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--only", nargs="+", choices=STAGES, help="Run only these stages.")
    for stage in STAGES:
        parser.add_argument(f"--skip-{stage}", action="store_true", help=f"Skip the {stage} stage.")
    parser.add_argument(
        "--full-external",
        action="store_true",
        help="Re-pull NASA POWER as well as ACS (~5,500 requests, ~1 hour, same values).",
    )
    parser.add_argument(
        "--skip-external",
        action="store_true",
        help="Make no network calls at all; reuse every existing external-derived file.",
    )
    parser.add_argument("--outcomes", nargs="+", help="Restrict the model stage to these outcomes.")
    args = parser.parse_args()

    selected = args.only or [s for s in STAGES if not getattr(args, f"skip_{s}")]

    if "data" in selected and not args.skip_external and not os.environ.get("CENSUS_API_KEY"):
        raise SystemExit(
            "CENSUS_API_KEY is not set. Export it (or put it in .env and source that), "
            "or pass --skip-data / --skip-external.\n"
            "Without a live ACS pull the housing-structure controls cannot be built, and "
            "the rebuild will stop rather than silently emit empty columns."
        )

    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("FIGURE_BG", "white")

    print(f"Stages: {' -> '.join(selected)}")
    print(f"Figure background: {os.environ['FIGURE_BG']}")
    started = time.monotonic()
    for stage in STAGES:
        if stage in selected:
            RUNNERS[stage](args)
    print(f"\nAll stages completed in {time.monotonic() - started:.0f}s.")


if __name__ == "__main__":
    main()
