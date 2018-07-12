# This file is part of the three2six project
# https://github.com/mbarkhau/three2six
# (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
#
# SPDX-License-Identifier:    MIT

import re
import ast
import sys
import astor
import typing as typ

from . import common
from . import fixers
from . import checkers


DEFAULT_SOURCE_ENCODING_DECLARATION = "# -*- coding: {} -*-"

DEFAULT_SOURCE_ENCODING = "utf-8"

# https://www.python.org/dev/peps/pep-0263/
SOURCE_ENCODING_RE = re.compile(r"""
    ^
    [ \t\v]*
    \#.*?coding[:=][ \t]*
    (?P<coding>[-_.a-zA-Z0-9]+)
""", re.VERBOSE)


def parse_module_header(module_source: typ.Union[bytes, str]) -> typ.Tuple[str, str]:
    shebang = False
    coding_declared = False
    coding = DEFAULT_SOURCE_ENCODING

    header_lines: typ.List[str] = []

    # NOTE (mb 2018-06-23): Sneaky replacement of coding is done during
    #   consumption of the generator.
    source_lines: typ.Iterable[str] = (
        line.decode(coding, errors="ignore") if isinstance(line, bytes) else line
        for line in module_source.splitlines()
    )

    for i, line in enumerate(source_lines):
        if i < 2:
            if i == 0 and line.startswith("#!") and "python" in line:
                shebang = True
            else:
                m = SOURCE_ENCODING_RE.match(line)
                if m:
                    coding = m.group("coding").strip()
                    coding_declared = True

        if not line.rstrip() or line.rstrip().startswith("#"):
            header_lines.append(line)
        else:
            break

    if not coding_declared:
        coding_declaration = DEFAULT_SOURCE_ENCODING_DECLARATION.format(coding)
        if shebang:
            header_lines.insert(1, coding_declaration)
        else:
            header_lines.insert(0, coding_declaration)

    header = "\n".join(header_lines) + "\n"
    return coding, header


CheckerType = typ.Type[checkers.CheckerBase]

FixerType = typ.Type[fixers.FixerBase]

CheckerOrFixer = typ.Union[CheckerType, FixerType]


def normalize_name(name: str) -> str:
    name = name.strip().lower().replace("_", "").replace("-", "")
    if name.endswith("fixer"):
        name = name[:-len("fixer")]
    if name.endswith("checker"):
        name = name[:-len("checker")]
    return name


def get_available_classes(
    module: object, clazz: CheckerOrFixer
) -> typ.Dict[str, CheckerOrFixer]:

    assert isinstance(clazz, type)
    clazz_name = clazz.__name__
    assert clazz_name.endswith("Base")
    assert getattr(module, clazz_name) is clazz

    maybe_classes = {
        name: getattr(module, name)
        for name in dir(module)
        if not name.endswith(clazz_name)
    }

    return {
        normalize_name(attr_name): attr
        for attr_name, attr in maybe_classes.items()
        if type(attr) == type and issubclass(attr, clazz)
    }


FuzzyNames = typ.Union[str, typ.List[str]]


def get_selected_names(names: FuzzyNames, available_names: typ.Set[str]) -> typ.List[str]:
    if isinstance(names, str):
        names_list = names.split(",")
    else:
        names_list = names

    selected_names = [normalize_name(name) for name in names_list if name.strip()]

    if selected_names:
        for name in selected_names:
            assert name in available_names
    else:
        # Nothing explicitly selected -> all selected
        selected_names = sorted(available_names)

    assert len(selected_names) > 0

    return selected_names


def iter_fuzzy_selected_checkers(names: FuzzyNames) -> typ.Iterable[checkers.CheckerBase]:
    available_classes = get_available_classes(checkers, checkers.CheckerBase)
    selected_names = get_selected_names(names, set(available_classes))
    for name in selected_names:
        checker_type = typ.cast(CheckerType, available_classes[name])
        yield checker_type()


def iter_fuzzy_selected_fixers(names: FuzzyNames) -> typ.Iterable[fixers.FixerBase]:
    available_classes = get_available_classes(fixers, fixers.FixerBase)
    selected_names = get_selected_names(names, set(available_classes))
    for name in selected_names:
        fixer_type = typ.cast(FixerType, available_classes[name])
        yield fixer_type()


def add_required_imports(tree: ast.Module, required_imports: typ.Set[common.ImportDecl]):
    """Add imports required by fixers.

    Some fixers depend on modules which may not be imported in
    the source module. As an example, occurrences of 'map' might
    be replaced with 'itertools.map', in which case,
    "import itertools" will be added in the module scope.

    A further quirk is that all reqired imports must be added
    before any other statment. This is because that statement
    could be subject to the fix which requires the import. As
    a side effect, a module may end up being imported twice, if
    the module is imported after some statement.
    """
    found_imports: typ.Set[common.ImportDecl] = set()
    prelude_end_index = 0

    for i, node in enumerate(tree.body):
        is_docstring = (
            i == 0 and
            isinstance(node, ast.Expr) and
            isinstance(node.value, ast.Str)
        )
        if is_docstring:
            prelude_end_index = 1
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.asname:
                    continue
                found_imports.add((alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            module_name = node.module
            if module_name is None:
                continue

            for alias in node.names:
                if alias.asname:
                    continue
                found_imports.add((module_name, alias.name))

            if node.module == "__future__":
                prelude_end_index = i
        elif i > 0:
            break

    missing_imports = sorted(required_imports - found_imports)

    import_node: ast.stmt
    for i, (module_name, import_name) in enumerate(missing_imports):
        if import_name is None:
            import_node = ast.Import(names=[
                ast.alias(name=module_name, asname=None)
            ])
        else:
            import_node = ast.ImportFrom(module=module_name, level=0, names=[
                ast.alias(name=import_name, asname=None)
            ])

        tree.body.insert(prelude_end_index + i, import_node)


def transpile_module(cfg: common.BuildConfig, module_source: str) -> str:
    checker_names: FuzzyNames = cfg.get("checkers", "")
    fixer_names: FuzzyNames = cfg.get("fixers", "")
    module_tree = ast.parse(module_source)
    required_imports: typ.Set[common.ImportDecl] = set()

    ver = sys.version_info
    src_version = f"{ver.major}.{ver.minor}"
    tgt_version = cfg["target_version"]

    for checker in iter_fuzzy_selected_checkers(checker_names):
        if checker.is_prohibited_for(tgt_version):
            checker(cfg, module_tree)

    for fixer in iter_fuzzy_selected_fixers(fixer_names):
        if not fixer.is_applicable_to(src_version, tgt_version):
            continue

        maybe_fixed_module = fixer(cfg, module_tree)
        if maybe_fixed_module is None:
            raise Exception(f"Error running fixer {type(fixer).__name__}")
        required_imports.update(fixer.required_imports)
        module_tree = maybe_fixed_module

    add_required_imports(module_tree, required_imports)
    coding, header = parse_module_header(module_source)
    return header + "".join(astor.to_source(module_tree))


def transpile_module_data(cfg: common.BuildConfig, module_source_data: bytes) -> bytes:
    coding, header = parse_module_header(module_source_data)
    module_source = module_source_data.decode(coding)
    fixed_module_source = transpile_module(cfg, module_source)
    return fixed_module_source.encode(coding)
