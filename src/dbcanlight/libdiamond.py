"""Functions for diamond."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Generator

from . import _config, logger
from ._utils import check_db


def diamond_build(input: str | Path, output: str | Path = _config.db_path.diamond, *, threads: int = 1) -> str | None:
    """Function for diamond build. Build a database from fasta file."""
    cmd = ["diamond", "makedb", "--db", str(output), "--in", str(input), "--threads", str(threads), "--quiet"]
    logger.debug(f'Command: {" ".join(cmd)}')
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return result.stderr.decode()


@check_db(_config.db_path.diamond)
def diamond_search(
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
    logger.debug(f'Command: {" ".join(cmd)}')
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
