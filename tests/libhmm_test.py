from __future__ import annotations

from pathlib import Path

from dbcanlight.libhmm import cazyme_search, subs_search
import dbcanlight._config as _config

input = Path("tests/data/example.faa")


def test_cazyme_search():
    r = list(cazyme_search(input, _config.db_path.cazyme_hmms))
    assert len(r) == 4
    assert len(r[0]) == len(_config.headers.cazyme)


def test_subs_search():
    r = list(subs_search(input, _config.db_path.subs_hmms))
    assert len(r) == 6
    assert len(r[0]) == len(_config.headers.sub)
