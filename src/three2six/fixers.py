# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import sys
import ast
import typing as typ

from . import common


class FixerBase:
    # src_versions="36+"
    # tgt_versions="27+"

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        raise NotImplementedError()


class TransformerFixerBase(FixerBase, ast.NodeTransformer):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        return self.visit(tree)


class FutureImportFixerBase(FixerBase):

    future_name: str

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        has_docstring = False
        for i, node in enumerate(tree.body):
            has_docstring = has_docstring or (
                i == 0 and
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Str)
            )
            is_already_fixed = (
                isinstance(node, ast.ImportFrom) and
                node.module == "__future__" and
                any(alias.name == self.future_name for alias in node.names)
            )
            if is_already_fixed:
                return tree

        alias_node = ast.alias(name=self.future_name, asname=None)
        import_node = ast.ImportFrom(module="__future__", level=0, names=[alias_node])
        if has_docstring:
            tree.body.insert(1, import_node)
        else:
            tree.body.insert(0, import_node)
        return tree


class AbsoluteImportFutureFixer(FutureImportFixerBase):
    future_name = "absolute_import"


class DivisionFutureFixer(FutureImportFixerBase):
    future_name = "division"


class PrintFunctionFutureFixer(FutureImportFixerBase):
    future_name = "print_function"


class UnicodeLiteralsFutureFixer(FutureImportFixerBase):
    future_name = "unicode_literals"


class RemoveFunctionDefAnnotationsFixer(FixerBase):

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            node.returns = None
            for arg in node.args.args:
                arg.annotation = None
            for arg in node.args.kwonlyargs:
                arg.annotation = None
            if node.args.vararg:
                node.args.vararg.annotation = None
            if node.args.kwarg:
                node.args.kwarg.annotation = None

        return tree


class RemoveAnnAssignFixer(TransformerFixerBase):

    def visit_AnnAssign(self, node: ast.AnnAssign) -> ast.Assign:
        name_node = node.target
        if not isinstance(name_node, ast.Name):
            raise Exception(f"Unexpected Node Type {name_node}")

        value: ast.expr
        if node.value is None:
            value = ast.NameConstant(value=None)
        else:
            value = node.value
        return ast.Assign(targets=[name_node], value=value)


class ShortToLongFormSuper(TransformerFixerBase):

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        for maybe_method in ast.walk(node):
            if not isinstance(maybe_method, ast.FunctionDef):
                continue
            method: ast.FunctionDef = maybe_method
            method_args: ast.arguments = method.args
            if len(method_args.args) == 0:
                continue
            self_arg: ast.arg = method_args.args[0]

            for maybe_super_call in ast.walk(method):
                if not isinstance(maybe_super_call, ast.Call):
                    continue
                func_node = maybe_super_call.func
                if not (isinstance(func_node, ast.Name) and func_node.id == "super"):
                    continue
                super_call = maybe_super_call
                if len(super_call.args) > 0:
                    continue

                super_call.args = [
                    ast.Name(id=node.name, ctx=ast.Load()),
                    ast.Name(id=self_arg.arg, ctx=ast.Load()),
                ]
        return node


class InlineKWOnlyArgs(TransformerFixerBase):

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        if not node.args.kwonlyargs:
            return node

        if node.args.kwarg:
            kw_name = node.args.kwarg.arg
        else:
            kw_name = "kwargs"
            node.args.kwarg = ast.arg(arg=kw_name, annotation=None)

        # NOTE (mb 2018-06-03): Only use defaults for kwargs
        #   if they are literals. Everything else would
        #   change the semantics too much and so we should
        #   raise an error.
        kwonlyargs = reversed(node.args.kwonlyargs)
        kw_defaults = reversed(node.args.kw_defaults)
        for arg, default in zip(kwonlyargs, kw_defaults):
            arg_name = arg.arg
            if default is None:
                new_node = ast.Assign(
                    targets=[ast.Name(id=arg_name, ctx=ast.Store())],
                    value=ast.Subscript(
                        value=ast.Name(id=kw_name, ctx=ast.Load()),
                        slice=ast.Index(value=ast.Str(s=arg_name)),
                        ctx=ast.Load(),
                    )
                )
            else:
                if not isinstance(default, (ast.Str, ast.Num, ast.NameConstant)):
                    raise Exception(
                        f"Keyword only arguments must be immutable. "
                        f"Found: {default} on {default.lineno}:{node.col_offset} for {arg_name}"
                    )

                new_node = ast.Assign(
                    targets=[ast.Name(
                        id=arg_name,
                        ctx=ast.Store(),
                    )],
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=kw_name, ctx=ast.Load()),
                            attr="get",
                            ctx=ast.Load(),
                        ),
                        args=[ast.Str(s=arg_name), default],
                        keywords=[],
                    )
                )

            node.body.insert(0, new_node)

        node.args.kwonlyargs = []

        return node


if sys.version_info >= (3, 6):

    class FStringFixer(TransformerFixerBase):

        def _formatted_value_str(
            self,
            fmt_val_node: ast.FormattedValue,
            arg_nodes: typ.List[ast.expr],
        ) -> str:
            arg_index = len(arg_nodes)
            arg_nodes.append(fmt_val_node.value)

            format_spec_node = fmt_val_node.format_spec
            if format_spec_node is None:
                format_spec = ""
            elif not isinstance(format_spec_node, ast.JoinedStr):
                raise Exception(f"Unexpected Node Type {format_spec_node}")
            else:
                format_spec = ":" + self._joined_str_str(format_spec_node, arg_nodes)

            return "{" + str(arg_index) + format_spec + "}"

        def _joined_str_str(
            self,
            joined_str_node: ast.JoinedStr,
            arg_nodes: typ.List[ast.expr],
        ) -> str:
            fmt_str = ""
            for val in joined_str_node.values:
                if isinstance(val, ast.Str):
                    fmt_str += val.s
                elif isinstance(val, ast.FormattedValue):
                    fmt_str += self._formatted_value_str(val, arg_nodes)
                else:
                    raise Exception(f"Unexpected Node Type {val}")
            return fmt_str

        def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.Call:
            arg_nodes: typ.List[ast.expr] = []

            fmt_str = self._joined_str_str(node, arg_nodes)
            format_attr_node = ast.Attribute(
                value=ast.Str(s=fmt_str),
                attr="format",
                ctx=ast.Load(),
            )
            return ast.Call(func=format_attr_node, args=arg_nodes, keywords=[])


class NewStyleClassesFixer(TransformerFixerBase):

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        if len(node.bases) == 0:
            node.bases.append(ast.Name(id='object', ctx=ast.Load()))
        return node


class ItertoolsBuiltinsFixer(TransformerFixerBase):

    # WARNING (mb 2018-06-09): This fix is very broad, and should
    #   only be used in combination with a sanity check that the
    #   builtin names are not being overridden.

    def __call__(self, cfg: common.BuildConfig, tree: ast.Module) -> ast.Module:
        self._fix_applied = False
        tree = self.visit(tree)
        if self._fix_applied:
            prelude_end_index = -1
            itertools_import_found = False

            for i, node in enumerate(tree.body):
                is_prelude = (
                    isinstance(node, ast.Expr) and isinstance(node.value, ast.Str) or
                    isinstance(node, ast.ImportFrom) and node.module == "__future__"
                )
                if prelude_end_index < 0 and not is_prelude:
                    prelude_end_index = i

                is_itertools_import = (
                    isinstance(node, ast.Import) and
                    any(alias.name == "itertools" for alias in node.names)
                )
                if is_itertools_import:
                    itertools_import_found = True
                    break

            if not itertools_import_found:
                tree.body.insert(
                    prelude_end_index,
                    ast.Import(names=[ast.alias(name="itertools", asname=None)]),
                )
        return tree

    def visit_Name(self, node: ast.Name) -> typ.Union[ast.Name, ast.Attribute]:
        if node.id not in ("map", "zip", "filter"):
            return node

        self._fix_applied = True

        return ast.Attribute(
            value=ast.Name(id="itertools", ctx=ast.Load()),
            attr="i" + node.id,
            ctx=ast.Load(),
        )
