# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ

from . import common
from . import fixer_base as fb


class NamedExprFixer(fb.TransformerFixerBase):

    version_info = common.VersionInfo(apply_since="2.7", apply_until="3.7")

    def _extract_and_replace_named_exprs(
        self, expr: ast.expr
    ) -> typ.Tuple[typ.List[ast.stmt], ast.expr]:
        new_assigns: typ.List[ast.stmt] = []
        if isinstance(expr, ast.NamedExpr):
            new_assigns.append(ast.Assign(targets=[expr.target], value=expr.value))
            new_expr = ast.Name(id=expr.target.id, ctx=ast.Load())
            return new_assigns, new_expr
        else:
            if isinstance(expr, ast.UnaryOp):
                new_sub_assigns, new_operand = self._extract_and_replace_named_exprs(expr.operand)
                new_assigns.extend(new_sub_assigns)
                expr.operand = new_operand
            if isinstance(expr, (ast.BinOp, ast.Compare)):
                new_sub_assigns, new_left = self._extract_and_replace_named_exprs(expr.left)
                new_assigns.extend(new_sub_assigns)
                expr.left = new_left
            if isinstance(expr, ast.BinOp):
                new_sub_assigns, new_right = self._extract_and_replace_named_exprs(expr.right)
                new_assigns.extend(new_sub_assigns)
                expr.right = new_right
            if isinstance(expr, ast.BoolOp):
                new_values = []
                for comp in expr.values:
                    new_sub_assigns, new_comp = self._extract_and_replace_named_exprs(comp)
                    new_values.append(new_comp)
                    new_assigns.extend(new_sub_assigns)
                expr.values = new_values
            if isinstance(expr, ast.Compare):
                new_comparators = []
                for comp in expr.comparators:
                    new_sub_assigns, new_comp = self._extract_and_replace_named_exprs(comp)
                    new_comparators.append(new_comp)
                    new_assigns.extend(new_sub_assigns)
                expr.comparators = new_comparators

            return new_assigns, expr

    def _update(self, nodelist: typ.List[ast.stmt], indent: int = 0) -> None:
        i = 0
        while i < len(nodelist):
            node = nodelist[i]
            if isinstance(node, (ast.If, ast.While)):
                new_assigns, new_test = self._extract_and_replace_named_exprs(node.test)
                if new_assigns and isinstance(node, ast.While):
                    loopcond_name = '__loop_condition'
                    # __loop_condition = True
                    loopcond_init_node = ast.Assign(
                        targets=[ast.Name(id=loopcond_name, ctx=ast.Store())],
                        value=ast.NameConstant(value=True, kind=None),
                    )
                    nodelist.insert(i, loopcond_init_node)

                    # while __loop_condition:
                    node.test = ast.Name(id=loopcond_name, ctx=ast.Load())

                    #   __loop_condition = test
                    loopcond_assign_node = ast.Assign(
                        targets=[ast.Name(id=loopcond_name, ctx=ast.Store())],
                        value=new_test,
                    )
                    # if __loop_condition:
                    new_ifnode = ast.If(
                        test=ast.Name(id=loopcond_name, ctx=ast.Load()),
                        body=node.body,
                        orelse=[],
                    )
                    node.body = new_assigns + [loopcond_assign_node, new_ifnode]
                    i += 1
                else:
                    node.test = new_test
                    if new_assigns:
                        nodelist[i:i] = new_assigns
                    i += 1 + len(new_assigns)
            else:
                i += 1

            for nodelist_name in ('body', 'orelse', 'handlers', 'finalbody'):
                sub_nodelist = getattr(node, nodelist_name, None)
                if sub_nodelist:
                    self._update(sub_nodelist, indent + 1)

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> ast.Module:
        self._update(tree.body)
        return tree
