"""Custom Argparse settings."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
import traceback
from typing import Callable

from . import AVAIL_CPUS, logger


class CustomHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter for argparse to enhance text wrapping and default value display.

    This formatter adjusts the text wrapping for better readability and ensures that the default value of an argument is displayed
    in the help message if not already present.
    """

    def _fill_text(self, text, width, indent):
        """Format the class/function docstring with appropriate wrapping."""
        text = [self._whitespace_matcher.sub(" ", paragraph.strip()) for paragraph in text.split("\n\n") if paragraph.strip()]
        return "\n\n".join([textwrap.fill(line, width) for line in text])

    def _split_lines(self, text, width):
        """Enable multi-line display in argument help message."""
        text = [self._whitespace_matcher.sub(" ", line.strip()) for line in text.split("\n") if line.strip()]
        return [wrapped_line for line in text for wrapped_line in textwrap.wrap(line, width)]

    def _get_help_string(self, action):
        """Allow additional message after default parameter displayed."""
        help = action.help
        pattern = r"\(default: .+\)"
        if re.search(pattern, action.help) is None:
            if action.default not in [argparse.SUPPRESS, None, False]:
                defaulting_nargs = [argparse.OPTIONAL, argparse.ZERO_OR_MORE]
                if action.option_strings or action.nargs in defaulting_nargs:
                    help += " (default: %(default)s)"
        return help


def args_parser(
    parser_func: Callable[[argparse.ArgumentParser], argparse.ArgumentParser],
    args: list[str] | None,
    *,
    prog: str | None = None,
    description: str | None = None,
    epilog: str | None = None,
) -> int:
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
            if args.threads > AVAIL_CPUS:
                args.threads = AVAIL_CPUS

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
        logger.debug("%s", traceback.format_exc())
        return 1

    except SystemExit as err:
        if err.code != 0:
            logger.error(err)
            logger.debug("%s", traceback.format_exc())
            return err.code

    return 0
