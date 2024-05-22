import sys

import pytest

if sys.version_info >= (3, 9):
    from collections.abc import Iterator
else:
    from typing import Iterator

from pathlib import Path

from dbcanlight.config import headers
from dbcanlight.dbcanlight import search, hmmsearch_module

input = "example/example.faa"
evalue = 1e-15
coverage = 0.35


def test_run_hmmsearch():
    hmm_file = Path.home() / ".dbcanlight/cazyme.hmm"
    finder = hmmsearch_module(Path(input), hmm_file, blocksize=None)
    assert isinstance(finder.run(evalue=evalue, coverage=coverage), Iterator)
