#!/usr/bin/env python3
"""Hmmsearch-parser module."""

from __future__ import annotations

import argparse
import csv
import logging
from operator import itemgetter
from pathlib import Path
from typing import Generator, Iterator, Sequence

from Bio import SearchIO

import dbcanlight._config as _config
from dbcanlight import __version__, entry_point_map
from dbcanlight._utils import args_parser, writer


class HmmsearchParser:
    """Parser class that help to process hmmer3/dbcanLight hmmsearch output."""

    def __init__(self, input: str | Path) -> None:
        """Initiate the object, determine whether the input is hmmer3 or dbcan format."""
        input = Path(input)
        try:
            self._data = self._hmmer_reader(input)
            logging.info("Input is hmmer3 format")
        except AssertionError:
            self._data = self._dbcan_reader(input)

    @property
    def data(self) -> list[list]:
        """Return processed data."""
        return self._data

    def _hmmer_reader(self, input: Path) -> list[list]:
        """Reader for files in hmmer3 domtblout format."""
        lines = []
        with open(input) as f:
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
        self._dbcanformat = False
        return lines

    def _dbcan_reader(self, input: Path) -> list[list]:
        """Reader for files in dbcan format."""
        with open(input) as f:
            logging.info("Input is dbcan format")
            first_3_lines = f.readline() + f.readline() + f.readline()
            try:
                dialect = csv.Sniffer().has_header(first_3_lines)
            except csv.Error:
                raise RuntimeError("Cannot found delimiter. The input does not appear to be in table format.")
            first_line_idx = 1 if dialect else 0
            first_line = first_3_lines.strip().split("\n")[first_line_idx].split("\t")

            if len(first_line) == 10:
                try:
                    [int(first_line[i]) for i in (1, 3, 5, 6, 7, 8)]
                    [float(first_line[i]) for i in (4, 9)]
                except ValueError:
                    raise RuntimeError("Input is neither hmmer3 nor dbcan format.")
                self._dbcanformat = True
            else:
                raise RuntimeError("Input is neither hmmer3 nor dbcan format.")

            f.seek(0)
            reader = csv.reader(f, delimiter="\t")
            if dialect:
                next(reader, None)
            lines = [(line) for line in reader]
        return lines

    def eval_cov_filter(self, *, evalue: float, coverage: float) -> Generator[dict[str, list[list]], None, None]:
        """Filter the hits by the evalue."""
        results = {}
        for line in self._data:
            if self._dbcanformat:
                # 4: evalue; 9: coverage; 7: domain_from; 8: domain_to
                line[4], line[9] = float(line[4]), float(line[9])
                line[7], line[8] = int(line[7]), int(line[8])
            if line[4] > evalue or line[9] < coverage:
                continue
            results.setdefault(line[2], []).append(line)
        logging.info(f"Found {len(results)} genes have hits")
        yield results


def overlap_filter(results: Sequence[dict[str, list[list]]] | Iterator[dict[str, list[list]]]) -> Generator[list, None, None]:
    """Filter the overlapped hits."""
    for results_batch in results:
        for gene in sorted(results_batch.keys()):
            hits = results_batch[gene]
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
            else:
                continue
            for hit in hits:
                hit[4], hit[9] = f"{hit[4]:0.1e}", f"{hit[9]:0.3}"
                yield hit


def main(args: list[str] | None = None) -> int:
    """
    Dbcanlight hmmsearch parser.

    Parse the CAZyme searching output in dbcan[*1] or domtblout format[*2], filter with the given evalue and coverage cutoff, and
    output in dbcan format.

    *1 - dbcan format: hmm_name, hmm_length, gene_name, gene_length, evalue, hmm_from, hmm_to, gene_from, gene_to, coverage. (10
    columns)

    *2 - domtblout format: hmmsearch output with --domtblout enabled
    """
    return args_parser(_menu, args, prog=entry_point_map[__name__], description=main.__doc__)


def _run(input: str | Path, output: str | Path, **kwargs) -> None:
    """Process the data."""
    data_parser = HmmsearchParser(input)
    results = data_parser.eval_cov_filter(**kwargs)
    results = overlap_filter(results)
    writer(results, Path(output), header=_config.headers.cazyme)


def _menu(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Menu for this entry point."""
    parser.add_argument(
        "-i", "--input", metavar="file", type=str, required=True, help="CAZyme search output in dbcan or hmmsearch format"
    )
    parser.add_argument("-o", "--output", metavar="file", default="./cazymes.tsv", help="Output file")
    parser.add_argument("-e", "--evalue", metavar="float", default=1e-15, help="Evalue cutoff")
    parser.add_argument(
        "-c", "--coverage", metavar="float", type=float, default=0.35, help="Coverage cutoff (not applicable on diamond)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.set_defaults(func=_run)

    return parser


if __name__ == "__main__":
    main()
