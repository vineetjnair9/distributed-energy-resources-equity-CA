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

    # Results only, without the presentation panels or the site mirror
    python scripts/run_all.py --only figures --skip-assets

    # Execute one notebook and stop (replaces the old run_notebook.py)
    python scripts/run_all.py --run-notebook plotting_outcomes

Stages
------
    data       rebuild_processed_data.py       -> data/processed/*.csv
    models     notebooks/regression.ipynb      -> outputs/{standardized_,}tables/*.csv
    clustering notebooks/clustering.ipynb      -> outputs/tables/pca_kmeans_*.csv
    figures    regenerate_standardized_figures.py -> outputs/standardized_figures/*.png
               build_site_index_assets.py --sync  -> outputs/figures/**, site/assets
                                                     (skip with --skip-assets)
    database   backend/schemas/create_db.py
               backend/schemas/populate_tables.py
               backend/schemas/generate_summaries.py  -> data/der_tool.db

Notebook execution lives here rather than in separate runner scripts. The models stage
rewrites OUTCOMES_TO_RUN in regression.ipynb before executing it, so a partial rerun is
`--outcomes y_pv y_storage`; every notebook is written to outputs/executed_notebooks/.

The database stage is NOT run by default: it takes a while and the last step makes
OpenAI calls. Run it explicitly with --only database.

data/der_tool.db is deliberately not version-controlled. It is ~300MB, exceeds
GitHub's 100MB per-file limit, and is fully rebuildable from the processed CSVs. Of its
ten tables only summary_responses is LLM-generated, and that is five rows -- everything
else, including the 246k evidence_chunks, is deterministic string formatting over
metric_observations and model_outputs.

Environment
-----------
    CENSUS_API_KEY   required unless --skip-data or --skip-external
    OPENAI_API_KEY   required for the database stage's summary step
    FIGURE_BG        'transparent' (default) or 'white' (opaque, for journals)
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
NOTEBOOK_DIR = ROOT / "notebooks"
EXECUTED_DIR = ROOT / "outputs" / "executed_notebooks"

STAGES = ["data", "models", "clustering", "figures", "database"]

DEFAULT_OUTCOMES = [
    "y_pv",
    "y_storage",
    "y_chargers",
    "y_wind_mw",
    "any_turbines",
    "y_level1_chargers",
    "y_level2_chargers",
    "y_dc_fast_chargers",
    "energy_burden_pct",
    "log_energy_gap_per_capita",
]


def _run(cmd: list[str], label: str) -> None:
    print(f"\n{'=' * 72}\n[{label}] {' '.join(str(c) for c in cmd)}\n{'=' * 72}", flush=True)
    started = time.monotonic()
    result = subprocess.run(cmd, cwd=ROOT)
    elapsed = time.monotonic() - started
    if result.returncode != 0:
        raise SystemExit(f"[{label}] FAILED after {elapsed:.0f}s (exit {result.returncode})")
    print(f"[{label}] done in {elapsed:.0f}s", flush=True)


# --------------------------------------------------------------------------- notebooks

def _patched_source(source: str, *, outcomes: list[str]) -> str:
    """Rewrite the OUTCOMES_TO_RUN assignment in regression.ipynb's second cell.

    The assignment spans several lines, so this tracks bracket depth to skip the whole
    literal rather than only its first line.
    """
    patched: list[str] = []
    skipping_assignment = False
    bracket_depth = 0
    replaced = False

    for line in source.splitlines():
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


def execute_notebook(
    name: str,
    *,
    outcomes: list[str] | None = None,
    timeout: int = 3600,
    kernel: str = "python3",
) -> Path:
    """Execute a notebook and save an executed copy under outputs/executed_notebooks/.

    Imported lazily so that stages which need no notebook (figures, database) do not
    require nbclient to be installed.
    """
    import nbformat
    from nbclient import NotebookClient

    path = NOTEBOOK_DIR / (name if name.endswith(".ipynb") else f"{name}.ipynb")
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in NOTEBOOK_DIR.glob("*.ipynb")))
        raise SystemExit(f"No such notebook: {path}\nAvailable: {available}")

    nb = nbformat.read(path, as_version=4)
    if outcomes:
        nb.cells[1].source = _patched_source(nb.cells[1].source, outcomes=outcomes)

    NotebookClient(
        nb,
        timeout=timeout,
        kernel_name=kernel,
        resources={"metadata": {"path": str(NOTEBOOK_DIR)}},
        allow_errors=False,
    ).execute()

    EXECUTED_DIR.mkdir(parents=True, exist_ok=True)
    out = EXECUTED_DIR / f"{path.stem}.executed.ipynb"
    nbformat.write(nb, out)
    return out


def _run_notebook_stage(name: str, label: str, args: argparse.Namespace,
                        outcomes: list[str] | None = None) -> None:
    print(f"\n{'=' * 72}\n[{label}] notebooks/{name}.ipynb\n{'=' * 72}", flush=True)
    started = time.monotonic()
    out = execute_notebook(name, outcomes=outcomes, timeout=args.timeout, kernel=args.kernel)
    print(f"[{label}] done in {time.monotonic() - started:.0f}s -> {out.relative_to(ROOT)}",
          flush=True)


# ------------------------------------------------------------------------------ stages

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
    _run_notebook_stage("regression", "models", args,
                        outcomes=list(args.outcomes) if args.outcomes else DEFAULT_OUTCOMES)


def stage_clustering(args: argparse.Namespace) -> None:
    _run_notebook_stage("clustering", "clustering", args)


def stage_figures(args: argparse.Namespace) -> None:
    # Coefficient figures first: build_site_index_assets reads the standardized tables and
    # mirrors the finished PNGs, so it has to run second.
    _run([sys.executable, str(SCRIPTS / "regenerate_standardized_figures.py")],
         "figures:standardized")
    if args.skip_assets:
        print("[figures] --skip-assets: panels and site mirror not rebuilt", flush=True)
        return
    _run([sys.executable, str(SCRIPTS / "build_site_index_assets.py"), "--sync"],
         "figures:assets")


def stage_database(args: argparse.Namespace) -> None:
    """Rebuild data/der_tool.db from the processed CSVs."""
    if not os.environ.get("OPENAI_API_KEY"):
        print("[database] OPENAI_API_KEY not set - schema and tables will be rebuilt, "
              "but the five LLM summaries will be skipped.", flush=True)
    scripts = ["create_db.py", "populate_tables.py"]
    if os.environ.get("OPENAI_API_KEY"):
        scripts.append("generate_summaries.py")
    for script in scripts:
        _run([sys.executable, str(ROOT / "backend" / "schemas" / script)],
             f"database:{script.replace('.py', '')}")


RUNNERS = {
    "data": stage_data,
    "models": stage_models,
    "clustering": stage_clustering,
    "figures": stage_figures,
    "database": stage_database,
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
    parser.add_argument(
        "--skip-assets",
        action="store_true",
        help="In the figures stage, build the coefficient figures but not the presentation "
             "panels or the site mirror. Results are unaffected.",
    )
    parser.add_argument(
        "--run-notebook",
        metavar="NAME",
        help="Execute one notebook by stem and exit, e.g. 'plotting_outcomes'.",
    )
    parser.add_argument("--timeout", type=int, default=3600,
                        help="Per-cell notebook timeout in seconds.")
    parser.add_argument("--kernel", default="python3", help="Jupyter kernel name.")
    args = parser.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("FIGURE_BG", "transparent")

    if args.run_notebook:
        out = execute_notebook(args.run_notebook, timeout=args.timeout, kernel=args.kernel)
        print(out.relative_to(ROOT))
        return

    # "database" is opt-in only: it is slow and its last step costs OpenAI calls.
    default_stages = [s for s in STAGES if s != "database"]
    selected = args.only or [s for s in default_stages if not getattr(args, f"skip_{s}")]

    if "data" in selected and not args.skip_external and not os.environ.get("CENSUS_API_KEY"):
        raise SystemExit(
            "CENSUS_API_KEY is not set. Export it (or put it in .env and source that), "
            "or pass --skip-data / --skip-external.\n"
            "Without a live ACS pull the housing-structure controls cannot be built, and "
            "the rebuild will stop rather than silently emit empty columns."
        )

    print(f"Stages: {' -> '.join(selected)}")
    print(f"Figure background: {os.environ['FIGURE_BG']}")
    started = time.monotonic()
    for stage in STAGES:
        if stage in selected:
            RUNNERS[stage](args)
    print(f"\nAll stages completed in {time.monotonic() - started:.0f}s.")


if __name__ == "__main__":
    main()
