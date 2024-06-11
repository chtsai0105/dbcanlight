from __future__ import annotations

from itertools import product
from typing import Generator

import pytest

import dbcanlight.hmmsearch_parser as hmmsearch_parser
from dbcanlight import __version__
from dbcanlight.hmmsearch_parser import HmmsearchParser, main, overlap_filter


class TestHmmsearchParser:
    def test_hmmsearch_parser_dbcan_format(self):
        data_parser = HmmsearchParser("tests/data/cazymes.tsv")
        assert isinstance(data_parser.data, list) and len(data_parser.data) == 3
        results = data_parser.eval_cov_filter(evalue=1e-90, coverage=0.5)
        results = next(results)
        assert isinstance(results, dict) and len(results) == 2

    def test_hmmsearch_parser_hmmsearch_format(self):
        data_parser = HmmsearchParser("tests/data/hmmsearch_output")
        assert isinstance(data_parser.data, list) and len(data_parser.data) == 356
        results = data_parser.eval_cov_filter(evalue=1e-90, coverage=0.5)
        results = next(results)
        assert isinstance(results, dict) and len(results) == 3

    def test_hmmsearch_parser_invalid_format(self):
        with pytest.raises(RuntimeError, match="Cannot found delimiter. The input does not appear to be in table format."):
            HmmsearchParser("tests/data/example.faa")

    def test_hmmsearch_parser_invalid_tsv_format(self):
        with pytest.raises(RuntimeError, match="Input is neither hmmer3 nor dbcan format."):
            HmmsearchParser("tests/data/diamond.tsv")

    def test_hmmsearch_parser_invalid_format_with_10_columns(self):
        with pytest.raises(RuntimeError, match="Input is neither hmmer3 nor dbcan format."):
            HmmsearchParser("tests/data/bedpe.tsv")


def test_overlap_filter():
    input = [
        {
            "scof1": [
                ["a.hmm", 100, "scof1", 500, 2.23e-30, 1, 51, 101, 151, 0.50],
                ["a.hmm", 100, "scof1", 500, 2.23e-30, 1, 51, 126, 176, 0.50],
                ["a.hmm", 100, "scof1", 500, 5.23e-22, 11, 46, 126, 161, 0.35],
            ],
            "scof2": [
                ["a.hmm", 100, "scof2", 1000, 2.23e-30, 1, 51, 301, 351, 0.50],
                ["b.hmm", 150, "scof1", 1000, 1.25e-33, 11, 21, 281, 381, 0.67],
                ["b.hmm", 150, "scof1", 1000, 1.11e-33, 11, 21, 271, 372, 0.68],
            ],
        }
    ]
    expect = [
        ["a.hmm", 100, "scof1", 500, "2.2e-30", 1, 51, 101, 151, "0.5"],
        ["a.hmm", 100, "scof1", 500, "2.2e-30", 1, 51, 126, 176, "0.5"],
        ["b.hmm", 150, "scof1", 1000, "1.1e-33", 11, 21, 271, 372, "0.68"],
    ]
    assert list(overlap_filter(input)) == expect


def test_main_help():
    assert main(["--help"]) == main(["-h"]) == 0


def test_main_version(capsys: pytest.CaptureFixture):
    assert main(["--version"]) == main(["-V"])
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert captured[0] == captured[1] == __version__


@pytest.mark.parametrize(
    "input, output",
    tuple(product(("mock_input1", "mock_input2"), ("mock_output1", "mock_output2"))),
)
def test_main(input: str, output: str, monkeypatch: Generator, capsys: pytest.CaptureFixture):
    def mockreturn(**kwargs):
        for k, v in kwargs.items():
            print(f"{k}: {v}")

    monkeypatch.setattr(hmmsearch_parser, "_run", mockreturn)
    assert main(["-i", input, "-o", output]) == 0
    captured: str = capsys.readouterr().out
    captured = captured.split("\n")
    assert f"input: {input}" in captured
    assert f"output: {output}" in captured
