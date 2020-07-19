# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import ast

from . import common


class CheckerBase:

    # no info -> always apply
    version_info: common.VersionInfo = common.VersionInfo()

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        raise NotImplementedError()
