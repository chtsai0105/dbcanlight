"""Functions for diamond."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Callable, Generator, TypeVar

from . import DB_PATH, logger
from ._utils import CheckDB, check_binary

_C = TypeVar("Callable", bound=Callable[..., Any])


def _diamond_bin(func: _C) -> _C:
    def wrapper(*args, **kwargs):
        check_binary("diamond", ("diamond",), "bioconda::diamond", "https://github.com/bbuchfink/diamond")
        return func(*args, **kwargs)

    return wrapper


@_diamond_bin
def diamond_build(input: str | Path, output: str | Path = DB_PATH["diamond"], *, threads: int = 1) -> str | None:
    """Function for diamond build. Build a database from fasta file."""
    cmd = ["diamond", "makedb", "--db", str(output), "--in", str(input), "--threads", str(threads), "--quiet"]
    logger.debug(f"Command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        return result.stderr.decode()


@CheckDB(DB_PATH["diamond"])
@_diamond_bin
def diamond_search(
    input: str | Path, *, evalue: float = 1e-102, coverage: float = 0.35, threads: int = 1
) -> Generator[list, None, None]:
    """Function for cazyme diamond blastp. Returns a generator of list of results."""
    cmd = [
        "diamond",
        "blastp",
        "--db",
        str(DB_PATH["diamond"]),
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
    logger.debug(f"Command: {' '.join(cmd)}")
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
