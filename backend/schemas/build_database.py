"""Build and validate SQLite data before atomically publishing the database.

Replacement is opt-in. The previous database, including generated summaries, is
archived beside the target as ``<database>.backup-<timestamp>-*.sqlite3``. Stop
database writers before rebuilding; active journal/WAL files block replacement.
Summary generation is a separate, explicit operation and is never run here.
"""

import argparse
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.database import (
    DatabaseNotReady,
    connect_readonly,
    database_path,
    validate_database,
)
from backend.schemas.create_db import initialize_database
from backend.schemas.populate_tables import populate_database, preflight_inputs


@dataclass(frozen=True)
class BuildResult:
    path: Path
    backup_path: Path | None


def _check_replacement(path, replace_existing):
    if path.exists() and not replace_existing:
        raise FileExistsError(
            f"Database already exists at {path}. No data was changed. "
            "Use --replace-existing to rebuild and archive the previous database."
        )
    if path.exists() and not path.is_file():
        raise ValueError(f"Database target is not a regular file: {path}")
    # Replacing the main file while another connection owns a journal or WAL
    # can detach committed writes from the file they belong to.
    sidecars = [Path(f"{path}{suffix}") for suffix in ("-wal", "-shm", "-journal")]
    if any(item.exists() for item in sidecars):
        raise RuntimeError(
            f"SQLite journal or WAL files exist beside {path}. "
            "Stop database writers and close their connections before rebuilding. "
            "The current database was not changed."
        )


def _archive_database(path):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    fd, name = tempfile.mkstemp(
        prefix=f"{path.name}.backup-{stamp}-", suffix=".sqlite3", dir=path.parent
    )
    os.close(fd)
    backup = Path(name)
    try:
        shutil.copy2(path, backup)
        with backup.open("rb") as handle:
            os.fsync(handle.fileno())
    except BaseException:
        backup.unlink(missing_ok=True)
        raise
    return backup


def build_database(path=None, *, processed_dir=None, replace_existing=False):
    """Publish a fully validated staging database; failures preserve live data."""
    path = Path(path if path is not None else database_path()).expanduser().resolve()
    _check_replacement(path, replace_existing)
    preflight_inputs(processed_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    lock = path.with_name(f".{path.name}.build.lock")
    try:
        lock_fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise RuntimeError(
            f"A database build lock exists at {lock}. Wait for that build to finish. "
            "If a previous build was interrupted, remove the lock only after "
            "confirming that process has stopped."
        ) from exc
    stage = None
    backup = None
    try:
        os.write(lock_fd, str(os.getpid()).encode("ascii"))
        os.close(lock_fd)
        lock_fd = None
        _check_replacement(path, replace_existing)
        fd, name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".building", dir=path.parent
        )
        os.close(fd)
        stage = Path(name)
        initialize_database(stage)
        populate_database(stage, processed_dir=processed_dir)
        with closing(connect_readonly(stage)) as conn:
            validate_database(conn, full_check=True)
        with stage.open("rb") as handle:
            os.fsync(handle.fileno())
        # Recheck after the potentially lengthy build. The destination may have
        # been created, or a writer may have started, while population ran.
        _check_replacement(path, replace_existing)
        if path.exists():
            backup = _archive_database(path)
        os.replace(stage, path)
        return BuildResult(path, backup)
    finally:
        if lock_fd is not None:
            os.close(lock_fd)
        if stage is not None:
            for suffix in ("", "-wal", "-shm", "-journal"):
                Path(f"{stage}{suffix}").unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database", type=Path, default=None,
        help="Database destination (default: DER_DB_PATH or data/der_tool.db).",
    )
    parser.add_argument(
        "--processed-dir", type=Path, default=None,
        help="Directory containing the four processed CSV inputs.",
    )
    parser.add_argument(
        "--replace-existing", action="store_true",
        help="Explicitly replace an existing database, retaining a dated backup.",
    )
    args = parser.parse_args(argv)
    try:
        result = build_database(
            args.database,
            processed_dir=args.processed_dir,
            replace_existing=args.replace_existing,
        )
    except (OSError, ValueError, RuntimeError, sqlite3.Error, DatabaseNotReady) as exc:
        parser.exit(1, f"Database build failed: {exc}\n")
    print(f"Database is ready at {result.path}")
    if result.backup_path is not None:
        print(f"Previous database, including saved summaries, archived at {result.backup_path}")
    print("Summary generation was not run.")


if __name__ == "__main__":
    main()
