# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
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

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        raise NotImplementedError()

    @classmethod
    def is_required_for(cls, version: str) -> bool:
        version_num = [int(part) for part in version.split(".")]
        nfo         = cls.version_info
        return nfo.apply_since <= version_num <= nfo.apply_until

    @classmethod
    def is_compatible_with(cls, version: str) -> bool:
        version_num = [int(part) for part in version.split(".")]
        nfo         = cls.version_info
        return nfo.works_since <= version_num and (
            nfo.works_until is None or version_num <= nfo.works_until
        )

    @classmethod
    def is_applicable_to(cls, src_version: str, tgt_version: str) -> bool:
        return cls.is_compatible_with(src_version) and cls.is_required_for(tgt_version)


class TransformerFixerBase(FixerBase, ast.NodeTransformer):
    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        try:
            return self.visit(tree)
        except common.FixerError as ex:
            if ex.module is None:
                ex.module = tree
            raise
