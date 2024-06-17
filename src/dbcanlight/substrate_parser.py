#!/usr/bin/env python3
"""Substrate-parser module."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path
from typing import Generator, Iterator, Sequence

from . import __entry_points__, __version__, _config
from ._utils import args_parser, check_db, writer
from .hmmsearch_parser import HmmsearchParser


@check_db(_config.db_path.subs_mapper)
def substrate_mapping(results: Sequence[list] | Iterator[list]) -> Generator[list, None, None]:
    """Map the hmm profiles to the corresponding substrates."""

    def get_subs_dict() -> dict[set]:
        subs_dict = {}
        with open(_config.db_path.subs_mapper) as f:
            next(f, None)
            for line in csv.reader(f, delimiter="\t"):
                subs = set(re.split(r",[\s]|,", re.sub(r",[\s]and|[\s]and", ",", line[0])))
                if line[4]:
                    subs_dict[line[2], line[4].strip()] = subs
                else:
                    subs_dict[line[2], "-"] = subs
        return subs_dict

    subs_dict = get_subs_dict()

    for line in results:
        if line == _config.headers.cazyme:
            continue
        subfam = None
        sub_composition = []
        sub_ec = []
        substrate = set()
        key1 = None
        key2 = ["-"]

        for p in line[0].split("|"):
            if p.endswith(".hmm"):
                subfam = p
                key1 = p.split("_")[0]
            elif len(p.split(".")) == 4:
                sub_ec.append(p)
                key2.append(p.split(":")[0])
            else:
                sub_composition.append(p)

        for ec in key2:
            try:
                substrate.update(subs_dict[key1, ec])
            except KeyError:
                # logging.debug(f"No substrate found in {profile[0]}")
                pass

        yield [
            subfam,
            ("|").join(sub_composition) if sub_composition else "-",
            ("|").join(sub_ec) if sub_ec else "-",
            (",").join(list(substrate)) if substrate else "-",
            *line[1:-1],
            f"{float(line[-1]):0.3}",
        ]


def main(args: list[str] | None = None) -> int:
    """
    Dbcanlight substrate parser.

    Parse the dbcan substrate search output in dbcan format[*1], map them against the dbcan substrate mapping table[*2] and output
    in dbcan format. The domtblout output should first being processed by dbcanlight-hmmparser before mapping by this script.

    *1 - dbcan format: hmm_name, hmm_length, gene_name, gene_length, evalue, hmm_from, hmm_to, gene_from, gene_to, coverage. (10
    columns)

    *2 - dbcan substrate mapping table: http://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv
    """
    return args_parser(_menu, args, prog=__entry_points__[__name__], description=main.__doc__)


def _run(input: str | Path, output: str | Path, **kwargs) -> None:
    """Process the data."""
    data_parser = HmmsearchParser(input)
    results = substrate_mapping(data_parser.data)
    writer(results, Path(output), header=_config.headers.sub)


def _menu(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Menu for this entry point."""
    parser.add_argument("-i", "--input", type=Path, required=True, help="dbcan-sub search output in dbcan format")
    parser.add_argument("-o", "--output", metavar="file", default="./substrates.tsv", help="Output file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.set_defaults(func=_run)

    return parser


if __name__ == "__main__":
    main()
