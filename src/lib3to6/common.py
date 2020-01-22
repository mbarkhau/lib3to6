# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ
import builtins

PackageDir  = typ.Dict[str, str]
BuildConfig = typ.Dict[str, str]


class InvalidPackage(Exception):
    pass


class CheckError(Exception):
    def __init__(self, msg: str, node: ast.AST = None, parent: ast.AST = None) -> None:
        node_lineno   = node.lineno if isinstance(node, (ast.stmt, ast.expr)) else 0
        parent_lineno = parent.lineno if isinstance(parent, (ast.stmt, ast.expr)) else 0
        lineno        = node_lineno or parent_lineno

        if lineno:
            msg += f" on line {lineno}"
        super().__init__(msg)


class FixerError(Exception):

    msg   : str
    node  : ast.AST
    module: typ.Optional[ast.Module]

    def __init__(self, msg: str, node: ast.AST, module: ast.Module = None) -> None:
        self.msg    = msg
        self.node   = node
        self.module = module


# NOTE (mb 2018-06-29): None of the fixers use asname. If a
#   module already has an import using asname, it won't be
#   detected as already imported, and another import (without the
#   asname) will be added to the module.
class ImportDecl(typ.NamedTuple):
    module_name    : str
    import_name    : typ.Optional[str]
    py2_module_name: typ.Optional[str]


# NOTE (mb 2018-06-24): This also includes builtins from py27
#   because a fixer might add a reference to it when building for
#   py27, in which case, we don't want other code to have
#   replaced it with something other than the old builtin.
#   For example replace range -> xrange, so it would be nice if
#   xrange isn't a string or something.
BUILTIN_NAMES = {
    "ArithmeticError",
    "AssertionError",
    "AttributeError",
    "BaseException",
    "BlockingIOError",
    "BrokenPipeError",
    "BufferError",
    "BytesWarning",
    "ChildProcessError",
    "ConnectionAbortedError",
    "ConnectionError",
    "ConnectionRefusedError",
    "ConnectionResetError",
    "DeprecationWarning",
    "EOFError",
    "Ellipsis",
    "EnvironmentError",
    "Exception",
    "False",
    "FileExistsError",
    "FileNotFoundError",
    "FloatingPointError",
    "FutureWarning",
    "GeneratorExit",
    "IOError",
    "ImportError",
    "ImportWarning",
    "IndentationError",
    "IndexError",
    "InterruptedError",
    "IsADirectoryError",
    "KeyError",
    "KeyboardInterrupt",
    "LookupError",
    "MemoryError",
    "ModuleNotFoundError",
    "NameError",
    "None",
    "NotADirectoryError",
    "NotImplemented",
    "NotImplementedError",
    "OSError",
    "OverflowError",
    "PendingDeprecationWarning",
    "PermissionError",
    "ProcessLookupError",
    "RecursionError",
    "ReferenceError",
    "ResourceWarning",
    "RuntimeError",
    "RuntimeWarning",
    "StopAsyncIteration",
    "StopIteration",
    "SyntaxError",
    "SyntaxWarning",
    "SystemError",
    "SystemExit",
    "TabError",
    "TimeoutError",
    "True",
    "TypeError",
    "UnboundLocalError",
    "UnicodeDecodeError",
    "UnicodeEncodeError",
    "UnicodeError",
    "UnicodeTranslateError",
    "UnicodeWarning",
    "UserWarning",
    "ValueError",
    "Warning",
    "ZeroDivisionError",
    "abs",
    "all",
    "any",
    "ascii",
    "bin",
    "bool",
    "bytearray",
    "bytes",
    "callable",
    "chr",
    "classmethod",
    "compile",
    "complex",
    "copyright",
    "credits",
    "delattr",
    "dict",
    "dir",
    "display",
    "divmod",
    "enumerate",
    "eval",
    "exec",
    "filter",
    "float",
    "format",
    "frozenset",
    "get_ipython",
    "getattr",
    "globals",
    "hasattr",
    "hash",
    "help",
    "hex",
    "id",
    "input",
    "int",
    "isinstance",
    "issubclass",
    "iter",
    "len",
    "license",
    "list",
    "locals",
    "map",
    "max",
    "memoryview",
    "min",
    "next",
    "object",
    "oct",
    "open",
    "ord",
    "pow",
    "print",
    "property",
    "range",
    "repr",
    "reversed",
    "round",
    "set",
    "setattr",
    "slice",
    "sorted",
    "staticmethod",
    "str",
    "sum",
    "super",
    "tuple",
    "type",
    "vars",
    "zip",
    "StandardError",
    "apply",
    "basestring",
    "buffer",
    "cmp",
    "coerce",
    "dreload",
    "execfile",
    "file",
    "intern",
    "long",
    "raw_input",
    "reduce",
    "reload",
    "unichr",
    "unicode",
    "xrange",
}

# In case somebody is working on py4k or something

BUILTIN_NAMES.update([name for name in dir(builtins) if not name.startswith("__")])
