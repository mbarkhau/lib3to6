# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2020 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
import ast
import typing as typ
import logging

from . import common
from . import checker_base as cb

# TODO (mb 2020-05-28):
#   instead of functools.singledispatch
#   from singledispatch import singledispatch
#   https://pypi.org/project/singledispatch/
#
#   instead of functools.lru_cache
#   from backports import functools_lru_cache
#   https://pypi.org/project/backports.functools-lru-cache/
#

logger = logging.getLogger(__name__)


class ModuleVersionInfo(typ.NamedTuple):

    available_since : str
    backport_module : typ.Optional[str]
    backport_package: typ.Optional[str]


MAYBE_UNUSABLE_MODULES = {
    # case 1 (simple). Always error because no backport available
    'asyncio': ModuleVersionInfo("3.4", None, None),
    'zipapp' : ModuleVersionInfo("3.5", None, None),
    # case 2 (simple). Always error because modules have different names and only
    #   backport should be used
    'csv'                : ModuleVersionInfo("3.0", "backports.csv"      , "backports.csv"),
    'selectors'          : ModuleVersionInfo("3.4", "selectors2"         , "selectors2"),
    'pathlib'            : ModuleVersionInfo("3.4", "pathlib2"           , "pathlib2"),
    "importlib.resources": ModuleVersionInfo("3.7", "importlib_resources", "importlib_resources"),
    'inspect'            : ModuleVersionInfo("3.6", "inspect2"           , "inspect2"),
    # case 3 (hard). Modules have the same name.
    # - By default, only logger.warning if these are modules are imported.
    # - If opt-in via '--install-requires' option or
    #   'install_requires' argument of 'lib3to6.fix', check that they
    #   have been explicitly whitelisted.
    'lzma'       : ModuleVersionInfo("3.3", "lzma"       , "backports.lzma"),
    'ipaddress'  : ModuleVersionInfo("3.4", "ipaddress"  , "py2-ipaddress"),
    'enum'       : ModuleVersionInfo("3.4", "enum"       , "enum34"),
    'typing'     : ModuleVersionInfo("3.5", 'typing'     , 'typing'),
    'secrets'    : ModuleVersionInfo("3.6", "secrets"    , "python2-secrets"),
    'statistics' : ModuleVersionInfo("3.4", "statistics" , "statistics"),
    'dataclasses': ModuleVersionInfo("3.7", "dataclasses", "dataclasses"),
    'contextvars': ModuleVersionInfo("3.7", "contextvars", "contextvars"),
}


def _iter_module_names(node: ast.AST) -> typ.Iterable[str]:
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name
    elif isinstance(node, ast.ImportFrom):
        mname = node.module
        if mname:
            yield mname


def _iter_maybe_unusable_modules(node: ast.AST) -> typ.Iterable[typ.Tuple[str, ModuleVersionInfo]]:
    for mname in _iter_module_names(node):
        vnfo = MAYBE_UNUSABLE_MODULES.get(mname)
        if vnfo:
            yield (mname, vnfo)


class NoUnusableImportsChecker(cb.CheckerBase):
    # NOTE (mb 2020-05-28): The (apparent double negation) naming of this does
    #   make sense; the name "OnlyUsableImportsChecker" would not be better,
    #   because this doesn't check all imports ever in existence, it only checks
    #   that unusable imports are not used at the top level.

    # NOTE (mb 2020-05-28): This checker only checks top level imports.
    #   This allows for the common idom to work without errors.
    #
    #   try:
    #       import newmodule
    #   except ImportError:
    #       improt backport_module as newmodule

    def __call__(self, ctx: common.BuildContext, tree: ast.Module) -> None:
        # NOTE (mb 2020-05-28):
        #   - Strict mode fails hard
        #   - Only raises an error if an unusable module is not used
        #   - Only warns about backported modules after
        #     opt-in to this check (by using the fix(install_requires) parameter).
        #   - Existing systems will have to update
        #     their config for this check to work and we don't want to
        #     break them.

        install_requires = ctx.cfg.install_requires

        target_version = ctx.cfg.target_version
        for node in ast.iter_child_nodes(tree):
            for mname, vnfo in _iter_maybe_unusable_modules(node):
                if target_version >= vnfo.available_since:
                    # target supports the newer name
                    continue

                bppkg = vnfo.backport_package

                # if the backport has a different name, then there is no
                # excuse not to use it -> hard error
                is_backport_name_same = mname == vnfo.backport_module

                is_whitelisted = (
                    is_backport_name_same
                    and install_requires is not None
                    and bppkg in install_requires
                )
                if is_whitelisted:
                    continue

                # From here, we either error or at least show a warning.

                # if there is no backport, then the import can obviously only
                # be using the stdlib module -> hard error
                is_backported  = vnfo.backport_package is not None
                is_strict_mode = install_requires      is not None
                is_hard_error  = not is_backported or is_strict_mode or not is_backport_name_same

                vnfo_msg = (
                    f"This module is available since Python {vnfo.available_since}, "
                    f"but you configured target_version='{target_version}'."
                )

                if is_hard_error:
                    errmsg = f"Prohibited import '{mname}'. {vnfo_msg}"
                    if bppkg:
                        errmsg += f" Use 'https://pypi.org/project/{bppkg}' instead."
                    else:
                        errmsg += " No backported for this package is known."

                    raise common.CheckError(errmsg, node)
                else:
                    lineno = common.get_node_lineno(node)
                    loc    = f"{ctx.filepath}@{lineno}"
                    logger.warning(f"{loc}: Use of import '{mname}'. {vnfo_msg}")
