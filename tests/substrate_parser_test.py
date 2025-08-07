from __future__ import annotations

from itertools import product
from typing import Generator

import pytest

import dbcanlight.substrate_parser as substrate_parser
from dbcanlight import VERSION
from dbcanlight.substrate_parser import main, substrate_mapping


def test_substrate_mapping():
    input = [
        [
            "CBM46_e1.hmm|CBM46:103|GH5_4:102|3.2.1.4:6|GH74:3|CBM64:1|CBM3:1|CBM2:1",
            86,
            "tr|D4P8C6|D4P8C6_9BACI",
            569,
            4.8e-19,
            10,
            85,
            474,
            558,
            0.872,
        ]
    ]
    expect = [
        [
            "CBM46_e1.hmm",
            "CBM46:103|GH5_4:102|GH74:3|CBM64:1|CBM3:1|CBM2:1",
            "3.2.1.4:6",
            "cellulose",
            86,
            "tr|D4P8C6|D4P8C6_9BACI",
            569,
            4.8e-19,
            10,
            85,
            474,
            558,
            0.872,
        ]
    ]
    list(substrate_mapping(input)) == expect


def test_main_help():
    assert main(["--help"]) == main(["-h"]) == 0


def test_main_version(capsys: pytest.CaptureFixture):
    assert main(["--version"]) == main(["-V"])
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert captured[0] == captured[1] == VERSION


@pytest.mark.parametrize(
    "input, output",
    tuple(product(("mock_input1", "mock_input2"), ("mock_output1", "mock_output2"))),
)
def test_main(input: str, output: str, monkeypatch: Generator, capsys: pytest.CaptureFixture):
    def mockreturn(**kwargs):
        for k, v in kwargs.items():
            print(f"{k}: {v}")

    monkeypatch.setattr(substrate_parser, "_run", mockreturn)
    assert main(["-i", input, "-o", output]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"input: {input}" in captured
    assert f"output: {output}" in captured
