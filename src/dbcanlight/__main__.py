#!/usr/bin/env python3
"""The dbcanlight cli menu."""

from __future__ import annotations

import argparse

from . import AUTHOR, AVAIL_CPUS, AVAIL_MODES, ENTRY_POINTS, VERSION
from ._args_parser import CustomHelpFormatter, args_parser
from .pipeline import build, conclude, search


def _menu_build(
    subparser: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser | None = None
) -> argparse.ArgumentParser:
    """Menu for build module."""
    p_build: argparse.ArgumentParser = subparser.add_parser(
        "build",
        parents=[parent_parser] if parent_parser else [],
        formatter_class=CustomHelpFormatter,
        help="Download and build the required databases",
        description=build.__doc__,
    )
    p_build.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force to rebuild the databases.",
    )
    p_build.add_argument(
        "-t",
        "--threads",
        type=int,
        default=AVAIL_CPUS if AVAIL_CPUS <= 4 else 4,
        help="Number of cpu to use. Will use at most 4 CPUs even if more are specified",
    )
    p_build.set_defaults(func=build)


def _menu_search(
    subparser: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser | None = None
) -> argparse.ArgumentParser:
    """Menu for search module."""
    p_search: argparse.ArgumentParser = subparser.add_parser(
        "search",
        parents=[parent_parser] if parent_parser else [],
        formatter_class=CustomHelpFormatter,
        help="Search the databases for cazyme candidates",
        description=search.__doc__,
    )
    p_search.add_argument("-i", "--input", metavar="file", type=str, required=True, help="Plain or gzipped protein fasta")
    p_search.add_argument("-o", "--output", metavar="directory", type=str, default=".", help="Output directory")
    p_search.add_argument(
        "-m", "--mode", choices=AVAIL_MODES.keys(), required=True, help="Search against cazyme or substrate database"
    )
    p_search.add_argument(
        "-e",
        "--evalue",
        metavar="float/AUTO",
        default="AUTO",
        help="Evalue cutoff. Use 1e-15 for hmmsearch and 1e-102 for diamond when specifying AUTO (default: AUTO)",
    )
    p_search.add_argument("-c", "--coverage", metavar="float", type=float, default=0.35, help="Coverage cutoff")
    p_search.add_argument("-t", "--threads", metavar="int", type=int, default=AVAIL_CPUS, help="Number of CPU to use")
    p_search.add_argument(
        "-b",
        "--blocksize",
        metavar="int",
        type=int,
        default=100000,
        help="Number of sequence to search per batch. Lower the blocksize to use fewer memory. "
        "Set as 0 to disable batching (default: 100000, not applicable on diamond)",
    )
    p_search.set_defaults(func=search)


def _menu_conclude(
    subparser: argparse._SubParsersAction, parent_parser: argparse.ArgumentParser | None = None
) -> argparse.ArgumentParser:
    """Menu for conclude module."""
    p_conclude: argparse.ArgumentParser = subparser.add_parser(
        "conclude",
        parents=[parent_parser] if parent_parser else [],
        formatter_class=CustomHelpFormatter,
        help="Conclude the results made by each module",
        description=conclude.__doc__,
    )
    p_conclude.add_argument("output", type=str, help="Folder that contains dbcanlight search results")
    p_conclude.set_defaults(func=conclude)
    parent_parser.add_help


def _menu(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Menu for this entry point."""
    parser.add_argument("-V", "--version", action="version", version=VERSION)

    subparsers = parser.add_subparsers(title="Modules", metavar="")

    # Module-wise shared args
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode for debug")

    _menu_build(subparsers, parent_parser)
    _menu_search(subparsers, parent_parser)
    _menu_conclude(subparsers, parent_parser)

    return parser


def main(args: list[str] | None = None) -> int:
    """
    A lightweight version of run_dbcan for CAZyme annotation.

    DbcanLight comprises 3 modules - download, search and conclude. The download module downloads the required databases from
    dbcan website. The search module searches against protein HMM, substrate HMM or diamond databases and reports the hits
    separately. The conclude module gathers all the results made by each module and reports a brief overview.
    """

    return args_parser(_menu, args, prog=ENTRY_POINTS[__name__], description=main.__doc__, epilog=f"Written by {AUTHOR}")


if __name__ == "__main__":
    main()
