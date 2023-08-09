#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import logging
import sys
import textwrap

try:
    from importlib.metadata import version
except ImportError:
    from importlib_metadata import version

from operator import itemgetter
from pathlib import Path

from Bio import SearchIO

from .config import header
from .utils import writer


class hmmsearch_parser:
    def __init__(self, input: str):
        try:
            self._input = self._hmmer_reader(input)
            logging.info("Input is in hmmer3 format")
            self._dbcanformat = False
        except AssertionError:
            f = open(input, "r")
            logging.info("Input is in dbcan format")
            self._dbcanformat = True
            self._input = csv.reader(f, delimiter="\t")

    def _hmmer_reader(self, input: str) -> list:
        lines = []
        with open(input, "r") as f:
            for hmm in SearchIO.parse(f, "hmmsearch3-domtab"):
                for hit in hmm.hits:
                    for hsp in hit.hsps:
                        cov = (hsp.query_span - 1) / hmm.seq_len
                        lines.append(
                            [
                                hmm.id,
                                hmm.seq_len,
                                hit.id,
                                hit.seq_len,
                                hsp.evalue,
                                hsp.query_start + 1,
                                hsp.query_end,
                                hsp.hit_start + 1,
                                hsp.hit_end,
                                cov,
                            ]
                        )
        return lines

    def eval_cov_filter(self, evalue: float, coverage: float) -> dict[list]:
        results = {}
        for line in self._input:
            if self._dbcanformat:
                # 4: evalue; 9: coverage; 7: domain_from; 8: domain_to
                line[4], line[9] = float(line[4]), float(line[9])
                line[7], line[8] = int(line[7]), int(line[8])
            if line[4] > evalue or line[9] < coverage:
                continue
            results.setdefault(line[2], []).append(line)
        logging.info(f"Found {len(results)} genes have hits")
        return results


def overlap_filter(results: dict[list]) -> list:
    filtered_results = []
    for gene in sorted(results.keys()):
        hits = results[gene]
        logging.debug(f"{gene}: Found {len(hits)} hits")
        if len(hits) > 1:
            # Sorted by the gene_from
            hits = sorted(hits, key=itemgetter(7))
            idx = 0
            while idx < len(hits) - 1:
                hit1, hit2 = hits[idx], hits[idx + 1]
                # Check if two hits are overlapped over 50%
                overlap = hit1[8] - hit2[7]  # Overlap between the two hits (positive if overlap)
                len1 = hit1[8] - hit1[7]  # Length of hit1
                len2 = hit2[8] - hit2[7]  # Length of hit2
                # If two hits are overlapped and the overlapped region
                # is 50% larger than the total length of either of the hit
                if overlap > 0 and (overlap / len1 > 0.5 or overlap / len2 > 0.5):
                    # Hit1 (idx) is more confident than hit2 (idx+1),
                    # pop hit2 and do not move the pointer (the next hit would become idx+1 after pop)
                    if hit1[4] <= hit2[4]:
                        hits.pop(idx + 1)
                    # Hit2 (idx+1) is more confident than hit1 (idx),
                    # pop hit1 (idx) and do not move the pointer
                    # (Hit 2 and the next hit will become idx and idx+1 in the next iteration)
                    else:
                        hits.pop(idx)
                else:
                    # If not overlapped than move the pointer
                    idx += 1
            logging.debug(f"{gene}: {len(hits)} hit(s) passed the filter")
        for hit in hits:
            hit[4], hit[9] = f"{hit[4]:0.1e}", f"{hit[9]:0.3}"
        filtered_results.extend(hits)
    logging.info(f"{len(results)} hits passed the filter")
    return filtered_results


def main():
    """
    dbcanLight hmmsearch parser.
    Parse the CAZyme searching output in dbcan[*1] or domtblout format[*2], filter
    with the given evalue and coverage cutoff, and output in dbcan format.

    *1 - dbcan format: hmm_name, hmm_length, gene_name, gene_length, evalue,
        hmm_from, hmm_to, gene_from, gene_to, coverage. (10 columns)
    *2 - domtblout format:
        hmmsearch output with --domtblout enabled
    """
    logging.basicConfig(format=f"%(asctime)s {main.__name__} %(levelname)s %(message)s", level="INFO")
    logger = logging.getLogger()

    parser = argparse.ArgumentParser(
        prog=main.__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(main.__doc__),
    )
    parser.add_argument(
        "-i", "--input", type=str, required=True, help="CAZyme searching output in dbcan or hmmsearch format"
    )
    parser.add_argument("-o", "--output", default=sys.stdout, help="Output file path (default=stdout)")
    parser.add_argument("-e", "--evalue", type=float, default=1e-15, help="Reporting evalue cutoff (default=1e-15)")
    parser.add_argument("-c", "--coverage", type=float, default=0.35, help="Reporting coverage cutoff (default=0.35)")
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

    data_parser = hmmsearch_parser(args.input)
    results = data_parser.eval_cov_filter(args.evalue, args.coverage)
    results = overlap_filter(results)
    if args.output == sys.stdout:
        out = args.output
    else:
        out = Path(args.output) / "substrates.tsv"
    writer(results, out, header.substrate)


main.__name__ = "dbcanLight-hmmparser"

if __name__ == "__main__":
    main()
