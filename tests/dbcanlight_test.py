from itertools import product
from typing import Generator

import pytest

import dbcanlight._config as _config
import dbcanlight.__main__ as dbcanlight_entry
from dbcanlight import __version__
from dbcanlight.__main__ import main


def test_main_help():
    assert main(["--help"]) == main(["-h"]) == main() == 0


def test_main_version(capsys: pytest.CaptureFixture):
    assert main(["--version"]) == main(["-V"])
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert captured[0] == captured[1] == __version__


@pytest.mark.parametrize(
    "file, output, mode",
    tuple(product(("mock_input1", "mock_input2"), ("mock_output1", "mock_output2"), _config.avail_modes.keys())),
)
def test_main_search(file: str, output: str, mode: str, monkeypatch, capsys: pytest.CaptureFixture):
    def mockreturn(**kwargs):
        for k, v in kwargs.items():
            print(f"{k}: {v}")

    monkeypatch.setattr(dbcanlight_entry, "search", mockreturn)
    assert main(["search", "-i", file, "-o", output, "-m", mode]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"input: {file}" in captured
    assert f"output: {output}" in captured
    assert f"mode: {mode}" in captured


@pytest.mark.parametrize(
    "output",
    ("mock_output1", "mock_output2"),
)
def test_main_conclude(output: str, monkeypatch: Generator, capsys: pytest.CaptureFixture):
    def mockreturn(**kwargs):
        for k, v in kwargs.items():
            print(f"{k}: {v}")

    monkeypatch.setattr(dbcanlight_entry, "conclude", mockreturn)
    assert main(["conclude", output]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"output: {output}" in captured
