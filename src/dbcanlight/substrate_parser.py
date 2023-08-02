#!/usr/bin/env python3
import argparse
import csv
import logging
import re
import sys
import textwrap
from pathlib import Path

from .utils import header, writer
from ._version import __version__

subs_dict = {}
with open("/srv/projects/db/CAZY/CAZyDB/v11.0/fam-substrate-mapping-08252022.tsv", "r") as f:
    next(f)
    for line in csv.reader(f, delimiter="\t"):
        subs = set(re.split(r",[\s]|,", re.sub(r",[\s]and|[\s]and", ",", line[0])))
        if line[4]:
            subs_dict[line[2], line[4].strip()] = subs
        else:
            subs_dict[line[2], "-"] = subs


def substrate_mapping(filtered_results):
    results = []
    for line in filtered_results:
        subfam = None
        sub_composition = []
        sub_ec = []
        substrate = set()
        key1 = None
        key2 = ["-"]

        for p in line[0].split("|"):
            if p.endswith(".hmm"):
                hmm = p.split(".")[0]  # Add only the marker name without .hmm suffix
                subfam = hmm
                key1 = hmm.split("_")[0]
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

        results.append(
            [
                subfam,
                ("|").join(sub_composition) if sub_composition else "-",
                ("|").join(sub_ec) if sub_ec else "-",
                (",").join(list(substrate)) if substrate else "-",
                *line[1:-1],
                f"{float(line[-1]):0.3}",
            ]
        )
    return results


def main():
    """
    dbcanLight substrate parser.
    Parse the dbcan substrate searching output in dbcan format[*1], map them against
    the dbcan substrate mapping table[*2] and output in dbcan format. The domtblout
    output should first being processed by hmmsearch_parser.py before mapping by
    this script.

    *1 - dbcan format: hmm_name, hmm_length, gene_name, gene_length, evalue,
        hmm_from, hmm_to, gene_from, gene_to, coverage. (10 columns)
    *2 - dbcan substrate mapping table:
        http://bcb.unl.edu/dbCAN2/download/Databases/fam-substrate-mapping-08252022.tsv
    """
    logging.basicConfig(format=f"%(asctime)s {main.__name__} %(levelname)s %(message)s", level="INFO")
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(
        prog=main.__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(main.__doc__),
    )
    parser.add_argument("-i", "--input", type=Path, required=True, help="dbcan-sub searching output in dbcan format")
    parser.add_argument("-o", "--output", default=sys.stdout, help="Output file path (default=stdout)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")
    parser.add_argument("-V", "--version", action="version", version=__version__)

    args = parser.parse_args()

    if args.output == sys.stdout:
        logger.setLevel("ERROR")
        for handler in logger.handlers:
            handler.setLevel("ERROR")

    if args.verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel("DEBUG")

    with open(args.input, "r") as f:
        results = substrate_mapping(csv.reader(f, delimiter="\t"))
        if args.output == sys.stdout:
            out = args.output
        else:
            out = Path(args.output) / "substrates.tsv"
        writer(results, out, header.substrate)


main.__name__ = "dbcanLight-subparser"


if __name__ == "__main__":
    main()
