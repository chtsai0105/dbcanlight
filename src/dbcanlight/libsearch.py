"""Functions for hmmsearch."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Generator

import pyhmmer

import dbcanlight._config as _config
from dbcanlight._utils import check_db
from dbcanlight.hmmsearch_parser import overlap_filter
from dbcanlight.substrate_parser import substrate_mapping


@check_db(_config.db_path.cazyme_hmms)
def cazyme_search(
    input: str | Path, hmms: str | Path, *, evalue: float = 1e-15, coverage: float = 0.35, threads: int = 1, blocksize: int = None
) -> Generator[list, None, None]:
    """Function for cazyme hmmsearch. Returns a generator of list of results."""
    return _hmmsearch_pipeline(Path(input), Path(hmms), evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)


@check_db(_config.db_path.subs_hmms, _config.db_path.subs_mapper)
def subs_search(
    input: str | Path, hmms: str | Path, *, evalue: float = 1e-15, coverage: float = 0.35, threads: int = 1, blocksize: int = None
) -> Generator[list, None, None]:
    """Function for substrate hmmsearch. Returns a generator of list of results."""
    return substrate_mapping(
        _hmmsearch_pipeline(Path(input), Path(hmms), evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)
    )


@check_db(_config.db_path.diamond)
def diamond(
    input: str | Path, *, evalue: float = 1e-102, coverage: float = 0.35, threads: int = 1
) -> Generator[list, None, None]:
    """Function for cazyme diamond blastp. Returns a generator of list of results."""
    cmd = [
        "diamond",
        "blastp",
        "--db",
        str(_config.db_path.diamond),
        "--query",
        str(input),
        "--evalue",
        str(evalue),
        "--threads",
        str(threads),
        "--query-cover",
        str(coverage),
        "--max-target-seqs",
        "1",
        "--outfmt",
        "6",
    ]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as p:
        while True:
            stdout_line = p.stdout.readline()
            stderr_line = p.stderr.readline()
            if stdout_line == b"" and stderr_line == b"" and p.poll() is not None:
                break

            if stdout_line:
                yield stdout_line.decode().strip().split("\t")

            if stderr_line:
                raise RuntimeError(stderr_line.decode())


def _hmmsearch_pipeline(
    input: Path,
    hmms: Path,
    *,
    evalue: float = 1e-15,
    coverage: float = 0.35,
    threads: int = 1,
    blocksize: int | None = None,
) -> Generator[list, None, None]:
    """Hmmsearch pipeline."""
    hmms = _load_hmms(hmms)
    results = _load_seqs_and_hmmsearch(input, hmms, evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)
    results = overlap_filter(results)
    return results


def _load_hmms(hmm_file: Path) -> pyhmmer.plan7.HMMPressedFile | pyhmmer.plan7.HMMFile:
    """Load hmm profiles."""
    f = pyhmmer.plan7.HMMFile(hmm_file)
    if f.is_pressed():
        hmms = f.optimized_profiles()
        hmms.rewind()
        logging.debug("Use hmm pressed file.")
        return hmms
    else:
        logging.debug("Use regular hmm file.")
        return f


def _load_seqs_and_hmmsearch(
    input: Path,
    hmms: pyhmmer.plan7.HMMPressedFile | pyhmmer.plan7.HMMFile,
    *,
    evalue: float = 1e-15,
    coverage: float = 0.35,
    threads: int = 1,
    blocksize: int | None = None,
) -> Generator[dict[str, list[list]], None, None]:
    """Load query sequences and run hmmsearch by batch."""
    with pyhmmer.easel.SequenceFile(input, digital=True) as seq_file:
        block_start = 0
        while True:
            seq_block = seq_file.read_block(sequences=blocksize)
            if not seq_block:
                break
            if blocksize:
                logging.debug(f"Hmmsearch on sequence {block_start}-{block_start + blocksize}...")
            yield _run_hmmsearch(seq_block, hmms, evalue=evalue, coverage=coverage, threads=threads)
            if blocksize:
                block_start += blocksize


def _run_hmmsearch(
    sequences: pyhmmer.easel.SequenceBlock,
    hmms: pyhmmer.plan7.HMMPressedFile | pyhmmer.plan7.HMMFile,
    *,
    evalue: float = 1e-15,
    coverage: float = 0.35,
    threads: int = 1,
) -> dict[str, list[list]]:
    """Run hmmsearch."""
    results = {}
    for hits in pyhmmer.hmmsearch(hmms, sequences, cpus=threads):
        cog = hits.query_name.decode()
        cog_length = hits.query_length
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
                        hit.length,
                        domain.i_evalue,
                        hmm_from,
                        hmm_to,
                        domain.alignment.target_from,
                        domain.alignment.target_to,
                        cov,
                    ]
                )
    logging.info(f"Found {len(results)} genes have hits.")
    return results
