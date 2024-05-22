import logging
from pathlib import Path
from typing import Generator

import pyhmmer

from dbcanlight.hmmsearch_parser import overlap_filter
from dbcanlight.substrate_parser import get_subs_dict, substrate_mapping


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

    def run(self, evalue: float, coverage: float, threads: int = 0) -> Generator[dict[list[list]], None, None]:
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


def hmmsearch(
    input: str | Path, hmms: str | Path, *, evalue: float = 1e-15, coverage: float = 0.35, threads: int = 1, blocksize: int = None
):
    finder = hmmsearch_module(Path(input), hmms, blocksize)
    results = finder.run(evalue=evalue, coverage=coverage, threads=threads)
    results = overlap_filter(results)
    return results


def subs_search(
    input: str | Path, hmms: str | Path, *, evalue: float = 1e-15, coverage: float = 0.35, threads: int = 1, blocksize: int = None
):
    results = substrate_mapping(hmmsearch(input, hmms, evalue, coverage, threads, blocksize), get_subs_dict())
    return results


def diamond():
    pass
