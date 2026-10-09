"""The startup fetch must never replace a working database with a bad one."""

import gzip
import hashlib
import shutil

import pytest

from backend.database import DatabaseNotReady, check_database
from backend.fixtures import build_fixture_db as fixture
from backend.serve import fetch_database


@pytest.fixture(scope="module")
def good_db(tmp_path_factory):
    return fixture.build_fixture_database(tmp_path_factory.mktemp("src") / "good.db")


def test_fetch_installs_a_valid_database(good_db, tmp_path):
    target = tmp_path / "live.db"
    digest = hashlib.sha256(good_db.read_bytes()).hexdigest()
    fetch_database(good_db.as_uri(), target, digest)
    check_database(target)


def test_fetch_unpacks_gzip(good_db, tmp_path):
    packed = tmp_path / "good.db.gz"
    with good_db.open("rb") as source, gzip.open(packed, "wb") as out:
        shutil.copyfileobj(source, out)
    target = tmp_path / "live.db"
    fetch_database(packed.as_uri(), target)
    check_database(target)


@pytest.mark.parametrize("problem", ["checksum", "not_a_database"])
def test_failed_fetch_keeps_existing_database_and_leaves_no_temp_files(
    good_db, tmp_path, problem
):
    target = tmp_path / "live.db"
    shutil.copy(good_db, target)
    before = target.read_bytes()
    source = good_db
    expected = "0" * 64
    if problem == "not_a_database":
        source = tmp_path / "junk.db"
        source.write_bytes(b"not sqlite")
        expected = None
    with pytest.raises((ValueError, DatabaseNotReady)):
        fetch_database(source.as_uri(), target, expected)
    assert target.read_bytes() == before
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(
        ["live.db"] + (["junk.db"] if problem == "not_a_database" else [])
    )


def test_fetch_rejects_plain_http(tmp_path):
    with pytest.raises(ValueError, match="https"):
        fetch_database("http://example.com/der.db", tmp_path / "live.db")
    assert not any(tmp_path.iterdir())


def test_fetch_caps_download_and_decompressed_size(good_db, tmp_path):
    target = tmp_path / "live.db"
    with pytest.raises(ValueError, match="exceeds"):
        fetch_database(good_db.as_uri(), target, max_bytes=1024)
    bomb = tmp_path / "bomb.db.gz"
    with gzip.open(bomb, "wb") as out:
        out.write(b"\0" * (4 << 20))
    with pytest.raises(ValueError, match="decompressed"):
        fetch_database(bomb.as_uri(), target, max_bytes=1 << 20)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["bomb.db.gz"]
