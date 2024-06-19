"""Functions for hmmsearch."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Generator

import pyhmmer

from . import _config, logger
from ._utils import check_db
from .hmmsearch_parser import overlap_filter
from .substrate_parser import substrate_mapping


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


def _load_hmms(hmm_file: Path) -> list[pyhmmer.plan7.OptimizedProfile | pyhmmer.plan7.HMM]:
    """Load hmm profiles."""
    f = pyhmmer.plan7.HMMFile(hmm_file)
    if f.is_pressed():
        f = f.optimized_profiles()
        f.rewind()
        logger.debug(f"Load {hmm_file} with pressed mode.")
    else:
        logger.debug(f"Load {hmm_file} with regular mode.")
    return list(f)


def _press_hmms(hmm_file: Path) -> None:
    """Press hmm into a database."""
    hmms = _load_hmms(hmm_file)
    logger.debug(f"Pressing {hmm_file}...")
    pyhmmer.hmmpress(hmms, hmm_file)


def _load_seqs_and_hmmsearch(
    input: Path,
    hmms: list[pyhmmer.plan7.OptimizedProfile | pyhmmer.plan7.HMM],
    *,
    evalue: float = 1e-15,
    coverage: float = 0.35,
    threads: int = 1,
    blocksize: int | None = None,
) -> Generator[dict[str, list[list]], None, None]:
    """Load query sequences and run hmmsearch by batch."""
    with pyhmmer.easel.SequenceFile(input, digital=True) as seq_file:
        for batch in itertools.count():
            seq_block = seq_file.read_block(sequences=blocksize)
            if not seq_block:
                break
            if blocksize:
                logger.debug(f"Hmmsearch on sequence {batch * blocksize + 1}-{batch * blocksize + len(seq_block)}...")
            yield _run_hmmsearch(seq_block, hmms, evalue=evalue, coverage=coverage, threads=threads)


def _run_hmmsearch(
    sequences: pyhmmer.easel.SequenceBlock,
    hmms: list[pyhmmer.plan7.OptimizedProfile | pyhmmer.plan7.HMM],
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
    logger.info(f"Found {len(results)} genes have hits.")
    return results
