"""Production entrypoint: make sure a database is present, then start uvicorn.

The image ships with the synthetic fixture database. To serve real data, set
DER_DB_URL to a downloadable der_tool.db (optionally .gz) and, ideally,
DER_DB_SHA256. The download is verified and validated before it replaces the
bundled database, so a bad URL leaves the service on the data it already had.

    PORT            port to bind (Render sets this; default 8000)
    DER_DB_PATH     database location inside the container
    DER_DB_URL      optional URL of a built database to fetch at startup
    DER_DB_SHA256   optional expected SHA-256 of the downloaded file
"""

import gzip
import hashlib
import logging
import os
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

import uvicorn

from backend.database import DatabaseNotReady, check_database, database_path

LOGGER = logging.getLogger("der.serve")
# https for real deployments; file for local testing. Never plain http, which
# would let anyone on the path substitute the database.
ALLOWED_SCHEMES = {"https", "file"}
MAX_DOWNLOAD_BYTES = 4 * 1024**3  # the real database is ~740 MB; refuse to fill the disk


def fetch_database(url, path, expected_sha256=None, max_bytes=MAX_DOWNLOAD_BYTES):
    scheme = urllib.parse.urlsplit(url).scheme.lower()
    if scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"DER_DB_URL must use https, not {scheme or 'no scheme'}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".download", dir=path.parent)
    os.close(fd)
    staged = Path(name)
    try:
        digest = hashlib.sha256()
        received = 0
        with urllib.request.urlopen(url, timeout=300) as response, staged.open("wb") as out:
            while chunk := response.read(1 << 20):
                received += len(chunk)
                if received > max_bytes:
                    raise ValueError(f"download exceeds {max_bytes} bytes")
                digest.update(chunk)
                out.write(chunk)
        if expected_sha256 and digest.hexdigest() != expected_sha256.lower():
            raise ValueError(f"checksum mismatch: got {digest.hexdigest()}")
        if url.endswith(".gz"):
            unpacked = staged.with_suffix(".unpacked")
            with gzip.open(staged) as source, unpacked.open("wb") as out:
                written = 0
                while chunk := source.read(1 << 20):
                    written += len(chunk)
                    if written > max_bytes:  # a small .gz can expand enormously
                        unpacked.unlink(missing_ok=True)
                        raise ValueError(f"decompressed database exceeds {max_bytes} bytes")
                    out.write(chunk)
            staged.unlink()
            staged = unpacked
        check_database(staged, full_check=True)
        os.replace(staged, path)
    finally:
        staged.unlink(missing_ok=True)


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    path = database_path()
    url = os.environ.get("DER_DB_URL")
    if url:
        if not os.environ.get("DER_DB_SHA256"):
            LOGGER.warning("DER_DB_URL is set without DER_DB_SHA256; the download "
                           "is validated but its origin is not verified.")
        try:
            fetch_database(url, path, os.environ.get("DER_DB_SHA256"))
            LOGGER.info("Fetched database from DER_DB_URL into %s", path.name)
        except (OSError, ValueError, DatabaseNotReady) as exc:
            LOGGER.error("Could not fetch DER_DB_URL (%s); keeping existing database.", exc)
    uvicorn.run(
        "backend.api.api:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
