# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import ast

from . import common


class CheckerBase:

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        raise NotImplementedError()


class VisitorCheckerBase(CheckerBase, ast.NodeVisitor):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        return self.visit(tree)


class NoOverrideBuiltinsCheck(CheckerBase):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        pass
