# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import re
import ast
import astor
import typing as typ

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


def transpile_module(cfg: common.BuildConfig, module_source_data: bytes) -> bytes:
    coding, header = parse_module_header(module_source_data)
    module_source = module_source_data.decode(coding)
    module_tree = ast.parse(module_source)

    checker_names = [
        name.strip()
        for name in cfg["checkers"].split(",")
        if name.strip()
    ]

    if not any(checker_names):
        maybe_classes = {
            name: getattr(checkers, name)
            for name in dir(checkers)
            if not name.endswith("CheckerBase")
        }
        checker_names = [
            name
            for name, attr in maybe_classes.items()
            if type(attr) == type and issubclass(attr, checkers.CheckerBase)
        ]

    for checker_name in checker_names:
        checker_class = getattr(checkers, checker_name)
        checker_class()(cfg, module_tree)

    fixer_names = [
        name.strip()
        for name in cfg["fixers"].split(",")
        if name.strip()
    ]

    if not any(fixer_names):
        maybe_classes = {
            name: getattr(fixers, name)
            for name in dir(fixers)
            if not name.endswith("FixerBase")
        }
        fixer_names = [
            name
            for name, attr in maybe_classes.items()
            if type(attr) == type and issubclass(attr, fixers.FixerBase)
        ]

    for fixer_name in fixer_names:
        fixer_class = getattr(fixers, fixer_name)
        module_tree = fixer_class()(cfg, module_tree)

    fixed_module_source = header + "".join(astor.to_source(module_tree))
    return fixed_module_source.encode(coding)
