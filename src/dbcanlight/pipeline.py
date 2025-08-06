"""Functions for each module's pipeline."""

from __future__ import annotations

import csv
import hashlib
import os
import re
from pathlib import Path
from typing import Generator

from ._header import Headers

from . import AVAIL_MODES, CFG_DIR, DB_PATH, _libbuild, logger
from ._utils import fetch_database_metadata, writer
from .libdiamond import diamond_search
from .libhmm import cazyme_search, subs_search


def build(force: bool = False, threads: int = 1, **kwargs) -> None:
    """
    Download and build the required databases.

    Clear the database files that already exist in the config folder. (~/.dbcanlight) Download from the dbcan website and use
    hmmpress to build the databases for hmm profile. Use the threads option to download parallelly.
    """
    if not os.access(CFG_DIR, os.W_OK):
        raise PermissionError(f"The config folder {CFG_DIR} is not writable.")

    if threads > 4:
        logger.warning("Specified more than 4 CPUs. Use only 4 at most.")
        threads = 4

    db_urls = fetch_database_metadata()

    logger.info("Checking databases...")
    for dbname, db_file in DB_PATH.items():
        print(dbname, end=" ", flush=True)
        if dbname == "diamond":
            filepath = CFG_DIR / "cazydb.fa"
        else:
            filepath = db_file

        if force:
            print("force rebuild")
        elif not db_file.is_file():
            print("not found")
        elif hashlib.md5(open(filepath, "rb").read()).hexdigest() != db_urls[dbname][1]:
            print("update required")
        else:
            print("ok")
            continue
        logger.info("Downloading %s from %s...", filepath, db_urls[dbname][0])
        getattr(_libbuild, dbname)(db_urls[dbname][0], filepath, threads=threads)


def search(
    input: str | Path,
    output: str | Path,
    *,
    mode: str = "cazyme",
    evalue: str | float = "AUTO",
    coverage: float = 0.35,
    threads: int = 1,
    blocksize: int = 100000,
    **kwargs,
) -> None:
    """
    The search module takes the protein fasta as input and searches against protein HMM, substrate HMM or diamond databases.

    Use "cazyme" mode to report the CAZyme families predicted by HMM; "sub" mode to report the potential substrates; and "diamond"
    mode to report the CAZyme families predicted by DIAMOND. (--tools hmmer/dbcansub/diamond in the original run_dbcan)
    """
    if mode != "diamond" and blocksize < 0:
        raise ValueError(f"blocksize={blocksize} which is smaller than 0.")
    if mode == "cazyme":
        evalue = 1e-15 if evalue == "AUTO" else evalue
        results = cazyme_search(
            input, DB_PATH["cazyme_hmms"], evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize
        )
    elif mode == "sub":
        evalue = 1e-15 if evalue == "AUTO" else evalue
        results = subs_search(input, DB_PATH["subs_hmms"], evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)
    elif mode == "diamond":
        if abs(blocksize) > 0:
            logger.warning('Parameter "blocksize" is not applicable on diamond.')
        evalue = 1e-102 if evalue == "AUTO" else evalue
        results = diamond_search(input, evalue=evalue, coverage=coverage, threads=threads)
    else:
        raise KeyError(f"{mode} is not an available mode.")
    header = getattr(Headers, mode)
    output = Path(output) / AVAIL_MODES[mode]

    return writer(results, output, header=header)


def conclude(output: str | Path, **kwargs) -> None:
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
            for mode in AVAIL_MODES.keys():
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
    for mode, file_name in AVAIL_MODES.items():
        file_path = Path(output) / file_name
        if file_path.is_file():
            logger.info(f"Processing {file_path}...")
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
                    results.setdefault(gene, {r: set() for r in tuple(AVAIL_MODES.keys()) + ("ec", "substrate")})

                    [results[gene][mode].add(fam) for fam in fams]
                    if mode == "sub":
                        [results[gene]["ec"].add(ec) for ec in ecs if ec != "-"]
                        [results[gene]["substrate"].add(sub) for sub in subs if sub != "-"]
            avail_results += 1
        else:
            logger.warning(f"Results from {mode} mode not exists.")
    if avail_results < 2:
        raise RuntimeError(f"Required at least 2 results to conclude but got {avail_results}. Aborted.")
    results = summarize(results)

    return writer(results, Path(output) / "overview.tsv", header=Headers.overview)
