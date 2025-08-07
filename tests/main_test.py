from __future__ import annotations

import logging
from itertools import product
from pathlib import Path
from typing import Generator

import pytest

import dbcanlight.__main__ as dbcanlight_entry
from dbcanlight import AVAIL_MODES, DB_PATH, VERSION
from dbcanlight.__main__ import main


def mockreturn(**kwargs):
    for k, v in kwargs.items():
        print(f"{k}: {v}")


def test_main_help():
    assert main(["--help"]) == main(["-h"]) == 0


def test_main_version(capsys: pytest.CaptureFixture):
    assert main(["--version"]) == main(["-V"])
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert captured[0] == captured[1] == VERSION


def test_main_build(monkeypatch: Generator):
    monkeypatch.setattr(dbcanlight_entry, "build", mockreturn)
    assert main(["build"]) == 0


def test_main_build_verbose(monkeypatch: Generator, caplog: pytest.LogCaptureFixture):
    monkeypatch.setattr(dbcanlight_entry, "build", mockreturn)
    with caplog.at_level(logging.DEBUG):
        main(["build", "-v"])
    assert any(record.levelname == "DEBUG" for record in caplog.records)
    assert "Debug mode enabled." in caplog.text


@pytest.mark.parametrize(
    "file, output, mode",
    tuple(product(("mock_input1", "mock_input2"), ("mock_output1", "mock_output2"), AVAIL_MODES.keys())),
)
def test_main_search(file: str, output: str, mode: str, monkeypatch: Generator, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(dbcanlight_entry, "search", mockreturn)
    assert main(["search", "-i", file, "-o", output, "-m", mode]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"input: {file}" in captured
    assert f"output: {output}" in captured
    assert f"mode: {mode}" in captured


def test_main_filenotfounderror(tmp_path: Path, monkeypatch: Generator, caplog: pytest.LogCaptureFixture):
    cazyme_hmms_db = DB_PATH["cazyme_hmms"]
    temp_path = cazyme_hmms_db.parent / "test"
    cazyme_hmms_db.rename(temp_path)
    with caplog.at_level(logging.ERROR):
        assert main(["search", "-i", "tests/data/example.faa", "-o", str(tmp_path), "-m", "cazyme"]) == 1
    assert any(record.levelname == "ERROR" for record in caplog.records)
    temp_path.rename(cazyme_hmms_db)


@pytest.mark.parametrize(
    "output",
    ("mock_output1", "mock_output2"),
)
def test_main_conclude(output: str, monkeypatch: Generator, capsys: pytest.CaptureFixture):
    monkeypatch.setattr(dbcanlight_entry, "conclude", mockreturn)
    assert main(["conclude", output]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"output: {output}" in captured
