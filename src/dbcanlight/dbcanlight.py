#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import re
import sys
import textwrap
from pathlib import Path

import dbcanlight.config as config
from dbcanlight import __name__, __version__
from dbcanlight.libsearch import diamond, hmmsearch, subs_search
from dbcanlight.utils import check_db, writer


class _CustomHelpFormatter(argparse.HelpFormatter):
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


def main_parser() -> argparse.Namespace:
    """Parser for command line inputs."""
    epilog = """
    Written by Cheng-Hung Tsai chenghung.tsai[at]email.ucr.edu
    """
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")

    parser = argparse.ArgumentParser(
        prog=main.__name__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(main.__doc__),
        epilog=textwrap.dedent(epilog),
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)

    subparsers(parser, parent_parser)

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    return args


def subparsers(parser: argparse.ArgumentParser, parent_parser: argparse.ArgumentParser) -> None:
    """Subparsers for each module."""
    subparsers = parser.add_subparsers()

    p_download = subparsers.add_parser(
        "download",
        parents=[parent_parser],
        formatter_class=_CustomHelpFormatter,
        help="Download the required databases",
        # description=download.__doc__,
    )
    p_download.set_defaults(func=download)

    p_search = subparsers.add_parser(
        "search",
        parents=[parent_parser],
        formatter_class=_CustomHelpFormatter,
        help="Search the databases for cazyme candidates.",
        description=search.__doc__,
    )
    p_search.add_argument("-i", "--input", type=str, required=True, help="Plain or gzipped protein fasta")
    p_search.add_argument("-o", "--output", default=sys.stdout, help="Output directory (default: stdout)")
    p_search.add_argument(
        "-m", "--mode", choices=["cazyme", "sub"], required=True, help="Search against cazyme or substrate database"
    )
    p_search.add_argument("-e", "--evalue", type=float, default=1e-15, help="Reporting evalue cutoff")
    p_search.add_argument("-c", "--coverage", type=float, default=0.35, help="Reporting coverage cutoff")
    p_search.add_argument("-t", "--threads", type=int, default=1, help="Total number of cpus allowed to use")
    p_search.add_argument(
        "-b",
        "--blocksize",
        type=int,
        default=100000,
        help="Number of sequences to search per round. Lower the block size to use fewer memory",
    )
    p_search.set_defaults(func=search)

    p_conclude = subparsers.add_parser(
        "conclude",
        parents=[parent_parser],
        formatter_class=_CustomHelpFormatter,
        help="Conclude the results made by each module.",
        # description=conclude.__doc__,
    )
    p_conclude.set_defaults(func=conclude)


def download():
    pass


def search(
    input: str, output: Path, mode: str, evalue: float, coverage: float, threads: int, blocksize: int = None, **kwargs
) -> None:
    if blocksize < 1:
        logging.error(f"Error. Blocksize={blocksize} is smaller than 1.")
        sys.exit(1)
    if mode == "cazyme":
        results = hmmsearch(input, config.db_path.cazyme_hmms, evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)
    elif mode == "subs":
        results = subs_search(input, config.db_path.subs_hmms, evalue=evalue, coverage=coverage, threads=threads, blocksize=blocksize)
    else:
        results = diamond()
    writer(results, output)


def conclude():
    pass


def main():
    """
    A lightweight version of run_dbcan which uses pyhmmer to improve the multithreading performance.
    This script take the protein fasta as input. It report the CAZyme family when using the "cazyme" mode and report
    the potential substrates when using the "sub" mode. (--tools hmmer/dbcansub in the original run_dbcan)
    """
    logging.basicConfig(format=f"%(asctime)s {__name__} %(levelname)s %(message)s", level="INFO")
    logger = logging.getLogger()

    args = main_parser()

    if args.output == sys.stdout:
        logger.setLevel("ERROR")
        for handler in logger.handlers:
            handler.setLevel("ERROR")
    else:
        args.output = Path(args.output)

    if args.verbose:
        logger.setLevel("DEBUG")
        for handler in logger.handlers:
            handler.setLevel("DEBUG")

    args.func(**vars(args))


if __name__ == "__main__":
    main()
