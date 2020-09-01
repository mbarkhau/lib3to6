#!/usr/bin/env python
# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import io
import re
import sys
import typing as typ
import difflib
import logging

import click

from . import common
from . import packaging
from . import transpile

try:
    import pretty_traceback

    pretty_traceback.install(envvar='ENABLE_PRETTY_TRACEBACK')
except ImportError:
    pass  # no need to fail because of missing dev dependency


logger = logging.getLogger("lib3to6")


def _configure_logging(verbose: int = 0) -> None:
    if verbose >= 2:
        log_format = "%(asctime)s.%(msecs)03d %(levelname)-7s %(name)-17s - %(message)s"
        log_level  = logging.DEBUG
    elif verbose == 1:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO
    else:
        log_format = "%(levelname)-7s - %(message)s"
        log_level  = logging.INFO

    logging.basicConfig(level=log_level, format=log_format, datefmt="%Y-%m-%dT%H:%M:%S")
    logger.debug("Logging configured.")


click.disable_unicode_literals_warning = True


def _print_diff(source_text: str, fixed_source_text: str) -> None:
    differ = difflib.Differ()

    source_lines       = source_text.splitlines()
    fixed_source_lines = fixed_source_text.splitlines()
    diff_lines         = differ.compare(source_lines, fixed_source_lines)
    if not sys.stdout.isatty():
        click.echo("\n".join(diff_lines))
        return

    for line in diff_lines:
        if line.startswith("+ "):
            click.echo("\u001b[32m" + line + "\u001b[0m")
        elif line.startswith("- "):
            click.echo("\u001b[31m" + line + "\u001b[0m")
        elif line.startswith("? "):
            click.echo("\u001b[36m" + line + "\u001b[0m")
        else:
            click.echo(line)
    print()


__INSTALL_REQUIRES_HELP = """
install_requires package dependencies (space separated).
Functions as a whitelist for backported modules.
"""

__DEFAULT_MODE_HELP = """
[enabled/disabled] Default transpile mode.
To transpile some files but not others.
"""


@click.command()
@click.option(
    '-v',
    '--verbose',
    count=True,
    help="Control log level. -vv for debug level.",
)
@click.option(
    "--target-version",
    default="2.7",
    metavar="<version>",
    help="Target version of python.",
)
@click.option(
    "--diff",
    default=False,
    is_flag=True,
    help="Output diff instead of transpiled source.",
)
@click.option(
    "--in-place",
    default=False,
    is_flag=True,
    help="Write result back to input file.",
)
@click.option(
    "--install-requires",
    default=None,
    metavar="<packages>",
    help=__INSTALL_REQUIRES_HELP.strip(),
)
@click.option(
    "--default-mode",
    default='enabled',
    metavar="<mode>",
    help=__DEFAULT_MODE_HELP.strip(),
)
@click.argument(
    "source_files",
    metavar="<source_file>",
    nargs=-1,
    type=click.File(mode="r"),
)
def main(
    target_version  : str,
    diff            : bool,
    in_place        : bool,
    install_requires: typ.Optional[str],
    source_files    : typ.Sequence[io.TextIOWrapper],
    default_mode    : str = 'enabled',
    verbose         : int = 0,
) -> None:
    _configure_logging(verbose)

    has_opt_error = False

    if target_version and not re.match(r"[0-9]+\.[0-9]+", target_version):
        print(f"Invalid argument --target-version={target_version}")
        has_opt_error = True

    if default_mode not in ('enabled', 'disabled'):
        print(f"Invalid argument --default-mode={default_mode}")
        print("    Must be either 'enabled' or 'disabled'")
        has_opt_error = True

    if not any(source_files):
        print("No files.")
        has_opt_error = True

    if has_opt_error:
        sys.exit(1)

    cfg = packaging.eval_build_config(
        target_version=target_version,
        install_requires=install_requires,
        default_mode=default_mode,
    )
    for src_file in source_files:
        ctx         = common.BuildContext(cfg, src_file.name)
        source_text = src_file.read()
        try:
            fixed_source_text = transpile.transpile_module(ctx, source_text)
        except common.CheckError as err:
            loc = src_file.name
            if err.lineno >= 0:
                loc += "@" + str(err.lineno)

            err.args = (loc + " - " + err.args[0],) + err.args[1:]
            raise

        if diff:
            _print_diff(source_text, fixed_source_text)
        elif in_place:
            with io.open(src_file.name, mode="w") as fobj:
                fobj.write(fixed_source_text)
        else:
            print(fixed_source_text)


if __name__ == '__main__':
    # NOTE (mb 2020-07-18): click supplies the parameters
    # pylint:disable=no-value-for-parameter
    main()  # type: ignore
