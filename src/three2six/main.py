#!/usr/bin/env python
# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import sys
import typing as typ
import pathlib2 as pl

from . import packaging
from . import transpile


def main(argv: typ.List[str]=sys.argv[1:]):
    # TODO (mb 2018-06-07): option --in-place
    cfg = packaging.eval_build_config()
    for arg in argv:
        path = pl.Path(arg)
        if not (path.exists() and path.suffix == ".py"):
            continue
        with path.open(mode="rb") as fh:
            source_data = fh.read()
            fixed_source_data = transpile.transpile_module(cfg, source_data)
            print(fixed_source_data.decode("utf-8"))


if __name__ == '__main__':
    sys.exit(main())
