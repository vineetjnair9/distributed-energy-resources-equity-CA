#!/usr/bin/env python3
"""Execute any project notebook in place and save an executed copy.

`run_regression_notebook.py` already does this for regression.ipynb (and additionally
patches OUTCOMES_TO_RUN). This is the generic version, used for clustering and
plotting, so every notebook in the pipeline is runnable from a script rather than only
by hand in Jupyter.

Usage
-----
    python scripts/run_notebook.py clustering
    python scripts/run_notebook.py plotting_outcomes --timeout 3600
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"
EXECUTED_DIR = ROOT / "outputs" / "executed_notebooks"


def run(name: str, timeout: int, kernel: str) -> Path:
    path = NOTEBOOK_DIR / (name if name.endswith(".ipynb") else f"{name}.ipynb")
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in NOTEBOOK_DIR.glob("*.ipynb")))
        raise SystemExit(f"No such notebook: {path}\nAvailable: {available}")

    nb = nbformat.read(path, as_version=4)
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("notebook", help="Notebook stem, e.g. 'clustering'.")
    parser.add_argument("--timeout", type=int, default=3600, help="Per-cell timeout in seconds.")
    parser.add_argument("--kernel", default="python3", help="Jupyter kernel name.")
    args = parser.parse_args()

    os.environ.setdefault("MPLBACKEND", "Agg")
    out = run(args.notebook, args.timeout, args.kernel)
    print(f"Executed {args.notebook} -> {out.relative_to(ROOT)}", file=sys.stderr)
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
