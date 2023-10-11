import sys

import pytest

if sys.version_info >= (3, 9):
    from collections.abc import Iterator
else:
    from typing import Iterator

from pathlib import Path

from dbcanlight.config import headers
from dbcanlight.dbcanlight import dbcan_runner, hmmsearch_module

input = "example/example.faa"
evalue = 1e-15
coverage = 0.35


def load_file(file):
    with open(file) as f:
        line_1 = f.readline().strip("\n").split("\t")
        line_2 = f.readline().strip("\n").split("\t")
    return line_1, line_2


@pytest.fixture(scope="module")
def shared_tmpdir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("shared_tmpdir")
    yield tmpdir


def test_run_hmmsearch():
    hmm_file = Path.home() / ".dbcanlight/cazyme.hmm"
    finder = hmmsearch_module(Path(input), hmm_file, blocksize=None)
    assert isinstance(finder.run(evalue=evalue, coverage=coverage), Iterator)


def test_cazyme_with_file(shared_tmpdir):
    output = Path(shared_tmpdir)
    hmm_file = Path.home() / ".dbcanlight/cazyme.hmm"
    expect = ["GT35.hmm", "674", "sp|P04045|PHSL1_SOLTU", "966", "3.6e-269", "1", "674", "163", "961", "0.999"]
    dbcan_runner(input=input, output=output, hmms=hmm_file, evalue=evalue, coverage=coverage, threads=1)
    line_1, line_2 = load_file(output / "cazymes.tsv")
    assert line_1 == headers.hmmsearch
    assert line_2 == expect


def test_cazyme_with_stdout(capsys):
    hmm_file = Path.home() / ".dbcanlight/cazyme.hmm"
    expect = ["GT35.hmm", "674", "sp|P04045|PHSL1_SOLTU", "966", "3.6e-269", "1", "674", "163", "961", "0.999"]
    dbcan_runner(input=input, output=sys.stdout, hmms=hmm_file, evalue=evalue, coverage=coverage, threads=1)
    output = capsys.readouterr().out
    output = [line.split("\t") for line in [lines for lines in output.split("\n")]]

    assert output[0] == expect
