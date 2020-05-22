#!/usr/bin/env python
# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import io
import os
import re
import sys
import typing as typ
import difflib

import click

from . import common
from . import packaging
from . import transpile

# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == '1':
    import backtrace

    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)


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


@click.command()
@click.option(
    "--target-version", default="2.7", metavar="<version>", help="Target version of python."
)
@click.option(
    "--diff", default=False, is_flag=True, help="Output diff instead of transpiled source."
)
@click.option("--in-place", default=False, is_flag=True, help="Write result back to input file.")
# @click.option(
#     "--config",
#     default="lib3to6.toml",
#     required=False,
#     metavar="<path>",
#     help="Path to config file.",
# )
@click.argument("source_files", metavar="<source_file>", nargs=-1, type=click.File(mode="r"))
def main(
    target_version: str,
    diff          : bool,
    in_place      : bool,
    # config        : str,
    source_files: typ.Sequence[io.TextIOWrapper],
) -> None:
    if not any(source_files):
        print("No files.")
        sys.exit(1)

    if target_version and not re.match(r"[0-9]+\.[0-9]+", target_version):
        print(f"Invalid argument --target-version={target_version}")
        sys.exit(1)

    cfg = packaging.eval_build_config(target_version=target_version)
    for src_file in source_files:
        source_text = src_file.read()
        try:
            fixed_source_text = transpile.transpile_module(cfg, source_text)
        except common.CheckError as err:
            err.args = (err.args[0] + f" of file {src_file.name} ",) + err.args[1:]
            raise

        if diff:
            _print_diff(source_text, fixed_source_text)
        elif in_place:
            with io.open(src_file.name, mode="w") as fh:
                fh.write(fixed_source_text)
        else:
            print(fixed_source_text)


if __name__ == '__main__':
    main()  # type: ignore
