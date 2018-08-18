import sys
from collections import namedtuple

import pytest

from three2six import transpile
from three2six import utils


FixerFixture = namedtuple("FixerFixture", [
    "names", "target_version", "test_source", "expected_source",
])


def test_numeric_literals_with_underscore():
    # NOTE (mb 2018-06-14): We don't need to transpile here
    #   this case is taken care off by the fact that there
    #   is no representation of the underscores at the ast
    #   level.
    a_ast = utils.parsedump_ast("x = 200_000_000")
    b_ast = utils.parsedump_ast("x = 200000000")
    assert a_ast == b_ast


def test_header_preserved():
    return
    test_source = """
    #!/usr/bin/env python
    # This file is part of the three2six project
    # https://github.com/mbarkhau/three2six
    # (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
    #
    # SPDX-License-Identifier:    MIT
    hello = 'world'
    """
    expected_source = """
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    # This file is part of the three2six project
    # https://github.com/mbarkhau/three2six
    # (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
    #
    # SPDX-License-Identifier:    MIT
    from __future__ import absolute_import
    from __future__ import division
    from __future__ import print_function
    from __future__ import unicode_literals
    hello = 'world'
    """
    test_source = utils.clean_whitespace(test_source)
    expected_source = utils.clean_whitespace(expected_source)

    result_coding, result_header, result_source = utils.transpile_and_dump(test_source)
    assert result_coding == "utf-8"
    assert expected_source == result_source

    expected_ast = utils.parsedump_ast(expected_source)
    result_ast = utils.parsedump_ast(result_source)
    assert expected_ast == result_ast


FIXTURES = [
    FixerFixture(
        [
            "absolute_import_future",
            "division_future",
            "print_function_future",
            "unicode_literals_future",
        ],
        "2.7",
        """
        #!/usr/bin/env python
        \"\"\"Module Docstring\"\"\"
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        \"\"\"Module Docstring\"\"\"
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        from __future__ import unicode_literals
        """,
    ),
    FixerFixture(
        [
            "absolute_import_future",
            "division_future",
            "print_function_future",
            "unicode_literals_future",
        ],
        "2.7",
        """
        #!/usr/bin/env python
        \"\"\"Module Docstring\"\"\"
        from __future__ import division, absolute_import, print_function
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        \"\"\"Module Docstring\"\"\"
        from __future__ import division, absolute_import, print_function
        from __future__ import unicode_literals
        """,
    ),
    FixerFixture(
        [
            "annotations_future",       # not applied to old versions
            "absolute_import_future",
            "division_future",
            "print_function_future",
            "unicode_literals_future",
        ],
        "2.7",
        """
        #!/usr/bin/env python
        \"\"\"Module Docstring\"\"\"
        import itertools    # check order of imports (__future__ first)
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        \"\"\"Module Docstring\"\"\"
        from __future__ import absolute_import
        from __future__ import division
        from __future__ import print_function
        from __future__ import unicode_literals
        import itertools
        """,
    ),
    FixerFixture(
        "remove_ann_assign",
        "2.7",
        """
        moduleannattr: moduleattr_annotation

        class Bar:
            classannattr_a: classattr_annotation
            classannattr_b: typ.Any
            classannassign: classattr_annotation = 22

            def method(self, arg):
                self.instance_attr: typ.Any = arg
        """,
        """
        moduleannattr = None

        class Bar:
            classannattr_a = None
            classannattr_b = None
            classannassign = 22

            def method(self, arg):
                self.instance_attr = arg
        """,
    ),
    FixerFixture(
        "remove_function_def_annotations",
        "2.7",
        """
        def foo(arg: arg_annotation) -> ret_annotation:
            def nested_fn(f: int = 22) -> int:
                pass

        class Bar:
            def foo(self, arg: arg_annotation) -> ret_annotation:
                def nested_fn(f: int = 22) -> int:
                    pass
        """,
        """
        def foo(arg):
            def nested_fn(f=22):
                pass

        class Bar:
            def foo(self, arg):
                def nested_fn(f=22):
                    pass
        """
    ),
    FixerFixture(
        "f_string_to_str_format",
        "2.7",
        "val = 33; f\"prefix {val / 2:>{3 * 3}} suffix\"",
        "val = 33; \"prefix {0:>{1}} suffix\".format(val / 2, 3 * 3)",
    ),
    FixerFixture(
        "f_string_to_str_format",
        "2.7",
        """
        who = "World"
        print(f"Hello {who}!")
        """,
        """
        who = "World"
        print("Hello {0}!".format(who))
        """,
    ),
    FixerFixture(
        "new_style_classes",
        "2.7",
        """
        class Foo:
            pass
        """,
        """
        class Foo(object):
            pass
        """,
    ),
    FixerFixture(
        "new_style_classes",
        "3.4",
        """
        class Foo:
            pass
        """,
        """
        class Foo:
            pass
        """,
    ),
    FixerFixture(
        "itertools_builtins,print_function_future",
        "2.7",
        """
        \"\"\"Module Docstring\"\"\"
        def fn(elem):
            return elem * 2

        list(map(fn, [1, 2, 3, 4]))
        dict(zip("abcd", [1, 2, 3, 4]))
        """,
        """
        \"\"\"Module Docstring\"\"\"
        from __future__ import print_function
        import itertools
        map = getattr(itertools, 'imap', map)
        zip = getattr(itertools, 'izip', zip)

        def fn(elem):
            return elem * 2

        list(map(fn, [1, 2, 3, 4]))
        dict(zip("abcd", [1, 2, 3, 4]))
        """,
    ),
    FixerFixture(
        "itertools_builtins",
        "2.7",
        """
        def fn(elem):
            list(map(fn, [1, 2, 3, 4]))
            dict(zip("abcd", [1, 2, 3, 4]))
            return elem * 2
        """,
        """
        import itertools

        map = getattr(itertools, 'imap', map)
        zip = getattr(itertools, 'izip', zip)

        def fn(elem):
            list(map(fn, [1, 2, 3, 4]))
            dict(zip("abcd", [1, 2, 3, 4]))
            return elem * 2
        """,
    ),
    FixerFixture(
        "itertools_builtins",
        "2.7",
        """
        def fn(elem):
            def fn_nested():
                list(map(moep, zip("abcd", [1, 2, 3, 4])))
        """,
        """
        import itertools

        map = getattr(itertools, 'imap', map)
        zip = getattr(itertools, 'izip', zip)

        def fn(elem):
            def fn_nested():
                list(map(moep, zip("abcd", [1, 2, 3, 4])))
        """,
    ),
    FixerFixture(
        "short_to_long_form_super",
        "2.7",
        """
        class FooClass:
            def foo_method(self, arg, *args, **kwargs):
                return super().foo_method(arg, *args, **kwargs)
        """,
        """
        class FooClass:
            def foo_method(self, arg, *args, **kwargs):
                return super(FooClass, self).foo_method(arg, *args, **kwargs)
        """,
    ),
    FixerFixture(
        "short_to_long_form_super",
        "3.4",
        """
        class FooClass:
            def foo_method(self, arg, *args, **kwargs):
                return super().foo_method(arg, *args, **kwargs)
        """,
        """
        class FooClass:
            def foo_method(self, arg, *args, **kwargs):
                return super().foo_method(arg, *args, **kwargs)
        """,
    ),
    FixerFixture(
        "remove_function_def_annotations,inline_kw_only_args",
        "2.7",
        """
        def foo(
            self,
            x: int = None,
            *args: Tuple[str, ...],
            mykwonly_required: str,
            mykwonly_none=None,
            mykwonly_str: str="moep",
            mykwonly_bool: boolean=True,
            mykwonly_int: int=22,
            mykwonly_required2: str,
            mykwonly_float: float=12.3,
        ) -> None:
            pass
        """,
        """
        def foo(self, x=None, *args, **kwargs):
            mykwonly_required = kwargs["mykwonly_required"]
            mykwonly_none = kwargs.get("mykwonly_none", None)
            mykwonly_str = kwargs.get("mykwonly_str", "moep")
            mykwonly_bool = kwargs.get("mykwonly_bool", True)
            mykwonly_int = kwargs.get("mykwonly_int", 22)
            mykwonly_required2 = kwargs["mykwonly_required2"]
            mykwonly_float = kwargs.get("mykwonly_float", 12.3)
            pass
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        a = [0, *[1, 2], 3, *[4, 5]]
        """,
        """
        a = [0, 1, 2, 3, 4, 5]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        b = {*[1, 2], 3, *[4, 5]}
        """,
        """
        b = {1, 2, 3, 4, 5}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        c = (*[1, 2], 3, *[4, 5])
        """,
        """
        c = (1, 2, 3, 4, 5)
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        a = [*[1, 2], x, *x, *[4, 5]]
        """,
        """
        a = [1, 2, x] + list(x) + [4, 5]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        b = {*[1, 2], x, *x, *[4, 5], *(6, 7)}
        """,
        """
        b = set([1, 2, x] + list(x) + [4, 5, 6, 7])
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        c = (*[1, 2], x, *[4, 5], *(6, 7), *y)
        """,
        """
        c = tuple([1, 2, x, 4, 5, 6, 7] + list(y))
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        a = [*x, 0]
        """,
        """
        a = list(x) + [0]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        lambda x: [*x, 0]
        """,
        """
        lambda x: (list(x) + [0])
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        print(*[1])
        print(*[1], 2)
        print(*[1], *[2], 3)
        print(*[1], *x, 3)
        """,
        """
        print(*[1])
        print(1, 2)
        print(1, 2, 3)
        print(*[1] + list(x) + [3])
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        def foo():
            print(*[1], *[2], 3)
        """,
        """
        def foo():
            print(1, 2, 3)
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        foo(**x, bar=22)
        """,
        """
        import itertools

        foo(**dict(itertools.chain(
            x.items(),
            {"bar": 22}.items(),
        )))
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        dict(**dict(**{"x": 1}), **dict(**{"y": 2}), z=3)
        """,
        """
        {"x": 1, "y": 2, "z": 3}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        {**{'x': 1}, 'y': 2}
        """,
        """
        {'x': 1, 'y': 2}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        x = "x"
        y = "y"
        d = {**{x: 1}, y: 2}
        assert d == {"x": 1, "y": 2}
        """,
        """
        x = "x"
        y = "y"
        d = {x: 1, y: 2}
        assert d == {"x": 1, "y": 2}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        foo(**dict(**{"x": 1}), **dict(**{"y": 2}), z=3)
        """,
        """
        foo(**{"x": 1, "y": 2, "z": 3})
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        dict(**dict(**{"x": 1}), **y, z=3)
        """,
        """
        import itertools

        dict(itertools.chain(
            {"x": 1}.items(),
            y.items(),
            {"z": 3}.items(),
        ))
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        dict(**{"x": 1})
        testfn(**{"a": 1}, b=2, **{"c": 3}, d=4)
        dict(**{"a": 1}, b=2, **{"c": 3}, d=4)
        """,
        """
        {"x": 1}
        testfn(**{"a": 1, "b": 2, "c": 3, "d": 4})
        {"a": 1, "b": 2, "c": 3, "d": 4}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        a = [1, 2, 3]
        b = [4, 5, 6]
        x = {"x": 11}
        z = {"z": 33}
        testfn(0, *a, *b, 7, 8, **x, y=22, **z)
        """,
        """
        import itertools

        a = [1, 2, 3]
        b = [4, 5, 6]
        x = {"x": 11}
        z = {"z": 33}
        testfn(
            *([0] + list(a) + list(b) + [7, 8]),
            **dict(itertools.chain(x.items(), {"y": 22}.items(), z.items()))
        )
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        with foo(*[1, 2, 3], 4) as x:
            pass
        """,
        """
        with foo(1, 2, 3, 4) as x:
            pass
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        for x in [*[1, 2, 3], 4]:
            for y in foo(*[1, 2, 3], 4, *[5, 6, 7], **{"foo": 1}, bar=2, **{"baz": 3}):
                bar(x, y)
        """,
        """
        for x in [1, 2, 3, 4]:
            for y in foo(1, 2, 3, 4, 5, 6, 7, **{"foo": 1, "bar": 2, "baz": 3}):
                bar(x, y)
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        x = [1, 2, 3]
        (
            lambda l: l.extend([*[1, 2, *l, 4], 5])
        )(x)
        assert x == [1, 2, 3, 1, 2, 1, 2, 3, 4, 5]
        """,
        """
        x = [1, 2, 3]
        (
            lambda l: l.extend(
                list([1, 2] + list(l) + [4]) + [5]
            )
        )(x)
        assert x == [1, 2, 3, 1, 2, 1, 2, 3, 4, 5]
        """,
        # NOTE (mb 2018-07-08): Ideally we could
        #   be simplified to:
        #
        #     lambda l: l.extend(
        #         [1, 2] + list(l) + [4, 5]
        #     )
        #
        # But since the existing transpile is correct
        # and these examples are corner cases anyway,
        # I'm not putting in any more effort.
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        with foo(*[1, 2, 3], 4) as x:
            try:
                if bar:
                    pass
                else:
                    a = [*[1, 2, *[3, 4], 5], 6]
            finally:
                b = {**{'x': 2}, 'x': 1}
        """,
        """
        with foo(1, 2, 3, 4) as x:
            try:
                if bar:
                    pass
                else:
                    a = [1, 2, 3, 4, 5, 6]
            finally:
                b = {'x': 2, 'x': 1}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        x = [*[1, 2], 3] if True else [*[4, 5], 6]
        """,
        """
        x = [1, 2, 3] if True else [4, 5, 6]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        x = [a, b, c][([*[1], 2])[0]]
        """,
        """
        x = [a, b, c][ [1, 2][0] ]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        "2.7",
        """
        x = [n for n in [*[1, 2], 3, 4] if n % 2 == 0]
        """,
        """
        x = [n for n in [1, 2, 3, 4] if n % 2 == 0]
        """,
    ),
    FixerFixture(
        "range_to_xrange",
        "2.7",
        """
        myrange = range
        """,
        """
        range = getattr(__builtins__, "xrange", range)
        myrange = range
        """
    ),
    FixerFixture(
        "range_to_xrange",
        "2.7",
        """
        def foo():
            if True:
                for x in range(9):
                    print(x)
        """,
        """
        range = getattr(__builtins__, "xrange", range)
        def foo():
            if True:
                for x in range(9):
                    print(x)
        """
    ),
    FixerFixture(
        "named_tuple_class_to_assign",
        "2.7",
        """
        import typing

        class Foo(typing.NamedTuple):
            bar: int
            baz: bool
        """,
        """
        import typing

        Foo = typing.NamedTuple("Foo", [
            ("bar", int),
            ("baz", bool),
        ])
        """
    ),
    FixerFixture(
        "named_tuple_class_to_assign",
        "2.7",
        """
        import typing as typ

        class Foo(typ.NamedTuple):
            bar: int
            baz: bool
        """,
        """
        import typing as typ

        Foo = typ.NamedTuple("Foo", [
            ("bar", int),
            ("baz", bool),
        ])
        """
    ),
    FixerFixture(
        "named_tuple_class_to_assign",
        "2.7",
        """
        from typing import NamedTuple

        class Foo(NamedTuple):
            bar: int
            baz: bool
        """,
        """
        from typing import NamedTuple

        Foo = NamedTuple("Foo", [
            ("bar", int),
            ("baz", bool),
        ])
        """
    ),
    # FixerFixture(
    #     "generator_return_to_stop_iteration_exception",
    #     "2.7",
    #     """
    #     """,
    #     """
    #     """,
    # ),
]


def _normalized_source(in_source):
    """This is mostly to get rid of comments"""
    in_source = utils.clean_whitespace(in_source)
    out_source = utils.parsedump_source(in_source)
    assert utils.parsedump_ast(out_source) == utils.parsedump_ast(in_source)
    return out_source


@pytest.mark.parametrize("fixture", FIXTURES)
def test_fixers(fixture):
    if "--capture=no" in sys.argv:
        print()

    expected_source = utils.clean_whitespace(fixture.expected_source)
    expected_ast = utils.parsedump_ast(expected_source)
    expected_coding, expected_header = transpile.parse_module_header(expected_source)

    test_source = utils.clean_whitespace(fixture.test_source)
    test_ast = utils.parsedump_ast(test_source)
    print(">>>>>>>>" * 9)
    print(test_ast)
    print("--------" * 9)
    print(repr(test_source))
    print(">>>>>>>>" * 9)

    print("????????" * 9)
    # print(expected_ast)
    # print("--------" * 9)
    print(repr(expected_source))
    print("????????" * 9)

    cfg = {"fixers": fixture.names, "target_version": fixture.target_version}
    result_coding, result_header, result_source = utils.transpile_and_dump(test_source, cfg)
    result_ast = utils.parsedump_ast(result_source)

    print("<<<<<<<<" * 9)
    # print(result_ast)
    # print("--------" * 9)
    print(repr(result_source))
    print("<<<<<<<<" * 9)

    assert result_coding == expected_coding
    assert result_header == expected_header

    assert result_ast == expected_ast
    assert _normalized_source(result_source) == _normalized_source(expected_source)
