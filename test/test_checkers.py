import sys
from collections import namedtuple

import pytest

from lib3to6 import utils
from lib3to6 import common

CheckFixture = namedtuple("CheckFixture", ["names", "test_source", 'expected_error_msg'])


def make_fixture(names, test_source, expected_error_msg):
    test_source = utils.clean_whitespace(test_source)
    return CheckFixture(names, test_source, expected_error_msg)


FIXTURES = [
    make_fixture(
        "no_overridden_fixer_imports",
        """
        import itertools
        """,
        None,
    ),
    make_fixture(
        "no_overridden_fixer_imports",
        """
        itertools = "foo"
        """,
        "Prohibited override of import 'itertools'",
    ),
    make_fixture(
        "no_overridden_fixer_imports",
        """
        def itertools():
            pass
        """,
        "Prohibited override of import 'itertools'",
    ),
    make_fixture(
        "no_overridden_fixer_imports",
        """
        import x as itertools
        """,
        "Prohibited override of import 'itertools'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        def map(x):
            pass
        """,
        "Prohibited override of builtin 'map'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        class filter(x):
            pass
        """,
        "Prohibited override of builtin 'filter'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        zip = "foobar"
        """,
        "Prohibited override of builtin 'zip'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        repr: str = "foobar"
        """,
        "Prohibited override of builtin 'repr'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        import foobar as iter
        """,
        "Prohibited override of builtin 'iter'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        import reversed
        """,
        "Prohibited override of builtin 'reversed'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        def foo(input):
            pass
        """,
        "Prohibited override of builtin 'input'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        def foo(min=None):
            pass
        """,
        "Prohibited override of builtin 'min'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        def foo(*, max=None):
            pass
        """,
        "Prohibited override of builtin 'max'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        class foo:
            dict = None
        """,
        "Prohibited override of builtin 'dict'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        class foo:
            list:  None
        """,
        "Prohibited override of builtin 'list'",
    ),
    make_fixture(
        "no_overridden_builtins",
        """
        def foo(x: int = None):
            pass
        """,
        None,
    ),
    make_fixture(
        "no_async_await",
        """
        async def foo():
            bar()
        """,
        "Prohibited use of 'async def'",
    ),
    make_fixture(
        "no_async_await",
        """
        def foo():
            await bar()
        """,
        "Prohibited use of 'await'",
    ),
    make_fixture(
        "no_yield_from",
        """
        def foo():
            yield from bar()
        """,
        "Prohibited use of 'yield from'",
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        data = open(filepath, mode="rb").read()
        assert isinstance(data, bytes)
        """,
        None,
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="wb") as fobj:
            fobj.write(b"test")
        """,
        None,
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        with open(filepath, x) as fobj:
            fobj.write("test")
        """,
        "Prohibited value for argument 'mode' of builtin.open. Expected ast.Str node",
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode=x) as fobj:
            fobj.write("test")
        """,
        "Prohibited value for argument 'mode' of builtin.open. Expected ast.Str node",
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="w") as fobj:
            fobj.write("test")
        """,
        [
            "Prohibited value 'w' for argument 'mode' of builtin.open. ",
            "Only binary modes are allowed, use io.open as an alternative.",
        ],
    ),
    make_fixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="w", encoding="utf-8") as fobj:
            fobj.write("test")
        """,
        "Prohibited keyword argument 'encoding' to builtin.open.",
    ),
    make_fixture(
        "no_star_imports",
        """
        from math import *
        """,
        "Prohibited from math import *.",
    ),
    make_fixture(
        "no_complex_named_tuple",
        """
        import typing
        class Foo(typing.NamedTuple):
            bar: int
            baz: int = 1
        """,
        "Prohibited use of default value for field 'baz' of class 'Foo'",
    ),
    make_fixture(
        "no_complex_named_tuple",
        """
        import typing
        class Foo(typing.NamedTuple):
            bar: int
            def baz(self):
                pass
        """,
        "Prohibited definition of method 'baz' for class 'Foo'",
    ),
    make_fixture(
        "no_complex_named_tuple",
        """
        import typing as typ
        class Foo(typ.NamedTuple):
            bar: int
            baz: int = 1
        """,
        "Prohibited use of default value for field 'baz' of class 'Foo'",
    ),
    make_fixture(
        "no_unusable_imports",
        """
        import lzma
        """,
        "Prohibited import 'lzma'. This module is available since Python 3.3",
    ),
    make_fixture(
        "no_unusable_imports",
        """
        from pathlib import Path
        """,
        [
            "Prohibited import 'pathlib'. This module is available since Python 3.4",
            "Use 'https://pypi.org/project/pathlib2' instead.",
        ],
    ),
    make_fixture(
        "no_unusable_imports",
        """
        import asyncio
        """,
        ["Prohibited import 'asyncio'. This module is available since Python 3.4", "No backport"],
    ),
    make_fixture(
        "no_mat_mult_op",
        "foo = bar @ baz",
        "Prohibited use of matrix multiplication",
    ),
]


@pytest.mark.parametrize("fixture", FIXTURES)
def test_checkers(fixture):
    if "--capture=no" in sys.argv:
        print()

    if isinstance(fixture.expected_error_msg, list):
        expected_error_messages = fixture.expected_error_msg
    else:
        expected_error_messages = [fixture.expected_error_msg]

    ctx = common.init_build_context(checkers=fixture.names, install_requires=set())
    try:
        utils.transpile_and_dump(ctx, fixture.test_source)
        assert fixture.expected_error_msg is None, f"Missing CheckError for '{fixture.names}'"
    except common.CheckError as result_error:
        assert fixture.expected_error_msg is not None

        for expected_error_msg in expected_error_messages:
            assert expected_error_msg in str(result_error)


def _test_unusable_imports(source, ver="2.7", req=None):
    ctx = common.init_build_context(
        checkers="no_unusable_imports",
        target_version=ver,
        install_requires=set(req.split(" ")) if req else None,
    )
    utils.transpile_and_dump(ctx, source)


def test_backport_checker_warning(caplog):
    assert len(caplog.records) == 0
    _test_unusable_imports("import typing", "2.7")
    assert len(caplog.records) == 1
    for record in caplog.records:
        assert record.levelname == 'WARNING'
        assert "Use of import 'typing'" in record.message


def test_backport_checker_nowarning(caplog):
    assert len(caplog.records) == 0
    _test_unusable_imports("import typing", "2.7", req="typing")
    assert len(caplog.records) == 0


def test_backport_checker_errors():
    # no error expected, target is new enough
    _test_unusable_imports("import asyncio", "3.4")

    try:
        _test_unusable_imports("import asyncio", "3.3")
        assert False, "expected CheckError"
    except common.CheckError as err:
        assert "Prohibited import 'asyncio'" in str(err)

    # no error expected, target new enough
    _test_unusable_imports("import pathlib", "3.4")
    # no error expected, backport used
    _test_unusable_imports("import pathlib2 as pathlib", "2.7", req="pathlib2")

    try:
        _test_unusable_imports("import pathlib", "2.7")
        assert False, "expected CheckError"
    except common.CheckError as err:
        assert "Prohibited import 'pathlib'" in str(err)

    try:
        _test_unusable_imports("import pathlib", "2.7", req="pathlib")
        assert False, "expected CheckError"
    except common.CheckError as err:
        # invalid backport
        assert "Prohibited import 'pathlib'" in str(err)

    try:
        _test_unusable_imports("import pathlib", "2.7", req="pathlib2")
        assert False, "expected CheckError"
    except common.CheckError as err:
        # use of stdlib instead of backported module
        assert "Prohibited import 'pathlib'" in str(err)

    # no error expected, target new enough
    _test_unusable_imports("import lzma", "3.3")
    # no error expected, backport used
    _test_unusable_imports("import lzma", "2.7", req="backports.lzma")

    try:
        _test_unusable_imports("import lzma", "2.7", req="lzma")
        assert False, "expected CheckError"
    except common.CheckError as err:
        # invalid backport requirement/package
        assert "Prohibited import 'lzma'" in str(err)
