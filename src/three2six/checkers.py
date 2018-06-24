# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import ast

from . import common


class VersionInfo:

    prohibited_until: str

    def __init__(self, prohibited_until: str) -> None:
        self.prohibited_until = prohibited_until


class CheckerBase:

    version_info: VersionInfo

    def is_prohibited_for(self, version):
        return self.version_info.prohibited_until >= version

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        raise NotImplementedError()


class VisitorCheckerBase(CheckerBase, ast.NodeVisitor):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        return self.visit(tree)


class NoOverriddenBuiltinsChecker(CheckerBase):

    version_info = VersionInfo(prohibited_until="3.4")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                name_in_scope = node.name
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name_in_scope = node.id
            elif isinstance(node, ast.alias):
                name_in_scope = node.name if node.asname is None else node.asname
            elif isinstance(node, ast.arg):
                name_in_scope = node.arg
            else:
                continue

            if name_in_scope and name_in_scope in common.BUILTIN_NAMES:
                # TODO (mb 2018-06-14): line numbers and file path
                raise common.CheckError(f"Prohibited override of builtin '{name_in_scope}'")


MODULE_BACKPORTS = {
    "lzma"                : ((3, 3), "backports.lzma"),
    "pathlib"             : ((3, 4), "pathlib2"),
    "statistics"          : ((3, 4), "statistics"),
    "ipaddress"           : ((3, 4), "py2-ipaddress"),
    "asyncio"             : ((3, 4), None),
    "selectors"           : ((3, 4), None),
    "enum"                : ((3, 4), "enum34"),
    "zipapp"              : ((3, 5), None),
    "typing"              : ((3, 5), "typing"),
    "contextvars"         : ((3, 7), "contextvars"),
    "dataclasses"         : ((3, 7), "dataclasses"),
    "importlib.resources" : ((3, 7), "importlib_resources"),
}


class NoThreeOnlyImports(CheckerBase):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        pass


class NoOpenWithEncodingChecker(CheckerBase):

    version_info = VersionInfo(prohibited_until="2.7")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # print(node, dir(node))
                pass


class NoAsyncAwait(CheckerBase):

    version_info = VersionInfo(prohibited_until="3.4")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        pass
