import pytest

from three2six import transpile
from . import test_util


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
        '''Module Docstring'''
        """,
        """
        #!/usr/bin/env python
        # -*- coding: utf-8 -*-
        '''Module Docstring'''
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
        # -*- coding: utf-8 -*-
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
        # -*- coding: utf-8 -*-
        class Foo(object):
            pass
        """,
    ),
    "itertools_builtins,print_function_future": (
        """
        '''Module Docstring'''
        def fn(elem):
            return elem * 2

        list(map(fn, [1, 2, 3, 4]))
        dict(zip("abcd", [1, 2, 3, 4]))
        """,
        """
        # -*- coding: utf-8 -*-
        '''Module Docstring'''
        from __future__ import print_function
        import itertools

        def fn(elem):
            return elem * 2

        list(itertools.imap(fn, [1, 2, 3, 4]))
        dict(itertools.izip("abcd", [1, 2, 3, 4]))
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
    in_coding, in_header, result_str = test_util.transpile_and_dump(in_str, cfg)
    expected_str = test_util.clean_whitespace(expected_str)
    expected_data = expected_str.encode("utf-8")
    expected_coding, expected_header = transpile.parse_module_header(expected_data)

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

    expected_ast = test_util.parsedump_ast(expected_str)
    result_ast = test_util.parsedump_ast(result_str)
    assert expected_ast == result_ast
