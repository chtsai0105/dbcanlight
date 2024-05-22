import sys
from pathlib import Path

from dbcanlight.config import headers
from dbcanlight._utils import writer

cazyme_input = [
    ["a.hmm", 674, "scof1", 966, 3.6e-269, 1, 674, 163, 961, 0.999],
    ["b.hmm", 303, "scof1", 520, 1.5e-162, 1, 302, 37, 337, 0.993],
    ["c.hmm", 276, "scof2", 569, 1.8e-91, 2, 276, 66, 346, 0.993],
]

subs_input = [
    ["a.hmm", "GT35|GH77|GH13_39", "2.4.1.1:158", "-", 712, "scof1", 966, 3.4e-131, 1, 306, 164, 470, 0.428],
    ["a.hmm", "GT35|GH77|GH13_39", "2.4.1.1:158", "-", 712, "scof1", 966, 1.0e-172, 312, 711, 558, 961, 0.56],
    ["b.hmm", "AA1_1|AA1|CE4, 1.10.3.2:77", "lignin", 353, "scof2", 520, 2.2e-186, 6, 353, 29, 486, 0.983],
]


def read_output(string):
    return [line.split("\t") for line in [line for line in string.strip("\n").split("\n")]]


def test_writer_cazymes_to_stdout(capsys):
    results = iter(cazyme_input)
    writer(results, sys.stdout)
    output = capsys.readouterr().out
    output = read_output(output)
    expect = [list(map(str, x)) for x in cazyme_input]
    assert output == expect


def test_writer_subs_to_stdout(capsys):
    results = iter(subs_input)
    writer(results, sys.stdout)
    output = capsys.readouterr().out
    output = read_output(output)
    expect = [list(map(str, x)) for x in subs_input]
    assert output == expect


def test_writer_cazymes_to_file(tmpdir):
    output = Path(tmpdir)
    results = iter(cazyme_input)
    writer(results, Path(output))
    with open(output / "cazymes.tsv") as f:
        output = read_output(f.read())
    expect = [list(map(str, x)) for x in cazyme_input]
    assert output[0] == headers.hmmsearch and output[1:] == expect


def test_writer_subs_to_file(tmpdir):
    output = Path(tmpdir)
    results = iter(subs_input)
    writer(results, Path(output))
    with open(output / "substrates.tsv") as f:
        output = read_output(f.read())
    expect = [list(map(str, x)) for x in subs_input]
    assert output[0] == headers.substrate and output[1:] == expect
