from pathlib import Path

from dbcanlight.dbcanlight import hmmsearch_module

input = "example/example.faa"


def test_hmmsearch():
    hmm_file = Path.home() / ".dbcanlight/cazyme.hmm"
    finder = hmmsearch_module(Path(input), hmm_file)
    assert isinstance(finder.run(evalue=1e-30, coverage=0.35), dict)
