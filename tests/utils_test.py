from io import StringIO
from pathlib import Path

import pytest

from dbcanlight.config import headers
from dbcanlight.utils import writer

cazyme_input = ["a.hmm", 100, "scof1", 500, 2.23e-30, 1, 51, 101, 151, 0.50]


def load_file(file):
    with open(file) as f:
        line_1 = f.readline().strip("\n").split("\t")
        line_2 = f.readline().strip("\n").split("\t")
    return line_1, line_2


def test_writer_without_header():
    results = iter([cazyme_input])
    output = StringIO()
    expect = ["a.hmm", "100", "scof1", "500", "2.23e-30", "1", "51", "101", "151", "0.5"]
    writer(results, output)
    output.seek(0)
    line = output.read().strip("\n").split("\t")
    assert line == expect


def test_writer_cazymes(tmpdir):
    output = Path(tmpdir)
    results = iter([cazyme_input])
    expect = ["a.hmm", "100", "scof1", "500", "2.23e-30", "1", "51", "101", "151", "0.5"]
    writer(results, Path(output))
    line_1, line_2 = load_file(output / "cazymes.tsv")
    assert line_1 == headers.hmmsearch and line_2 == expect


def test_writer_substrates(tmpdir):
    output = Path(tmpdir)
    results = iter([["subfam", "composition", "ec_number", "subs", 100, "scof1", 500, 2.23e-30, 1, 51, 101, 151, 0.50]])
    expect = [
        "subfam",
        "composition",
        "ec_number",
        "subs",
        "100",
        "scof1",
        "500",
        "2.23e-30",
        "1",
        "51",
        "101",
        "151",
        "0.5",
    ]
    writer(results, output)
    line_1, line_2 = load_file(output / "substrates.tsv")
    assert line_1 == headers.substrate and line_2 == expect
