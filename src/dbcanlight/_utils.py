"""Utilities for package (internal use only)."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from functools import wraps
from pathlib import Path
from typing import Callable, Iterator, Sequence
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from . import _config, logger


class CustomHelpFormatter(argparse.HelpFormatter):
    """HelpFormatter that have customized function for text filling, line splitting and default parameter showing."""

    def _fill_text(self, text, width, indent):
        text = [self._whitespace_matcher.sub(" ", line).strip() for line in text.split("\n\n") if line != ""]
        return "\n\n".join([textwrap.fill(line, width) for line in text])

    def _split_lines(self, text, width):
        text = [self._whitespace_matcher.sub(" ", line).strip() for line in text.split("\n") if line != ""]
        formatted_text = []
        [formatted_text.extend(textwrap.wrap(line, width)) for line in text]
        # The textwrap module is used only for formatting help.
        # Delay its import for speeding up the common usage of argparse.
        return formatted_text

    def _get_help_string(self, action):
        help = action.help
        pattern = r"\(default: .+\)"
        if re.search(pattern, action.help) is None:
            if action.default not in [argparse.SUPPRESS, None, False]:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += " (default: %(default)s)"
        return help


def check_db(*dbs: Path) -> None:
    """A decorator to check whether the databases are exist."""

    def decorator(func: Callable):
        """The actual decorator function that wraps the class method."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """The wrapper function that checks the databases existence."""
            dbmissingList = []
            for db in dbs:
                dbmissingList.append(str(db)) if not db.exists() else logger.debug(f"Found database: {db.absolute()}")
            if dbmissingList:
                raise FileNotFoundError(
                    f'Database file missing {", ".join(dbmissingList)}. '
                    "Please use the build module to download the required databases."
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def args_parser(
    parser_func: Callable[[argparse.ArgumentParser], argparse.ArgumentParser],
    args: list[str] | None,
    *,
    prog: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
):
    """Preset menu structure for entry-point scripts."""
    try:
        parser = argparse.ArgumentParser(
            prog=prog,
            formatter_class=CustomHelpFormatter,
            description=description,
            epilog=epilog,
        )
        parser = parser_func(parser)

        args = args or sys.argv[1:]
        if not args:
            parser.print_help(sys.stderr)
            raise SystemExit(0)
        args = parser.parse_args(args)

        if hasattr(args, "threads"):
            if args.threads > _config.avail_cpus:
                args.threads = _config.avail_cpus

        if args.verbose:
            logger.setLevel("DEBUG")
            for handler in logger.handlers:
                handler.setLevel("DEBUG")
            logger.debug("Debug mode enabled.")
            logger.debug(vars(args))

        args.func(**vars(args))

    except KeyboardInterrupt:
        logger.warning("Terminated by user.")
        return 1

    except Exception as err:
        logger.error(err)
        return 1

    except SystemExit as err:
        if err.code != 0:
            logger.error(err)
            return 1

    return 0


def download(url: str, dest_dir: Path = _config.cfg_dir, filename: str | None = None) -> None:
    """Download from URL and save to file."""
    if filename is None:
        filename = url.split("/")[-1]
        full_path = dest_dir / filename
    else:
        full_path = dest_dir / filename
    try:
        logger.info(f"Downloading from {url} ...")
        with urlopen(url) as response:
            data = response.read()
            with open(full_path, "wb") as f:
                f.write(data)
    except HTTPError as e:
        raise HTTPError("URL currently unavailble.") from e
    except URLError as e:
        raise URLError("URL not found or no internet connection available.") from e


def writer(results: Iterator[list[str]], output: Path, *, header: Sequence) -> None:
    """Writer function that write the results to the output file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Write output to {output}")
    with open(output, "w") as f:
        f.write("\t".join(header) + "\n")

        for line in results:
            line[0] = line[0].rstrip(".hmm")
            f.write("\t".join([str(x) for x in line]) + "\n")
