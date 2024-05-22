import subprocess
import sys
from pathlib import Path

import pytest

from dbcanlight.hmmsearch_parser import hmmsearch_parser, overlap_filter
from dbcanlight._utils import headers, writer


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


def test_hmmsearch_parser():
    input = "example/hmmsearch_output"
    data_parser = hmmsearch_parser(Path(input))
    results = data_parser.eval_cov_filter(1e-30, 0.35)
    results = overlap_filter(results)
    results = list(results)
    assert len(results) == 4 and len(results[0]) == 10
