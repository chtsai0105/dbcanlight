#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
import textwrap
import tracemalloc

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

if sys.version_info >= (3, 9):
    from collections.abc import Iterator
else:
    from typing import Iterator

from pathlib import Path

import pyhmmer

from dbcanlight.config import db_path, header
from dbcanlight.hmmsearch_parser import overlap_filter
from dbcanlight.substrate_parser import get_subs_dict, substrate_mapping
from dbcanlight.utils import check_db, writer


class hmmsearch_module:
    def __init__(self, faa_file: Path, hmm_file: Path, blocksize=None):
        self._faa = faa_file
        self._hmm_file = hmm_file
        self._blocksize = blocksize

    def load_hmms(self) -> None:
        f = pyhmmer.plan7.HMMFile(self._hmm_file)
        if f.is_pressed():
            self._hmms = f.optimized_profiles()
        else:
            self._hmms = list(f)

        self._hmms_length = {}
        for hmm in self._hmms:
            self._hmms_length[hmm.name.decode()] = hmm.M
        if f.is_pressed():
            self._hmms.rewind()

    def _run_hmmsearch(
        self, sequences: pyhmmer.easel.DigitalSequenceBlock, evalue: float, coverage: float, threads: int
    ) -> dict[list[list]]:
        results = {}
        logging.debug("Start hmmsearch")
        for hits in pyhmmer.hmmsearch(self._hmms, sequences, cpus=threads):
            cog = hits.query_name.decode()
            cog_length = self._hmms_length[cog]
            for hit in hits:
                for domain in hit.domains:
                    hmm_from = domain.alignment.hmm_from
                    hmm_to = domain.alignment.hmm_to
                    cov = (hmm_to - hmm_from) / cog_length
                    if domain.i_evalue > evalue or cov < coverage:
                        continue
                    results.setdefault(hit.name.decode(), []).append(
                        [
                            cog,
                            cog_length,
                            hit.name.decode(),
                            len(sequences[self._kh[hit.name]]),
                            domain.i_evalue,
                            hmm_from,
                            hmm_to,
                            domain.alignment.target_from,
                            domain.alignment.target_to,
                            cov,
                        ]
                    )
        logging.info(f"Found {len(results)} genes have hits")
        return results

    def run(self, evalue: float, coverage: float, threads: int = 0) -> Iterator[dict[list[list]]]:
        self.load_hmms()
        with pyhmmer.easel.SequenceFile(self._faa, digital=True) as seq_file:
            while True:
                seq_block = seq_file.read_block(sequences=self._blocksize)
                if not seq_block:
                    break
                self._kh = pyhmmer.easel.KeyHash()
                for seq in seq_block:
                    self._kh.add(seq.name)
                yield self._run_hmmsearch(seq_block, evalue, coverage, threads)


def dbcan_runner(
    input: str, output, hmms, evalue: float, coverage: float, threads: int, blocksize: int = None, **kwargs
) -> None:
    tracemalloc.start()
    finder = hmmsearch_module(Path(input), hmms, blocksize)
    results = finder.run(evalue=evalue, coverage=coverage, threads=threads)
    results = overlap_filter(results)
    if hmms == db_path.subs_hmms:
        results = substrate_mapping(results, get_subs_dict())

    writer(results, output, header.hmmsearch)
    _, peak = tracemalloc.get_traced_memory()
    logging.debug(f"Peak momery usage: {peak / 10**6} MB")
    tracemalloc.stop()


def main():
    """
    A lightweight version of run_dbcan which uses pyhmmer to improve the multithreading performance.
    This script take the protein fasta as input. It report the CAZyme family when using the "cazyme" mode and report
    the potential substrates when using the "sub" mode. (--tools hmmer/dbcansub in the original run_dbcan)
    """
    logging.basicConfig(format=f"%(asctime)s {main.__name__} %(levelname)s %(message)s", level="INFO")
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(
        prog=main.__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(main.__doc__),
        epilog=textwrap.dedent(main._epilog),
    )
    parser.add_argument("-i", "--input", type=str, required=True, help="Plain or gzipped protein fasta")
    parser.add_argument("-o", "--output", default=sys.stdout, help="Output directory (default=stdout)")
    parser.add_argument(
        "-m", "--mode", choices=["cazyme", "sub"], required=True, help="Search against cazyme or substrate database"
    )
    parser.add_argument("-e", "--evalue", type=float, default=1e-15, help="Reporting evalue cutoff (default=1e-15)")
    parser.add_argument("-c", "--coverage", type=float, default=0.35, help="Reporting coverage cutoff (default=0.35)")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Total number of cpus allowed to use")
    parser.add_argument(
        "-b",
        "--blocksize",
        type=int,
        default=100000,
        help="Number of sequences to search per round. Lower the block size to use fewer memory (default=100000)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")
    parser.add_argument("-V", "--version", action="version", version=version("dbcanLight"))

    args = parser.parse_args()

    if args.output == sys.stdout:
        logger.setLevel("ERROR")
        for handler in logger.handlers:
            handler.setLevel("ERROR")
    else:
        args.output = Path(args.output)
        args.output.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel("DEBUG")

    if args.blocksize is not None:
        if args.blocksize < 1:
            logging.error(f"Error. Blocksize={args.blocksize} is smaller than 1.")
            sys.exit(1)

    if args.mode == "cazyme":
        check_db(db_path.cazyme_hmms)
        hmm_file = db_path.cazyme_hmms
        args.output = args.output / "cazymes.tsv"
    else:
        check_db(db_path.subs_hmms, db_path.subs_mapper)
        hmm_file = db_path.subs_hmms
        args.output = args.output / "substrates.tsv"
    dbcan_runner(**vars(args), hmms=hmm_file)


main.__name__ = "dbcanLight"
main._epilog = """
run_dbcan rewrite by Cheng-Hung Tsai chenghung.tsai[at]email.ucr.edu
"""

if __name__ == "__main__":
    main()
