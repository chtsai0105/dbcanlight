from __future__ import annotations

from pathlib import Path

from dbcanlight import DB_PATH
from dbcanlight._header import Headers
from dbcanlight.libhmm import cazyme_search, subs_search

input = Path("tests/data/example.faa")


def test_cazyme_search():
    r = list(cazyme_search(input, DB_PATH["cazyme_hmms"]))
    assert len(r) == 1
    assert len(r[0]) == len(Headers.cazyme)


def test_subs_search():
    r = list(subs_search(input, DB_PATH["subs_hmms"]))
    assert len(r) == 2
    assert len(r[0]) == len(Headers.sub)
