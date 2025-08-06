"""Utilities for package (internal use only)."""

from __future__ import annotations

import json
import shutil
import threading
import time
import warnings
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Iterator, Literal, Sequence, TypeVar

import urllib3

from . import AVAIL_CPUS, DATABASE_METADATA

_C = TypeVar("Callable", bound=Callable[..., Any])
URLLIB_TIMEOUT = urllib3.util.Timeout(connect=5.0, read=10.0)


def load_db(db_config_path: Path, cfg_dir: Path):
    with open(db_config_path) as f:
        db_urls: dict[Literal["cazyme_hmms", "subs_hmms", "subs_mapper", "diamond"], str] = json.load(f)

    db_path: dict[Literal["cazyme_hmms", "subs_hmms", "subs_mapper", "diamond"], Path] = {}
    for dbname, filename in zip(db_urls.keys(), ("cazyme.hmm", "substrate.hmm", "substrate_mapping.tsv", "cazydb.dmnd")):
        db_file = cfg_dir / filename
        if db_file.is_file():
            db_path[dbname] = db_file
    return db_urls, db_path


class CheckDB:
    def __init__(self, *dbs: Path):
        self._dbs = dbs

    def __call__(self, func: _C) -> _C:
        @wraps(func)
        def wrapper(*args, **kwargs):
            missing_dbs = []
            for db in self._dbs:
                if not db.is_file():
                    missing_dbs.append(db)
            if missing_dbs:
                raise FileNotFoundError(
                    f"Database file missing {', '.join(missing_dbs)}. "
                    "Please use the build module to download the required databases."
                )
            return func(*args, **kwargs)

        return wrapper


def check_threads(func: _C) -> _C:
    """Decorator to validate and adjust the 'threads' parameter passed to a function.

    Ensures the 'threads' parameter is a positive integer and does not exceed the number of available CPU cores. If 'threads'
    exceeds the available cores, it is adjusted to the maximum available.

    Args:
        func (Callable): The function to wrap.

    Returns:
        Callable: The wrapped function with validated 'threads' parameter.

    Raises:
        TypeError: If the 'threads' argument is not an integer.
        ValueError: If the 'threads' argument is not greater than 0.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """Validate and adjust the 'threads' parameter before passing to a function."""
        if "threads" in kwargs:
            kwargs["threads"] = check(kwargs["threads"])
        else:
            args = list(args)
            import inspect

            sig = inspect.signature(func)
            params = list(sig.parameters)
            if "threads" in params:
                threads_index = params.index("threads")
                if len(args) > threads_index:
                    args[threads_index] = check(args[threads_index])

        return func(*args, **kwargs)

    def check(threads: int) -> int:
        if not isinstance(threads, int):
            raise TypeError("Argument threads must be an integer.")
        if threads <= 0:
            raise ValueError("Argument threads must be an integer greater than 0.")
        if threads > 0 and threads > AVAIL_CPUS:
            warnings.warn(f"Argument threads={threads} exceeds available CPU cores {AVAIL_CPUS}. Setting it to {AVAIL_CPUS}.")
            threads = AVAIL_CPUS
        return threads

    return wrapper


def check_binary(prog: str, bins: tuple, conda_url: str | None = None, source_url: str | None = None) -> str:
    """Find the path of a binary from the given sequence of entry points.

    This function searches for the binaries in the system's PATH and returns the path of the first binary found. If none are
    found, it raises an error.

    Args:
        *bins (str): Entry points (binary names) to search for.

    Returns:
        Path: The full path to the first available binary.

    Raises:
        BinaryNotFoundError: If none of the binaries are found in the system's PATH.
    """
    for bin in bins:
        bin_path = shutil.which(bin)
        if bin_path:
            return bin_path

    conda_msg = ""
    source_msg = ""
    if conda_url or source_url:
        install_msg = " Please install it "
    if conda_url:
        conda_msg = f"through 'conda install {conda_url}'"
        if source_url:
            conda_msg += " or "
    if source_url:
        source_msg = f"from source following the instruction on {source_url}"

    raise RuntimeError(f"{prog} not found.{install_msg}{conda_msg}{source_msg}")


def fetch_database_metadata():
    http = urllib3.PoolManager(timeout=URLLIB_TIMEOUT)
    response = http.request("GET", DATABASE_METADATA)

    if response.status == 200:
        data = json.loads(response.data.decode("utf-8"))
        return data
    else:
        print(f"Failed to fetch data: HTTP {response.status}")


class Downloader:
    def __init__(self, url: str, dest: str | Path, *, overwrite: bool = False, threads: int = 4, update_interval: int = 2):
        self._url = url

        dest = Path(dest)
        self._dest: Path = dest
        self.run(overwrite, threads, update_interval)

    def run(self, overwrite, threads, update_interval) -> None:
        self._overwrite = overwrite
        filename = self._url.split("/")[-1]
        if self._dest.exists():
            if self._dest.is_dir():
                self._dest = self._dest / filename
            else:
                if not overwrite:
                    return
        else:
            if not self._dest.parent.is_dir():
                raise NotADirectoryError("Dest is not exists and its upper level is not a directory.")

        self._http = urllib3.PoolManager(num_pools=threads, maxsize=threads, timeout=URLLIB_TIMEOUT)
        file_size = self.get_file_size()
        if not file_size:
            print("Could not determine file size. Server might not support range requests.")
            threads = 1

        # Initialize progress tracking
        self._chunk_files: list[Path] = [Path(f"{self._dest}.part{i}") for i in range(threads)] if threads > 1 else [self._dest]
        chunk_size: int = file_size // threads
        res = []
        self._progress: dict = {
            "progress": {i: 0 for i in range(threads)},
            "done": [False] * threads,
            "start_time": time.time(),
        }

        # Start progress monitoring in a separate thread
        progress_thread = threading.Thread(target=self.show_progress, args=(file_size, update_interval))
        progress_thread.daemon = True
        progress_thread.start()

        try:
            # Download file in parts
            for i in range(threads):
                start = i * chunk_size
                if file_size:
                    end = (file_size - 1) if i == (threads - 1) else (start + chunk_size - 1)
                else:
                    end = 0
                thread = threading.Thread(target=self.download_chunk, args=(start, end, i))
                res.append(thread)
                thread.start()

            # Wait for all threads to complete
            for i, thread in enumerate(res):
                thread.join()
                self._progress["done"][i] = True  # Mark as done

            # Merge parts after completion
            self.merge_chunks()
        except Exception:
            Path(self._dest).unlink()
            for i in range(threads):
                file = self._chunk_files[i]
                if file.is_file():
                    file.unlink()
            raise

        print("Download complete!")

    def get_file_size(self):
        """Get file size from the server."""
        response = self._http.request("HEAD", self._url)
        content_length = response.headers.get("Content-Length")
        return int(content_length) if content_length else None

    def download_chunk(self, start: int, end: int, part: int):
        """Download a file chunk using HTTP Range headers."""
        headers = {"Range": f"bytes={start}-{end}"} if end > 0 else None
        response = self._http.request("GET", self._url, headers=headers, preload_content=False)

        file = self._chunk_files[part]
        with open(file, "wb") as f:
            downloaded = 0
            for chunk in response.stream(1024):
                f.write(chunk)
                downloaded += len(chunk)
                self._progress["progress"][part] = downloaded  # Update progress dictionary

        response.release_conn()

    def merge_chunks(self):
        """Merge downloaded file chunks into the final file."""
        with open(self._dest, "wb") as outfile:
            for file in self._chunk_files:
                with open(file, "rb") as infile:
                    outfile.write(infile.read())
                file.unlink()

    def show_progress(self, total_size: int, update_interval: int):
        """Display download progress in real-time."""
        while any(not done for done in self._progress["done"]):
            downloaded = sum(self._progress["progress"].values())
            percent = f" ({(downloaded / total_size):.2%}) " if total_size else ""
            total_size_repr = f"{(total_size / (1024 * 1024)):.2f}" if total_size else "?"
            speed = downloaded / (time.time() - self._progress["start_time"]) / (1024 * 1024)  # MB/s

            print(
                f"Downloaded: {downloaded / (1024 * 1024):.2f} MB / {total_size_repr} MB{percent}- Speed: {speed:.2f} MB/s",
                end="\r",
            )
            time.sleep(update_interval)


def writer(results: Iterator[list[str]], output: Path, *, header: Sequence) -> None:
    """Writer function that write the results to the output file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    # logger.info(f"Write output to {output}")
    with open(output, "w") as f:
        f.write("\t".join(header) + "\n")

        for line in results:
            line[0] = line[0].rstrip(".hmm")
            f.write("\t".join([str(x) for x in line]) + "\n")
