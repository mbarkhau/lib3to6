# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import ast
import typing as typ
import builtins

PackageName      = str
PackageDirectory = str
PackageDir       = typ.Dict[PackageName, PackageDirectory]

InstallRequires = typ.Optional[typ.Set[str]]


ConstantNodeTypes: typ.Tuple[typ.Type[ast.Constant], ...] = (ast.Constant,)

# Deprecated since version 3.8: Class ast.Constant is now used for all
# constants. Old classes ast.Num, ast.Str, ast.Bytes, ast.NameConstant and
# ast.Ellipsis are still available, but they will be removed in future Python
# releases.

if hasattr(ast, 'Num'):
    ConstantNodeTypes += (ast.Num, ast.Str, ast.Bytes, ast.NameConstant, ast.Ellipsis)


LeafNodeTypes = ConstantNodeTypes + (
    ast.Name,
    ast.cmpop,
    ast.boolop,
    ast.operator,
    ast.unaryop,
    ast.expr_context,
)


ContainerNodes = (ast.List, ast.Set, ast.Tuple)


class BuildConfig(typ.NamedTuple):

    target_version  : str  # e.g. "2.7"
    cache_enabled   : bool
    default_mode    : str
    fixers          : str
    checkers        : str
    install_requires: InstallRequires


class BuildContext(typ.NamedTuple):

    cfg     : BuildConfig
    filepath: str


def init_build_context(
    target_version  : str             = "2.7",
    cache_enabled   : bool            = True,
    default_mode    : str             = 'enabled',
    fixers          : str             = "",
    checkers        : str             = "",
    install_requires: InstallRequires = None,
    filepath        : str             = "<filepath>",
) -> BuildContext:
    cfg = BuildConfig(
        target_version=target_version,
        cache_enabled=cache_enabled,
        default_mode=default_mode,
        fixers=fixers,
        checkers=checkers,
        install_requires=install_requires,
    )
    return BuildContext(cfg=cfg, filepath=filepath)


# Additional items:
#   'filepath': "/path/to/inputfile.py"


class InvalidPackage(Exception):
    pass


def get_node_lineno(node: ast.AST = None, parent: ast.AST = None) -> int:
    if isinstance(node, (ast.stmt, ast.expr)):
        return node.lineno
    if isinstance(parent, (ast.stmt, ast.expr)):
        return parent.lineno
    return -1


class CheckError(Exception):

    lineno: int

    def __init__(self, msg: str, node: ast.AST = None, parent: ast.AST = None) -> None:
        self.lineno = get_node_lineno(node, parent)
        super().__init__(msg)


class FixerError(Exception):

    msg   : str
    node  : ast.AST
    module: typ.Optional[ast.Module]

    def __init__(self, msg: str, node: ast.AST, module: ast.Module = None) -> None:
        self.msg    = msg
        self.node   = node
        self.module = module
        super().__init__(msg)


class VersionInfo:
    """Compatibility info for Fixer and Checker classes.

    Used as a class attribute (not an instance attribute) of a fixer or checker.
    The compatability info relates to the fixer/checker rather than the feature
    it deals with. The question that is being ansered is: "should this
    fixer/checker be exectued for this (src_version, tgt_version) pair"
    """

    # since/until is inclusive
    apply_since: typ.List[int]
    apply_until: typ.Optional[typ.List[int]]
    works_since: typ.List[int]
    works_until: typ.Optional[typ.List[int]]

    def __init__(
        self,
        apply_since: str = "1.0",
        apply_until: typ.Optional[str] = None,
        works_since: typ.Optional[str] = None,
        works_until: typ.Optional[str] = None,
    ) -> None:

        self.apply_since = [int(part) for part in apply_since.split(".")]
        if apply_until is None:
            self.apply_until = None
        else:
            self.apply_until = [int(part) for part in apply_until.split(".")]

        if works_since is None:
            # Implicitly, if it's applied since a version, it
            # also works since then.
            self.works_since = self.apply_since
        else:
            self.works_since = [int(part) for part in works_since.split(".")]

        if works_until is None:
            self.works_until = None
        else:
            self.works_until = [int(part) for part in works_until.split(".")]

    def is_required_for(self, version: str) -> bool:
        version_num = [int(part) for part in version.split(".")]
        apply_until = self.apply_until
        if apply_until and apply_until < version_num:
            return False
        return self.apply_since <= version_num

    def is_compatible_with(self, version: str) -> bool:
        version_num = [int(part) for part in version.split(".")]
        works_since = self.works_since
        works_until = self.works_until
        if works_since and version_num < works_since:
            return False
        if works_until and works_until < version_num:
            return False
        return True

    def is_applicable_to(self, source_version: str, target_version: str) -> bool:
        return self.is_required_for(target_version) and self.is_compatible_with(source_version)


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
