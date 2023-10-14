import subprocess

import pytest
from dbcanlight.config import headers

faa_input = "example/example.faa"
hmm_input = "example/hmmsearch_output"


@pytest.fixture(scope="class")
def shared_tmpdir(tmpdir_factory):
    tmpdir = tmpdir_factory.mktemp("shared_tmpdir")
    yield tmpdir


def read_output(string):
    return [line.split("\t") for line in [line for line in string.strip("\n").split("\n")]]


class TestCazymeDetection:
    def test_cazyme_to_file(self, shared_tmpdir):
        subprocess.check_call(
            ["dbcanLight", "-i", faa_input, "-o", shared_tmpdir, "-m", "cazyme", "-t", "4"], text=True
        )
        with open(f"{shared_tmpdir}/cazymes.tsv") as f:
            output = read_output(f.read())

        assert len(output) == 5
        assert output[0] == headers.hmmsearch
        assert len(output[1]) == 10

    def test_cazyme_to_stdout(self, shared_tmpdir):
        output = subprocess.check_output(["dbcanLight", "-i", faa_input, "-m", "cazyme", "-t", "4"], text=True)
        output = read_output(output)
        with open(f"{shared_tmpdir}/cazymes.tsv") as f:
            output_from_file = read_output(f.read())

        assert len(output) == 4
        assert len(output[0]) == 10
        assert output == output_from_file[1:]


class TestHmmsearchAndSubstrateParser:
    def test_hmmsearch_parser_to_file(self, shared_tmpdir):
        subprocess.check_call(["dbcanLight-hmmparser", "-i", hmm_input, "-o", shared_tmpdir], text=True)
        with open(f"{shared_tmpdir}/cazymes.tsv") as f:
            output = read_output(f.read())

        assert len(output) == 7
        assert output[0] == headers.hmmsearch
        assert len(output[1]) == 10

    def test_hmmsearch_parser_to_stdout(self, shared_tmpdir):
        output = subprocess.check_output(["dbcanLight-hmmparser", "-i", hmm_input], text=True)
        output = read_output(output)
        with open(f"{shared_tmpdir}/cazymes.tsv") as f:
            output_from_file = read_output(f.read())

        assert len(output) == 6
        assert len(output[0]) == 10
        assert output == output_from_file[1:]

    def test_substrate_parser_to_file(self, shared_tmpdir):
        subprocess.check_call(
            ["dbcanLight-subparser", "-i", f"{shared_tmpdir}/cazymes.tsv", "-o", shared_tmpdir], text=True
        )
        with open(f"{shared_tmpdir}/substrates.tsv") as f:
            output = read_output(f.read())

        assert len(output) == 7
        assert output[0] == headers.substrate
        assert len(output[1]) == 13

    def test_substrate_parser_to_stdout(self, shared_tmpdir):
        output = subprocess.check_output(["dbcanLight-subparser", "-i", f"{shared_tmpdir}/cazymes.tsv"], text=True)
        output = read_output(output)
        with open(f"{shared_tmpdir}/substrates.tsv") as f:
            output_from_file = read_output(f.read())

        assert len(output) == 6
        assert len(output[0]) == 13
        assert output == output_from_file[1:]

    def test_pipe_hmmsearch_to_substrate_parser(self, shared_tmpdir):
        output = subprocess.check_output(
            ["dbcanLight-hmmparser -i example/hmmsearch_output | dbcanLight-subparser -i /dev/stdin"],
            shell=True,
            text=True,
        )
        output = read_output(output)
        with open(f"{shared_tmpdir}/substrates.tsv") as f:
            output_from_file = read_output(f.read())

        assert len(output) == 6
        assert len(output[0]) == 13
        assert output == output_from_file[1:]


class TestSubstrateDetection:
    def test_subs_to_file(self, shared_tmpdir):
        subprocess.check_call(["dbcanLight", "-i", faa_input, "-o", shared_tmpdir, "-m", "sub", "-t", "4"], text=True)
        with open(f"{shared_tmpdir}/substrates.tsv") as f:
            output = read_output(f.read())

        assert len(output) == 7
        assert output[0] == headers.substrate
        assert len(output[1]) == 13

    def test_subs_to_stdout(self, shared_tmpdir):
        output = subprocess.check_output(["dbcanLight", "-i", faa_input, "-m", "sub", "-t", "4"], text=True)
        output = read_output(output)
        with open(f"{shared_tmpdir}/substrates.tsv") as f:
            output_from_file = read_output(f.read())

        assert len(output) == 6
        assert len(output[0]) == 13
        assert output == output_from_file[1:]
