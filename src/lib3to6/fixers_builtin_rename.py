# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast

from . import common
from . import fixer_base as fb


class BuiltinsRenameFixerBase(fb.FixerBase):

    new_name: str
    old_name: str

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> ast.Module:
        for node in ast.walk(tree):
            is_access_to_builtin = (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and node.id == self.new_name
            )

            if is_access_to_builtin:
                self.required_imports.add(common.ImportDecl("builtins", None, "__builtin__"))
                builtin_renmae_decl_str = f"""
                {self.new_name} = getattr(builtins, '{self.old_name}', {self.new_name})
                """
                self.module_declarations.add(builtin_renmae_decl_str.strip())

        return tree


class XrangeToRangeFixer(BuiltinsRenameFixerBase):

    version_info = common.VersionInfo(apply_until="2.7")

    new_name = "range"
    old_name = "xrange"


class UnicodeToStrFixer(BuiltinsRenameFixerBase):

    version_info = common.VersionInfo(apply_until="2.7")

    new_name = "str"
    old_name = "unicode"


class UnichrToChrFixer(BuiltinsRenameFixerBase):

    version_info = common.VersionInfo(apply_until="2.7")

    new_name = "chr"
    old_name = "unichr"


class RawInputToInputFixer(BuiltinsRenameFixerBase):

    version_info = common.VersionInfo(apply_until="2.7")

    new_name = "input"
    old_name = "raw_input"
