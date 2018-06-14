# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import re
import ast
import astor
import typing as typ
import typing_extensions as typext

from . import common
from . import fixers
from . import checkers


DEFAULT_SOURCE_ENCODING_DECLARATION = "# -*- coding: {} -*-"

DEFAULT_SOURCE_ENCODING = "utf-8"

SOURCE_ENCODING_RE = re.compile(rb"""
    ^
    [ \t\v]*
    \#.*?coding[:=][ \t]*
    (?P<coding>[-_.a-zA-Z0-9]+)
""", re.VERBOSE)


def parse_module_header(module_source_data: bytes) -> typ.Tuple[str, str]:
    header_lines = []
    for line in module_source_data.splitlines():
        if not line.strip() or line.strip().startswith(b"#"):
            header_lines.append(line)
        else:
            break

    shebang = False
    coding_declared = False

    coding = DEFAULT_SOURCE_ENCODING
    for i, line in enumerate(header_lines):
        if i >= 2:
            break
        if i == 0 and line.startswith(b"#!") and b"python" in line:
            shebang = True
        m = SOURCE_ENCODING_RE.match(header_lines[i])
        if m:
            coding = m.group("coding").decode("ascii").strip()
            coding_declared = True

    if not coding_declared:
        coding_declaration = DEFAULT_SOURCE_ENCODING_DECLARATION.format(coding)
        coding_declaration_data = coding_declaration.encode(coding)
        if shebang:
            header_lines.insert(1, coding_declaration_data)
        else:
            header_lines.insert(0, coding_declaration_data)

    header = (b"\n".join(header_lines) + b"\n").decode(coding)
    return coding, header


class CheckerOrFixer(typext.Protocol):

    __name__: str

    def __call__(
        self, cfg: common.BuildConfig, tree: ast.Module
    ) -> typ.Optional[ast.Module]:
        ...


T = typ.TypeVar("T", CheckerOrFixer, CheckerOrFixer)


def iter_fuzzy_selected_classes(names: str, module: object, clazz: T) -> typ.Iterable[T]:
    assert isinstance(clazz, type)
    clazz_name = clazz.__name__
    assert clazz_name.endswith("Base")
    assert getattr(module, clazz_name) is clazz
    optional_suffix = clazz_name[:-4]

    def normalize_name(name: str) -> str:
        name = name.lower().replace("_", "").replace("-", "")
        if name.endswith(optional_suffix.lower()):
            name = name[:-len(optional_suffix)]
        return name

    maybe_classes = {
        name: getattr(module, name)
        for name in dir(module)
        if not name.endswith(clazz_name)
    }
    available_classes = {
        normalize_name(attr_name): attr
        for attr_name, attr in maybe_classes.items()
        if type(attr) == type and issubclass(attr, clazz)
    }

    # Nothing explicitly selected -> all selected
    if names:
        selected_names = [
            normalize_name(name.strip())
            for name in names.split(",")
            if name.strip()
        ]
    else:
        selected_names = list(available_classes.keys())

    assert len(selected_names) > 0
    for name in selected_names:
        yield available_classes[name]()


def transpile_module(cfg: common.BuildConfig, module_source_data: bytes) -> bytes:
    coding, header = parse_module_header(module_source_data)
    module_source = module_source_data.decode(coding)
    module_tree = ast.parse(module_source)

    for checker in iter_fuzzy_selected_classes(cfg["checkers"], checkers, checkers.CheckerBase):
        checker(cfg, module_tree)

    for fixer in iter_fuzzy_selected_classes(cfg["fixers"], fixers, fixers.FixerBase):
        maybe_fixed_module = fixer(cfg, module_tree)
        if maybe_fixed_module is None:
            raise Exception(f"Error running fixer {type(fixer).__name__}")
        module_tree = maybe_fixed_module

    fixed_module_source = header + "".join(astor.to_source(module_tree))
    return fixed_module_source.encode(coding)
