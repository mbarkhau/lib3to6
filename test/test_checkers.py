import sys
from collections import namedtuple

import pytest

from lib3to6 import utils
from lib3to6.common import CheckError

CheckFixture = namedtuple("CheckFixture", ["names", "test_source", 'expected_error_msg'])


FIXTURES = [
    CheckFixture(
        "no_overridden_fixer_imports",
        """
        import itertools
        """,
        None,
    ),
    CheckFixture(
        "no_overridden_fixer_imports",
        """
        itertools = "foo"
        """,
        "Prohibited override of import 'itertools'",
    ),
    CheckFixture(
        "no_overridden_fixer_imports",
        """
        def itertools():
            pass
        """,
        "Prohibited override of import 'itertools'",
    ),
    CheckFixture(
        "no_overridden_fixer_imports",
        """
        import x as itertools
        """,
        "Prohibited override of import 'itertools'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        def map(x):
            pass
        """,
        "Prohibited override of builtin 'map'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        class filter(x):
            pass
        """,
        "Prohibited override of builtin 'filter'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        zip = "foobar"
        """,
        "Prohibited override of builtin 'zip'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        repr: str = "foobar"
        """,
        "Prohibited override of builtin 'repr'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        import foobar as iter
        """,
        "Prohibited override of builtin 'iter'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        import reversed
        """,
        "Prohibited override of builtin 'reversed'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        def foo(input):
            pass
        """,
        "Prohibited override of builtin 'input'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        def foo(min=None):
            pass
        """,
        "Prohibited override of builtin 'min'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        def foo(*, max=None):
            pass
        """,
        "Prohibited override of builtin 'max'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        class foo:
            dict = None
        """,
        "Prohibited override of builtin 'dict'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        class foo:
            list:  None
        """,
        "Prohibited override of builtin 'list'",
    ),
    CheckFixture(
        "no_overridden_builtins",
        """
        def foo(x: int = None):
            pass
        """,
        None,
    ),
    CheckFixture(
        "no_async_await",
        """
        async def foo():
            bar()
        """,
        "Prohibited use of async/await",
    ),
    CheckFixture(
        "no_async_await",
        """
        async def foo():
            await bar()
        """,
        "Prohibited use of async/await",
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        data = open(filepath, mode="rb").read()
        assert isinstance(data, bytes)
        """,
        None,
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="wb") as fh:
            fh.write(b"test")
        """,
        None,
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        with open(filepath, x) as fh:
            fh.write("test")
        """,
        "Prohibited value for argument 'mode' of builtin.open. Expected ast.Str node",
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode=x) as fh:
            fh.write("test")
        """,
        "Prohibited value for argument 'mode' of builtin.open. Expected ast.Str node",
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="w") as fh:
            fh.write("test")
        """,
        [
            "Prohibited value 'w' for argument 'mode' of builtin.open. ",
            "Only binary modes are allowed, use io.open as an alternative.",
        ],
    ),
    CheckFixture(
        "no_open_with_encoding",
        """
        with open(filepath, mode="w", encoding="utf-8") as fh:
            fh.write("test")
        """,
        "Prohibited keyword argument 'encoding' to builtin.open.",
    ),
    CheckFixture(
        "no_star_imports",
        """
        from math import *
        """,
        "Prohibited from math import *.",
    ),
    CheckFixture(
        "no_complex_named_tuple",
        """
        import typing
        class Foo(typing.NamedTuple):
            bar: int
            baz: int = 1
        """,
        "Prohibited use of default value for field 'baz' of class 'Foo'",
    ),
    CheckFixture(
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
    CheckFixture(
        "no_complex_named_tuple",
        """
        import typing as typ
        class Foo(typ.NamedTuple):
            bar: int
            baz: int = 1
        """,
        "Prohibited use of default value for field 'baz' of class 'Foo'",
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
    cfg         = {'checkers': fixture.names, 'target_version': "2.7"}
    test_source = utils.clean_whitespace(fixture.test_source)
    try:
        utils.transpile_and_dump(test_source, cfg)
        assert fixture.expected_error_msg is None
    except CheckError as result_error:
        # result_error_msg = str(result_error)
        # print("!!!", repr(result_error_msg))

        assert fixture.expected_error_msg is not None

        for expected_error_msg in expected_error_messages:
            # print("???", repr(expected_error_msg))
            assert expected_error_msg in str(result_error)
