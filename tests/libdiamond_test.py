from __future__ import annotations

from pathlib import Path

import pytest

import dbcanlight._config as _config
from dbcanlight.libdiamond import diamond_build, diamond_search


def test_diamond_build():
    diamond_build(Path("tests/data/cazydb.fa"))

@pytest.mark.slow
def test_diamond_search():
    r = list(diamond_search(Path("tests/data/example.faa")))
    assert len(r) == 3
    assert len(r[0]) == len(_config.headers.diamond)
