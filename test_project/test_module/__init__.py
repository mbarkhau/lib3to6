# This file is part of the lib3to6 project
# https://github.com/mbarkhau/lib3to6
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT
"""A docstring.

This is a grab bag of test cases that should run on all supported
versions of python. As such, some fixers that are only applied for
newer versions of python are not covered.

If you're feeling adventerous, you could try to generate this file
based on the fixtures in test/test_checkers.py
"""

import typing

assert __doc__.startswith("A docstring.")

x = [*[1, 2], 3]
(
    lambda l: l.extend([*[1, 2, *l, 4], 5])
)(x)
assert x == [1, 2, 3, 1, 2, 1, 2, 3, 4, 5]

class Foo:

    @classmethod
    def foo(f: 'Foo') -> 'Foo':
        pass


class Bar(typing.NamedTuple):
    x: int
    y: str


res = ""
x = 10
while (x := x - 1) > 0:
    res += str(x)
    assert len(res) < 10

assert res == "987654321"


def test_unpacking_generalization(*args, **kwargs):
    return args, kwargs


def kwonly_func(*, kwonly_arg=1):
    return kwonly_arg * 2


assert kwonly_func() == 2
assert kwonly_func(kwonly_arg=3) == 6

valid_error_messages = [
    "kwonly_func() takes 0 positional arguments but 1 was given",
    "kwonly_func() takes exactly 0 arguments (1 given)",
]

try:
    kwonly_func(3)
    assert False
except TypeError as err:
    assert any(msg in str(err) for msg in valid_error_messages)



a: typing.List[int] = [1, 2, 3]
b = [4, 5, 6]
x = {"x": 11}
z = {"z": 33}


args, kwargs = test_unpacking_generalization(0, *a, *b, 7, 8, **x, y=22, **z)
assert args == (0, 1, 2, 3, 4, 5, 6, 7, 8)
assert kwargs == {"x": 11, "y": 22, "z": 33}


okfail = "ok"

print(f"all {okfail}")
