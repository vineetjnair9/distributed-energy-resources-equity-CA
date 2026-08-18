#!/usr/bin/env python3
"""
Fetch exact public raw inputs that can be reproduced from stable upstream sources.

This script intentionally covers only sources that could be tied to a specific,
publicly accessible endpoint with enough confidence to reproduce the file that
the current 2023-aligned workflow expects.

It does not try to regenerate every file under data/raw/. Some dashboard exports
and hand-cleaned workbooks in this repo still need a separate provenance pass.
See data/raw/SOURCES.md for details.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import shutil
import zipfile
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

TIMEOUT = 300
CHUNK_SIZE = 1024 * 1024

# Tracking the Sun. LBNL publishes no direct file URL; each edition is a bit.ly
# shortener onto Google Drive. Recorded here so the acquisition route is written down,
# but deliberately not fetched automatically -- see fetch_tts_2023_aligned.
TTS_FILENAME = "TTS_LBNL_public_file_21-Aug-2024_all.csv"
TTS_BITLY = "https://bit.ly/trackingthesun2024"
TTS_DRIVE_FILE_ID = "1Wpkzx2fe3syIcwMeKo2GPCBxWxOqpDpA"
TTS_LANDING_PAGE = "https://emp.lbl.gov/tracking-the-sun"
# SHA-256 of the 21-Aug-2024 release, computed from the copy this project was built on
# and cross-checked against the Git LFS object id, which is the same digest.
TTS_SHA256 = "ba5a886d05538bd67c55f0d496e0cf0fba41e6c1158a1f2404ab8e651596f9bb"

DG_2023_12_31_URL = "https://www.californiadgstats.ca.gov/download/interconnection_rule21_projects/Interconnected_Project_Sites_2023-12-31.zip/"
USWTDB_CSV_ZIP_URL = "https://energy.usgs.gov/uswtdb/assets/data/uswtdbCSV.zip"
COUNTY_2023_ZIP_URL = "https://www2.census.gov/geo/tiger/TIGER2023/COUNTY/tl_2023_us_county.zip"
ZCTA_2023_ZIP_URL = "https://www2.census.gov/geo/tiger/TIGER2023/ZCTA520/tl_2023_us_zcta520.zip"
CA_UTILITY_TERRITORIES_URL = (
    "https://services.arcgis.com/BLN4oKB0N1YSgvY8/arcgis/rest/services/"
    "California_Electric_Utility_Service_Territory_SCOUT/FeatureServer/0/query"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Redownload and overwrite files even if the expected outputs already exist.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        choices=["tts", "interconnection", "wind", "boundaries", "utility-territories"],
        help="Restrict the run to specific source groups.",
    )
    return parser.parse_args()


def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "DER-data-fetch/1.0"})
    return s


def should_skip(path: Path, force: bool) -> bool:
    return path.exists() and not force


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def stream_to_file(s: requests.Session, url: str, dest: Path) -> None:
    ensure_parent(dest)
    with s.get(url, stream=True, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        with dest.open("wb") as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)


def download_bytes(s: requests.Session, url: str) -> bytes:
    with s.get(url, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        return resp.content


def extract_member(zf: zipfile.ZipFile, member_name: str, dest: Path) -> None:
    ensure_parent(dest)
    with zf.open(member_name) as src, dest.open("wb") as out:
        shutil.copyfileobj(src, out)


def extract_by_suffixes(zf: zipfile.ZipFile, suffixes: tuple[str, ...], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for member in zf.namelist():
        name = Path(member).name
        if not name:
            continue
        if name.endswith(suffixes):
            extract_member(zf, member, out_dir / name)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch_tts_2023_aligned(_: requests.Session, force: bool) -> None:
    """Tracking the Sun is a documented manual step, not an automated download.

    LBNL does not publish a direct file URL. The download route, verified against
    emp.lbl.gov, is a bit.ly shortener per edition that redirects to Google Drive:

        2024 edition  https://bit.ly/trackingthesun2024
                      -> https://drive.google.com/file/d/1Wpkzx2fe3syIcwMeKo2GPCBxWxOqpDpA/view

    Neither hop is safe to automate in a reproducibility pipeline. The shortener is a
    mutable third-party redirect that LBNL can retarget, the Drive file can be replaced
    in place, and Drive's large-file flow needs an interactive confirm token. Fetching
    through that chain could silently return a different vintage than the one the
    published results were built on, which is exactly the failure this script exists to
    prevent. So the URL is recorded rather than followed.

    Set TTS_SHA256 below once the file is in hand and this becomes a verified step.
    """
    target = RAW / "solar" / TTS_FILENAME
    if target.exists() and not force:
        if TTS_SHA256:
            digest = sha256_file(target)
            if digest != TTS_SHA256:
                raise RuntimeError(
                    f"{target.relative_to(ROOT)} does not match the pinned checksum.\n"
                    f"  expected {TTS_SHA256}\n  found    {digest}\n"
                    "This is a different Tracking the Sun release than the results were built on."
                )
            print(f"verified {target.relative_to(ROOT)}")
        else:
            print(f"skip {target.relative_to(ROOT)} (present; no checksum pinned)")
        return

    raise RuntimeError(
        f"{TTS_FILENAME} is missing and cannot be downloaded automatically.\n"
        f"  1. Open {TTS_BITLY}\n"
        f"     (currently redirects to Google Drive file {TTS_DRIVE_FILE_ID})\n"
        f"  2. Download the public data file and unzip it\n"
        f"  3. Place it at {target.relative_to(ROOT)}\n"
        "The 2024 edition is the one to use: it is the first release covering "
        "installations through year-end 2023, which is what this project is aligned to."
    )


def fetch_interconnection_2023_12_31(s: requests.Session, force: bool) -> None:
    targets = [
        RAW / "interconnection" / "PGE_Interconnected_Project_Sites_2023-12-31.csv",
        RAW / "interconnection" / "SCE_Interconnected_Project_Sites_2023-12-31.csv",
        RAW / "interconnection" / "SDGE_Interconnected_Project_Sites_2023-12-31.csv",
    ]
    if all(should_skip(path, force) for path in targets):
        for path in targets:
            print(f"skip {path.relative_to(ROOT)}")
        return

    payload = download_bytes(s, DG_2023_12_31_URL)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        members = {Path(m).name: m for m in zf.namelist()}
        for path in targets:
            member = members.get(path.name)
            if member is None:
                raise RuntimeError(f"Archive missing expected file: {path.name}")
            extract_member(zf, member, path)
            print(f"wrote {path.relative_to(ROOT)}")


def fetch_uswtdb(s: requests.Session, force: bool) -> None:
    target = RAW / "wind" / "USWTDB_wind_data.csv"
    if should_skip(target, force):
        print(f"skip {target.relative_to(ROOT)}")
        return

    payload = download_bytes(s, USWTDB_CSV_ZIP_URL)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        csv_members = [m for m in zf.namelist() if m.lower().endswith(".csv")]
        if not csv_members:
            raise RuntimeError("USWTDB archive did not contain a CSV file")
        if len(csv_members) != 1:
            raise RuntimeError(f"Expected 1 CSV in USWTDB archive, found {len(csv_members)}")
        extract_member(zf, csv_members[0], target)
    print(f"wrote {target.relative_to(ROOT)}")


def fetch_boundary_zip(s: requests.Session, url: str, out_dir: Path, force: bool) -> None:
    shp = next(out_dir.glob("*.shp"), None)
    if shp is not None and not force:
        print(f"skip {out_dir.relative_to(ROOT)}")
        return

    payload = download_bytes(s, url)
    with zipfile.ZipFile(io.BytesIO(payload)) as zf:
        extract_by_suffixes(zf, (".shp", ".shx", ".dbf", ".prj", ".cpg", ".xml"), out_dir)
    print(f"wrote {out_dir.relative_to(ROOT)}")


def fetch_boundaries(s: requests.Session, force: bool) -> None:
    fetch_boundary_zip(s, COUNTY_2023_ZIP_URL, RAW / "boundaries" / "tl_2023_us_county", force)
    fetch_boundary_zip(s, ZCTA_2023_ZIP_URL, RAW / "boundaries" / "tl_2023_us_zcta520", force)


def fetch_ca_utility_territories(s: requests.Session, force: bool) -> None:
    target = RAW / "boundaries" / "ca_utility_territories.geojson"
    if should_skip(target, force):
        print(f"skip {target.relative_to(ROOT)}")
        return

    params = {
        "where": "1=1",
        "outFields": "*",
        "outSR": "4326",
        "f": "geojson",
    }
    with s.get(CA_UTILITY_TERRITORIES_URL, params=params, timeout=TIMEOUT) as resp:
        resp.raise_for_status()
        payload = resp.json()

    if payload.get("type") != "FeatureCollection":
        raise RuntimeError("Utility territory endpoint did not return GeoJSON FeatureCollection")

    ensure_parent(target)
    target.write_text(json.dumps(payload), encoding="utf-8")
    print(f"wrote {target.relative_to(ROOT)}")


def main() -> None:
    args = parse_args()
    groups = set(args.only or ["tts", "interconnection", "wind", "boundaries", "utility-territories"])
    s = session()

    if "tts" in groups:
        fetch_tts_2023_aligned(s, args.force)
    if "interconnection" in groups:
        fetch_interconnection_2023_12_31(s, args.force)
    if "wind" in groups:
        fetch_uswtdb(s, args.force)
    if "boundaries" in groups:
        fetch_boundaries(s, args.force)
    if "utility-territories" in groups:
        fetch_ca_utility_territories(s, args.force)


if __name__ == "__main__":
    main()
