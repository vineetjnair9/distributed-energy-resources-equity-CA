#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "regression.ipynb"
EXECUTED_DIR = ROOT / "outputs" / "executed_notebooks"
DEFAULT_OUTCOMES = [
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_wind_mw",
    "y_level1_chargers",
    "y_level2_chargers",
    "y_dc_fast_chargers",
    "energy_burden_pct",
    "log_energy_gap_per_capita",
]


def _patched_source(source: str, *, outcomes: list[str]) -> str:
    lines = source.splitlines()
    patched = []
    skipping_assignment = False
    bracket_depth = 0
    replaced = False

    for line in lines:
        stripped = line.strip()
        if skipping_assignment:
            bracket_depth += stripped.count("[") - stripped.count("]")
            if bracket_depth <= 0:
                skipping_assignment = False
            continue
        if stripped.startswith("OUTCOMES_TO_RUN = "):
            patched.append(f"OUTCOMES_TO_RUN = {outcomes!r}")
            replaced = True
            rhs = stripped.split("=", 1)[1].strip()
            bracket_depth = rhs.count("[") - rhs.count("]")
            skipping_assignment = bracket_depth > 0
            continue
        patched.append(line)

    if not replaced:
        raise ValueError("Could not find OUTCOMES_TO_RUN in regression.ipynb cell 1.")
    return "\n".join(patched) + ("\n" if source.endswith("\n") else "")


def run_notebook(outcomes: list[str], timeout: int) -> Path:
    nb = nbformat.read(NOTEBOOK, as_version=4)
    nb.cells[1].source = _patched_source(nb.cells[1].source, outcomes=outcomes)

    client = NotebookClient(
        nb,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK.parent)}},
        allow_errors=False,
    )
    client.execute()

    EXECUTED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = EXECUTED_DIR / "regression.executed.ipynb"
    nbformat.write(nb, out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run regression.ipynb for one or more outcomes.")
    parser.add_argument(
        "--outcomes",
        nargs="+",
        default=DEFAULT_OUTCOMES,
        help="Outcome columns to rerun.",
    )
    parser.add_argument("--timeout", type=int, default=1800, help="Per-cell timeout in seconds.")
    parser.add_argument(
        "--skip-figure-scripts",
        action="store_true",
        help="Only execute the notebook; do not rebuild shared figure assets afterward.",
    )
    args = parser.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")

    executed = [run_notebook(list(args.outcomes), timeout=args.timeout)]

    print("Executed notebooks:")
    for path in executed:
        print(path.relative_to(ROOT))

    if not args.skip_figure_scripts:
        for script in [
            "regenerate_standardized_figures.py",
            "build_site_index_assets.py",
            "sync_figure_assets.py",
        ]:
            subprocess.run([sys.executable, str(ROOT / "scripts" / script)], check=True, cwd=ROOT)


if __name__ == "__main__":
    main()
