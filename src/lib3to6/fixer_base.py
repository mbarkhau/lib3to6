# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# Copyright (c) 2019-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ

from . import common

# NOTE (mb 2018-06-24): Version info pulled from:
# https://docs.python.org/3/library/__future__.html


class FixerBase:

    version_info       : common.VersionInfo
    required_imports   : typ.Set[common.ImportDecl]
    module_declarations: typ.Set[str]

    def __init__(self) -> None:
        self.required_imports    = set()
        self.module_declarations = set()

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> ast.Module:
        try:
            return self.apply_fix(ctx, tree)
        except common.FixerError as ex:
            if ex.parent is None:
                ex.parent = tree
            if ex.filepath is None:
                ex.filepath = ctx.filepath
            raise

    def apply_fix(self, ctx: common.BuildContext, tree: ast.Module) -> ast.Module:
        raise NotImplementedError()


class TransformerFixerBase(FixerBase, ast.NodeTransformer):
    def apply_fix(self, ctx: common.BuildContext, tree: ast.Module) -> ast.Module:
        new_tree = self.visit(tree)
        return typ.cast(ast.Module, new_tree)
