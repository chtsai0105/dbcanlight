"""Functions for each module's pipeline."""

import csv
import logging
import re
from pathlib import Path
from typing import Generator

import dbcanlight._config as _config
from dbcanlight._utils import writer
from dbcanlight.libsearch import cazyme_search, diamond, subs_search


def build(**kwargs):
    """
    Download and build the required databases.

    (not completed)
    """
    pass


def search(
    input: str | Path,
    output: str | Path,
    *,
    mode: str = "cazyme",
    evalue: str | float = "AUTO",
    coverage: float = 0.35,
    threads: int = 1,
    blocksize: int = None,
    **kwargs,
) -> None:
    """
    The search module takes the protein fasta as input and searches against protein HMM, substrate HMM or diamond databases.

    Use "cazyme" mode to report the CAZyme families predicted by HMM; "sub" mode to report the potential substrates; and "diamond"
    mode to report the CAZyme families predicted by DIAMOND. (--tools hmmer/dbcansub/diamond in the original run_dbcan)
    """
    if mode != "diamond" and blocksize is not None:
        if blocksize < 1:
            raise ValueError(f"blocksize={blocksize} which is smaller than 1.")
    if mode == "cazyme":
        evalue = 1e-15 if evalue == "AUTO" else evalue
        results = cazyme_search(
            input, _config.db_path.cazyme_hmms, evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize
        )
    elif mode == "sub":
        evalue = 1e-15 if evalue == "AUTO" else evalue
        results = subs_search(
            input, _config.db_path.subs_hmms, evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize
        )
    elif mode == "diamond":
        if blocksize is not None:
            logging.warning('Parameter "blocksize" is not applicable on diamond.')
        evalue = 1e-102 if evalue == "AUTO" else evalue
        results = diamond(input, evalue=evalue, coverage=coverage, threads=threads)
    else:
        raise KeyError(f"{mode} is not an available mode.")
    header = getattr(_config.headers, mode)
    output = Path(output) / _config.avail_modes[mode]

    return writer(results, output, header=header)


def conclude(output: str | Path, **kwargs):
    """
    Conclude the results made by each module.

    Please make sure the predictions made by each module are included in the same folder and keep the original file names. (since
    the conclude module rely on the file name to identify the files and the corresponding tools that made it) The output
    "overview.tsv" will be output to the same folder.
    """

    def sort_helper(string: str):
        re_groups = re.search(r"\((\d+)-(\d+)\)", string)
        return (-(int(re_groups[2]) - int(re_groups[1])), int(re_groups[1]))

    def summarize(results: dict) -> Generator[list, dict, None]:
        for gene in results:
            tools_count = 0
            line = [gene, "+".join(x for x in sorted(results[gene]["ec"])) if results[gene]["ec"] else "-"]
            for mode in _config.avail_modes.keys():
                if mode == "cazyme":
                    fam = sorted(results[gene][mode], key=sort_helper)
                else:
                    fam = sorted(results[gene][mode])
                if fam:
                    line.append("+".join(fam))
                    tools_count += 1
                else:
                    line.append("-")
            line.append("+".join(x for x in sorted(results[gene]["substrate"])) if results[gene]["substrate"] else "-")
            line.append(tools_count)
            yield line

    results = {}
    avail_results = 0
    for mode, file_name in _config.avail_modes.items():
        file_path = Path(output) / file_name
        if file_path.is_file():
            logging.info(f"Processing {file_path}...")
            with open(file_path) as f:
                reader = csv.reader(f, delimiter="\t")
                next(reader, None)
                for line in reader:
                    if mode == "cazyme":
                        gene, fams = line[2], [f"{line[0]}({line[7]}-{line[8]})"]
                    elif mode == "sub":
                        gene, fams, ecs, subs = line[5], [line[0]], line[2].split("|"), line[3].split(",")
                    elif mode == "diamond":
                        gene, fams = line[0], line[1].split("|")[1:]
                    results.setdefault(gene, {r: set() for r in tuple(_config.avail_modes.keys()) + ("ec", "substrate")})

                    [results[gene][mode].add(fam) for fam in fams]
                    if mode == "sub":
                        [results[gene]["ec"].add(ec) for ec in ecs]
                        [results[gene]["substrate"].add(sub) for sub in subs]
            avail_results += 1
        else:
            logging.warning(f"Results from {mode} mode not exists.")
    if avail_results < 2:
        raise SystemExit(f"Required at least 2 results to conclude but got {avail_results}. Aborted.")
    results = summarize(results)

    return writer(results, Path(output) / "overview.tsv", header=_config.headers.overview)
