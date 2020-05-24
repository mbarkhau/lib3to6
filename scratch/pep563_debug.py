from __future__ import annotations

from typing import List, Tuple

class Foo:

    foo: Foo
    foos: List[Foo]
    foo_item: Tuple[Foo, Tuple[Tuple[Foo, Bar], Foo]]

    @staticmethod
    def doer(foo: Foo, *foos: Foo, **kwfoos: Foo) -> Foo:
        def nested_doer(foo: Foo) -> Tuple[Tuple[Foo, Bar], Bar]:
            return ...
        return ...


class Bar:
    pass


def bar(b: Bar, s: str) -> Bar:
    ...
