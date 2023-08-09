from pathlib import Path

from dbcanlight.config import header
from dbcanlight.utils import writer


def load_file(file):
    with open(file) as f:
        line_1 = f.readline().strip("\n").split("\t")
        line_2 = f.readline().strip("\n").split("\t")
    return line_1, line_2


def test_writer_cazymes(tmpdir):
    file = tmpdir.join("cazymes.tsv")
    results = [["a.hmm", 100, "scof1", 500, 2.23e-30, 1, 51, 101, 151, 0.50]]
    expect = ["a.hmm", "100", "scof1", "500", "2.23e-30", "1", "51", "101", "151", "0.5"]
    writer(results, Path(file), header=header.hmmsearch)
    line_1, line_2 = load_file(file)
    assert line_1 == header.hmmsearch and line_2 == expect


def test_writer_substrates(tmpdir):
    file = tmpdir.join("substrates.tsv")
    results = [["subfam", "composition", "ec_number", "subs", 100, "scof1", 500, 2.23e-30, 1, 51, 101, 151, 0.50]]
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
    writer(results, Path(file), header=header.substrate)
    line_1, line_2 = load_file(file)
    assert line_1 == header.substrate and line_2 == expect
