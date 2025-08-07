from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Generator

import pytest

import dbcanlight
import dbcanlight.pipeline as pipeline
from dbcanlight._header import Headers
from dbcanlight.pipeline import build, conclude, search


def get_file_checksum(file: str | Path) -> str:
    """Compute the crc checksum of a file."""
    return hashlib.md5(open(file, "rb").read()).hexdigest()


@pytest.fixture
def base_db_urls():
    return {
        "cazyme_hmms": dbcanlight.DB_PATH["cazyme_hmms"],
        "subs_hmms": dbcanlight.DB_PATH["subs_hmms"],
        "subs_mapper": dbcanlight.DB_PATH["subs_mapper"],
        "diamond": dbcanlight.CFG_DIR / "cazydb.fa",
    }


@pytest.fixture
def patch_build(monkeypatch: Generator):
    def mock_download(url: str, filepath: Path, *, threads):
        print(f"Download database from mock/{url} to {filepath}")

    for dbname in dbcanlight.DB_PATH:
        monkeypatch.setattr(pipeline._libbuild, dbname, mock_download)


class TestBuild:
    def test_build_already_exist(self, monkeypatch: Generator, capsys: pytest.CaptureFixture, patch_build, base_db_urls):
        def mock_fetch_database_metadata():
            db_urls = {}
            for dbname, file in base_db_urls.items():
                db_urls[dbname] = [file, get_file_checksum(file)]
            return db_urls

        monkeypatch.setattr(pipeline, "fetch_database_metadata", mock_fetch_database_metadata)
        build()
        captured: str = capsys.readouterr().out
        captured = captured.split("\n")
        for dbname in dbcanlight.DB_PATH:
            assert f"{dbname} ok" in captured

    def test_build_need_update(self, monkeypatch: Generator, capsys: pytest.CaptureFixture, patch_build, base_db_urls):
        def mock_fetch_database_metadata():
            db_urls = {}
            for dbname, file in base_db_urls.items():
                if dbname == "subs_hmms":
                    db_urls[dbname] = [file, "fakemd5checksum"]
                else:
                    db_urls[dbname] = [file, get_file_checksum(file)]

            return db_urls

        monkeypatch.setattr(pipeline, "fetch_database_metadata", mock_fetch_database_metadata)
        build()
        captured: str = capsys.readouterr().out
        captured = captured.split("\n")
        for dbname in dbcanlight.DB_PATH:
            if dbname == "subs_hmms":
                assert f"{dbname} update required" in captured
            else:
                assert f"{dbname} ok" in captured

    def test_build_not_found(
        self, tmp_path: Path, monkeypatch: Generator, capsys: pytest.CaptureFixture, patch_build, base_db_urls
    ):
        def mock_fetch_database_metadata():
            db_urls = {}
            for dbname, file in base_db_urls.items():
                if dbname == "cazyme_hmms":
                    db_urls[dbname] = [file, "fakemd5checksum"]
                else:
                    db_urls[dbname] = [file, get_file_checksum(file)]

            return db_urls

        cazyme_hmms_db = dbcanlight.DB_PATH["cazyme_hmms"]
        cazyme_hmms_db_newpath = tmp_path / cazyme_hmms_db.name
        cazyme_hmms_db.rename(cazyme_hmms_db_newpath)

        monkeypatch.setattr(pipeline, "fetch_database_metadata", mock_fetch_database_metadata)
        build()
        captured: str = capsys.readouterr().out
        captured = captured.split("\n")
        for dbname in dbcanlight.DB_PATH:
            if dbname == "cazyme_hmms":
                assert f"{dbname} not found" in captured
            else:
                assert f"{dbname} ok" in captured

        cazyme_hmms_db_newpath.rename(cazyme_hmms_db)


class TestSearch:
    input = Path("tests/data/example.faa")

    @pytest.mark.parametrize(
        "mode, search_func", zip(dbcanlight.AVAIL_MODES.keys(), ("cazyme_search", "subs_search", "diamond_search"))
    )
    def test_search(self, mode: str, search_func: str, monkeypatch: Generator):
        def mock_search(*args, **kwargs):
            return args[0]

        def mock_writer(input, output, *, header):
            return input, output, header

        monkeypatch.setattr(pipeline, search_func, mock_search)
        monkeypatch.setattr(pipeline, "writer", mock_writer)
        r = search(self.input, "output", mode=mode)
        assert r[0] == self.input
        assert r[1] == Path("output") / dbcanlight.AVAIL_MODES[mode]
        assert r[2] == getattr(Headers, mode)

    @pytest.mark.parametrize("mode", ("cazyme", "sub"))
    def test_search_valueerror(self, tmp_path: Path, mode: str):
        with pytest.raises(ValueError, match=r"blocksize=.+ which is smaller than 0."):
            search(self.input, tmp_path, mode=mode, blocksize=-1)

    def test_search_keyerror(self, tmp_path: Path):
        with pytest.raises(KeyError, match=r".+ is not an available mode."):
            search(self.input, tmp_path, mode="Invalidmode")


class TestConclude:
    def test_conclude(self, tmp_path: Path):
        for file in dbcanlight.AVAIL_MODES.values():
            shutil.copy(f"tests/data/{file}", tmp_path)
        conclude(tmp_path)
        output = tmp_path / "overview.tsv"
        assert output.is_file()
        assert get_file_checksum(output) == get_file_checksum("tests/data/overview.tsv")

    @pytest.mark.parametrize("file", dbcanlight.AVAIL_MODES.values())
    def test_conclude_runtimeerror(self, file: str, tmp_path: Path):
        shutil.copy(f"tests/data/{file}", tmp_path)
        with pytest.raises(RuntimeError, match=r"Required at least 2 results to conclude but got 1. Aborted."):
            conclude(tmp_path)
