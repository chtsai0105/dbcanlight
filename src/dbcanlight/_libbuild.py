from __future__ import annotations

from pathlib import Path

from . import DB_PATH
from ._utils import Downloader
from .libdiamond import diamond_build
from .libhmm import press_hmms


def _download(url: str, filepath: Path, *, threads: int = 1):
    filepath.unlink(missing_ok=True)
    Downloader(url, filepath, overwrite=True, threads=threads)


def _hmms(db_file: Path):
    hmm_binaries = [Path(f"{db_file}.{suffix}") for suffix in ("h3f", "h3i", "h3m", "h3p")]
    for hmm_binary in hmm_binaries:
        hmm_binary.unlink(missing_ok=True)
    # logger.info("Running hmmpress...")
    press_hmms(db_file)


def cazyme_hmms(url: str, filepath: Path, *, threads: int = 1):
    _download(url, filepath, threads=threads)
    _hmms(Path(DB_PATH["cazyme_hmms"]))


def subs_hmms(url: str, filepath: Path, *, threads: int = 1):
    _download(url, filepath, threads=threads)
    _hmms(Path(DB_PATH["subs_hmms"]))


def subs_mapper(url: str, filepath: Path, *, threads: int = 1):
    _download(url, filepath, threads=threads)
    pass


def diamond(url, filepath, *, threads: int = 1):
    _download(url, filepath, threads=threads)
    # logger.info("Building diamond database...")
    diamond_build(filepath, Path(DB_PATH["diamond"]), threads=threads)
