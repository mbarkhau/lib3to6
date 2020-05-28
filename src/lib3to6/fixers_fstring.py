# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ

from . import common
from . import fixer_base as fb


class FStringToStrFormatFixer(fb.TransformerFixerBase):

    version_info = common.VersionInfo(apply_since="2.6", apply_until="3.5")

    def _formatted_value_str(
        self, fmt_val_node: ast.FormattedValue, arg_nodes: typ.List[ast.expr]
    ) -> str:
        arg_index = len(arg_nodes)
        arg_nodes.append(fmt_val_node.value)

        format_spec_node = fmt_val_node.format_spec
        if format_spec_node is None:
            format_spec = ""
        elif not isinstance(format_spec_node, ast.JoinedStr):
            raise common.FixerError("Unexpected Node Type", format_spec_node)
        else:
            format_spec = ":" + self._joined_str_str(format_spec_node, arg_nodes)

        return "{" + str(arg_index) + format_spec + "}"

    def _joined_str_str(self, joined_str_node: ast.JoinedStr, arg_nodes: typ.List[ast.expr]) -> str:
        fmt_str = ""
        for val in joined_str_node.values:
            if isinstance(val, ast.Str):
                fmt_str += val.s
            elif isinstance(val, ast.FormattedValue):
                fmt_str += self._formatted_value_str(val, arg_nodes)
            else:
                raise common.FixerError("Unexpected Node Type", val)
        return fmt_str

    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.Call:
        arg_nodes: typ.List[ast.expr] = []

        fmt_str          = self._joined_str_str(node, arg_nodes)
        format_attr_node = ast.Attribute(value=ast.Str(s=fmt_str), attr="format", ctx=ast.Load())
        return ast.Call(func=format_attr_node, args=arg_nodes, keywords=[])
