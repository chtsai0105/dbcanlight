from __future__ import annotations

from pathlib import Path

from dbcanlight._header import Headers
from dbcanlight.libdiamond import diamond_build, diamond_search


def test_diamond_build():
    diamond_build(Path("tests/data/cazydb.fa"))


def test_diamond_search():
    r = list(diamond_search(Path("tests/data/example.faa")))
    assert len(r) == 1
    assert len(r[0]) == len(Headers.diamond)
