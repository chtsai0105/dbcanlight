#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import sys
import textwrap

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

from pathlib import Path

import pyhmmer

from dbcanlight.config import db_path, header
from dbcanlight.hmmsearch_parser import overlap_filter
from dbcanlight.substrate_parser import get_subs_dict, substrate_mapping
from dbcanlight.utils import writer


class hmmsearch_module:
    def __init__(self, faa_file: Path, hmm_file: Path):
        self._faa = faa_file
        self._hmm_file = hmm_file

    def _load_input(self) -> None:
        seq_file = pyhmmer.easel.SequenceFile(self._faa, digital=True)
        self._sequences = seq_file.read_block()
        self._kh = pyhmmer.easel.KeyHash()
        for seq in self._sequences:
            self._kh.add(seq.name)

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
                            len(self._sequences[self._kh[hit.name]]),
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

    def run(self, evalue: float, coverage: float, threads: int = 0) -> dict[list[list]]:
        self._load_input()
        return self._run_hmmsearch(self._sequences, evalue, coverage, threads)


def cazyme_finder(input: str, output, evalue: float, coverage: float, threads: int, **kwargs) -> None:
    hmm_file = db_path.cazyme_hmms
    finder = hmmsearch_module(Path(input), hmm_file)
    results = finder.run(evalue=evalue, coverage=coverage, threads=threads)
    results = overlap_filter(results)
    if output == sys.stdout:
        out = output
    else:
        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        out = out / "cazymes.tsv"
    writer(results, out, header.hmmsearch)


def substrate_finder(input: str, output, evalue: float, coverage: float, threads: int, **kwargs) -> None:
    hmm_file = db_path.subs_hmms
    finder = hmmsearch_module(Path(input), hmm_file)
    results = finder.run(evalue=evalue, coverage=coverage, threads=threads)
    results = overlap_filter(results)
    results = substrate_mapping(results, get_subs_dict())
    if output == sys.stdout:
        out = output
    else:
        out = Path(output)
        out.mkdir(parents=True, exist_ok=True)
        out = out / "substrates.tsv"
    writer(results, out, header.substrate)


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
    parser.add_argument("-m", "--mode", choices=["cazyme", "sub"], required=True, help="mode")
    parser.add_argument("-e", "--evalue", type=float, default=1e-15, help="Reporting evalue cutoff (default=1e-15)")
    parser.add_argument("-c", "--coverage", type=float, default=0.35, help="Reporting coverage cutoff (default=0.35)")
    parser.add_argument("-t", "--threads", type=int, default=1, help="Total number of cpus allowed to use")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")
    parser.add_argument("-V", "--version", action="version", version=version("dbcanLight"))

    args = parser.parse_args()

    if args.output == sys.stdout:
        logger.setLevel("ERROR")
        for handler in logger.handlers:
            handler.setLevel("ERROR")

    if args.verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel("DEBUG")

    if args.mode == "cazyme":
        cazyme_finder(**vars(args))
    else:
        substrate_finder(**vars(args))


main.__name__ = "dbcanLight"
main._epilog = """
run_dbcan rewrite by Cheng-Hung Tsai chenghung.tsai[at]email.ucr.edu
"""

if __name__ == "__main__":
    main()
