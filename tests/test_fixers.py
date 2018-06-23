import pytest

from three2six import transpile
from . import test_util


def test_numeric_literals_with_underscore():
    # NOTE (mb 2018-06-14): We don't need to transpile here
    #   this case is taken care off by the fact that there
    #   is no representation of the underscores at the ast
    #   level.
    a_ast = test_util.parsedump_ast("x = 200_000_000")
    b_ast = test_util.parsedump_ast("x = 200000000")
    assert a_ast == b_ast


def test_header_preserved():
    in_str = """
    #!/usr/bin/env python
    # This file is part of the three2six project
    # https://github.com/mbarkhau/three2six
    # (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
    #
    # SPDX-License-Identifier:    MIT
    hello = "world"
    """
    expected_str = """
    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    # This file is part of the three2six project
    # https://github.com/mbarkhau/three2six
    # (C) 2018 Manuel Barkhau <mbarkhau@gmail.com>
    #
    # SPDX-License-Identifier:    MIT
    from __future__ import unicode_literals
    from __future__ import print_function
    from __future__ import division
    from __future__ import absolute_import
    hello = "world"
    """
    in_coding, in_header, result_str = test_util.transpile_and_dump(in_str)
    expected_ast = test_util.parsedump_ast(expected_str)
    result_ast = test_util.parsedump_ast(result_str)
    assert expected_ast == result_ast


TEST_STRINGS = {
    ",".join([
        "absolute_import_future",
        "division_future",
        "print_function_future",
        "unicode_literals_future",
    ]): (
        """
        #!/usr/bin/env python
        \"\"\"Module Docstring\"\"\"
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        \"\"\"Module Docstring\"\"\"
        from __future__ import unicode_literals
        from __future__ import print_function
        from __future__ import division
        from __future__ import absolute_import
        """,
    ),
    "remove_ann_assign": (
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
    "remove_function_def_annotations": (
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
    "f_string_to_str_format": (
        "val = 33; f\"prefix {val / 2:>{3 * 3}} suffix\"",
        "val = 33; \"prefix {0:>{1}} suffix\".format(val / 2, 3 * 3)",
    ),
    "f_string_to_str_format": (
        """
        who = "World"
        print(f"Hello {who}!")
        """,
        """
        who = "World"
        print("Hello {0}!".format(who))
        """,
    ),
    "new_style_classes": (
        """
        class Foo:
            pass
        """,
        """
        class Foo(object):
            pass
        """,
    ),
    "itertools_builtins,print_function_future,1": (
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
    "itertools_builtins,2": (
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
    "itertools_builtins,3": (
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
    "short_to_long_form_super": (
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
    "remove_function_def_annotations,inline_kw_only_args": (
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
    "unpacking_generalizations,1": (
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
    "unpacking_generalizations,2": (
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
    "unpacking_generalizations,3": (
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
    "unpacking_generalizations,4": (
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
    "unpacking_generalizations,5": (
        """
        [*[1, 2], 3, *[4, 5]]
        {*[1, 2], 3, *[4, 5]}
        (*[1, 2], 3, *[4, 5])
        """,
        """
        upg_args_0 = []
        upg_args_0.extend([1, 2])
        upg_args_0.append(3)
        upg_args_0.extend([4, 5])
        list(*upg_args_0)
        del upg_args_0

        upg_args_1 = []
        upg_args_1.extend([1, 2])
        upg_args_1.append(3)
        upg_args_1.extend([4, 5])
        set(*upg_args_1)
        del upg_args_1

        upg_args_2 = []
        upg_args_2.extend([1, 2])
        upg_args_2.append(3)
        upg_args_2.extend([4, 5])
        tuple(*upg_args_2)
        del upg_args_2
        """,
    ),
    "unpacking_generalizations,6": (
        """
        for x in [*[1, 2, 3], 4]:
            for y in foo(*[1, 2, 3], 4, *[5, 6, 7], **{"foo": 1}, bar=2, **{"baz": 3}):
                bar(x, y)
        """,
        """
        upg_args_2 = []
        upg_args_2.extend([1, 2, 3])
        upg_args_2.append(4)

        for x in list(*upg_args_2):
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
    "unpacking_generalizations,7": (
        """
        with foo(*[1,2,3], 4) as x:
            pass
        """,
        """
        upg_args_0 = []
        upg_args_0.extend([1,2,3])
        upg_args_0.append(4)
        with foo(*upg_args_0) as x:
            pass
        del upg_args_0
        """,
    ),
    "unpacking_generalizations,8": (
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
        upg_args_0.extend(list(*upg_args_1))
        del upg_args_1
        upg_args_0.append(6)
        a = list(*upg_args_0)
        del upg_args_0
        """,
    ),
    "unpacking_generalizations,9": (
        """
        with foo(*[1,2,3], 4) as x:
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
        upg_args_3.extend([1,2,3])
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
                    upg_args_0.extend(list(*upg_args_1))
                    del upg_args_1
                    upg_args_0.append(6)
                    a = list(*upg_args_0)
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
    # "generator_return_to_stop_iteration_exception": (
    #     """
    #     """,
    #     """
    #     """,
    # ),
}


@pytest.mark.parametrize("test_desc, fixture", list(TEST_STRINGS.items()))
def test_fixers(test_desc, fixture):
    fixer_names = [
        name
        for name in test_desc.split(",")
        if not name.isdigit()
    ]
    cfg = {"fixers": ",".join(fixer_names)}

    in_str, expected_str = fixture

    expected_str = test_util.clean_whitespace(expected_str)
    expected_ast = test_util.parsedump_ast(expected_str)
    expected_data = expected_str.encode("utf-8")
    expected_coding, expected_header = transpile.parse_module_header(expected_data)

    print(expected_ast)

    in_coding, in_header, result_str = test_util.transpile_and_dump(in_str, cfg)

    assert in_coding == expected_coding
    assert in_header == expected_header

    # if fixer_names != "remove_functiond_def_annotations":
    #     return

    # print()
    # print(in_str)
    # print("###" * 20)
    # print(test_util.parsedump_ast(in_str))
    # print("###" * 20)
    # print(test_util.parsedump_ast(expected_str))
    # print("###" * 20)
    # print(test_util.parsedump_ast(result_str))

    in_source = test_util.parsedump_source(in_str)
    expected_source = test_util.parsedump_source(expected_str)
    result_source = test_util.parsedump_source(result_str)
    print(">>>>>>>>" * 9)
    print(in_source)
    print("????????" * 9)
    print(expected_source)
    print("????????" * 9)
    print(result_source)
    print("<<<<<<<<" * 9)
    assert expected_source == result_source
