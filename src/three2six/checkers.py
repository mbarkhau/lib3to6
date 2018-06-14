# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import ast

import builtins

from . import common


class CheckerBase:

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        raise NotImplementedError()


class VisitorCheckerBase(CheckerBase, ast.NodeVisitor):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        return self.visit(tree)


BUILTIN_NAMES = {
    name
    for name in dir(builtins)
    if name.lower() == name and not name.startswith("__")
}


class NoOverriddenBuiltinsChecker(CheckerBase):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                name_in_scope = node.name
            elif isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    name_in_scope = node.id
            elif isinstance(node, ast.alias):
                name_in_scope = node.name if node.asname is None else node.asname
            elif isinstance(node, ast.arg):
                name_in_scope = node.arg
            else:
                continue

            if name_in_scope and name_in_scope in BUILTIN_NAMES:
                # TODO (mb 2018-06-14): line numbers and file path
                raise common.CheckError(f"Prohibited override of builtin '{name_in_scope}'")
