# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import ast
import typing as typ

from . import common
from . import utils


class VersionInfo:

    prohibited_until: typ.Optional[str]

    def __init__(self, prohibited_until: str = None) -> None:
        self.prohibited_until = prohibited_until


class CheckerBase:

    version_info: VersionInfo

    def is_prohibited_for(self, version: str) -> bool:
        return (
            self.version_info.prohibited_until is None or
            self.version_info.prohibited_until >= version
        )

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        raise NotImplementedError()


class NoStarImports(CheckerBase):

    version_info = VersionInfo()

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue

            for alias in node.names:
                if alias.name == "*":
                    raise common.CheckError(f"Prohibited from {node.module} import *.")


class NoOverriddenStdlibImportsChecker(CheckerBase):
    """Don't override names that fixers may reference."""

    version_info = VersionInfo()
    prohibited_import_overrides = {"itertools", "six", "builtins"}

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                name_in_scope = node.name
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                name_in_scope = node.id
            elif isinstance(node, ast.alias) and node.asname:
                name_in_scope = node.asname
            elif isinstance(node, ast.arg):
                name_in_scope = node.arg
            else:
                continue

            if name_in_scope and name_in_scope in self.prohibited_import_overrides:
                raise common.CheckError(f"Prohibited override of import '{name_in_scope}'")


class NoOverriddenBuiltinsChecker(CheckerBase):
    """Don't override names that fixers may reference."""

    version_info = VersionInfo()

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

    version_info = VersionInfo(prohibited_until="2.7")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        pass


PROHIBITED_OPEN_ARGUMENTS = {"encoding", "errors", "newline", "closefd", "opener"}


class NoOpenWithEncodingChecker(CheckerBase):

    version_info = VersionInfo(prohibited_until="2.7")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue

            func_node = node.func
            if not isinstance(func_node, ast.Name):
                continue
            if func_node.id != "open" or not isinstance(func_node.ctx, ast.Load):
                continue

            mode = "r"
            if len(node.args) >= 2:
                mode_node = node.args[1]
                if isinstance(mode_node, ast.Str):
                    mode = mode_node.s
                else:
                    raise common.CheckError(
                        "Prohibited value for argument 'mode' of builtin.open. " +
                        f"Expected ast.Str node, got: {mode_node}"
                    )

            if len(node.args) > 3:
                raise common.CheckError(
                    f"Prohibited positional arguments to builtin.open"
                )

            for kw in node.keywords:
                if kw.arg in PROHIBITED_OPEN_ARGUMENTS:
                    raise common.CheckError(
                        f"Prohibited keyword argument '{kw.arg}' to builtin.open."
                    )
                if kw.arg != "mode":
                    continue

                mode_node = kw.value
                if isinstance(mode_node, ast.Str):
                    mode = mode_node.s
                else:
                    raise common.CheckError(
                        "Prohibited value for argument 'mode' of builtin.open. " +
                        f"Expected ast.Str node, got: {mode_node}"
                    )

            if "b" not in mode:
                raise common.CheckError(
                    f"Prohibited value '{mode}' for argument 'mode' of builtin.open. " +
                    "Only binary modes are allowed, use io.open as an alternative."
                )


ASYNC_AWAIT_NODE_TYPES = (
    ast.AsyncFor,
    ast.AsyncWith,
    ast.AsyncFunctionDef,
    ast.Await,
)


class NoAsyncAwait(CheckerBase):

    version_info = VersionInfo(prohibited_until="3.4")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        for node in ast.walk(tree):
            if isinstance(node, ASYNC_AWAIT_NODE_TYPES):
                raise common.CheckError("Prohibited use of async/await")


class NoComplexNamedTuple(CheckerBase):

    version_info = VersionInfo(prohibited_until="3.4")

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
        _typing_module_name: typ.Optional[str] = None
        _namedtuple_class_name: str = "NamedTuple"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "typing":
                        if alias.asname is None:
                            _typing_module_name = alias.name
                        else:
                            _typing_module_name = alias.asname

            if isinstance(node, ast.ImportFrom) and node.module == "typing":
                for alias in node.names:
                    if alias.name == "NamedTuple":
                        if alias.asname is None:
                            _namedtuple_class_name = alias.name
                        else:
                            _namedtuple_class_name = alias.asname

            if not isinstance(node, ast.ClassDef):
                continue

            if not (_typing_module_name or _namedtuple_class_name):
                continue

            if not utils.has_base_class(node, _typing_module_name, _namedtuple_class_name):
                continue

            for subnode in node.body:
                if isinstance(subnode, ast.AnnAssign):
                    if subnode.value:
                        tgt = subnode.target
                        assert isinstance(tgt, ast.Name)
                        raise common.CheckError(
                            f"Prohibited use of default value " +
                            f"for field '{tgt.id}' of class '{node.name}'"
                        )
                elif isinstance(subnode, ast.FunctionDef):
                    raise common.CheckError(
                        f"Prohibited definition of method " +
                        f"'{subnode.name}' for class '{node.name}'"
                    )
                else:
                    raise common.CheckError(
                        f"Unexpected subnode defined for class {node.name}: {subnode}"
                    )


# NOTE (mb 2018-06-24): I don't know how this could be done reliably.
#   The main issue is that there are objects other than dict, which
#   have methods named items,keys,values which this check wouldn't
#   apply to.
# class NoAssignedDictViews(CheckerBase):
#
#     check_before = "3.0"
#
#     def __call__(self, cfg: common.BuildConfig, tree: ast.Module):
#         pass
