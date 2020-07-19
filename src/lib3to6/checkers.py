# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ

from . import utils
from . import common
from . import checker_base as cb
from .checkers_backports import NoUnusableImportsChecker


class NoStarImports(cb.CheckerBase):
    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue

            for alias in node.names:
                if alias.name == "*":
                    raise common.CheckError(f"Prohibited from {node.module} import *.", node)


def _iter_scope_names(tree: ast.Module) -> typ.Iterable[typ.Tuple[str, ast.AST]]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            yield node.name, node
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            yield node.id, node
        elif isinstance(node, (ast.ImportFrom, ast.Import)):
            for alias in node.names:
                name = alias.name if alias.asname is None else alias.asname
                yield name, node
        elif isinstance(node, ast.arg):
            yield node.arg, node


class NoOverriddenFixerImportsChecker(cb.CheckerBase):
    """Don't override names that fixers may reference."""

    prohibited_import_overrides = {"itertools", "six", "builtins"}

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        for name_in_scope, node in _iter_scope_names(tree):
            is_fixer_import = (
                isinstance(node, ast.Import)
                and len(node.names) == 1
                and node.names[0].asname is None
                and node.names[0].name == name_in_scope
            )
            if is_fixer_import:
                continue

            if name_in_scope in self.prohibited_import_overrides:
                msg = f"Prohibited override of import '{name_in_scope}'"
                raise common.CheckError(msg, node)


class NoOverriddenBuiltinsChecker(cb.CheckerBase):
    """Don't override names that fixers may reference."""

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        for name_in_scope, node in _iter_scope_names(tree):
            if name_in_scope in common.BUILTIN_NAMES:
                msg = f"Prohibited override of builtin '{name_in_scope}'"
                raise common.CheckError(msg, node)


PROHIBITED_OPEN_ARGUMENTS = {"encoding", "errors", "newline", "closefd", "opener"}


class NoOpenWithEncodingChecker(cb.CheckerBase):

    version_info = common.VersionInfo(apply_until="2.7")

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
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
                if not isinstance(mode_node, ast.Str):
                    msg = (
                        "Prohibited value for argument 'mode' of builtin.open. "
                        + f"Expected ast.Str node, got: {mode_node}"
                    )
                    raise common.CheckError(msg, node)

                mode = mode_node.s

            if len(node.args) > 3:
                raise common.CheckError("Prohibited positional arguments to builtin.open", node)

            for keyword in node.keywords:
                if keyword.arg in PROHIBITED_OPEN_ARGUMENTS:
                    msg = f"Prohibited keyword argument '{keyword.arg}' to builtin.open."
                    raise common.CheckError(msg, node)
                if keyword.arg != 'mode':
                    continue

                mode_node = keyword.value
                if not isinstance(mode_node, ast.Str):
                    msg = (
                        "Prohibited value for argument 'mode' of builtin.open. "
                        + f"Expected ast.Str node, got: {mode_node}"
                    )
                    raise common.CheckError(msg, node)

                mode = mode_node.s

            if "b" not in mode:
                msg = (
                    f"Prohibited value '{mode}' for argument 'mode' of builtin.open. "
                    + "Only binary modes are allowed, use io.open as an alternative."
                )
                raise common.CheckError(msg, node)


class NoAsyncAwait(cb.CheckerBase):

    version_info = common.VersionInfo(apply_until="3.4", works_since="3.5")

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        async_await_node_types = (ast.AsyncFor, ast.AsyncWith, ast.AsyncFunctionDef, ast.Await)
        for node in ast.walk(tree):
            if not isinstance(node, async_await_node_types):
                continue

            if isinstance(node, ast.AsyncFor):
                keywords = "async for"
            elif isinstance(node, ast.AsyncWith):
                keywords = "async with"
            elif isinstance(node, ast.AsyncFunctionDef):
                keywords = "async def"
            elif isinstance(node, ast.Await):
                keywords = "await"
            else:
                # probably dead codepath
                keywords = "async/await"

            msg = (
                f"Prohibited use of '{keywords}', which is not supported "
                f"for target_version='{ctx.cfg.target_version}'."
            )
            raise common.CheckError(msg, node)


class NoYieldFromChecker(cb.CheckerBase):

    version_info = common.VersionInfo(apply_until="3.2", works_since="3.3")

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:

        for node in ast.walk(tree):
            if isinstance(node, ast.YieldFrom):
                msg = (
                    "Prohibited use of 'yield from', which is not supported "
                    f"for your target_version={ctx.cfg.target_version}"
                )
                raise common.CheckError(msg, node)


class NoMatMultOpChecker(cb.CheckerBase):

    version_info = common.VersionInfo(apply_until="3.4", works_since="3.5")

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        if not hasattr(ast, 'MatMult'):
            return

        for node in ast.walk(tree):
            if not isinstance(node, ast.BinOp):
                continue

            if not isinstance(node.op, ast.MatMult):
                continue

            msg = "Prohibited use of matrix multiplication '@' operator."
            raise common.CheckError(msg, node)


def _raise_if_complex_named_tuple(node: ast.ClassDef) -> None:
    for subnode in node.body:
        if isinstance(subnode, ast.Expr) and isinstance(subnode.value, ast.Str):
            # docstring is fine
            continue

        if isinstance(subnode, ast.AnnAssign):
            if subnode.value:
                tgt = subnode.target
                assert isinstance(tgt, ast.Name)
                msg = (
                    "Prohibited use of default value "
                    + f"for field '{tgt.id}' of class '{node.name}'"
                )
                raise common.CheckError(msg, subnode, node)
        elif isinstance(subnode, ast.FunctionDef):
            msg = "Prohibited definition of method " + f"'{subnode.name}' for class '{node.name}'"
            raise common.CheckError(msg, subnode, node)
        else:
            msg = f"Unexpected subnode defined for class {node.name}: {subnode}"
            raise common.CheckError(msg, subnode, node)


class NoComplexNamedTuple(cb.CheckerBase):

    version_info = common.VersionInfo(apply_until="3.4", works_since="3.5")

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        _typing_module_name   : typ.Optional[str] = None
        _namedtuple_class_name: str = "NamedTuple"

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'typing':
                        _typing_module_name = alias.name if alias.asname is None else alias.asname
                continue

            if isinstance(node, ast.ImportFrom) and node.module == 'typing':
                for alias in node.names:
                    if alias.name == 'NamedTuple':
                        _namedtuple_class_name = (
                            alias.name if alias.asname is None else alias.asname
                        )
                continue

            is_namedtuple_class = (
                isinstance(node, ast.ClassDef)
                and (_typing_module_name or _namedtuple_class_name)
                and utils.has_base_class(node, _typing_module_name, _namedtuple_class_name)
            )
            if is_namedtuple_class:
                assert isinstance(node, ast.ClassDef), "mypy is stupid sometimes"
                _raise_if_complex_named_tuple(node)


# NOTE (mb 2018-06-24): I don't know how this could be done reliably.
#   The main issue is that there are objects other than dict, which
#   have methods named items,keys,values which this check wouldn't
#   apply to.
# class NoAssignedDictViews(cb.CheckerBase):
#
#     check_before = "3.0"
#
#     def __call__(self, ctx: common.BuildContext, tree: ast.Module):
#         pass

__all__ = [
    'NoStarImports',
    'NoOverriddenFixerImportsChecker',
    'NoOverriddenBuiltinsChecker',
    'NoOpenWithEncodingChecker',
    'NoAsyncAwait',
    'NoComplexNamedTuple',
    'NoUnusableImportsChecker',
    'NoYieldFromChecker',
    'NoMatMultOpChecker',
]
