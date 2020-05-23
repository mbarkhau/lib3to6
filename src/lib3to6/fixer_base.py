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


class VersionInfo:

    apply_since: typ.List[int]
    apply_until: typ.List[int]
    works_since: typ.List[int]
    works_until: typ.Optional[typ.List[int]]

    def __init__(
        self, apply_since: str, apply_until: str, works_since: str = None, works_until: str = None
    ) -> None:

        self.apply_since = [int(part) for part in apply_since.split(".")]
        self.apply_until = [int(part) for part in apply_until.split(".")]
        if works_since is None:
            # Implicitly, if it's applied since a version, it
            # also works since then.
            self.works_since = self.apply_since
        else:
            self.works_since = [int(part) for part in works_since.split(".")]
        self.works_until = [int(part) for part in works_until.split(".")] if works_until else None


class FixerBase:

    version_info       : VersionInfo
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
