'''This is a doc string.

This is a test file to debug https://gitlab.com/mbarkhau/lib3to6/-/issues/4
You should get syntactically correct python3.6 when running this command:

$ lib3to6 --target-version=3.6 scratch/pep563.py

'''
from __future__ import annotations

import typing
# from typing import List, Tuple


def bar(foos: typing.Optional[typing.Sequence[Foo, str, Foo, str], Foo, str, Foo, m.Bar]):
    pass


def baz(x: typing.Optional):
    pass


def before_foo(foo: Optional[Sequence[Sequence[Foo]]]):
    ...


class Foo:

    foo: Foo
    foos: typing.List[Foo]
    foo_item: Tuple[Foo, Tuple[Tuple[Foo, Bar], 'Foo']]

    @staticmethod
    def doer(foo: Foo, *foos: Foo, **kwfoos: Foo) -> Foo:
        def nested_doer(foo: Foo) -> Tuple[Tuple[Foo, Bar], Bar]:
            return ...
        return ...


def after_foo(foo: Optional[Sequence[Sequence[Foo]]]):
    ...


class Bar:
    pass


def bar(b: Bar, s: str) -> Bar:
    ...
