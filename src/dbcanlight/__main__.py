#!/usr/bin/env python3
"""The dbcanlight cli menu."""

from __future__ import annotations

import argparse

import dbcanlight._config as _config
from dbcanlight import __author__, __version__, entry_point_map
from dbcanlight._utils import CustomHelpFormatter, args_parser
from dbcanlight.pipeline import build, conclude, search


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
        "-m", "--mode", choices=_config.avail_modes.keys(), required=True, help="Search against cazyme or substrate database"
    )
    p_search.add_argument(
        "-e",
        "--evalue",
        metavar="float/AUTO",
        default="AUTO",
        help="Evalue cutoff. Use 1e-15 for hmmsearch and 1e-102 for diamond when specifying AUTO (default: AUTO)",
    )
    p_search.add_argument("-c", "--coverage", metavar="float", type=float, default=0.35, help="Coverage cutoff")
    p_search.add_argument("-t", "--threads", metavar="int", type=int, default=1, help="Number of cpu to use")
    p_search.add_argument(
        "-b",
        "--blocksize",
        metavar="int",
        type=int,
        default=100000,
        help="Number of sequence to search per batch. Lower the blocksize to use fewer memory (not applicable on diamond)",
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


def _menu(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """Menu for this entry point."""
    parser.add_argument("-V", "--version", action="version", version=__version__)

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
    return args_parser(
        _menu, args, prog=entry_point_map[__name__], description=main.__doc__, epilog=f'Written by {__author__}'
    )


if __name__ == "__main__":
    main()
