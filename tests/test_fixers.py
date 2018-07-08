import sys
from collections import namedtuple

import pytest

from three2six import transpile
from three2six import utils


FixerFixture = namedtuple("FixerFixture", [
    "names", "test_source", "expected_source",
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
        """
        #!/usr/bin/env python
        \"\"\"Module Docstring\"\"\"
        from __future__ import division
        import itertools
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        \"\"\"Module Docstring\"\"\"
        from __future__ import absolute_import
        from __future__ import print_function
        from __future__ import unicode_literals
        from __future__ import division
        import itertools
        """,
    ),
    FixerFixture(
        "remove_ann_assign",
        """
        moduleannattr: moduleattr_annotation

        class Bar:
            classannattr: classattr_annotation
            classannassign: classattr_annotation = 22
        """,
        """
        moduleannattr = None

        class Bar:
            classannattr = None
            classannassign = 22
        """,
    ),
    FixerFixture(
        "remove_function_def_annotations",
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
        "val = 33; f\"prefix {val / 2:>{3 * 3}} suffix\"",
        "val = 33; \"prefix {0:>{1}} suffix\".format(val / 2, 3 * 3)",
    ),
    FixerFixture(
        "f_string_to_str_format",
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
        "itertools_builtins,print_function_future",
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

        def fn(elem):
            return elem * 2

        list(itertools.imap(fn, [1, 2, 3, 4]))
        dict(itertools.izip("abcd", [1, 2, 3, 4]))
        """,
    ),
    FixerFixture(
        "itertools_builtins",
        """
        def fn(elem):
            list(map(fn, [1, 2, 3, 4]))
            dict(zip("abcd", [1, 2, 3, 4]))
            return elem * 2
        """,
        """
        import itertools

        def fn(elem):
            list(itertools.imap(fn, [1, 2, 3, 4]))
            dict(itertools.izip("abcd", [1, 2, 3, 4]))
            return elem * 2
        """,
    ),
    FixerFixture(
        "itertools_builtins",
        """
        def fn(elem):
            def fn_nested():
                list(map(moep, zip("abcd", [1, 2, 3, 4])))
        """,
        """
        import itertools

        def fn(elem):
            def fn_nested():
                list(itertools.imap(moep, itertools.izip("abcd", [1, 2, 3, 4])))
        """,
    ),
    FixerFixture(
        "short_to_long_form_super",
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
        "remove_function_def_annotations,inline_kw_only_args",
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
        """
        print(*[1])
        print(*[1], 2)
        print(*[1], *[2], 3)
        """,
        """
        print(*[1])

        upg_args_0 = []
        upg_args_0.extend([1])
        upg_args_0.append(2)
        print(*upg_args_0)
        del upg_args_0

        upg_args_1 = []
        upg_args_1.extend([1])
        upg_args_1.extend([2])
        upg_args_1.append(3)
        print(*upg_args_1)
        del upg_args_1
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        def foo():
            print(*[1], *[2], 3)
        """,
        """
        def foo():
            upg_args_0 = []
            upg_args_0.extend([1])
            upg_args_0.extend([2])
            upg_args_0.append(3)
            print(*upg_args_0)
            del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        dict(**{"x": 1})

        dict(**{"x": 1}, y=2, **{"z": 3})

        a = {"x": 11}
        b = {"z": 33}
        dict(**a, y=22, **b)
        """,
        """
        dict(**{"x": 1})

        upg_kwargs_0 = {}
        upg_kwargs_0.update({"x": 1})
        upg_kwargs_0["y"] = 2
        upg_kwargs_0.update({"z": 3})
        dict(**upg_kwargs_0)
        del upg_kwargs_0

        a = {"x": 11}
        b = {"z": 33}
        upg_kwargs_1 = {}
        upg_kwargs_1.update(a)
        upg_kwargs_1["y"] = 22
        upg_kwargs_1.update(b)
        dict(**upg_kwargs_1)
        del upg_kwargs_1
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        {**{'x': 2}, 'x': 1}
        """,
        """
        upg_kwargs_0 = {}
        upg_kwargs_0.update({"x": 2})
        upg_kwargs_0["x"] = 1
        dict(**upg_kwargs_0)
        del upg_kwargs_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        a = [*[1, 2], 3, *[4, 5]]
        """,
        """
        a = [1, 2, 3, 4, 5]
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        b = {*[1, 2], 3, *[4, 5]}
        """,
        """
        b = {1, 2, 3, 4, 5}
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        c = (*[1, 2], 3, *[4, 5])
        """,
        """
        c = (1, 2, 3, 4, 5)
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        a = [*[1, 2], x, *x, *[4, 5]]
        """,
        """
        upg_args_0 = [1, 2]
        upg_args_0.append(x)
        upg_args_0.extend(x)
        upg_args_0.extend([4, 5])
        a = upg_args_0
        del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        b = {*[1, 2], x, *x, *[4, 5], *(6, 7)}
        """,
        """
        upg_args_0 = {1, 2}
        upg_args_0.add(x)
        upg_args_0.update(x)
        upg_args_0.update((4, 5, 6, 7))
        b = upg_args_0
        del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        c = (*[1, 2], x, *[4, 5], *(6, 7), *y)
        """,
        """
        upg_args_0 = (1, 2)
        upg_args_0 += (x,)
        upg_args_0 += tuple([4, 5])
        upg_args_0 += (6, 7)
        upg_args_0 += tuple(y)
        c = upg_args_0
        del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        for x in [*[1, 2, 3], 4]:
            for y in foo(*[1, 2, 3], 4, *[5, 6, 7], **{"foo": 1}, bar=2, **{"baz": 3}):
                bar(x, y)
        """,
        """
        upg_args_2 = []
        upg_args_2.extend([1, 2, 3])
        upg_args_2.append(4)

        for x in upg_args_2:
            upg_args_0 = []
            upg_args_0.extend([1, 2, 3])
            upg_args_0.append(4)
            upg_args_0.extend([5, 6, 7])

            upg_kwargs_1 = {}
            upg_kwargs_1.update({"foo": 1})
            upg_kwargs_1["bar"] = 2
            upg_kwargs_1.update({"baz": 3})

            for y in foo(*upg_args_0, **upg_kwargs_1):
                bar(x, y)

            del upg_args_0
            del upg_kwargs_1

        del upg_args_2
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        with foo(*[1, 2, 3], 4) as x:
            pass
        """,
        """
        upg_args_0 = []
        upg_args_0.extend([1, 2, 3])
        upg_args_0.append(4)
        with foo(*upg_args_0) as x:
            pass
        del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        a = [*[1, 2, *[3, 4], 5], 6]
        """,
        """
        upg_args_0 = []
        upg_args_1 = []
        upg_args_1.append(1)
        upg_args_1.append(2)
        upg_args_1.extend([3, 4])
        upg_args_1.append(5)
        upg_args_0.extend(upg_args_1)
        del upg_args_1
        upg_args_0.append(6)
        a = upg_args_0
        del upg_args_0
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        def foo(l):
            return [*[1, 2, *l, 5], 6]
        """,
        """
        def foo(l):
            upg_args_0 = []
            upg_args_1 = []
            upg_args_1.append(1)
            upg_args_1.append(2)
            upg_args_1.extend(l)
            upg_args_1.append(5)
            upg_args_0.extend(upg_args_1)
            del upg_args_1
            upg_args_0.append(6)
            return upg_args_0
            # NOTE (mb 2018-06-24): No del at end of function
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        lambda x: [*x, 0]
        """,
        """
        def temp_lambda_as_def(x):
            upg_args_0 = []
            upg_args_0.extend(x)
            upg_args_0.append(0)
            return upg_args_0

        temp_lambda_as_def
        del temp_lambda_as_def
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        (lambda l: l.extend([*[1, 2, *l, 5], 6]))(*[1, 2, 3], 4)
        """,
        """
        upg_args_2 = []
        upg_args_2.extend([1, 2, 3])
        upg_args_2.append(4)

        def temp_lambda_as_def(l):
            upg_args_0 = []
            upg_args_1 = []
            upg_args_1.append(1)
            upg_args_1.append(2)
            upg_args_1.extend(l)
            upg_args_1.append(5)
            upg_args_0.extend(upg_args_1)
            del upg_args_1
            upg_args_0.append(6)
            return l.extend(upg_args_0)

        (temp_lambda_as_def)(*upg_args_2)
        del upg_args_2
        del temp_lambda_as_def
        """,
        # TODO (mb 2018-06-24): After simplification
        # """
        # def temp_lambda_as_def(l):
        #     upg_args_0 = [1, 2]
        #     upg_args_0.extend(l)
        #     upg_args_0.append(5)
        #     upg_args_0.append(6)
        #     return l.extend(upg_args_0)
        #
        # (temp_lambda_as_def)(1, 2, 3, 4)
        # del temp_lambda_as_def
        # """,
    ),
    FixerFixture(
        "unpacking_generalizations",
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
        upg_args_3 = []
        upg_args_3.extend([1, 2, 3])
        upg_args_3.append(4)
        with foo(*upg_args_3) as x:
            try:
                if bar:
                    pass
                else:
                    upg_args_0 = []
                    upg_args_1 = []
                    upg_args_1.append(1)
                    upg_args_1.append(2)
                    upg_args_1.extend([3, 4])
                    upg_args_1.append(5)
                    upg_args_0.extend(upg_args_1)
                    del upg_args_1
                    upg_args_0.append(6)
                    a = upg_args_0
                    del upg_args_0
            finally:
                upg_kwargs_2 = {}
                upg_kwargs_2.update({"x": 2})
                upg_kwargs_2["x"] = 1
                b = dict(**upg_kwargs_2)
                del upg_kwargs_2
        del upg_args_3
        """,
    ),
    FixerFixture(
        "unpacking_generalizations",
        """
        x = [*[1, 2], 3] if True else [*[4, 5], 6]
        """,
        """
        upg_args_0 = []
        upg_args_0.extend([1, 2])
        upg_args_0.append(3)
        upg_args_1 = []
        upg_args_1.extend([4, 5])
        upg_args_1.append(6)
        x = upg_args_0 if True else upg_args_1
        del upg_args_0
        del upg_args_1
        """,
    ),
    FixerFixture(
        "range_to_xrange",
        """
        myrange = range
        """,
        """
        myrange = xrange
        """
    ),
    FixerFixture(
        "range_to_xrange",
        """
        def foo():
            if True:
                for x in range(9):
                    print(x)
        """,
        """
        def foo():
            if True:
                for x in xrange(9):
                    print(x)
        """
    ),
    # FixerFixture(
    #     "generator_return_to_stop_iteration_exception",
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
    print(repr(test_source))
    print("--------" * 9)
    print(test_ast)
    print(">>>>>>>>" * 9)

    print("????????" * 9)
    print(repr(expected_header))
    print(expected_source)
    print("--------" * 9)
    print(expected_ast)
    print("????????" * 9)

    cfg = {"fixers": fixture.names}
    result_coding, result_header, result_source = utils.transpile_and_dump(test_source, cfg)
    result_ast = utils.parsedump_ast(result_source)

    print("<<<<<<<<" * 9)
    print(repr(result_header))
    print(repr(result_source))
    print(result_source)
    print("--------" * 9)
    print(result_ast)
    print("<<<<<<<<" * 9)

    assert result_coding == expected_coding
    assert result_header == expected_header

    assert result_ast == expected_ast
    assert _normalized_source(result_source) == _normalized_source(expected_source)
