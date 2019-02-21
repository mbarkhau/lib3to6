# This file is part of the lib3to6 project
# https://gitlab.com/mbarkhau/lib3to6
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import re
import ast
import sys
import astor
import typing as typ

from . import utils
from . import common
from . import fixers
from . import checkers


DEFAULT_SOURCE_ENCODING_DECLARATION = "# -*- coding: {} -*-"

DEFAULT_SOURCE_ENCODING = "utf-8"

DEFAULT_TARGET_VERSION = "2.7"

# https://www.python.org/dev/peps/pep-0263/
SOURCE_ENCODING_RE = re.compile(
    r"""
    ^
    [ \t\v]*
    \#.*?coding[:=][ \t]*
    (?P<coding>[-_.a-zA-Z0-9]+)
""",
    re.VERBOSE,
)


def parse_module_header(module_source: typ.Union[bytes, str]) -> typ.Tuple[str, str]:
    shebang         = False
    coding_declared = False
    coding          = DEFAULT_SOURCE_ENCODING

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
                    coding          = m.group("coding").strip()
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
        name = name[: -len("fixer")]
    if name.endswith("checker"):
        name = name[: -len("checker")]
    return name


def get_available_classes(module: object, clazz: CheckerOrFixer) -> typ.Dict[str, CheckerOrFixer]:

    assert isinstance(clazz, type)
    clazz_name = clazz.__name__
    assert clazz_name.endswith("Base")
    assert getattr(module, clazz_name) is clazz

    maybe_classes = {
        name: getattr(module, name) for name in dir(module) if not name.endswith(clazz_name)
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
    selected_names    = get_selected_names(names, set(available_classes))
    for name in selected_names:
        checker_type = typ.cast(CheckerType, available_classes[name])
        yield checker_type()


def iter_fuzzy_selected_fixers(names: FuzzyNames) -> typ.Iterable[fixers.FixerBase]:
    available_classes = get_available_classes(fixers, fixers.FixerBase)
    selected_names    = get_selected_names(names, set(available_classes))
    for name in selected_names:
        fixer_type = typ.cast(FixerType, available_classes[name])
        yield fixer_type()


def parse_imports(tree: ast.Module) -> typ.Tuple[int, int, typ.Set[common.ImportDecl]]:
    future_imports_offset = -1
    imports_end_offset    = -1

    import_decls: typ.Set[common.ImportDecl] = set()

    for body_offset, node in enumerate(tree.body):
        is_docstring = (
            body_offset == 0 and isinstance(node, ast.Expr) and isinstance(node.value, ast.Str)
        )
        if is_docstring:
            future_imports_offset = body_offset
            imports_end_offset    = body_offset
            continue

        if isinstance(node, ast.Import):
            imports_end_offset = body_offset
            for alias in node.names:
                if alias.asname:
                    # we never use asname, so this is user code
                    pass
                else:
                    import_decls.add(common.ImportDecl(alias.name, None))
        elif isinstance(node, ast.ImportFrom):
            imports_end_offset = body_offset
            module_name        = node.module
            if module_name:
                if module_name == '__future__':
                    future_imports_offset = body_offset

                for alias in node.names:
                    if alias.asname:
                        # we never use asname, so this is user code
                        pass
                    else:
                        import_decls.add(common.ImportDecl(module_name, alias.name))
        else:
            break

    return (future_imports_offset, imports_end_offset, import_decls)


def add_required_imports(tree: ast.Module, required_imports: typ.Set[common.ImportDecl]) -> None:
    """Add imports required by fixers.

    Some fixers depend on modules which may not be imported in
    the source module. As an example, occurrences of 'map' might
    be replaced with 'itertools.imap', in which case,
    "import itertools" will be added in the module scope.

    A further quirk is that all reqired imports must be added
    before any other statment. This is because that statement
    could be subject to the fix which requires the import. As
    a side effect, a module may end up being imported twice, if
    the module is imported after some statement.
    """
    (future_imports_offset, imports_end_offset, found_imports) = parse_imports(tree)

    missing_imports = sorted(required_imports - found_imports)

    import_node: ast.stmt
    for import_decl in missing_imports:
        if import_decl.import_name is None:
            import_node = ast.Import(names=[ast.alias(name=import_decl.module_name, asname=None)])
        else:
            import_node = ast.ImportFrom(
                module=import_decl.module_name,
                level=0,
                names=[ast.alias(name=import_decl.import_name, asname=None)],
            )

        if import_decl.module_name == '__future__':
            tree.body.insert(future_imports_offset + 1, import_node)
            future_imports_offset += 1
            imports_end_offset    += 1
        else:
            tree.body.insert(imports_end_offset + 1, import_node)
            imports_end_offset += 1


def add_module_declarations(tree: ast.Module, module_declarations: typ.Set[str]) -> None:
    """Add global declarations required by fixers.

    Some fixers declare globals (or override builtins) the source
    module. As an example, occurrences of 'map' might be replaced
    by 'map = getattr(itertools, "map", map)'.

    These declarations are added directly after imports.
    """
    _, imports_end_offset, _ = parse_imports(tree)

    for decl_str in sorted(module_declarations):
        decl_node = utils.parse_stmt(decl_str)
        tree.body.insert(imports_end_offset + 1, decl_node)
        imports_end_offset += 1


def transpile_module(cfg: common.BuildConfig, module_source: str) -> str:
    checker_names: FuzzyNames = cfg.get("checkers", "")
    fixer_names  : FuzzyNames = cfg.get("fixers"  , "")
    module_tree = ast.parse(module_source)
    required_imports   : typ.Set[common.ImportDecl] = set()
    module_declarations: typ.Set[str              ] = set()

    ver         = sys.version_info
    src_version = f"{ver.major}.{ver.minor}"
    tgt_version = cfg.get("target_version", DEFAULT_TARGET_VERSION)

    for checker in iter_fuzzy_selected_checkers(checker_names):
        if checker.is_prohibited_for(tgt_version):
            checker(cfg, module_tree)

    for fixer in iter_fuzzy_selected_fixers(fixer_names):
        if fixer.is_applicable_to(src_version, tgt_version):
            maybe_fixed_module = fixer(cfg, module_tree)
            if maybe_fixed_module is None:
                raise Exception(f"Error running fixer {type(fixer).__name__}")
            required_imports.update(fixer.required_imports)
            module_declarations.update(fixer.module_declarations)
            module_tree = maybe_fixed_module

    if any(required_imports):
        add_required_imports(module_tree, required_imports)
    if any(module_declarations):
        add_module_declarations(module_tree, module_declarations)
    coding, header = parse_module_header(module_source)
    return header + "".join(astor.to_source(module_tree))


def transpile_module_data(cfg: common.BuildConfig, module_source_data: bytes) -> bytes:
    coding, header = parse_module_header(module_source_data)
    module_source       = module_source_data.decode(coding)
    fixed_module_source = transpile_module(cfg, module_source)
    return fixed_module_source.encode(coding)
