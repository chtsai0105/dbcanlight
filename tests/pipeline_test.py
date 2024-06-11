from __future__ import annotations

import shutil
from pathlib import Path
from typing import Generator
from zlib import crc32

import pytest

import dbcanlight._config as _config
import dbcanlight.pipeline as pipeline
from dbcanlight.pipeline import conclude, search


def get_file_checksum(file: str | Path) -> int:
    """Compute the crc checksum of a file."""
    file = Path(file)
    if not file.exists():
        raise FileNotFoundError(f"{file} not found.")
    crc = 0
    with open(file, "rb") as f:
        crc += crc32(f.read())
    return crc


class TestSearch:
    input = Path("tests/data/example.faa")

    @pytest.mark.parametrize("mode, search_func", zip(_config.avail_modes.keys(), ("cazyme_search", "subs_search", "diamond")))
    def test_search(self, mode: str, search_func: str, monkeypatch: Generator):
        def mock_search(*args, **kwargs):
            return args[0]

        def mock_writer(input, output, *, header):
            return input, output, header

        monkeypatch.setattr(pipeline, search_func, mock_search)
        monkeypatch.setattr(pipeline, "writer", mock_writer)
        r = search(self.input, "output", mode=mode)
        assert r[0] == self.input
        assert r[1] == Path("output") / _config.avail_modes[mode]
        assert r[2] == getattr(_config.headers, mode)

    @pytest.mark.parametrize("mode", ("cazyme", "sub"))
    def test_search_valueerror(self, tmp_path: Path, mode: str):
        with pytest.raises(ValueError, match=r"blocksize=\d+ which is smaller than 1."):
            search(self.input, tmp_path, mode=mode, blocksize=0)

    def test_search_keyerror(self, tmp_path: Path):
        with pytest.raises(KeyError, match=r".+ is not an available mode."):
            search(self.input, tmp_path, mode="Invalidmode")


class TestConclude:
    def test_conclude(self, tmp_path: Path):
        for file in _config.avail_modes.values():
            shutil.copy(f"tests/data/{file}", tmp_path)
        conclude(tmp_path)
        output = tmp_path / "overview.tsv"
        assert output.is_file()
        assert get_file_checksum(output) == get_file_checksum("tests/data/overview.tsv")

    @pytest.mark.parametrize("file", _config.avail_modes.values())
    def test_conclude_systemexit(self, file: str, tmp_path: Path):
        shutil.copy(f"tests/data/{file}", tmp_path)
        with pytest.raises(SystemExit, match=r"Required at least 2 results to conclude but got 1. Aborted."):
            conclude(tmp_path)
