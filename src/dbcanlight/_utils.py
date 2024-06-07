"""Utilities for package (internal use only)."""

import argparse
import logging
import re
import sys
import textwrap
from functools import wraps
from pathlib import Path
from typing import Callable, Iterator, Sequence


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

    def decorator(func):
        """The actual decorator function that wraps the class method."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """The wrapper function that checks the databases existence."""
            dbmissingList = []
            for db in dbs:
                dbmissingList.append(db) if not db.exists() else logging.debug(f"Found database: {db.absolute()}")
            if dbmissingList:
                print(
                    f"Database file {*dbmissingList,} missing. "
                    "Please follow the instructions in https://github.com/chtsai0105/dbcanLight#requirements "
                    "and download the required databases."
                )
                sys.exit(1)
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
        logging.basicConfig(format="%(asctime)s %(name)s %(levelname)s %(message)s", level="INFO")
        logger = logging.getLogger(prog)

        parser = argparse.ArgumentParser(
            prog=prog,
            formatter_class=CustomHelpFormatter,
            description=description,
            epilog=epilog,
        )
        parser = parser_func(parser)

        args = args if args else sys.argv[1:]
        if not args or "help" in args:
            parser.print_help(sys.stderr)
            raise SystemExit(0)
        args = parser.parse_args(args)

        if args.verbose:
            logger.setLevel("DEBUG")
            for handler in logger.handlers:
                handler.setLevel("DEBUG")
            logging.debug("Debug mode enabled.")

        args.func(**vars(args))

    except KeyboardInterrupt:
        logging.warning("Terminated by user.")
        return 1

    except SystemExit as err:
        if err.code != 0:
            logging.error(err)
            return 1

    return 0


def writer(results: Iterator[list[str]], output: Path, *, header: Sequence) -> None:
    """Writer function that write the results to the output file."""
    output.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Write output to {output}")
    with open(output, "w") as f:
        print("\t".join(header), file=f)

        for line in results:
            line[0] = line[0].rstrip(".hmm")
            print("\t".join([str(x) for x in line]), file=f)
